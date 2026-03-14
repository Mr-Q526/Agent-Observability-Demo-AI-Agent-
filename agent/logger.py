"""全量日志记录器 - 记录 Agent 运行时的每一个细节"""

import uuid
import copy
import time
from datetime import datetime
from typing import Optional


class RunLog:
    """一次完整的 Agent 运行日志"""
    
    def __init__(self, user_input: str):
        self.run_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now().isoformat()
        self.end_time: Optional[str] = None
        self.user_input = user_input
        self.final_response: Optional[str] = None
        self.steps: list[dict] = []
        self.total_tokens = 0
        self.status = "running"  # running | awaiting_confirmation | completed
        self.pending_confirmation: Optional[dict] = None
        self._on_finish = None  # 持久化回调
    
    def add_step(self, step: dict):
        step["step_index"] = len(self.steps)
        step["timestamp"] = datetime.now().isoformat()
        self.steps.append(step)
    
    def finish(self, final_response: str):
        self.final_response = final_response
        self.end_time = datetime.now().isoformat()
        self.status = "completed"
        if self._on_finish:
            self._on_finish()
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "user_input": self.user_input,
            "final_response": self.final_response,
            "status": self.status,
            "total_tokens": self.total_tokens,
            "pending_confirmation": self.pending_confirmation,
            "steps_count": len(self.steps),
            "steps": self.steps,
        }


def create_llm_call_step(
    messages: list[dict],
    tools: list[dict],
    model: str,
    temperature: float,
    response_content: Optional[str],
    response_tool_calls: Optional[list],
    finish_reason: str,
    usage: dict,
    decision: Optional[dict] = None,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个 LLM 调用步骤的日志"""
    step = {
        "type": "llm_call",
        "request": {
            "model": model,
            "messages": copy.deepcopy(messages),
            "tools": copy.deepcopy(tools),
            "temperature": temperature,
            "messages_count": len(messages),
        },
        "response": {
            "content": response_content,
            "tool_calls": response_tool_calls,
            "finish_reason": finish_reason,
            "usage": usage,
        },
    }
    
    if decision:
        step["decision"] = decision
    
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    
    return step


def create_tool_call_step(
    tool_name: str,
    arguments: dict,
    result: any,
    duration_ms: float,
    requires_confirmation: bool = False,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个 Tool 调用步骤的日志"""
    step = {
        "type": "tool_call",
        "tool_execution": {
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "duration_ms": round(duration_ms, 2),
            "requires_confirmation": requires_confirmation,
        },
    }
    
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    
    return step


def create_follow_up_step(
    question: str,
    missing_info: str,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个拒答追问步骤的日志"""
    step = {
        "type": "follow_up_question",
        "follow_up": {
            "question": question,
            "missing_info": missing_info,
        },
    }
    
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    
    return step


def create_confirmation_step(
    action: str,
    tool_name: str,
    arguments: dict,
    description: str,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个等待用户确认步骤的日志"""
    step = {
        "type": "awaiting_confirmation",
        "confirmation": {
            "action": action,
            "tool_name": tool_name,
            "arguments": arguments,
            "description": description,
        },
    }
    
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    
    return step


def create_user_confirmed_step(
    confirmed: bool,
    tool_name: str,
    arguments: dict,
    result: Optional[any] = None,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个用户确认结果步骤的日志"""
    step = {
        "type": "user_confirmed",
        "confirmation_result": {
            "confirmed": confirmed,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
        },
    }
    
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    
    return step


def create_react_iteration_step(
    iteration: int,
    decision: str,
    tool_names: list[str] | None = None,
    thought: str | None = None,
    checkpoint_state: Optional[dict] = None,
) -> dict:
    """创建一个 ReAct 循环迭代步骤的日志"""
    step = {
        "type": "react_iteration",
        "react": {
            "iteration": iteration,
            "decision": decision,  # "tool_call" | "final_answer" | "fallback"
            "tool_names": tool_names or [],
            "thought": thought,  # LLM 在调工具时同时输出的思考文本
        },
    }
    if checkpoint_state:
        step["checkpoint"] = {
            "checkpoint_id": str(uuid.uuid4())[:8],
            **checkpoint_state,
        }
    return step


def create_state_snapshot_step(
    label: str,
    memory_dict: dict,
    messages_count: int = 0,
    iteration: int = 0,
    total_tool_calls: int = 0,
    total_tokens: int = 0,
    elapsed_ms: float = 0,
) -> dict:
    """创建 State 快照步骤（run 开始/结束时记录完整状态）"""
    return {
        "type": "state_snapshot",
        "state": {
            "label": label,
            "memory": memory_dict,
            "messages_count": messages_count,
            "iteration": iteration,
            "total_tool_calls": total_tool_calls,
            "total_tokens": total_tokens,
            "elapsed_ms": round(elapsed_ms, 2),
        },
    }


def create_memory_note_step(
    before: str,
    after: str,
    version: int,
) -> dict:
    """创建一个记忆笔记更新步骤的日志"""
    return {
        "type": "memory_note_update",
        "memory_note": {
            "before": before,
            "after": after,
            "version": version,
        },
    }


class LogStore:
    """日志存储（内存 + 文件持久化）"""

    PERSIST_FILE = "data/runs.json"

    def __init__(self):
        self.runs: dict[str, RunLog] = {}
        self._load_from_file()

    def _load_from_file(self):
        """启动时从文件加载历史 runs"""
        import json, os
        if not os.path.exists(self.PERSIST_FILE):
            return
        try:
            with open(self.PERSIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for rd in data:
                run = RunLog(rd["user_input"])
                run.run_id = rd["run_id"]
                run.start_time = rd["start_time"]
                run.end_time = rd.get("end_time")
                run.final_response = rd.get("final_response")
                run.steps = rd.get("steps", [])
                run.total_tokens = rd.get("total_tokens", 0)
                run.status = rd.get("status", "completed")
                run.pending_confirmation = rd.get("pending_confirmation")
                self.runs[run.run_id] = run
            print(f"  📂 已加载 {len(self.runs)} 条历史 runs")
        except Exception as e:
            print(f"  ⚠️ 加载历史 runs 失败: {e}")

    def _save_to_file(self):
        """保存所有 runs 到文件"""
        import json, os
        os.makedirs(os.path.dirname(self.PERSIST_FILE), exist_ok=True)
        data = [r.to_dict() for r in self.runs.values()]
        with open(self.PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_run(self, user_input: str) -> RunLog:
        run = RunLog(user_input)
        run._on_finish = self._save_to_file
        self.runs[run.run_id] = run
        return run

    def finish_run(self, run_id: str):
        """run 完成后触发持久化"""
        self._save_to_file()

    def get_run(self, run_id: str) -> Optional[RunLog]:
        return self.runs.get(run_id)

    def list_runs(self) -> list[dict]:
        return [
            {
                "run_id": r.run_id,
                "start_time": r.start_time,
                "user_input": r.user_input[:50] + ("..." if len(r.user_input) > 50 else ""),
                "status": r.status,
                "steps_count": len(r.steps),
                "total_tokens": r.total_tokens,
            }
            for r in reversed(self.runs.values())
        ]

    def clear(self):
        """清空所有 runs"""
        self.runs.clear()
        self._save_to_file()


# 全局日志存储实例
log_store = LogStore()
