"""多会话管理器 - 类似 ChatGPT/Claude 的对话管理

每个 Conversation 拥有独立的:
- AgentMemory (工作记忆 + 任务记忆 + 用户画像 + 长期摘要)
- chat_messages (前端聊天消息列表)
- run_ids (关联的 trace runs)
"""

import json
import os
import uuid
from datetime import datetime
from typing import Optional
from agent.memory import AgentMemory


class Conversation:
    """一个独立的对话"""

    def __init__(self, conv_id: str = None, title: str = "新对话"):
        self.id = conv_id or str(uuid.uuid4())[:8]
        self.title = title
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.messages: list[dict] = []   # {role, content}
        self.run_ids: list[str] = []
        self.memory = AgentMemory()

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.updated_at = datetime.now().isoformat()

    def add_run(self, run_id: str):
        self.run_ids.append(run_id)

    def auto_title(self, user_input: str):
        """根据第一条用户消息自动生成标题"""
        if self.title == "新对话":
            self.title = user_input[:20] + ("..." if len(user_input) > 20 else "")

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages),
            "run_count": len(self.run_ids),
        }

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": self.messages,
            "run_ids": self.run_ids,
            "memory": self.memory.to_dict(),
        }


class ConversationManager:
    """会话管理器 - 管理多个对话"""

    PERSIST_FILE = "data/conversations.json"

    def __init__(self):
        self.conversations: dict[str, Conversation] = {}
        self.active_id: Optional[str] = None
        self._load()

    def _load(self):
        if not os.path.exists(self.PERSIST_FILE):
            return
        try:
            with open(self.PERSIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for cd in data.get("conversations", []):
                conv = Conversation(cd["id"], cd.get("title", "新对话"))
                conv.created_at = cd.get("created_at", conv.created_at)
                conv.updated_at = cd.get("updated_at", conv.updated_at)
                conv.messages = cd.get("messages", [])
                conv.run_ids = cd.get("run_ids", [])
                # 恢复记忆
                mem_data = cd.get("memory")
                if mem_data:
                    self._restore_memory(conv.memory, mem_data)
                self.conversations[conv.id] = conv
            self.active_id = data.get("active_id")
            print(f"  💬 已加载 {len(self.conversations)} 个历史对话")
        except Exception as e:
            print(f"  ⚠️ 加载对话历史失败: {e}")

    @staticmethod
    def _restore_memory(memory: AgentMemory, data: dict):
        """从持久化数据恢复 AgentMemory 的全部层"""
        # ① 记忆笔记
        note = data.get("memory_note", {})
        if note.get("content"):
            memory.note.content = note["content"]
            memory.note.version = note.get("version", 0)
            memory.note.history = note.get("history", [])
        # ② 工作记忆
        wm = data.get("working_memory", {})
        if wm.get("current_intent"):
            memory.working.current_intent = wm["current_intent"]
            memory.working.slots = wm.get("slots", {})
            memory.working.turn_count = wm.get("turn_count", 0)
        # ③ 任务记忆（最近 episodes）
        ep = data.get("episodic_memory", {})
        if ep.get("episodes"):
            memory.episodic.episodes = ep["episodes"]
        # ④ 用户画像
        up = data.get("user_profile", {})
        if up.get("tags"):
            memory.profile.tags = list(up["tags"])
        if up.get("preferences"):
            memory.profile.preferences = up["preferences"]
        if up.get("behavior_stats"):
            saved_stats = up["behavior_stats"]
            # 只恢复标量字段，intent_history 保留默认空列表（序列化时被转成 top_intents）
            for key in ["total_queries", "refund_count", "search_categories", "sentiment_trend"]:
                if key in saved_stats:
                    memory.profile.behavior_stats[key] = saved_stats[key]
        # ⑤ 长期摘要
        lt = data.get("long_term_summary", {})
        if lt.get("summaries"):
            memory.long_term.summaries = lt["summaries"]

    def _save(self):
        os.makedirs(os.path.dirname(self.PERSIST_FILE), exist_ok=True)
        data = {
            "active_id": self.active_id,
            "conversations": [c.to_dict() for c in self.conversations.values()],
        }
        with open(self.PERSIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create(self, title: str = "新对话") -> Conversation:
        conv = Conversation(title=title)
        self.conversations[conv.id] = conv
        self.active_id = conv.id
        self._save()
        return conv

    def get(self, conv_id: str) -> Optional[Conversation]:
        return self.conversations.get(conv_id)

    def get_active(self) -> Conversation:
        """获取当前活跃对话，不存在则自动创建"""
        if self.active_id and self.active_id in self.conversations:
            return self.conversations[self.active_id]
        return self.create()

    def switch(self, conv_id: str) -> Optional[Conversation]:
        if conv_id in self.conversations:
            self.active_id = conv_id
            self._save()
            return self.conversations[conv_id]
        return None

    def delete(self, conv_id: str) -> bool:
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            if self.active_id == conv_id:
                self.active_id = None
            self._save()
            return True
        return False

    def list_all(self) -> list[dict]:
        """按更新时间倒序返回所有对话摘要"""
        convs = sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return [c.to_summary() for c in convs]

    def save(self):
        self._save()


# 全局会话管理器
conv_manager = ConversationManager()
