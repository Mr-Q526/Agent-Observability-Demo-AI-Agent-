"""Skill 定义 - 每个意图对应一个 Skill

每个 Skill 包含：
- name: 中文名
- route_type: 路由类型 ("intent" | "skill" | "workflow")
  - intent: 简单意图(如闲聊)，直接 LLM 回复
  - skill: 单工具任务，走 Auto-Retrieve → Act
  - workflow: 多步任务，走完整 Auto-Retrieve → Observe → Plan → Act → Reflect
- description: 用于 embedding 意图路由的描述文本
- system_prompt: 该 skill 专属的 LLM 指令
- ask_templates: 缺 slot 时的追问模板（不调 LLM）
- tool_name: 关联的工具
- required_slots / optional_slots
- workflow_steps: (仅 workflow) 多步骤模板
"""


class Skill:
    """一个可路由的 Skill"""

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str,
        ask_templates: dict[str, str],
        tool_name: str | None,
        required_slots: list[str],
        optional_slots: list[str] | None = None,
        route_type: str = "skill",
        workflow_steps: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.ask_templates = ask_templates
        self.tool_name = tool_name
        self.required_slots = required_slots
        self.optional_slots = optional_slots or []
        self.route_type = route_type  # "intent" | "skill" | "workflow"
        self.workflow_steps = workflow_steps or []


# ========== Skill 注册表 ==========

SKILLS: dict[str, Skill] = {
    "search_product": Skill(
        name="商品搜索",
        route_type="skill",
        description="用户想搜索商品、浏览商品、找产品、推荐产品、有什么手机、耳机推荐",
        system_prompt=(
            "你是电商客服的商品推荐专员。根据搜索结果，用简洁友好的中文向用户介绍商品。"
            "突出价格、特点和库存情况。如果有多个结果，做简要对比。"
        ),
        ask_templates={
            "query": "请问您想搜索什么商品？比如手机、耳机、笔记本等。",
        },
        tool_name="search_products",
        required_slots=["query"],
        optional_slots=["category", "price_range"],
    ),
    "product_detail": Skill(
        name="商品详情",
        route_type="skill",
        description="用户想查看某个商品的详细信息、价格、库存、参数",
        system_prompt=(
            "你是电商客服的商品咨询专员。根据商品信息，详细介绍商品的价格、库存、功能特点。"
            "用友好专业的中文回复。"
        ),
        ask_templates={
            "product_id": "请提供商品编号（如 P001），我帮您查看详情。",
        },
        tool_name="get_product_detail",
        required_slots=["product_id"],
    ),
    "order_query": Skill(
        name="订单查询",
        route_type="skill",
        description="用户想查看订单、查询订单状态、物流信息、订单详情",
        system_prompt=(
            "你是电商客服的订单服务专员。根据订单信息，清晰地告知用户订单状态、"
            "物流信息、支付详情等。用友好专业的中文回复。"
        ),
        ask_templates={
            "order_id": "请提供您的订单号（如 ORD001），我帮您查询。",
        },
        tool_name="get_order_info",
        required_slots=["order_id"],
    ),
    "refund": Skill(
        name="退款申请",
        route_type="skill",
        description="用户想退款、申请退货退款、退钱、不想要了",
        system_prompt=(
            "你是电商客服的退款处理专员。根据退款结果，告知用户退款进度、"
            "预计到账时间等。注意态度温和，安抚用户情绪。"
        ),
        ask_templates={
            "order_id": "请提供您要退款的订单号（如 ORD001）。",
            "reason": "请告知退款原因，以便我们为您更好地处理。",
        },
        tool_name="apply_refund",
        required_slots=["order_id", "reason"],
    ),
    "knowledge_query": Skill(
        name="知识查询",
        route_type="skill",
        description="用户想了解退换货政策、运费说明、会员权益、支付方式、售后服务",
        system_prompt=(
            "你是电商客服的知识助手。根据知识库检索结果，用简洁清晰的中文回答用户问题。"
            "如果信息不足，引导用户联系人工客服。"
        ),
        ask_templates={
            "question": "请问您想了解什么？比如退换货政策、运费、会员权益等。",
        },
        tool_name="query_knowledge",
        required_slots=["question"],
    ),
    "compare_products": Skill(
        name="商品对比",
        route_type="workflow",
        description="用户想对比两个或多个商品的价格、功能、参数、选择困难、哪个好",
        system_prompt=(
            "你是电商客服的商品对比分析师。根据多款商品的详细信息，从价格、功能、"
            "库存、性价比等维度进行全面对比，并给出个性化推荐建议。"
        ),
        ask_templates={
            "product_ids": "请告诉我您想对比哪些商品？可以提供商品编号（如 P001、P003）。",
        },
        tool_name="get_product_detail",
        required_slots=["product_ids"],
        workflow_steps=[
            {"step": 1, "action": "tool", "tool": "get_product_detail", "slot": "product_ids[0]", "description": "查询第一款商品详情"},
            {"step": 2, "action": "tool", "tool": "get_product_detail", "slot": "product_ids[1]", "description": "查询第二款商品详情"},
            {"step": 3, "action": "llm",  "description": "对比分析两款商品并给出推荐"},
        ],
    ),
    "chitchat": Skill(
        name="闲聊",
        route_type="intent",
        description="用户在打招呼、闲聊、问好、你好、谢谢",
        system_prompt=(
            "你是友好的电商客服。简短回应用户的问候或闲聊，"
            "然后引导用户进入正题。推荐用户尝试商品搜索、订单查询等功能。"
        ),
        ask_templates={},
        tool_name=None,
        required_slots=[],
    ),
}

# 敏感 skill（需要用户确认才能执行）
SENSITIVE_SKILLS = {"refund"}
