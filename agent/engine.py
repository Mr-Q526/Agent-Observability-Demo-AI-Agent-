"""Agent 核心引擎 - 认知环路架构

Pipeline (根据 route_type 动态裁剪):
  intent:   Guardrails → NLU → Act → Output Guardrails
  skill:    Guardrails → NLU → Auto-Retrieve → Act → Reflect → Output Guardrails
  workflow: Guardrails → NLU → Auto-Retrieve → Observe → Plan → Act → Reflect → Output Guardrails

关键设计：
- NLU 路由到 intent / skill / workflow 三种类型
- Auto-Retrieve 根据意图自动检索相关知识/商品
- Plan 阶段由 LLM 生成多步执行计划（仅 workflow）
- Reflect 阶段检查执行结果质量
- LLM 全权决定调用哪些工具（ReAct 循环）
"""

import json
import re
import time
import copy
import uuid
from openai import OpenAI

from agent.tools import TOOL_SCHEMAS, TOOL_FUNCTIONS, SENSITIVE_TOOLS
from agent.config import agent_config
from agent import guardrails
from agent.memory import AgentMemory
from agent.logger import (
    log_store,
    RunLog,
    create_llm_call_step,
    create_tool_call_step,
    create_react_iteration_step,
    create_memory_note_step,
    create_state_snapshot_step,
)

# ========== 配置 ==========
import os

# --- LLM Client 初始化 ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    print("Warning: DEEPSEEK_API_KEY not found in environment variables.")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
TEMPERATURE = 0.3
MAX_REACT_ITERATIONS = 5

# ========== Client ==========
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)

# ========== System Prompt ==========
SYSTEM_PROMPT = """你是一个专业的电商智能客服助手。请用友好、专业的中文回复用户。

你有以下工具可以使用：
- search_products：搜索商品（按名称、类别等）
- get_product_detail：获取商品详情（需要商品ID如P001）
- get_order_info：查询订单信息（需要订单号如ORD001）
- apply_refund：申请退款（需要订单号和原因）⚠️ 敏感操作
- query_knowledge：查询知识库（退换货政策、运费、会员权益、支付方式、售后服务等）

使用规则：
1. 根据用户的需求选择合适的工具。如果用户想找商品，使用 search_products。
2. 如果用户想了解政策、运费、会员等，使用 query_knowledge。
3. 不要编造数据，必须通过工具获取真实信息。
4. 回复时使用自然语言，不要返回 JSON 格式。
5. 如果工具返回没有结果，诚实告知用户并建议替代方案。"""


# ========== 活跃记忆 (由 conversation manager 切换) ==========
agent_memory = AgentMemory()

def set_active_memory(memory: AgentMemory):
    """切换活跃记忆到指定会话的记忆"""
    global agent_memory
    agent_memory = memory

def get_active_memory() -> AgentMemory:
    return agent_memory


def _print_llm_request(messages, model=MODEL, temperature=TEMPERATURE, tools=None, label="ReAct"):
    """打印发送给大模型的完整请求"""
    print(f"\n{'='*60}")
    print(f"📤 LLM 请求 [{label}]  model={model}  temp={temperature}")
    print(f"{'='*60}")
    for i, m in enumerate(messages):
        role = m.get('role', '?')
        content = m.get('content', '')
        tc = m.get('tool_calls')
        tid = m.get('tool_call_id', '')
        icons = {'system':'📜','user':'👤','assistant':'🤖','tool':'🔧'}
        icon = icons.get(role, '❓')
        print(f"  [{i}] {icon} {role}")
        if content:
            for line in str(content).split('\n'):
                print(f"      {line}")
        if tc:
            for call in tc:
                fn = call.get('function', {})
                print(f"      → tool_call: {fn.get('name','')}({fn.get('arguments','')})")
        if tid:
            print(f"      ← tool_call_id: {tid}")
    if tools:
        names = [t['function']['name'] for t in tools if 'function' in t]
        print(f"  🛠️  tools: [{', '.join(names)}]")
    print(f"{'='*60}\n")


def _get_checkpoint(messages, total_tool_calls, total_tokens, pending=None):
    return {
        "messages_snapshot": copy.deepcopy(messages),
        "state": {
            "current_messages_count": len(messages),
            "total_tool_calls_so_far": total_tool_calls,
            "accumulated_tokens": total_tokens,
            "pending_confirmation": pending,
            "session_context": {
                "memory_note": agent_memory.note.content[:100] if agent_memory.note.content else "",
            },
        },
    }


