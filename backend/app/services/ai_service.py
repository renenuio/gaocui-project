import asyncio
import json
from hashlib import sha256
from time import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.recommendation_agent import RecommendationAgent
from app.core.redis import redis_client
from app.models.product import Product
from app.services.embedding_service import semantic_embedding_service

class AIService:
    _sample_embeddings_synced = False
    _response_cache: dict[str, tuple[float, dict]] = {}
    RESPONSE_CACHE_TTL_SECONDS = 600
    EMBEDDING_TIMEOUT_SECONDS = 3.5
    CARD_LIMIT = 3
    CACHE_VERSION = "contract-session-v1"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend(self, query: str, limit: int = 10, session_id: str = "anonymous") -> dict:
        limit = self.CARD_LIMIT
        try:
            agent = RecommendationAgent()
            session_profile = await agent.get_session_profile_async(session_id)
            intent = agent.classify_intent_with_session(query, session_profile)
            if intent != "jade_query":
                # PRD boundary: NON_JADE must not enter embedding, vector search, ranking, product recommendation, or jade fallback.
                await agent.update_session_profile_async(session_id, query, intent)
                return agent.normalize_contract_response({
                    "sessionId": session_id,
                    "embedding_enabled": False,
                    "seed_created": False,
                    "cache_hit": False,
                    "fallback": False,
                    **agent.non_jade_requirement_response(query, intent),
                })

            jade_scene_query = query
            updated_profile = await agent.update_session_profile_async(session_id, query, intent)
            retrieval_text = self._session_retrieval_text(query, updated_profile)
            cache_key = self._cache_key(f"{session_id}:{retrieval_text}", limit)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response is not None:
                cached_response["query"] = query
                cached_response["intent"] = intent
                cached_response["jade_scene_query"] = jade_scene_query
                cached_response["sessionId"] = session_id
                return cached_response

            understanding = agent.understand_query(jade_scene_query)
            expanded_queries = agent.expand_query(retrieval_text, understanding)

            try:
                query_embedding = await asyncio.wait_for(
                    asyncio.to_thread(self.generate_embedding, " ".join(expanded_queries)),
                    timeout=self.EMBEDDING_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                response = await self._fallback_response(
                    query=query,
                    limit=limit,
                    fallback_reason=f"embedding_failed: {type(exc).__name__}",
                    agent=agent,
                    understanding=understanding,
                    expanded_queries=expanded_queries,
                    intent=intent,
                    jade_scene_query=jade_scene_query,
                    session_id=session_id,
                )
                await self._set_cached_response(cache_key, response)
                return response

            try:
                seed_created = await self.ensure_product_embeddings()
            except Exception:
                seed_created = False

            try:
                candidates = await self._vector_candidates(
                    query_embedding,
                    min(max(limit * 2, limit), 20),
                    understanding.category,
                )
                if len(candidates) < limit:
                    candidates = await self._ensure_minimum_candidates(candidates, limit, understanding.category)
            except Exception as exc:
                await self._safe_rollback()
                response = await self._fallback_response(
                    query=query,
                    limit=limit,
                    fallback_reason=f"vector_search_failed: {type(exc).__name__}",
                    agent=agent,
                    understanding=understanding,
                    expanded_queries=expanded_queries,
                    intent=intent,
                    jade_scene_query=jade_scene_query,
                    session_id=session_id,
                )
                await self._set_cached_response(cache_key, response)
                return response

            try:
                agent_result = await agent.recommend(
                    query=jade_scene_query,
                    candidates=candidates,
                    limit=limit,
                    user_key=session_id,
                    understanding=understanding,
                    expanded_queries=expanded_queries,
                )
            except Exception as exc:
                agent_result = self._fallback_agent_result(
                    query=query,
                    candidates=candidates,
                    limit=limit,
                    understanding=understanding,
                    expanded_queries=expanded_queries,
                    fallback_reason=f"agent_failed: {type(exc).__name__}",
                )

            response = {
                **agent_result,
                "sessionId": session_id,
                "query": query,
                "intent": intent,
                "jade_scene_query": jade_scene_query,
                "jade_scene_mapping": agent.jade_scene_mapping(query, jade_scene_query),
                "scene_mapping": agent.jade_scene_mapping(query, jade_scene_query),
                "jade_requirement_spec": agent.generate_jade_requirement_spec(query, jade_scene_query),
                "embedding_enabled": True,
                "seed_created": seed_created,
                "cache_hit": False,
                "fallback": False,
            }
            response = agent.normalize_contract_response(response)
            await self._set_cached_response(cache_key, response)
            return response
        except Exception as exc:
            return await self._fallback_response(
                query=query,
                limit=limit,
                fallback_reason=f"recommendation_failed: {type(exc).__name__}",
                session_id=session_id,
            )

    async def ensure_product_embeddings(self) -> bool:
        changed = False
        result = await self.db.execute(
            select(Product).where(
                Product.seller_id.is_not(None),
                Product.status == "active",
                Product.category == "jade",
                Product.embedding.is_(None),
            )
        )
        for product in result.scalars().all():
            embedding_text = " ".join(
                value
                for value in [product.name, product.description, product.detail, product.category]
                if value
            )
            product.embedding = self.generate_embedding(embedding_text)
            changed = True

        if changed:
            await self.db.commit()
        return changed

    def generate_embedding(self, text: str) -> list[float]:
        return semantic_embedding_service.embed(text)

    async def _vector_candidates(
        self,
        query_embedding: list[float],
        candidate_limit: int,
        category: str | None,
    ) -> list[dict]:
        distance = Product.embedding.cosine_distance(query_embedding).label("distance")
        category_filter = category or "jade"
        statement = (
            select(Product, distance)
            .where(
                Product.embedding.is_not(None),
                Product.category == category_filter,
                Product.status == "active",
                Product.seller_id.is_not(None),
            )
            .order_by(distance)
            .limit(candidate_limit)
        )
        result = await self.db.execute(statement)
        rows = result.all()
        if not rows:
            await self._safe_rollback()
            result = await self.db.execute(
                select(Product)
                .where(Product.category == category_filter, Product.status == "active", Product.seller_id.is_not(None))
                .limit(candidate_limit)
            )
            return [
                self._product_to_candidate(product, None, 1.0)
                for product in result.scalars().all()
            ]
        return [
            self._product_to_candidate(product, float(score), 1.0)
            for product, score in rows
        ]

    async def _ensure_minimum_candidates(
        self,
        candidates: list[dict],
        limit: int,
        category: str | None,
    ) -> list[dict]:
        if len(candidates) >= limit:
            return candidates

        seen_ids = {candidate.get("id") for candidate in candidates}
        fallback_candidates = await self._fallback_candidates(limit * 2, category or "jade")
        for candidate in fallback_candidates:
            candidate_id = candidate.get("id")
            if candidate_id in seen_ids:
                continue
            candidates.append(candidate)
            seen_ids.add(candidate_id)
            if len(candidates) >= limit:
                break
        return candidates

    async def _fallback_response(
        self,
        query: str,
        limit: int,
        fallback_reason: str,
        agent: RecommendationAgent | None = None,
        understanding=None,
        expanded_queries: list[str] | None = None,
        intent: str | None = None,
        jade_scene_query: str | None = None,
        session_id: str = "anonymous",
    ) -> dict:
        agent = agent or RecommendationAgent()
        session_profile = await agent.get_session_profile_async(session_id)
        intent = intent or agent.classify_intent_with_session(query, session_profile)
        if intent != "jade_query":
            # PRD boundary: NON_JADE fallback returns only requirement spec and UI suggestions; no jade items.
            return agent.normalize_contract_response({
                "sessionId": session_id,
                "embedding_enabled": False,
                "seed_created": False,
                "cache_hit": False,
                "fallback": False,
                "fallback_reason": fallback_reason,
                **agent.non_jade_requirement_response(query, intent),
            })

        jade_scene_query = jade_scene_query or query
        understanding = understanding or agent.understand_query(jade_scene_query)
        expanded_queries = expanded_queries or agent.expand_query(jade_scene_query, understanding)
        candidates = await self._fallback_candidates(limit, understanding.category)
        agent_result = self._fallback_agent_result(
            query=jade_scene_query,
            candidates=candidates,
            limit=limit,
            understanding=understanding,
            expanded_queries=expanded_queries,
            fallback_reason=fallback_reason,
        )
        response = {
            "sessionId": session_id,
            "query": query,
            "intent": intent,
            "jade_scene_query": jade_scene_query,
            "jade_scene_mapping": agent.jade_scene_mapping(query, jade_scene_query),
            "scene_mapping": agent.jade_scene_mapping(query, jade_scene_query),
            "jade_requirement_spec": agent.generate_jade_requirement_spec(query, jade_scene_query),
            "embedding_enabled": False,
            "seed_created": False,
            "cache_hit": False,
            "fallback": True,
            "fallback_reason": fallback_reason,
            **agent_result,
        }
        return agent.normalize_contract_response(response)

    def _session_retrieval_text(self, query: str, session_profile: dict) -> str:
        parts = [query]
        for key in ("budget", "type", "quality"):
            value = session_profile.get(key)
            if value:
                parts.append(f"{key}:{value}")
        return " ".join(str(part) for part in parts if part)

    async def _fallback_candidates(self, limit: int, category: str | None = None) -> list[dict]:
        await self._safe_rollback()
        category_filter = category or "jade"
        try:
            result = await self.db.execute(
                select(Product)
                .where(Product.category == category_filter, Product.status == "active", Product.seller_id.is_not(None))
                .limit(limit)
            )
            products = result.scalars().all()
            if products:
                return [
                    self._product_to_candidate(product, None, 1.0)
                    for product in products
                ]
        except Exception:
            pass

        return []

    def _product_to_candidate(
        self,
        product: Product,
        distance: float | None,
        category_match_score: float,
    ) -> dict:
        embedding_similarity = self._embedding_similarity(distance)
        price_score = self._price_score(product.price)
        business_score = self._business_score(product.price, product)
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": str(product.price) if product.price is not None else None,
            "image": product.image_url,
            "imageUrl": product.image_url,
            "images": product.images or [],
            "tags": product.tags or [],
            "sellerId": product.seller_id,
            "distance": distance,
            "embedding_similarity": embedding_similarity,
            "category_match_score": category_match_score,
            "price_score": price_score,
            "business_score": business_score,
            "hybrid_search_score": round(category_match_score * 0.6 + embedding_similarity * 0.25 + business_score * 0.15, 6),
        }

    def _embedding_similarity(self, distance: float | None) -> float:
        if distance is None:
            return 0.0
        return round(max(0.0, 1.0 - min(max(float(distance), 0.0), 2.0) / 2.0), 6)

    def _fallback_agent_result(
        self,
        query: str,
        candidates: list[dict],
        limit: int,
        understanding,
        expanded_queries: list[str],
        fallback_reason: str,
    ) -> dict:
        items = []
        for index, candidate in enumerate(candidates[:limit], start=1):
            item = dict(candidate)
            embedding_similarity = item.get("embedding_similarity", 0.0) or 0.0
            category_match_score = item.get("category_match_score", 1.0) or 1.0
            price_score = item.get("price_score")
            if price_score is None:
                price_score = self._price_score(item.get("price"))
            business_score = item.get("business_score")
            if business_score is None:
                business_score = self._business_score(item.get("price"), item)
            score = round(category_match_score * 0.6 + embedding_similarity * 0.25 + business_score * 0.15, 6)
            item["embedding_score"] = embedding_similarity
            item["embedding_similarity"] = embedding_similarity
            item["category_match_score"] = category_match_score
            item["price_score"] = price_score
            item["business_score"] = business_score
            item["llm_score"] = 0.0
            item["rank_score"] = score
            item["memory_score"] = 0.0
            item["agent_score"] = score
            item["final_score"] = score
            item["score"] = score
            item["reason"] = "Fallback recommendation returned because AI ranking was unavailable."
            item["explanation"] = item["reason"]
            item["llm_fallback"] = True
            items.append(item)

        items = sorted(items, key=lambda item: item["final_score"], reverse=True)[:limit]

        return {
            "agent_enabled": True,
            "query_intent": understanding.intent,
            "query_category": understanding.category,
            "expanded_queries": expanded_queries,
            "memory_hits": [],
            "memory_score": 0.0,
            "memory_profile": {
                "recent_query_count": 0,
                "top_categories": [],
                "category_weights": {},
                "long_term_preference_vector": {},
                "decay_function": "0.85 ** recency_index",
            },
            "user_preference_summary": "Fallback mode; memory profile unavailable.",
            "memory": {
                "enabled": False,
                "recent_queries": [],
            },
            "fallback_reason": fallback_reason,
            "items": items,
            "count": len(items),
            "all_jade": all(item.get("category") == "jade" for item in items),
        }

    async def _safe_rollback(self) -> None:
        try:
            await self.db.rollback()
        except Exception:
            return

    def _price_score(self, price) -> float:
        try:
            value = float(price)
        except (TypeError, ValueError):
            return 0.0
        if value <= 0:
            return 0.0
        ceiling = 20000.0
        return round(max(0.0, 1.0 - min(value, ceiling) / ceiling), 6)

    def _business_score(self, price, product_or_candidate=None) -> float:
        price_score = self._price_score(price)
        popularity_score = 0.0
        if isinstance(product_or_candidate, dict):
            for key in ("popularity", "sales", "sales_count"):
                value = product_or_candidate.get(key)
                if value is None:
                    continue
                try:
                    popularity_score = min(max(float(value), 0.0) / 1000.0, 1.0)
                    break
                except (TypeError, ValueError):
                    continue
        return round(min(price_score * 0.8 + popularity_score * 0.2, 1.0), 6)

    def _cache_key(self, query: str, limit: int) -> str:
        normalized = " ".join((query or "").strip().lower().split())
        digest = sha256(f"{self.CACHE_VERSION}:{normalized}:{limit}".encode("utf-8")).hexdigest()
        return f"recommendation:response:{digest}"

    async def _get_cached_response(self, cache_key: str) -> dict | None:
        if cache_key in self._response_cache:
            expires_at, cached_response = self._response_cache[cache_key]
            if expires_at > time():
                cached = dict(cached_response)
                cached["cache_hit"] = True
                return cached
            self._response_cache.pop(cache_key, None)

        try:
            raw_response = await redis_client.get(cache_key)
        except Exception:
            return None
        if not raw_response:
            return None

        try:
            response = json.loads(raw_response)
        except json.JSONDecodeError:
            return None
        response["cache_hit"] = True
        self._response_cache[cache_key] = (time() + self.RESPONSE_CACHE_TTL_SECONDS, response)
        return response

    async def _set_cached_response(self, cache_key: str, response: dict) -> None:
        self._response_cache[cache_key] = (time() + self.RESPONSE_CACHE_TTL_SECONDS, dict(response))
        try:
            await redis_client.setex(
                cache_key,
                self.RESPONSE_CACHE_TTL_SECONDS,
                json.dumps(response, ensure_ascii=False),
            )
        except Exception:
            return
