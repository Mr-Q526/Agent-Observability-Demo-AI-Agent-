"""全局配置 — NLU / Guardrails 模式切换

前端通过 /api/config 读写，运行时即时生效。
"""


class AgentConfig:
    """单例配置，线程间共享"""

    def __init__(self):
        # NLU 意图路由模式: "embedding" | "llm"
        self.nlu_mode: str = "embedding"
        # Guardrails 安全检查模式: "regex" | "llm"
        self.guardrails_mode: str = "regex"

    def to_dict(self) -> dict:
        return {
            "nlu_mode": self.nlu_mode,
            "guardrails_mode": self.guardrails_mode,
        }

    def update(self, **kwargs):
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


# 全局单例
agent_config = AgentConfig()
