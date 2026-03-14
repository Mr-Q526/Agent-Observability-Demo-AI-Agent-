"""Tool 定义 - OpenAI function calling schema + 实现映射"""

from agent.mock_data import (
    search_products,
    get_product_detail,
    get_order_info,
    apply_refund,
    query_knowledge,
)

# ========== Tool Schema (OpenAI function calling 格式) ==========

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "搜索商品。根据用户提供的关键词（名称、类别等）搜索商品列表。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，如商品名称、类别（手机、耳机、笔记本等）"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_detail",
            "description": "获取商品详细信息。根据商品 ID 查询完整的商品信息（价格、库存、描述等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "商品 ID，如 P001、P002"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_info",
            "description": "查询订单信息。根据订单号查询订单的详细信息（商品、状态、金额等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，如 ORD001、ORD002"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_refund",
            "description": "申请退款。为指定订单提交退款申请。注意：这是一个敏感操作，执行前必须确认。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "要退款的订单号"
                    },
                    "reason": {
                        "type": "string",
                        "description": "退款原因"
                    }
                },
                "required": ["order_id", "reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge",
            "description": "查询知识库。搜索退换货政策、运费说明、会员权益、支付方式、售后服务等常见问题的答案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "要查询的问题，如'退货政策'、'运费多少'、'会员权益'"
                    }
                },
                "required": ["question"]
            }
        }
    },
]

# ========== Tool 实现映射 ==========

TOOL_FUNCTIONS = {
    "search_products": search_products,
    "get_product_detail": get_product_detail,
    "get_order_info": get_order_info,
    "apply_refund": apply_refund,
    "query_knowledge": query_knowledge,
}

# ========== 需要用户确认的敏感 Tool ==========

SENSITIVE_TOOLS = {"apply_refund"}
