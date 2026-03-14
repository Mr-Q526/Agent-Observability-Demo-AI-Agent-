"""RAG 检索引擎 - 使用 API Embedding + Qdrant 内存向量库

使用 volcengine doubao embedding API（标准 /api/v3/embeddings 端点），无需下载模型。
支持关键词搜索、向量搜索、混合检索(RRF重排序)。
"""

import time
import re
import httpx
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, ScoredPoint

from agent.mock_data import PRODUCTS, KNOWLEDGE_BASE

import os

# SiliconFlow API配置
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY")
EMBEDDING_URL = "https://ark.cn-beijing.volces.com/api/v3/embeddings/multimodal"
EMBEDDING_MODEL = "doubao-embedding-vision-250615"

COLLECTION_KNOWLEDGE = "knowledge"
COLLECTION_PRODUCTS = "products"

_HEADERS = {
    "Authorization": f"Bearer {EMBEDDING_API_KEY}",
    "Content-Type": "application/json",
}


def _get_embedding(text: str) -> list[float]:
    """单条文本 → embedding vector（多模态端点）"""
    body = {
        "model": EMBEDDING_MODEL,
        "input": [{"type": "text", "text": text[:16000]}],
        "encoding_format": "float",
    }
    resp = httpx.post(EMBEDDING_URL, headers=_HEADERS, json=body, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    raw = data.get("data", {})
    if isinstance(raw, dict):
        return raw.get("embedding", [])
    if isinstance(raw, list) and raw:
        return raw[0].get("embedding", [])
    return []


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    """批量获取向量（逐条调用多模态端点）"""
    return [_get_embedding(t) for t in texts]


class RAGEngine:
    """RAG 检索引擎"""

    def __init__(self):
        self.client = QdrantClient(":memory:")
        self._initialized = False

    def initialize(self):
        """初始化：创建集合并灌入数据"""
        if self._initialized:
            return

        print("🔄 RAG Engine: 初始化向量数据库...")

        # --- 知识库集合 ---
        knowledge_docs = []
        knowledge_payloads = []

        for i, item in enumerate(KNOWLEDGE_BASE):
            paragraphs = [p.strip() for p in item["content"].split("\n") if p.strip() and not p.strip().startswith("【")]
            for j, para in enumerate(paragraphs):
                knowledge_docs.append(para)
                knowledge_payloads.append({
                    "topic": item["topic"],
                    "keywords": ",".join(item["keywords"]),
                    "full_content": item["content"],
                    "paragraph": para,
                    "source": "knowledge_base",
                })

        # 批量获取 embeddings
        print(f"  📡 正在调用 embedding API ({len(knowledge_docs)} 条知识)...")
        knowledge_vectors = _get_embeddings(knowledge_docs)
        dim = len(knowledge_vectors[0])

        self.client.create_collection(
            collection_name=COLLECTION_KNOWLEDGE,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        self.client.upsert(
            collection_name=COLLECTION_KNOWLEDGE,
            points=[
                PointStruct(id=i, vector=vec, payload=pay)
                for i, (vec, pay) in enumerate(zip(knowledge_vectors, knowledge_payloads))
            ],
        )
        print(f"  ✅ 知识库: {len(knowledge_docs)} 条已索引 (dim={dim})")

        # --- 商品集合 ---
        product_docs = []
        product_payloads = []

        for p in PRODUCTS:
            doc_text = f"{p['name']} {p['category']} {p['description']}"
            product_docs.append(doc_text)
            product_payloads.append({
                "product_id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "price": p["price"],
                "stock": p["stock"],
                "description": p["description"],
                "source": "products",
            })

        print(f"  📡 正在调用 embedding API ({len(product_docs)} 条商品)...")
        product_vectors = _get_embeddings(product_docs)

        self.client.create_collection(
            collection_name=COLLECTION_PRODUCTS,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        self.client.upsert(
            collection_name=COLLECTION_PRODUCTS,
            points=[
                PointStruct(id=i, vector=vec, payload=pay)
                for i, (vec, pay) in enumerate(zip(product_vectors, product_payloads))
            ],
        )
        print(f"  ✅ 商品库: {len(product_docs)} 条已索引")

        self._initialized = True
        print("✅ RAG Engine 初始化完成")

    def retrieve(
        self,
        query: str,
        collection: str = COLLECTION_KNOWLEDGE,
        strategy: str = "hybrid",
        top_k: int = 5,
    ) -> dict:
        """
        执行检索。strategy: keyword | vector | hybrid
        Returns full retrieval log for observability.
        """
        self.initialize()

        retrieval_log = {
            "strategy": strategy,
            "query": query,
            "collection": collection,
            "top_k": top_k,
            "keyword_results": None,
            "vector_results": None,
            "rerank_details": None,
            "timing": {},
        }

        final_results = []

        if strategy == "keyword":
            t0 = time.time()
            keyword_results = self._keyword_search(query, collection, top_k)
            retrieval_log["timing"]["keyword_ms"] = round((time.time() - t0) * 1000, 2)
            retrieval_log["keyword_results"] = keyword_results
            final_results = keyword_results

        elif strategy == "vector":
            t0 = time.time()
            vector_results = self._vector_search(query, collection, top_k)
            retrieval_log["timing"]["vector_ms"] = round((time.time() - t0) * 1000, 2)
            retrieval_log["vector_results"] = vector_results
            final_results = vector_results

        elif strategy == "hybrid":
            t0 = time.time()
            keyword_results = self._keyword_search(query, collection, top_k)
            t1 = time.time()
            vector_results = self._vector_search(query, collection, top_k)
            t2 = time.time()

            retrieval_log["timing"]["keyword_ms"] = round((t1 - t0) * 1000, 2)
            retrieval_log["timing"]["vector_ms"] = round((t2 - t1) * 1000, 2)
            retrieval_log["keyword_results"] = keyword_results
            retrieval_log["vector_results"] = vector_results

            t3 = time.time()
            final_results, rerank_details = self._rrf_rerank(keyword_results, vector_results, top_k)
            retrieval_log["timing"]["rerank_ms"] = round((time.time() - t3) * 1000, 2)
            retrieval_log["rerank_details"] = rerank_details

        retrieval_log["timing"]["total_ms"] = round(sum(retrieval_log["timing"].values()), 2)

        return {
            "strategy": strategy,
            "query": query,
            "results": final_results,
            "results_count": len(final_results),
            "retrieval_log": retrieval_log,
        }

    def _vector_search(self, query: str, collection: str, top_k: int) -> list:
        """向量搜索"""
        query_vec = _get_embedding(query)
        results = self.client.query_points(
            collection_name=collection,
            query=query_vec,
            limit=top_k,
        )
        return [
            {
                "id": str(r.id),
                "score": round(r.score, 4),
                "source": "vector",
                "metadata": r.payload,
            }
            for r in results.points
        ]

    def _keyword_search(self, query: str, collection: str, top_k: int) -> list:
        """关键词搜索（基于 payload 文本匹配打分）"""
        # 获取全部文档的 payload
        all_points = self.client.scroll(
            collection_name=collection,
            limit=100,
        )[0]

        query_terms = set(self._tokenize(query))
        scored = []

        for point in all_points:
            payload = point.payload or {}
            doc_text = " ".join(str(v) for v in payload.values())
            doc_terms = set(self._tokenize(doc_text))

            overlap = query_terms & doc_terms
            if overlap:
                keyword_score = len(overlap) / max(len(query_terms), 1)
                scored.append({
                    "id": str(point.id),
                    "score": round(keyword_score, 4),
                    "matched_terms": list(overlap),
                    "source": "keyword",
                    "metadata": payload,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _tokenize(self, text: str) -> list:
        """简单分词"""
        tokens = []
        tokens.extend(re.findall(r'[a-zA-Z0-9]+', text.lower()))
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(chinese_chars)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i + 1])
        return tokens

    def _rrf_rerank(self, keyword_results: list, vector_results: list, top_k: int) -> tuple:
        """RRF 重排序"""
        k = 60
        rrf_scores = {}
        doc_data = {}
        rank_info = {}

        for rank, item in enumerate(keyword_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank)
            doc_data[doc_id] = item
            rank_info[doc_id] = {"keyword_rank": rank, "keyword_score": item["score"]}

        for rank, item in enumerate(vector_results, 1):
            doc_id = item["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (k + rank)
            if doc_id not in doc_data:
                doc_data[doc_id] = item
            if doc_id not in rank_info:
                rank_info[doc_id] = {}
            rank_info[doc_id]["vector_rank"] = rank
            rank_info[doc_id]["vector_score"] = item["score"]

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        rerank_details = {"k": k, "fusion_entries": []}

        for doc_id in sorted_ids[:top_k]:
            item = doc_data[doc_id].copy()
            item["rrf_score"] = round(rrf_scores[doc_id], 6)
            item["source"] = "hybrid"
            item["rank_info"] = rank_info.get(doc_id, {})
            results.append(item)
            rerank_details["fusion_entries"].append({
                "doc_id": doc_id,
                "rrf_score": round(rrf_scores[doc_id], 6),
                "metadata": doc_data[doc_id].get("metadata", {}),
                **rank_info.get(doc_id, {}),
            })

        return results, rerank_details

    def compare_strategies(self, query: str, collection: str = COLLECTION_KNOWLEDGE, top_k: int = 5) -> dict:
        """对比三种策略"""
        results = {}
        for strategy in ["keyword", "vector", "hybrid"]:
            results[strategy] = self.retrieve(query, collection, strategy, top_k)

        keyword_ids = set(r["id"] for r in results["keyword"]["results"])
        vector_ids = set(r["id"] for r in results["vector"]["results"])
        hybrid_ids = set(r["id"] for r in results["hybrid"]["results"])

        return {
            "query": query,
            "results": results,
            "overlap_stats": {
                "keyword_vector_overlap": len(keyword_ids & vector_ids),
                "keyword_hybrid_overlap": len(keyword_ids & hybrid_ids),
                "vector_hybrid_overlap": len(vector_ids & hybrid_ids),
                "all_three_overlap": len(keyword_ids & vector_ids & hybrid_ids),
                "keyword_unique": len(keyword_ids - vector_ids - hybrid_ids),
                "vector_unique": len(vector_ids - keyword_ids - hybrid_ids),
            },
        }


# 全局实例
rag_engine = RAGEngine()
