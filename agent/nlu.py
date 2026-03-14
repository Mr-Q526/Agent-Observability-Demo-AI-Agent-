"""NLU 模块 - 意图路由 + Slot 抽取

意图路由：embedding / LLM 可切换
Slot 抽取：正则 + 规则 + 关键词表
"""

import json
import re
import time
import math
from agent.skills import SKILLS
from agent.config import agent_config


# ========== Slot 抽取：正则 + 规则 ==========

# 商品类别关键词表
CATEGORY_KEYWORDS = {
    "手机": ["手机", "phone", "iphone", "华为", "小米", "oppo", "vivo"],
    "耳机": ["耳机", "headphone", "earphone", "airpods", "降噪"],
    "笔记本": ["笔记本", "电脑", "laptop", "macbook", "thinkpad"],
    "平板": ["平板", "ipad", "pad"],
    "运动鞋": ["运动鞋", "鞋", "nike", "跑鞋", "球鞋"],
    "家电": ["家电", "吸尘器", "空调", "冰箱", "洗衣机", "戴森"],
    "服饰": ["服饰", "衣服", "内衣", "外套", "裤子"],
    "游戏机": ["游戏机", "switch", "ps5", "xbox", "游戏"],
}

# 意图关键词快速匹配（作为 embedding 的 fallback）
INTENT_KEYWORDS = {
    "refund": ["退款", "退钱", "退货退款", "不想要了", "申请退款"],
    "order_query": ["订单", "查订单", "物流", "快递到哪了", "发货了吗"],
    "product_detail": ["详情", "具体信息", "参数", "配置"],
    "search_product": ["搜索", "找", "推荐", "有什么", "有没有", "想买"],
    "knowledge_query": ["政策", "运费", "会员", "权益", "怎么退", "支付方式", "售后", "保修"],
    "compare_products": ["对比", "比较", "哪个好", "选哪个", "区别", "vs"],
    "chitchat": ["你好", "hello", "hi", "谢谢", "再见", "嗯", "好的"],
}

# 意图描述（LLM 路由需要）
INTENT_DESCRIPTIONS = {k: v.description for k, v in SKILLS.items()}


class NLUResult:
    """NLU 处理结果"""

    def __init__(
        self,
        intent: str,
        confidence: float,
        slots: dict[str, str | None],
        missing_slots: list[str],
        top_k: list[dict],
        routing_method: str,
        route_type: str,
        extraction_details: dict,
    ):
        self.intent = intent
        self.confidence = confidence
        self.slots = slots
        self.missing_slots = missing_slots
        self.top_k = top_k
        self.routing_method = routing_method  # "embedding" | "keyword" | "llm" | "fallback"
        self.route_type = route_type  # "intent" | "skill" | "workflow"
        self.extraction_details = extraction_details

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "slots": self.slots,
            "missing_slots": self.missing_slots,
            "top_k": self.top_k,
            "routing_method": self.routing_method,
            "route_type": self.route_type,
            "extraction_details": self.extraction_details,
        }