def _update_memory_note(run_log: RunLog, user_input: str, response: str, tool_result: str = None):
    """调 LLM 更新记忆笔记（滚动摘要），并记录为可观测步骤"""
    before_content = agent_memory.note.content or ""
    current_note = before_content or "无"
    tool_info = f"\n工具结果: {tool_result[:200]}" if tool_result else ""

    prompt = f"""你是记忆管理助手。根据最新对话更新记忆笔记。
规则：
- 保留重要信息（用户偏好、推荐过的商品、操作结果）
- 删除已过时的细节
- 控制在 100 字内
- 只输出更新后的笔记内容，不要其他文字

【当前笔记】{current_note}

【最新对话】
用户: {user_input[:100]}
AI: {response[:150]}{tool_info}

请输出更新后的笔记："""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )
        new_note = resp.choices[0].message.content.strip()
        agent_memory.note.update(new_note)
        run_log.total_tokens += resp.usage.total_tokens if resp.usage else 0
        print(f"  📝 记忆笔记 v{agent_memory.note.version}: {new_note[:80]}...")

        run_log.add_step(create_memory_note_step(
            before=before_content,
            after=new_note,
            version=agent_memory.note.version,
        ))
    except Exception as e:
        print(f"  ⚠️ 记忆笔记更新失败: {e}")


# ========== 认知环路阶段函数 ==========

def _auto_retrieve(user_input: str, intent: str, slots: dict, run_log: RunLog) -> dict:
    """③ Auto-Retrieve: 根据意图和 slots 自动检索相关上下文"""
    t0 = time.time()
    result = {
        "triggered": False,
        "collection": None,
        "query": None,
        "results": [],
        "results_count": 0,
        "retrieval_log": None,
        "rag_context": "",
        "duration_ms": 0,
    }

    # 决定是否触发检索以及使用哪个集合
    intent_to_collection = {
        "search_product": "products",
        "product_detail": "products",
        "compare_products": "products",
        "knowledge_query": "knowledge",
    }

    collection = intent_to_collection.get(intent)
    if not collection:
        result["duration_ms"] = round((time.time() - t0) * 1000, 2)
        return result

    # 构建检索 query — 优先用当前用户输入，避免使用上一轮残留的 slot
    slot_question = slots.get("question") or slots.get("query") or ""
    # 只有当 slot 值确实是从当前输入中提取的才使用，否则用原始输入
    query = slot_question if slot_question and slot_question in user_input else user_input
    result["triggered"] = True
    result["collection"] = collection
    result["query"] = query

    try:
        from agent.rag import rag_engine
        rag_result = rag_engine.retrieve(
            query=query,
            collection=collection,
            strategy="hybrid",
            top_k=5,
        )
        result["results"] = rag_result.get("results", [])
        result["results_count"] = len(result["results"])
        result["retrieval_log"] = rag_result.get("retrieval_log", {})

        # 构建 RAG context (滤除低分结果)
        rag_parts = []
        for r in result["results"][:3]:
            if r.get("score", 0) < 0.3:
                continue
            meta = r.get("metadata", {})
            text = meta.get("paragraph") or meta.get("full_content") or meta.get("description", "")
            if text:
                rag_parts.append(text)
        result["rag_context"] = "\n".join(rag_parts)

    except Exception as e:
        print(f"  ⚠️ Auto-Retrieve 失败: {e}")

    result["duration_ms"] = round((time.time() - t0) * 1000, 2)

    # 记录 trace step
    run_log.add_step({
        "type": "auto_retrieve",
        "auto_retrieve": result,
    })

    return result


