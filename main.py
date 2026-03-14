"""FastAPI 服务入口"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from agent.engine import run_agent, confirm_action, reset_session, get_session_context, set_active_memory
from agent.logger import log_store
from agent.conversations import conv_manager
from agent.config import agent_config

app = FastAPI(title="Agent Observability Demo - 智能客服")


# ========== Request / Response Models ==========

class ChatRequest(BaseModel):
    message: str

class ConfirmRequest(BaseModel):
    run_id: str
    confirmed: bool

class RetrievalTestRequest(BaseModel):
    query: str
    collection: str = "knowledge"
    strategy: str = "hybrid"
    top_k: int = 5

class CompareRequest(BaseModel):
    query: str
    collection: str = "knowledge"
    top_k: int = 5

class ConfigRequest(BaseModel):
    nlu_mode: Optional[str] = None       # "embedding" | "llm"
    guardrails_mode: Optional[str] = None  # "regex" | "llm"


# ========== 会话管理 API ==========

@app.get("/api/conversations")
async def list_conversations():
    """获取所有对话列表"""
    return {
        "conversations": conv_manager.list_all(),
        "active_id": conv_manager.active_id,
    }


@app.post("/api/conversations/new")
async def new_conversation():
    """创建新对话"""
    conv = conv_manager.create()
    set_active_memory(conv.memory)
    return {"conversation": conv.to_summary(), "active_id": conv.id}


@app.post("/api/conversations/{conv_id}/switch")
async def switch_conversation(conv_id: str):
    """切换到指定对话"""
    conv = conv_manager.switch(conv_id)
    if not conv:
        return {"error": f"对话 {conv_id} 不存在"}
    set_active_memory(conv.memory)
    return {
        "conversation": conv.to_dict(),
        "active_id": conv.id,
    }


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """获取对话详情（含消息历史）"""
    conv = conv_manager.get(conv_id)
    if not conv:
        return {"error": f"对话 {conv_id} 不存在"}
    return conv.to_dict()


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """删除对话"""
    ok = conv_manager.delete(conv_id)
    if not ok:
        return {"error": f"对话 {conv_id} 不存在"}
    # 如果删除的是当前对话，切换到另一个或创建新的
    if not conv_manager.active_id:
        all_convs = conv_manager.list_all()
        if all_convs:
            new_active = conv_manager.switch(all_convs[0]["id"])
            set_active_memory(new_active.memory)
        else:
            conv = conv_manager.create()
            set_active_memory(conv.memory)
    return {"status": "ok", "active_id": conv_manager.active_id}


# ========== Chat API (关联到当前活跃对话) ==========

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """发送用户消息，运行 Agent"""
    conv = conv_manager.get_active()
    set_active_memory(conv.memory)

    # 保存用户消息
    conv.add_message("user", req.message)
    conv.auto_title(req.message)

    result = run_agent(req.message)

    # 保存助手消息 & 关联 run
    conv.add_message("assistant", result.get("response", ""))
    conv.add_run(result["run_id"])
    conv_manager.save()

    return result


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    """用户确认/拒绝敏感操作"""
    conv = conv_manager.get_active()
    set_active_memory(conv.memory)

    result = confirm_action(req.run_id, req.confirmed)

    # 保存确认结果消息
    conv.add_message("assistant", result.get("response", ""))
    conv_manager.save()

    return result


@app.get("/api/runs")
async def list_runs():
    """获取当前对话关联的 run 列表"""
    conv = conv_manager.get_active()
    # 只返回当前对话的 runs
    all_runs = log_store.list_runs()
    conv_runs = [r for r in all_runs if r["run_id"] in conv.run_ids]
    return {"runs": conv_runs}


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    """获取某次 run 的完整日志"""
    run = log_store.get_run(run_id)
    if not run:
        return {"error": f"Run {run_id} 不存在"}
    return run.to_dict()


@app.get("/api/runs/{run_id}/checkpoints")
async def get_checkpoints(run_id: str):
    """获取某次 run 的所有 checkpoint"""
    run = log_store.get_run(run_id)
    if not run:
        return {"error": f"Run {run_id} 不存在"}

    checkpoints = []
    for step in run.steps:
        if "checkpoint" in step:
            checkpoints.append({
                "step_index": step["step_index"],
                "step_type": step["type"],
                "checkpoint": step["checkpoint"],
            })
    return {"checkpoints": checkpoints}


@app.get("/api/session")
async def get_session():
    """获取当前 session context"""
    return get_session_context()


@app.post("/api/session/reset")
async def session_reset():
    """重置 session context"""
    reset_session()
    return {"status": "ok", "message": "Session context 已重置"}


@app.post("/api/runs/clear")
async def clear_runs():
    """清空所有 run 日志"""
    log_store.clear()
    return {"status": "ok", "message": "所有 run 日志已清空"}


@app.post("/api/rag/retrieve")
async def rag_retrieve(req: RetrievalTestRequest):
    """直接测试 RAG 检索（用于 A/B 测试）"""
    try:
        from agent.rag import rag_engine
        result = rag_engine.retrieve(
            query=req.query,
            collection=req.collection,
            strategy=req.strategy,
            top_k=req.top_k,
        )
        return result
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/rag/compare")
async def rag_compare(req: CompareRequest):
    """对比三种检索策略的结果"""
    try:
        from agent.rag import rag_engine
        result = rag_engine.compare_strategies(
            query=req.query,
            collection=req.collection,
            top_k=req.top_k,
        )
        return result
    except Exception as e:
        return {"error": str(e)}


# ========== Config API (模式切换) ==========

@app.get("/api/config")
async def get_config():
    """获取当前 NLU / Guardrails 模式"""
    return agent_config.to_dict()


@app.post("/api/config")
async def update_config(req: ConfigRequest):
    """切换 NLU / Guardrails 模式"""
    updates = {}
    if req.nlu_mode and req.nlu_mode in ("embedding", "llm"):
        updates["nlu_mode"] = req.nlu_mode
    if req.guardrails_mode and req.guardrails_mode in ("regex", "llm"):
        updates["guardrails_mode"] = req.guardrails_mode
    agent_config.update(**updates)
    return {"status": "ok", **agent_config.to_dict()}


# ========== Startup ==========

@app.on_event("startup")
async def startup():
    """启动时初始化 RAG 引擎 + NLU + 活跃对话"""
    try:
        from agent.rag import rag_engine
        rag_engine.initialize()
    except Exception as e:
        print(f"⚠️ RAG 引擎初始化失败 (可能 qdrant 未安装): {e}")
        print("  知识查询将 fallback 到关键词搜索")

    try:
        from agent.nlu import initialize_nlu
        initialize_nlu()
    except Exception as e:
        print(f"⚠️ NLU 初始化失败: {e}")
        print("  意图路由将 fallback 到关键词匹配")

    # 恢复活跃对话的记忆
    conv = conv_manager.get_active()
    set_active_memory(conv.memory)
    print(f"  🟢 活跃对话: {conv.id} ({conv.title})")


# ========== Static Files ==========

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return FileResponse("static/index.html")


# ========== Run ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