class IntentRouter:
    """意图路由 - 基于 embedding 语义相似度"""

    def __init__(self):
        self._intent_embeddings: dict[str, list[float]] = {}
        self._initialized = False

    def initialize(self):
        """启动时预计算各 intent 描述的 embedding"""
        if self._initialized:
            return

        from agent.rag import _get_embeddings

        intents = list(SKILLS.keys())
        descriptions = [SKILLS[k].description for k in intents]

        print("  📡 NLU: 预计算 intent embeddings...")
        vectors = _get_embeddings(descriptions)

        for intent_id, vec in zip(intents, vectors):
            self._intent_embeddings[intent_id] = vec

        self._initialized = True
        print(f"  ✅ NLU: {len(intents)} 个 intent embedding 已就绪")

    def route(self, query: str, mode: str = "embedding") -> tuple[str, float, list[dict], str, dict]:
        """
        路由用户输入到 intent。
        mode: "embedding" | "llm"
        Returns: (intent_id, confidence, top_k, method, llm_info)
        """
        t0 = time.time()

        # LLM 模式
        if mode == "llm":
            return self._llm_route(query)

        # Embedding 模式
        if self._initialized and self._intent_embeddings:
            try:
                from agent.rag import _get_embedding
                query_vec = _get_embedding(query)

                scores = []
                for intent_id, intent_vec in self._intent_embeddings.items():
                    sim = self._cosine_similarity(query_vec, intent_vec)
                    scores.append({"intent": intent_id, "score": round(sim, 4)})

                scores.sort(key=lambda x: x["score"], reverse=True)
                top_k = scores[:5]

                best = scores[0]
                elapsed = time.time() - t0
                print(f"  🎯 NLU route: {best['intent']} ({best['score']:.3f}) in {elapsed*1000:.0f}ms")

                if best["score"] >= 0.4:  # embedding 相似度阈值（cosine）
                    return best["intent"], best["score"], top_k, "embedding", {}
            except Exception as e:
                print(f"  ⚠️ NLU embedding route failed: {e}")

        # Fallback: 关键词匹配
        i, c, top, m = self._keyword_route(query)
        return i, c, top, m, {}

    def _keyword_route(self, query: str) -> tuple[str, float, list[dict], str]:
        """关键词匹配路由"""
        query_lower = query.lower()
        scores = []

        for intent_id, keywords in INTENT_KEYWORDS.items():
            hit_count = sum(1 for kw in keywords if kw in query_lower)
            if hit_count > 0:
                score = min(hit_count / len(keywords) + 0.3, 0.9)
                scores.append({"intent": intent_id, "score": round(score, 4)})

        if scores:
            scores.sort(key=lambda x: x["score"], reverse=True)
            best = scores[0]
            return best["intent"], best["score"], scores[:5], "keyword"

        return "chitchat", 0.5, [{"intent": "chitchat", "score": 0.5}], "fallback"

    def _llm_route(self, query: str) -> tuple[str, float, list[dict], str, dict]:
        """使用大模型进行意图分类，返回 5-tuple 包含 LLM 提示词和原始回复"""
        t0 = time.time()

        # 延迟导入
        from agent.engine import client, MODEL

        intent_list = json.dumps(INTENT_DESCRIPTIONS, ensure_ascii=False, indent=2)
        prompt = f"""请分析以下用户输入，将其分类到最合适的意图中。

可选意图:
{intent_list}

用户输入: "{query}"

请严格按 JSON 格式回复: {{"intent": "意图ID", "confidence": 0.0-1.0, "reason": "简短理由"}}"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100,
            )
            raw = response.choices[0].message.content.strip()
            # 尝试解析 JSON
            raw_clean = re.sub(r'^```json\s*', '', raw).rstrip('`').strip()
            result = json.loads(raw_clean)
            intent = result.get("intent", "chitchat")
            confidence = float(result.get("confidence", 0.8))
            reason = result.get("reason", "")

            if intent not in SKILLS:
                intent = "chitchat"
                confidence = 0.5

            elapsed = time.time() - t0
            print(f"  🎯 NLU (LLM) route: {intent} ({confidence:.2f}) in {elapsed*1000:.0f}ms — {reason}")

            llm_info = {
                "prompt": prompt,
                "raw_response": raw,
                "parsed": result,
                "duration_ms": round(elapsed * 1000, 2),
            }
            return intent, confidence, [{"intent": intent, "score": confidence, "reason": reason}], "llm", llm_info
        except Exception as e:
            print(f"  ⚠️ LLM intent route error: {e}")
            i, c, top, m = self._keyword_route(query)
            return i, c, top, m, {"error": str(e)}

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """计算余弦相似度"""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class SlotExtractor:
    """Slot 抽取 - 纯规则（正则 + 关键词表）"""

    @staticmethod
    def extract(query: str, intent: str) -> tuple[dict, dict]:
        """
        从用户输入中抽取 slots。
        Returns: (slots_dict, extraction_details)
        """
        skill = SKILLS.get(intent)
        if not skill:
            return {}, {"method": "none", "patterns": []}

        slots = {}
        details = {"method": "regex+rules", "patterns": []}

        # --- 通用实体抽取 ---

        # order_id: ORD001 格式
        order_match = re.findall(r'(?i)(ORD\d{2,4})', query)
        if order_match:
            slots["order_id"] = order_match[0].upper()
            details["patterns"].append({"slot": "order_id", "pattern": r"ORD\d{2,4}", "matched": order_match[0]})

        # product_id: 取第一个
        product_match = re.findall(r'(?i)\b(P\d{2,4})\b', query)
        if product_match:
            slots["product_id"] = product_match[0].upper()
            details["patterns"].append({"slot": "product_id", "pattern": r"P\d{2,4}", "matched": product_match[0]})

        # product_ids: 只要匹配到商品ID，就塞进列表
        if product_match:
            # 去重并转大写
            unique_ids = list(dict.fromkeys(m.upper() for m in product_match))
            slots["product_ids"] = unique_ids
            details["patterns"].append({"slot": "product_ids", "pattern": r"P\d{2,4} (multiple)", "matched": unique_ids})

        # category: 关键词表匹配
        query_lower = query.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw in query_lower:
                    slots["category"] = category
                    details["patterns"].append({"slot": "category", "pattern": f"keyword:{kw}", "matched": category})
                    break
            if "category" in slots:
                break

        # price_range: "1000-5000" 或 "1000到5000元"
        price_match = re.findall(r'(\d+)\s*[-~到至]\s*(\d+)\s*元?', query)
        if price_match:
            slots["price_range"] = f"{price_match[0][0]}-{price_match[0][1]}"
            details["patterns"].append({"slot": "price_range", "pattern": r"\d+[-~到至]\d+", "matched": slots["price_range"]})

        # --- 按 intent 特定抽取 ---

        if intent == "search_product":
            if "query" not in slots:
                if "category" in slots:
                    slots["query"] = slots["category"]
                else:
                    cleaned = SlotExtractor._clean_text(query, list(slots.values()))
                    if len(cleaned) > 10 and any(p in cleaned for p in ['?', '？', '。', '！', '，', ',']):
                        llm_extracted = SlotExtractor._extract_query_with_llm(cleaned)
                        if llm_extracted:
                            slots["query"] = llm_extracted
                            details["patterns"].append({"slot": "query", "pattern": "llm_fallback", "matched": llm_extracted})
                        else:
                            slots["query"] = cleaned
                    else:
                        slots["query"] = cleaned if cleaned else query

        elif intent == "compare_products":
            # 确保有 product_ids
            if "product_ids" not in slots and "product_id" in slots:
                slots["product_ids"] = [slots["product_id"]]

        elif intent == "knowledge_query":
            if "question" not in slots:
                slots["question"] = query

        elif intent == "refund":
            if "reason" not in slots:
                reason_patterns = [
                    r'(?:原因|因为|由于)[：:\s]*(.+?)(?:[，。,.]|$)',
                    r'(?:质量问题|不合适|不喜欢|坏了|有问题|瑕疵|发错|少发)',
                ]
                for p in reason_patterns:
                    m = re.search(p, query)
                    if m:
                        reason_text = m.group(0) if not m.groups() else m.group(1)
                        slots["reason"] = reason_text.strip()
                        details["patterns"].append({"slot": "reason", "pattern": p, "matched": slots["reason"]})
                        break

        elif intent in ("product_detail", "order_query"):
            pass  # product_id / order_id 已在通用抽取中处理

        return slots, details

    @staticmethod
    def _clean_text(text: str, extracted_values: list) -> str:
        """去掉已提取的值，返回剩余文本"""
        cleaned = text
        for val in extracted_values:
            if val and isinstance(val, str):
                cleaned = cleaned.replace(val, "")
        cleaned = re.sub(r'^(我想|我要|帮我|请|给我|查一下|搜索|找|推荐|有什么|有没有)\s*', '', cleaned)
        return cleaned.strip()

    @staticmethod
    def _extract_query_with_llm(text: str) -> str:
        """使用轻量级 LLM 调用提取核心商品关键词"""
        try:
            from agent.engine import client, MODEL
            prompt = (
                f"用户原话：\"{text}\"\n"
                f"请从以上句子中提取用户想要搜索或购买的最核心的商品关键词（如品牌、品类、名称等）。\n"
                f"要求：\n"
                f"1. 直接输出关键词本身，不要包含多余的标点符号或句子结构（如'推荐一下'、'结果如何'、'有没有'等废话）。\n"
                f"2. 如果用户的话中不包含任何具体的商品实体，只是一些寒暄或意图不明的废话，请只输出四个字：提取失败。"
            )

            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20,
            )
            extracted = resp.choices[0].message.content.strip()

            if extracted == "提取失败":
                return ""
            return extracted
        except Exception as e:
            print(f"  ⚠️ NLU LLM_Fallback failed: {e}")
            return ""


# ========== NLU 主入口 ==========

_router = IntentRouter()


def initialize_nlu():
    """初始化 NLU（在 RAG 初始化之后调用）"""
    _router.initialize()


def classify(user_input: str, session_context: dict | None = None) -> NLUResult:
    """
    NLU 主入口：意图路由 + Slot 抽取。
    根据 agent_config.nlu_mode 决定使用 embedding 还是 LLM 路由。
    """
    t0 = time.time()

    # 读取当前配置的 NLU 模式
    nlu_mode = agent_config.nlu_mode

    # 1. 意图路由
    # [测试后门] 强制走 LLM 路由
    if user_input.startswith("[LLM路由测试]"):
        clean_input = user_input.replace("[LLM路由测试]", "").strip()
        intent, confidence, top_k, method, llm_info = _router._llm_route(clean_input)
    else:
        intent, confidence, top_k, method, llm_info = _router.route(user_input, mode=nlu_mode)

    # 2. 如果有 session context，检查是否在补充 slot
    if session_context and session_context.get("current_intent"):
        prev_intent = session_context["current_intent"]
        prev_slots = session_context.get("slots", {})
        if len(user_input) < 30 and confidence < 0.7:
            intent = prev_intent
            confidence = 0.8
            method = "session_continue"

    # 3. Slot 抽取
    slots, extraction_details = SlotExtractor.extract(user_input, intent)

    # 4. 合并 session 已有 slots (仅保留实体型 slot，不继承查询型 slot)
    #    查询型 slot (question, query, keyword, category) 是瞬态的，每轮重新抽取
    TRANSIENT_SLOTS = {"question", "query", "keyword", "category", "product_ids", "product_id", "reason"}
    if session_context and session_context.get("current_intent") == intent:
        prev_slots = session_context.get("slots", {})
        for k, v in prev_slots.items():
            if k in TRANSIENT_SLOTS:
                continue  # 不继承瞬态 slot
            if k not in slots and v is not None:
                slots[k] = v

    # 5. 检查缺失 slots
    skill = SKILLS.get(intent)
    missing_slots = []
    if skill:
        for s in skill.required_slots:
            if not slots.get(s):
                missing_slots.append(s)

    # 6. 获取 route_type
    route_type = skill.route_type if skill else "intent"

    elapsed_ms = (time.time() - t0) * 1000
    extraction_details["total_ms"] = round(elapsed_ms, 2)
    if llm_info:
        extraction_details["llm_routing"] = llm_info

    return NLUResult(
        intent=intent,
        confidence=confidence,
        slots=slots,
        missing_slots=missing_slots,
        top_k=top_k,
        routing_method=method,
        route_type=route_type,
        extraction_details=extraction_details,
    )