def _observe(nlu_result, retrieve_result: dict, memory_context: str, run_log: RunLog) -> dict:
    """④ Observe: 整合所有上下文，形成观察报告"""
    t0 = time.time()

    observation = {
        "intent": nlu_result.intent,
        "route_type": nlu_result.route_type,
        "confidence": nlu_result.confidence,
        "slots": nlu_result.slots,
        "missing_slots": nlu_result.missing_slots,
        "has_retrieved_context": bool(retrieve_result.get("rag_context")),
        "retrieved_docs_count": retrieve_result.get("results_count", 0),
        "has_memory_context": bool(memory_context),
        "summary": "",
    }

    # 生成人类可读的观察摘要
    parts = [f"用户意图: {nlu_result.intent} (置信度 {nlu_result.confidence:.2f})"]
    if nlu_result.slots:
        slot_str = ", ".join(f"{k}={v}" for k, v in nlu_result.slots.items())
        parts.append(f"已识别参数: {slot_str}")
    if nlu_result.missing_slots:
        parts.append(f"缺失参数: {', '.join(nlu_result.missing_slots)}")
    if retrieve_result.get("rag_context"):
        parts.append(f"已检索到 {retrieve_result['results_count']} 条相关信息")
    if memory_context:
        parts.append("已加载用户记忆上下文")
    observation["summary"] = " | ".join(parts)

    observation["duration_ms"] = round((time.time() - t0) * 1000, 2)

    # 记录 trace step
    run_log.add_step({
        "type": "observe",
        "observe": observation,
    })

    return observation


def _plan(observation: dict, skill, user_input: str, run_log: RunLog) -> list[dict]:
    """⑤ Plan: 任务规划
    - workflow: 直接使用 skills.py 中预定义的结构化步骤（代码驱动，确定性）
    - skill / intent: 不需要计划
    """
    route_type = observation.get("route_type", "intent")

    if route_type != "workflow":
        return []

    t0 = time.time()

    # workflow: 直接读取预定义步骤，不调 LLM
    workflow_steps = skill.workflow_steps if skill else []
    slots = observation.get("slots", {})

    plan = []
    for ws in workflow_steps:
        if isinstance(ws, dict):
            entry = {**ws, "status": "pending"}
        else:
            # 兼容旧的字符串格式
            entry = {"step": len(plan) + 1, "action": "llm", "description": str(ws), "status": "pending"}
        plan.append(entry)

    duration = round((time.time() - t0) * 1000, 2)
    run_log.add_step({
        "type": "plan",
        "plan": {
            "route_type": route_type,
            "method": "deterministic",
            "steps": plan,
            "total_steps": len(plan),
            "duration_ms": duration,
        },
    })

    print(f"  🗺️ Plan (确定性, {len(plan)} 步): {[p['description'] for p in plan]}")
    return plan


def _resolve_slot_value(slot_ref: str, slots: dict):
    """解析 slot 引用，如 'product_ids[0]' → 实际值
    
    支持:
    - list 类型: product_ids = ["P001", "P003"] → product_ids[0] = "P001"
    - 字符串逗号分隔: product_ids = "P001,P003" → product_ids[0] = "P001"
    """
    import re as _re
    m = _re.match(r'^(.+)\[(\d+)\]$', slot_ref)
    if m:
        key, idx = m.group(1), int(m.group(2))
        val = slots.get(key)
        if val is None:
            return None
        # 如果是字符串（逗号或空格分隔），先拆成列表
        if isinstance(val, str):
            # 按逗号、空格、顿号分割
            parts = [p.strip() for p in _re.split(r'[,，、\s]+', val) if p.strip()]
            if idx < len(parts):
                return parts[idx]
            return None
        if isinstance(val, list) and idx < len(val):
            return val[idx]
        return None
    return slots.get(slot_ref)


