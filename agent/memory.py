"""Agent 记忆系统 - 多层记忆架构

记忆层级：
┌─────────────────────────────────────────┐
│  ① 工作记忆 (Working Memory)           │ 当前对话 slot + intent
│  ② 任务记忆 (Episodic Memory)          │ 最近 N 轮完整交互摘要
│  ③ 用户画像 (User Profile)             │ 偏好、常用操作、情绪倾向
│  ④ 长期摘要 (Long-term Summary)        │ 跨 session 的压缩总结
└─────────────────────────────────────────┘

工作记忆：每轮更新，slot 级别
任务记忆：每轮完成后追加，保留最近 10 轮，包含意图+结果摘要
用户画像：根据行为自动推断，如"常购电子产品"、"曾退款2次"
长期摘要：超过 10 轮后压缩旧记忆为一段摘要
"""

import time
from datetime import datetime
from collections import Counter


class WorkingMemory:
    """① 工作记忆 - 当前轮次的状态"""

    def __init__(self):
        self.current_intent: str | None = None
        self.slots: dict = {}
        self.turn_count: int = 0

    def update(self, intent: str, slots: dict):
        if self.current_intent and self.current_intent != intent:
            self.slots = {}
        self.current_intent = intent
        for k, v in slots.items():
            if v is not None:
                self.slots[k] = v
        self.turn_count += 1

    def clear(self):
        self.current_intent = None
        self.slots = {}

    def to_dict(self):
        return {
            "layer": "工作记忆",
            "current_intent": self.current_intent,
            "slots": self.slots.copy(),
            "turn_count": self.turn_count,
        }


class EpisodicMemory:
    """② 任务记忆 - 最近 N 轮完整交互"""

    MAX_EPISODES = 10

    def __init__(self):
        self.episodes: list[dict] = []

    def add_episode(self, episode: dict):
        """添加一轮完整交互"""
        episode["timestamp"] = datetime.now().isoformat()
        episode["episode_id"] = len(self.episodes)
        self.episodes.append(episode)
        # 超过 MAX 时触发压缩
        if len(self.episodes) > self.MAX_EPISODES:
            self._compress_oldest()

    def _compress_oldest(self):
        """将最旧的 5 轮压缩为摘要"""
        if len(self.episodes) <= 5:
            return
        oldest = self.episodes[:5]
        summary = self._summarize_episodes(oldest)
        self.episodes = self.episodes[5:]
        # 把压缩摘要存入长期记忆（由外部调用）
        return summary

    @staticmethod
    def _summarize_episodes(episodes: list[dict]) -> str:
        """将多轮交互压缩为一段文字摘要"""
        intents = [e.get("intent", "unknown") for e in episodes]
        intent_counts = Counter(intents)
        parts = []
        for intent, count in intent_counts.items():
            parts.append(f"{intent}×{count}")
        return f"历史交互摘要({len(episodes)}轮): {', '.join(parts)}"

    def get_recent(self, n: int = 5) -> list[dict]:
        return self.episodes[-n:]

    def to_dict(self):
        return {
            "layer": "任务记忆",
            "total_episodes": len(self.episodes),
            "recent_episodes": self.get_recent(5),
        }


class UserProfile:
    """③ 用户画像 - 自动推断的用户偏好"""

    def __init__(self):
        self.preferences: dict = {}  # {"category_preference": "电子产品", ...}
        self.behavior_stats: dict = {
            "total_queries": 0,
            "intent_history": [],          # 所有意图历史
            "refund_count": 0,             # 退款次数
            "search_categories": [],        # 搜索过的品类
            "sentiment_trend": "neutral",   # positive/neutral/negative
        }
        self.tags: list[str] = []  # 自动标签, 如 ["电子产品爱好者", "价格敏感"]

    def update_from_episode(self, episode: dict):
        """从一轮交互更新用户画像"""
        intent = episode.get("intent", "")
        slots = episode.get("slots", {})
        result = episode.get("result_summary", "")

        self.behavior_stats["total_queries"] += 1
        self.behavior_stats["intent_history"].append(intent)

        # 退款计数
        if intent == "refund":
            self.behavior_stats["refund_count"] += 1

        # 搜索品类
        if intent == "search_product" and "category" in slots:
            cat = slots["category"]
            if cat not in self.behavior_stats["search_categories"]:
                self.behavior_stats["search_categories"].append(cat)

        # 自动推断标签
        self._infer_tags()

    def _infer_tags(self):
        """根据行为推断用户标签"""
        self.tags = []
        stats = self.behavior_stats
        intent_counter = Counter(stats["intent_history"])

        # 活跃度标签
        if stats["total_queries"] >= 10:
            self.tags.append("活跃用户")
        elif stats["total_queries"] >= 5:
            self.tags.append("普通用户")
        else:
            self.tags.append("新用户")

        # 偏好标签
        if intent_counter.get("search_product", 0) >= 3:
            self.tags.append("购物达人")
        if intent_counter.get("knowledge_query", 0) >= 3:
            self.tags.append("好奇宝宝")
        if stats["refund_count"] >= 2:
            self.tags.append("退款频繁")

        # 品类偏好
        if stats["search_categories"]:
            top_cat = Counter(stats["search_categories"]).most_common(1)
            if top_cat:
                self.preferences["偏好品类"] = top_cat[0][0]
                self.tags.append(f"{top_cat[0][0]}爱好者")

    def to_dict(self):
        return {
            "layer": "用户画像",
            "tags": self.tags,
            "preferences": self.preferences,
            "behavior_stats": {
                "total_queries": self.behavior_stats.get("total_queries", 0),
                "refund_count": self.behavior_stats.get("refund_count", 0),
                "search_categories": self.behavior_stats.get("search_categories", []),
                "sentiment_trend": self.behavior_stats.get("sentiment_trend", "neutral"),
                "top_intents": dict(Counter(self.behavior_stats.get("intent_history", [])).most_common(5)),
            },
        }