def _execute_workflow(plan: list[dict], slots: dict, skill, safe_input: str,
                      final_sys_prompt: str, run_log: RunLog) -> tuple:
    """⑥-WF 确定性工作流执行器

    代码驱动的 for 循环：
    - action=tool: 代码直接调用工具函数，不经过 LLM
    - action=llm:  调 LLM 进行总结/生成

    Returns:
        (final_content, last_tool_result, total_tool_calls, total_tokens)
    """
    wf_results = []  # 收集每步的结果
    total_tool_calls = 0
    total_tokens = 0
    last_tool_result = None
    all_tool_results = []  # 收集所有工具结果用于幻觉检测
    final_content = ""
    wf_start = time.time()

    for step_def in plan:
        step_num = step_def.get("step", 0)
        action = step_def.get("action", "llm")
        desc = step_def.get("description", "")
        step_def["status"] = "running"

        step_start = time.time()

        if action == "tool":
            tool_name = step_def.get("tool", "")
            slot_ref = step_def.get("slot", "")
            slot_val = _resolve_slot_value(slot_ref, slots) if slot_ref else None

            # 构建工具参数
            func = TOOL_FUNCTIONS.get(tool_name)
            if func and slot_val is not None:
                # 根据工具类型构建参数
                if tool_name == "get_product_detail":
                    tool_args = {"product_id": slot_val}
                elif tool_name == "get_order_info":
                    tool_args = {"order_id": slot_val}
                elif tool_name == "search_products":
                    tool_args = {"keyword": slot_val}
                elif tool_name == "query_knowledge":
                    tool_args = {"question": slot_val}
                else:
                    tool_args = {"input": slot_val}

                try:
                    tool_result = func(**tool_args)
                except Exception as e:
                    tool_result = {"error": f"工具执行出错: {str(e)}"}

                total_tool_calls += 1
                duration_ms = (time.time() - step_start) * 1000
                tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                last_tool_result = tool_result_str
                all_tool_results.append(tool_result_str)

                step_def["status"] = "done"
                wf_results.append({
                    "step": step_num,
                    "action": "tool",
                    "tool": tool_name,
                    "description": desc,
                    "args": tool_args,
                    "result": tool_result,
                    "duration_ms": round(duration_ms, 2),
                })

                # 不记录单独的 tool trace step — 全部汇聚到 workflow_execution 里

                print(f"  ⚙️ WF Step {step_num}: {tool_name}({tool_args}) → {len(tool_result_str)} chars")

            else:
                step_def["status"] = "error"
                err_msg = f"工具 '{tool_name}' 无法执行: slot '{slot_ref}' 未找到值"
                wf_results.append({
                    "step": step_num, "action": "tool",
                    "tool": tool_name, "description": desc, "error": err_msg,
                    "duration_ms": round((time.time() - step_start) * 1000, 2),
                })
                print(f"  ⚠️ WF Step {step_num}: {err_msg}")

        elif action == "llm":
            # LLM 步骤: 汇总前面工具结果，生成最终回复
            tool_context = ""
            for wr in wf_results:
                if wr.get("result"):
                    tool_context += f"\n【步骤{wr['step']}结果 ({wr.get('tool','')})】\n{json.dumps(wr['result'], ensure_ascii=False, indent=2)}\n"

            llm_prompt = f"{desc}\n\n{tool_context}"
            messages = [
                {"role": "system", "content": final_sys_prompt},
                {"role": "user", "content": safe_input},
                {"role": "assistant", "content": f"好的，我已经收集了所有需要的信息。"},
                {"role": "user", "content": llm_prompt},
            ]

            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=TEMPERATURE,
                )
                final_content = resp.choices[0].message.content or ""
                usage_tokens = resp.usage.total_tokens if resp.usage else 0
                total_tokens += usage_tokens
                run_log.total_tokens += usage_tokens

                step_def["status"] = "done"
                duration_ms = (time.time() - step_start) * 1000

                wf_results.append({
                    "step": step_num, "action": "llm",
                    "description": desc,
                    "response_preview": final_content[:300],
                    "duration_ms": round(duration_ms, 2),
                    "tokens": usage_tokens,
                    "llm_prompt": llm_prompt[:500],
                    "usage": {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens, "total_tokens": usage_tokens} if resp.usage else {},
                })

                # 不记录单独的 llm_call trace step — 全部汇聚到 workflow_execution 里

                print(f"  🤖 WF Step {step_num}: LLM 生成 {len(final_content)} chars")

            except Exception as e:
                step_def["status"] = "error"
                final_content = f"分析过程出错: {str(e)}"
                wf_results.append({
                    "step": step_num, "action": "llm", "description": desc, "error": str(e),
                    "duration_ms": round((time.time() - step_start) * 1000, 2),
                })

    # 记录完整的 workflow_execution trace
    wf_duration = round((time.time() - wf_start) * 1000, 2)
    run_log.add_step({
        "type": "workflow_execution",
        "workflow_execution": {
            "mode": "deterministic",
            "total_steps": len(plan),
            "completed_steps": sum(1 for s in plan if s.get("status") == "done"),
            "steps": wf_results,
            "duration_ms": wf_duration,
        },
    })

    if not final_content:
        final_content = "工作流执行完成，但未能生成最终分析。"

    return final_content, last_tool_result, total_tool_calls, total_tokens, all_tool_results


def _reflect(plan: list[dict], final_content: str, user_input: str,
             last_tool_result: str, run_log: RunLog) -> dict:
    """⑦ Reflect: 反思执行结果"""
    t0 = time.time()

    reflection = {
        "plan_steps": len(plan),
        "has_response": bool(final_content),
        "quality": "unknown",
        "needs_retry": False,
        "details": "",
        "method": "rule",
    }

    if not plan:
        # 无计划（intent 类型）不执行反思
        return {}

    # 规则检查
    if not final_content or len(final_content) < 10:
        reflection["quality"] = "poor"
        reflection["details"] = "回复内容过短或为空"
        reflection["needs_retry"] = True
    elif last_tool_result and "error" in str(last_tool_result).lower():
        reflection["quality"] = "warning"
        reflection["details"] = "工具执行出现错误"
    else:
        reflection["quality"] = "good"
        reflection["details"] = "执行结果正常，回复内容充分"

    reflection["duration_ms"] = round((time.time() - t0) * 1000, 2)

    # 记录 trace step
    run_log.add_step({
        "type": "reflect",
        "reflect": reflection,
    })

    return reflection


# ========== 主入口 ==========

def run_agent(user_input: str) -> dict:
    """
    Agent 主入口 - 认知环路架构。
    根据 route_type 动态裁剪 pipeline:
      intent:   Guardrails → NLU → Act → Output Guardrails
      skill:    Guardrails → NLU → Auto-Retrieve → Act → Reflect → Output Guardrails
      workflow: Guardrails → NLU → Auto-Retrieve → Observe → Plan → Act → Reflect → Output Guardrails
    """
    run_log = log_store.create_run(user_input)
    total_tool_calls = 0

    # =========================================
    # ① Input Guardrails
    # =========================================
    input_guard = guardrails.check_input(user_input)
    run_log.add_step({
        "type": "guardrail",
        "guardrail": {
            "direction": "input",
            **input_guard.to_dict(),
        },
    })

    if input_guard.blocked:
        run_log.finish(input_guard.block_reason)
        return {"run_id": run_log.run_id, "response": input_guard.block_reason, "status": "blocked"}

    safe_input = input_guard.sanitized_input or user_input

    # =========================================
    # ② NLU 解析 (Intent Routing + Slot Filling)
    # =========================================
    from agent.nlu import classify
    from agent.skills import SKILLS
    nlu_res = classify(user_input, agent_memory.working.to_dict())

    # 记录 NLU Trace
    run_log.add_step({
        "type": "nlu",
        "nlu": nlu_res.to_dict()
    })

    # 更新工作记忆
    agent_memory.working.current_intent = nlu_res.intent
    for k, v in nlu_res.slots.items():
        agent_memory.working.slots[k] = v

    route_type = nlu_res.route_type
    skill = SKILLS.get(nlu_res.intent)

    # =========================================
    # ③ Auto-Retrieve (skill / workflow 触发)
    # =========================================
    retrieve_result = {}
    rag_context = ""
    if route_type in ("skill", "workflow"):
        retrieve_result = _auto_retrieve(safe_input, nlu_res.intent, nlu_res.slots, run_log)
        rag_context = retrieve_result.get("rag_context", "")

    # =========================================
    # ④ Observe (仅 workflow 触发)
    # =========================================
    observation = {}
    memory_ctx = agent_memory.get_memory_context()
    if route_type == "workflow":
        observation = _observe(nlu_res, retrieve_result, memory_ctx, run_log)

    # =========================================
    # ⑤ Plan (仅 workflow 触发; 确定性步骤)
    # =========================================
    plan = []
    if route_type in ("skill", "workflow"):
        plan = _plan(
            observation if observation else {"intent": nlu_res.intent, "route_type": route_type, "slots": nlu_res.slots},
            skill, safe_input, run_log,
        )

    # =========================================
    # ⑥ Prompt Assembly
    # =========================================
    base_sys = SYSTEM_PROMPT.strip()
    skill_sys = skill.system_prompt if skill else ""

    # 将缺失 slots 通过 prompt 注入
    missing_ctx = ""
    if nlu_res.missing_slots:
        missing_ctx = f"\n\n【缺失信息追问】\n为了处理该意图，你还需要向用户询问以下信息：{', '.join(nlu_res.missing_slots)}。请引导用户提供。"

    # 注入检索上下文
    rag_ctx_prompt = ""
    if rag_context:
        rag_ctx_prompt = f"\n\n【检索到的相关信息】\n{rag_context}"

    # 注入执行计划（仅用于 prompt 可见性，workflow 实际由代码驱动）
    plan_ctx = ""
    if plan and route_type == "workflow":
        plan_text = "\n".join(f"{p['step']}. {p['description']}" for p in plan)
        plan_ctx = f"\n\n【执行计划（代码驱动）】\n以下步骤将由系统自动执行：\n{plan_text}"

    sys_parts = [base_sys]
    if skill_sys:
        sys_parts.append(f"【当前意图专属规则】\n{skill_sys}")
    if memory_ctx:
        sys_parts.append(memory_ctx)
    if missing_ctx:
        sys_parts.append(missing_ctx)
    if rag_ctx_prompt:
        sys_parts.append(rag_ctx_prompt)
    if plan_ctx:
        sys_parts.append(plan_ctx)

    final_sys_prompt = "\n\n".join(sys_parts)

    messages = [
        {"role": "system", "content": final_sys_prompt},
        {"role": "user", "content": safe_input},
    ]

    # 记录 Prompt Assembly Trace
    run_log.add_step({
        "type": "prompt_assembly",
        "assembly": {
            "base_prompt": base_sys,
            "skill_prompt": skill_sys,
            "memory_context": memory_ctx,
            "missing_slots_context": missing_ctx,
            "rag_context": rag_ctx_prompt,
            "plan_context": plan_ctx,
            "final_prompt": final_sys_prompt,
        }
    })

    # 记录记忆快照
    run_log.add_step({
        "type": "memory",
        "memory": agent_memory.to_dict(),
    })

    # 记录 State 快照（开始）
    run_log.add_step(create_state_snapshot_step(
        label="开始",
        memory_dict=agent_memory.to_dict(),
        messages_count=len(messages),
    ))

    # =========================================
    # ⑥ Act: Workflow (代码驱动) vs ReAct (LLM 驱动)
    # =========================================
    run_start_time = time.time()

    if route_type == "workflow" and plan:
        # ====== 确定性工作流执行 ======
        final_content, last_tool_result, total_tool_calls, wf_tokens, all_tool_results = _execute_workflow(
            plan=plan,
            slots=nlu_res.slots,
            skill=skill,
            safe_input=safe_input,
            final_sys_prompt=final_sys_prompt,
            run_log=run_log,
        )
        run_log.total_tokens += wf_tokens
        iteration = len(plan)  # for state snapshot

    else:
        # ====== ReAct Loop (LLM 自主决策) ======
        final_content = ""
        last_tool_result = None
        all_tool_results = []  # 收集所有工具结果用于幻觉检测
        iteration = 0

        while iteration < MAX_REACT_ITERATIONS:
            iteration += 1

            _print_llm_request(messages, MODEL, TEMPERATURE, tools=TOOL_SCHEMAS, label=f"ReAct #{iteration}")

            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=TEMPERATURE,
                    tools=TOOL_SCHEMAS,
                )
            except Exception as e:
                error_msg = f"LLM 调用失败: {str(e)}"
                run_log.finish(error_msg)
                return {"run_id": run_log.run_id, "response": error_msg, "status": "error"}

            choice = response.choices[0]
            content = choice.message.content or ""
            tool_calls = choice.message.tool_calls
            finish_reason = choice.finish_reason
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            run_log.total_tokens += usage.get("total_tokens", 0)

            # prompt cache 统计
            cache_info = None
            if hasattr(response.usage, "prompt_cache_hit_tokens"):
                cache_info = {
                    "cache_hit_tokens": response.usage.prompt_cache_hit_tokens,
                    "cache_miss_tokens": response.usage.prompt_cache_miss_tokens if hasattr(response.usage, "prompt_cache_miss_tokens") else None,
                }

            # 序列化 tool_calls 用于日志
            serialized_tool_calls = None
            if tool_calls:
                serialized_tool_calls = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in tool_calls
                ]

            # 记录 LLM 调用步骤
            llm_step = create_llm_call_step(
                messages=messages,
                tools=TOOL_SCHEMAS,
                model=MODEL,
                temperature=TEMPERATURE,
                response_content=content,
                response_tool_calls=serialized_tool_calls,
                finish_reason=finish_reason,
                usage=usage,
                checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
            )
            if cache_info:
                llm_step["prompt_cache"] = cache_info
            run_log.add_step(llm_step)

            # ---- 决策分支 ----

            if tool_calls and len(tool_calls) > 0:
                tool_names = [tc.function.name for tc in tool_calls]

                run_log.add_step(create_react_iteration_step(
                    iteration=iteration,
                    decision="tool_call",
                    tool_names=tool_names,
                    thought=content if content else None,
                    checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
                ))

                assistant_msg = {"role": "assistant", "content": content or None, "tool_calls": serialized_tool_calls}
                messages.append(assistant_msg)

                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        tool_args = {}

                    # === 敏感操作检查 ===
                    if tool_name in SENSITIVE_TOOLS:
                        desc = f"即将执行【{tool_name}】，参数: {json.dumps(tool_args, ensure_ascii=False)}"
                        run_log.status = "awaiting_confirmation"
                        run_log.pending_confirmation = {
                            "tool_call_id": tc.id,
                            "tool_name": tool_name,
                            "arguments": tool_args,
                            "messages_snapshot": copy.deepcopy(messages),
                        }

                        ask_confirm = f"⚠️ 需要您确认以下操作：\n工具：{tool_name}\n参数：{json.dumps(tool_args, ensure_ascii=False)}\n请回复确认或取消。"
                        return {
                            "run_id": run_log.run_id,
                            "response": ask_confirm,
                            "status": "awaiting_confirmation",
                            "confirmation_info": {
                                "tool_name": tool_name,
                                "arguments": tool_args,
                                "description": desc,
                            },
                        }

                    # === 执行工具 ===
                    func = TOOL_FUNCTIONS.get(tool_name)
                    total_tool_calls += 1
                    start_time = time.time()

                    if func:
                        try:
                            tool_result = func(**tool_args)
                        except Exception as e:
                            tool_result = {"error": f"工具执行出错: {str(e)}"}
                    else:
                        tool_result = {"error": f"未知工具: {tool_name}"}

                    duration_ms = (time.time() - start_time) * 1000
                    tool_result_str = json.dumps(tool_result, ensure_ascii=False, indent=2)
                    last_tool_result = tool_result_str
                    all_tool_results.append(tool_result_str)

                    # 记录 tool 执行步骤
                    tool_step = create_tool_call_step(
                        tool_name=tool_name,
                        arguments=tool_args,
                        result=tool_result,
                        duration_ms=duration_ms,
                        checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
                    )
                    run_log.add_step(tool_step)

                    # 将工具结果追加到 messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result_str,
                    })

                continue

            else:
                if content:
                    final_content = content
                else:
                    final_content = "抱歉，我暂时无法处理您的请求。请尝试换一种方式描述您的需求，或联系人工客服。"

                run_log.add_step(create_react_iteration_step(
                    iteration=iteration,
                    decision="final_answer",
                    checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
                ))
                break

        # 如果循环耗尽仍无结果
        if not final_content:
            final_content = "抱歉，处理过程过于复杂，请尝试简化您的问题或联系人工客服。"
            run_log.add_step(create_react_iteration_step(
                iteration=iteration,
                decision="fallback",
                checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
            ))

    # 清理可能的 JSON/代码块包裹
    clean = final_content
    if clean.startswith("```"):
        clean = re.sub(r'```\w*\s*', '', clean).strip().rstrip('`').strip()

    # =========================================
    # ⑦ Reflect (skill / workflow 触发)
    # =========================================
    if route_type in ("skill", "workflow"):
        _reflect(plan, clean, safe_input, last_tool_result, run_log)

    # =========================================
    # ⑧ Output Guardrails
    # =========================================
    combined_tool_results = "\n".join(all_tool_results) if all_tool_results else last_tool_result
    output_guard = guardrails.check_output(clean, combined_tool_results)
    run_log.add_step({
        "type": "guardrail",
        "guardrail": {
            "direction": "output",
            **output_guard.to_dict(),
        },
    })

    # =========================================
    # ⑨ Memory Update
    # =========================================
    agent_memory.complete_episode(
        intent="react_loop",
        slots={},
        user_input=run_log.user_input,
        response=clean,
        tool_name=None,
        tool_result=str(last_tool_result)[:200] if last_tool_result else None,
    )

    _update_memory_note(
        run_log=run_log,
        user_input=run_log.user_input,
        response=clean,
        tool_result=str(last_tool_result)[:200] if last_tool_result else None,
    )

    # 记录 State 快照（结束）
    run_log.add_step(create_state_snapshot_step(
        label="结束",
        memory_dict=agent_memory.to_dict(),
        messages_count=len(messages),
        iteration=iteration,
        total_tool_calls=total_tool_calls,
        total_tokens=run_log.total_tokens,
        elapsed_ms=(time.time() - run_start_time) * 1000,
    ))

    run_log.finish(clean)
    return {"run_id": run_log.run_id, "response": clean, "status": "completed"}