class LongTermSummary:
    """④ 长期摘要 - 跨 session 的压缩记忆"""

    def __init__(self):
        self.summaries: list[dict] = []

    def add_summary(self, text: str):
        self.summaries.append({
            "text": text,
            "created_at": datetime.now().isoformat(),
        })

    def get_context(self) -> str:
        """获取长期记忆上下文（注入 system prompt）"""
        if not self.summaries:
            return ""
        parts = [s["text"] for s in self.summaries[-3:]]  # 最近 3 段摘要
        return "【长期记忆】" + " | ".join(parts)

    def to_dict(self):
        return {
            "layer": "长期摘要",
            "summary_count": len(self.summaries),
            "summaries": self.summaries[-3:],
        }


class MemoryNote:
    """⑤ 记忆笔记 - LLM 驱动的滚动摘要
    
    每轮对话后由 LLM 更新，保留重要信息，压缩旧内容。
    注入 system prompt 让 LLM 知道“之前发生了什么”。
    """

    def __init__(self):
        self.content: str = ""  # 当前记忆笔记内容
        self.version: int = 0   # 更新次数
        self.history: list[dict] = []  # 历史版本（保留最近 5 次）

    def update(self, new_content: str):
        """更新记忆笔记"""
        if self.content:
            self.history.append({
                "version": self.version,
                "content": self.content,
                "updated_at": datetime.now().isoformat(),
            })
            self.history = self.history[-5:]  # 保留最近 5 个版本
        self.content = new_content
        self.version += 1

    def get_context(self) -> str:
        if not self.content:
            return ""
        return f"【记忆笔记 v{self.version}】{self.content}"

    def to_dict(self):
        return {
            "layer": "记忆笔记",
            "content": self.content,
            "version": self.version,
            "history": self.history,
        }


class AgentMemory:
    """​Agent 记忆系统 - 统一管理 5 层记忆"""

    def __init__(self):
        self.working = WorkingMemory()
        self.episodic = EpisodicMemory()
        self.profile = UserProfile()
        self.long_term = LongTermSummary()
        self.note = MemoryNote()  # LLM 驱动的记忆笔记

    def update_working(self, intent: str, slots: dict):
        self.working.update(intent, slots)

    def complete_episode(self, intent: str, slots: dict, user_input: str,
                         response: str, tool_name: str | None = None,
                         tool_result: str | None = None):
        """一轮对话完成后调用"""
        episode = {
            "intent": intent,
            "slots": slots,
            "user_input": user_input[:100],
            "response": response[:100],
            "tool_name": tool_name,
            "result_summary": tool_result[:100] if tool_result else None,
        }
        self.episodic.add_episode(episode)
        self.profile.update_from_episode(episode)

        # 检查是否需要压缩到长期记忆
        if len(self.episodic.episodes) > self.episodic.MAX_EPISODES:
            summary = self.episodic._compress_oldest()
            if summary:
                self.long_term.add_summary(summary)

    def get_memory_context(self) -> str:
        """生成注入 LLM 的记忆上下文（全部 4 层）"""
        parts = []

        # ① 记忆笔记（最高优先级，LLM 生成的滚动摘要）
        note_ctx = self.note.get_context()
        if note_ctx:
            parts.append(note_ctx)

        # ② 工作记忆：当前意图和已填槽位
        if self.working.current_intent:
            slots_str = ", ".join(f"{k}={v}" for k, v in self.working.slots.items()) if self.working.slots else "无"
            parts.append(f"【工作记忆】当前意图: {self.working.current_intent} | 已收集参数: {slots_str} | 对话轮次: {self.working.turn_count}")

        # ③ 用户画像：标签 + 偏好 + 行为统计
        profile_parts = []
        if self.profile.tags:
            profile_parts.append(f"标签: {', '.join(self.profile.tags)}")
        if self.profile.preferences:
            pref_str = ", ".join(f"{k}={v}" for k, v in self.profile.preferences.items())
            profile_parts.append(f"偏好: {pref_str}")
        stats = self.profile.behavior_stats
        if stats["total_queries"] > 0:
            profile_parts.append(f"总查询: {stats['total_queries']}次")
            if stats["refund_count"]:
                profile_parts.append(f"退款: {stats['refund_count']}次")
            if stats["search_categories"]:
                profile_parts.append(f"搜索品类: {', '.join(stats['search_categories'])}")
        if profile_parts:
            parts.append(f"【用户画像】{' | '.join(profile_parts)}")

        # ④ 长期摘要
        lt = self.long_term.get_context()
        if lt:
            parts.append(lt)

        return "\n".join(parts)

    def reset(self):
        self.__init__()

    def to_dict(self) -> dict:
        return {
            "memory_note": self.note.to_dict(),
            "working_memory": self.working.to_dict(),
            "episodic_memory": self.episodic.to_dict(),
            "user_profile": self.profile.to_dict(),
            "long_term_summary": self.long_term.to_dict(),
        }

# AgentMemory 实例现由 engine.py 和 conversations.py 管理