def confirm_action(run_id: str, confirmed: bool) -> dict:
    """用户确认/拒绝敏感操作后继续 ReAct 循环。"""
    run_log = log_store.get_run(run_id)
    if not run_log:
        return {"error": f"Run {run_id} 不存在"}

    if run_log.status != "awaiting_confirmation":
        return {"error": f"Run {run_id} 不在等待确认状态"}

    pending = run_log.pending_confirmation
    if not pending:
        return {"error": "没有待确认的操作"}

    tool_name = pending["tool_name"]
    arguments = pending["arguments"]
    tool_call_id = pending.get("tool_call_id", "call_manual")
    messages = pending.get("messages_snapshot", [])

    total_tool_calls = sum(1 for s in run_log.steps if s["type"] in ("tool_call", "awaiting_confirmation"))

    if confirmed:
        func = TOOL_FUNCTIONS.get(tool_name)
        start_time = time.time()
        if func:
            try:
                result = func(**arguments)
            except Exception as e:
                result = {"error": f"工具执行出错: {str(e)}"}
        else:
            result = {"error": f"未知工具: {tool_name}"}
        duration_ms = (time.time() - start_time) * 1000

        total_tool_calls += 1
        tool_result_str = json.dumps(result, ensure_ascii=False, indent=2)

        from agent.logger import create_user_confirmed_step
        confirmed_step = create_user_confirmed_step(
            confirmed=True,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
        )
        run_log.add_step(confirmed_step)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": tool_result_str,
        })

        run_log.status = "running"
        run_log.pending_confirmation = None

        try:
            _print_llm_request(messages, MODEL, TEMPERATURE, tools=TOOL_SCHEMAS, label="确认后回复")
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=TEMPERATURE,
                tools=TOOL_SCHEMAS,
            )
            choice = response.choices[0]
            content = choice.message.content or "操作已完成。"
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            run_log.total_tokens += usage.get("total_tokens", 0)

            llm_step = create_llm_call_step(
                messages=messages, tools=TOOL_SCHEMAS, model=MODEL, temperature=TEMPERATURE,
                response_content=content, response_tool_calls=None, finish_reason=choice.finish_reason,
                usage=usage,
                checkpoint_state=_get_checkpoint(messages, total_tool_calls, run_log.total_tokens),
            )
            run_log.add_step(llm_step)
        except Exception as e:
            content = f"LLM 调用失败: {str(e)}"

        clean = content
        if clean.startswith("```"):
            clean = re.sub(r'```\w*\s*', '', clean).strip().rstrip('`').strip()

        output_guard = guardrails.check_output(clean, result)
        run_log.add_step({
            "type": "guardrail",
            "guardrail": {"direction": "output", **output_guard.to_dict()},
        })

        agent_memory.complete_episode(
            intent="react_loop",
            slots={},
            user_input=run_log.user_input,
            response=clean,
            tool_name=tool_name,
            tool_result=str(result)[:200],
        )
        _update_memory_note(
            run_log=run_log,
            user_input=run_log.user_input,
            response=clean,
            tool_result=str(result)[:200],
        )

        run_log.finish(clean)
        return {"run_id": run_log.run_id, "response": clean, "status": "completed"}

    else:
        from agent.logger import create_user_confirmed_step
        confirmed_step = create_user_confirmed_step(
            confirmed=False, tool_name=tool_name, arguments=arguments, result=None,
            checkpoint_state=_get_checkpoint([], total_tool_calls, run_log.total_tokens),
        )
        run_log.add_step(confirmed_step)

        run_log.status = "running"
        run_log.pending_confirmation = None

        cancel_msg = "好的，已取消操作。有其他需要可以随时告诉我。"
        run_log.finish(cancel_msg)
        return {"run_id": run_log.run_id, "response": cancel_msg, "status": "completed"}


def reset_session():
    global agent_memory
    agent_memory.reset()


def get_session_context() -> dict:
    return agent_memory.to_dict()
