import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.core.redis import redis_client


@dataclass(frozen=True)
class QueryUnderstanding:
    intent: str
    category: str | None
    keywords: list[str]
    structured_query: dict[str, Any] | None = None


class RecommendationAgent:
    """Dual-channel AI layer.

    JADE_CHANNEL is the product recommendation engine.
    NON_JADE_CHANNEL is the scene understanding and requirement generation system.
    The two channels must not share embedding, ranking, product generation, or fallback paths.
    """

    _memory: dict[str, deque[str]] = defaultdict(lambda: deque(maxlen=5))
    _session_profiles: dict[str, dict[str, Any]] = defaultdict(dict)
    _llm_executor = ThreadPoolExecutor(max_workers=4)
    MEMORY_LIMIT = 20
    MEMORY_TTL_SECONDS = 7 * 24 * 60 * 60
    LLM_RERANK_LIMIT = 12
    LLM_TIMEOUT_SECONDS = 4.0
    CARD_LIMIT = 3
    JADE_RELATED_TERMS = {
        "翡翠",
        "玉",
        "玉石",
        "玉镯",
        "手镯",
        "镯",
        "冰种",
        "糯种",
        "飘花",
        "紫罗兰",
        "福豆",
        "葫芦",
        "a货",
        "A货",
        "jade",
        "bracelet",
        "bangle",
    }

    CATEGORY_KEYWORDS: dict[str, set[str]] = {
        "beauty": {"护肤", "美妆", "补水", "敏感肌", "保湿", "修护", "皮肤"},
        "bag": {"包", "背包", "通勤", "差旅", "电脑包", "收纳"},
        "home": {"家用", "家庭", "清洁", "空气", "净化", "宠物", "母婴", "扫地", "新房"},
        "electronics": {"智能", "手表", "运动", "心率", "睡眠", "电子", "健身"},
        "education": {"学习", "儿童", "孩子", "课程", "绘本", "小学", "护眼"},
        "food": {"营养", "代餐", "蛋白", "健身", "控糖", "低脂", "饱腹"},
        "office": {"办公", "久坐", "椅子", "腰背", "扶手", "工学"},
        "travel": {"旅行", "户外", "露营", "便携", "咖啡", "差旅"},
        "camera": {"摄影", "相机", "拍摄", "人像", "短视频", "画质"},
        "jewelry": {"珠宝", "首饰", "戒指", "项链", "吊坠", "耳坠", "珍珠", "镶嵌"},
        "jade": {"翡翠", "玉", "玉石", "手镯", "玉镯", "飘花", "冰种", "糯种", "紫罗兰", "福豆", "葫芦"},
        "gemstone": {"宝石", "玉石", "和田玉", "玛瑙", "水晶", "天然石", "珠串"},
        "accessory": {"配饰", "手链", "手串", "耳饰", "挂件", "搭配"},
    }

    RELATED_CATEGORIES: dict[str, set[str]] = {
        "jade": {"jewelry", "gemstone", "accessory"},
        "jewelry": {"jade", "gemstone", "accessory"},
        "gemstone": {"jade", "jewelry", "accessory"},
        "accessory": {"jade", "jewelry", "gemstone"},
    }

    EXPANSION_DICTIONARY: dict[str, list[str]] = {
        "翡翠": ["jade"],
        "玉石": ["jade", "stone"],
        "手镯": ["bracelet", "jade bracelet"],
        "咖啡机": ["coffee machine", "espresso machine"],
    }

    SYNONYM_GRAPH: dict[str, list[str]] = {
        "jade": ["jewelry"],
        "jewelry": ["gemstone"],
        "gemstone": ["bracelet"],
        "bracelet": ["luxury accessory"],
        "luxury accessory": ["accessory"],
        "stone": ["gemstone", "luxury jewelry"],
        "luxury jewelry": ["jewelry"],
        "coffee machine": ["espresso machine"],
        "espresso machine": ["coffee maker"],
    }

    SYNONYM_EDGE_WEIGHTS: dict[tuple[str, str], float] = {
        ("jade", "jewelry"): 0.95,
        ("jewelry", "gemstone"): 0.85,
        ("gemstone", "bracelet"): 0.75,
        ("bracelet", "luxury accessory"): 0.7,
        ("luxury accessory", "accessory"): 0.7,
        ("stone", "gemstone"): 0.85,
        ("stone", "luxury jewelry"): 0.75,
        ("luxury jewelry", "jewelry"): 0.9,
        ("coffee machine", "espresso machine"): 0.9,
        ("espresso machine", "coffee maker"): 0.8,
    }

    async def recommend(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        limit: int,
        user_key: str = "anonymous",
        understanding: QueryUnderstanding | None = None,
        expanded_queries: list[str] | None = None,
    ) -> dict[str, Any]:
        intent = self.classify_intent(query)
        if intent != "jade_query":
            return self.non_jade_requirement_response(query, intent)

        understanding = understanding or self.understand_query(query)
        expanded_queries = expanded_queries or self.expand_query(query, understanding)
        recent_queries = await self._get_memory(user_key)
        memory_hits = self._memory_hits(query, expanded_queries, recent_queries)
        memory_profile = self._memory_profile(recent_queries)
        user_preference_summary = self._user_preference_summary(memory_profile)
        ranked_items = self.rerank(
            query,
            understanding,
            expanded_queries,
            candidates,
            recent_queries,
            memory_hits,
            memory_profile,
            user_preference_summary,
        )
        await self._remember(user_key, query)

        items = ranked_items[: self.CARD_LIMIT]
        return self.normalize_contract_response({
            "agent_enabled": True,
            "intent": intent,
            "jade_scene_query": query,
            "jade_scene_mapping": self.jade_scene_mapping(query, query),
            "scene_mapping": self.jade_scene_mapping(query, query),
            "jade_requirement_spec": self.generate_jade_requirement_spec(query, query),
            "query_intent": understanding.intent,
            "query_category": understanding.category,
            "expanded_queries": expanded_queries,
            "memory_hits": memory_hits,
            "memory_score": self._response_memory_score(memory_hits, recent_queries),
            "memory_profile": memory_profile,
            "user_preference_summary": user_preference_summary,
            "memory": {
                "enabled": True,
                "recent_queries": recent_queries,
            },
            "items": items,
            "count": len(items),
            "all_jade": all(item.get("category") == "jade" for item in items),
        })

    def understand_query(self, query: str) -> QueryUnderstanding:
        normalized = (query or "").strip().lower()
        keywords = self._extract_keywords(normalized)
        structured_query = self.normalize_query(query)

        category_scores = {
            category: sum(1 for keyword in keywords if keyword in category_keywords or keyword == category)
            for category, category_keywords in self.CATEGORY_KEYWORDS.items()
        }
        category, score = max(category_scores.items(), key=lambda item: item[1])
        matched_category = structured_query.get("category") or (category if score > 0 else "jade")

        if any(word in normalized for word in ["适合", "推荐", "买", "选择", "需要"]):
            intent = "product_recommendation"
        elif any(word in normalized for word in ["比较", "区别", "哪个好"]):
            intent = "product_comparison"
        else:
            intent = "general_recommendation"

        return QueryUnderstanding(
            intent=intent,
            category=matched_category,
            keywords=keywords,
            structured_query=structured_query,
        )

    def route_query(self, query: str) -> str:
        return self.classify_intent(query)

    def classify_intent(self, query: str) -> str:
        normalized = (query or "").strip().lower()
        if self.is_jade_related(query):
            return "jade_query"
        if not normalized:
            return "general_query"
        if self._is_general_query(normalized):
            return "general_query"
        if self._has_purchase_signal(normalized):
            return "non_jade_query"
        return "general_query"

    def classify_intent_with_session(self, query: str, session_profile: dict[str, Any] | None = None) -> str:
        intent = self.classify_intent(query)
        if intent == "general_query" and session_profile and session_profile.get("last_intent") == "jade_query":
            if self._is_followup_query(query):
                return "jade_query"
        return intent

    def _has_purchase_signal(self, normalized: str) -> bool:
        terms = ["买", "想要", "我要", "推荐", "送礼", "礼物", "预算", "需要", "看看", "找"]
        return any(term in normalized for term in terms)

    def _is_general_query(self, normalized: str) -> bool:
        terms = ["你好", "hello", "hi", "天气", "几点", "谢谢", "你是谁", "怎么用", "帮助"]
        return any(term in normalized for term in terms)

    def _is_followup_query(self, query: str) -> bool:
        normalized = (query or "").strip().lower()
        terms = ["便宜", "贵", "换", "还有", "类似", "大点", "小点", "冰种", "糯种", "手镯", "吊坠", "戒指", "预算"]
        return any(term in normalized for term in terms)

    def is_jade_related(self, query: str) -> bool:
        normalized = (query or "").strip().lower()
        return any(term.lower() in normalized for term in self.JADE_RELATED_TERMS)

    def map_to_jade_scene(self, query: str) -> str:
        normalized = (query or "").strip().lower()
        if not normalized:
            return "日常佩戴轻奢翡翠手串"
        if "iphone" in normalized or "手机" in normalized:
            return "商务高端翡翠手镯"
        if "辣条" in normalized or "零食" in normalized:
            return "日常轻奢翡翠吊坠"
        if "游戏" in normalized or "电竞" in normalized:
            return "年轻人潮流翡翠戒指"
        if "奶茶" in normalized or "饮品" in normalized:
            return "日常佩戴翡翠手串"
        return "送礼收藏两用翡翠手镯"

    def non_jade_requirement_response(self, query: str, intent: str | None = None) -> dict[str, Any]:
        # PRD boundary: NON_JADE must not enter embedding, vector search, ranking, product generation, or jade fallback.
        # It can only return scene understanding, requirement spec, and UI suggestions.
        detected_intent = intent or self.classify_intent(query)
        jade_scene_query = self.map_to_jade_scene(query)
        return {
            "agent_enabled": True,
            "query": query,
            "intent": detected_intent,
            "jade_scene_mapping": self.jade_scene_mapping(query, jade_scene_query),
            "scene_mapping": self.jade_scene_mapping(query, jade_scene_query),
            "jade_requirement_spec": self.generate_jade_requirement_spec(query, jade_scene_query),
            "suggestions": self.non_jade_suggestions(jade_scene_query),
            "query_intent": "requirement_generation",
            "query_category": None,
            "expanded_queries": [],
            "memory_hits": [],
            "memory_score": 0.0,
            "memory_profile": {
                "recent_query_count": 0,
                "top_categories": [],
                "category_weights": {},
                "long_term_preference_vector": {},
                "decay_function": "0.85 ** recency_index",
            },
            "user_preference_summary": "NON_JADE isolated flow; recommendation pipeline was not executed.",
            "memory": {"enabled": False, "recent_queries": []},
            "items": [],
            "count": 0,
            "all_jade": False,
        }

    def non_jade_suggestions(self, jade_scene_query: str) -> list[str]:
        return [
            f"可继续补充预算范围，用于细化“{jade_scene_query}”需求。",
            "可说明自戴或送礼对象，便于调整款式与寓意。",
            "可选择偏好：手镯、吊坠、戒指、手串。",
        ]

    def jade_scene_mapping(self, query: str, jade_scene_query: str | None = None) -> str:
        normalized = (query or "").strip()
        scene_query = jade_scene_query or (query if self.is_jade_related(query) else self.map_to_jade_scene(query))
        if not normalized:
            return f"将空输入转化为翡翠消费场景：{scene_query}。"
        return f"基于原始需求“{normalized}”，转化为翡翠消费场景：{scene_query}。"

    def generate_jade_requirement_spec(self, query: str, jade_scene_query: str | None = None) -> dict[str, Any]:
        scene_query = jade_scene_query or (query if self.is_jade_related(query) else self.map_to_jade_scene(query))
        profile = self._scene_product_profile(scene_query)
        title = profile["title"]
        short_description = profile["short_description"]
        detailed_description = (
            f"用户原始需求经过场景理解后，转化为“{scene_query}”这一翡翠消费场景。"
            f"该需求适合追求{profile['style']}、注重{profile['emotional_value']}的人群，"
            f"重点不是照搬原始输入，而是提炼其背后的生活方式、身份表达与情绪价值。"
            f"在实际购买中，可围绕{profile['category']}展开，选择{profile['quality']}、"
            f"{profile['color']}等更能体现质感的特征，兼顾日常佩戴、商务社交、节日送礼或个人收藏。"
            f"整体需求强调自然材质、舒适佩戴和体面表达，让翡翠成为生活升级、审美表达与情感传递的载体。"
            f"设计上应避免过度繁复，突出主石的水润感、颜色稳定性和轮廓辨识度；"
            f"预算配置可优先保障主石品质，其次考虑镶嵌材质与配件完整度。"
            f"若用于送礼，应强化寓意、包装和证书可信度；若用于自戴，则更重视尺寸适配、佩戴舒适度与日常搭配性。"
        )
        return {
            "title": title,
            "short_description": short_description,
            "detailed_description": detailed_description,
            "tags": [
                profile["style"],
                profile["category"],
                profile["use_case"],
                profile["quality"],
                profile["audience"],
                "轻奢",
                "天然翡翠",
                "礼赠自戴",
                "温润细腻",
                "重视品位人群",
            ],
            "parameters": {
                "产品品类": profile["category"],
                "核心卖点": profile["selling_point"],
                "主石材质": "天然翡翠",
                "翡翠造型": profile["shape"],
                "翡翠种水": profile["quality"],
                "翡翠颜色": profile["color"],
                "配石材质": "可选小颗粒天然宝石或珍珠点缀",
                "镶嵌工艺": profile["craft"],
                "瑕疵情况": "少棉少裂，肉眼观感干净",
                "款式风格": profile["style"],
                "适用场景": profile["use_case"],
                "产品寓意": profile["meaning"],
                "镶嵌材质": profile["metal"],
                "镶嵌配件": profile["accessory"],
                "尺寸规格": profile["size"],
            },
            "top_10_tags_table": [
                {"维度": "style", "标签": profile["style"]},
                {"维度": "category", "标签": profile["category"]},
                {"维度": "use case", "标签": profile["use_case"]},
                {"维度": "quality", "标签": profile["quality"]},
                {"维度": "audience", "标签": profile["audience"]},
                {"维度": "style", "标签": "轻奢"},
                {"维度": "category", "标签": "天然翡翠"},
                {"维度": "use case", "标签": "礼赠自戴"},
                {"维度": "quality", "标签": "温润细腻"},
                {"维度": "audience", "标签": "重视品位人群"},
            ],
            "product_parameter_table": {
                "产品品类": profile["category"],
                "核心卖点": profile["selling_point"],
                "主石材质": "天然翡翠",
                "翡翠造型": profile["shape"],
                "翡翠种水": profile["quality"],
                "翡翠颜色": profile["color"],
                "配石材质": "可选小颗粒天然宝石或珍珠点缀",
                "镶嵌工艺": profile["craft"],
                "瑕疵情况": "少棉少裂，肉眼观感干净",
                "款式风格": profile["style"],
                "适用场景": profile["use_case"],
                "产品寓意": profile["meaning"],
                "镶嵌材质": profile["metal"],
                "镶嵌配件": profile["accessory"],
                "尺寸规格": profile["size"],
            },
        }

    def _scene_product_profile(self, jade_scene_query: str) -> dict[str, str]:
        normalized = (jade_scene_query or "").strip().lower()
        if "手镯" in normalized:
            return {
                "title": "高端翡翠手镯",
                "short_description": "适合商务礼赠与身份表达的高端手镯需求",
                "category": "翡翠手镯",
                "shape": "圆条或正圈手镯",
                "quality": "冰种或高冰种",
                "color": "晴水绿、淡阳绿或飘花",
                "style": "端庄高雅",
                "use_case": "商务社交、重要礼赠、收藏佩戴",
                "audience": "成熟商务人群",
                "selling_point": "通透水润、佩戴体面、具有身份象征",
                "emotional_value": "成就感与体面感",
                "meaning": "圆满顺遂、事业稳健",
                "craft": "素面精抛或贵金属轻镶",
                "metal": "18K金或素面无镶嵌",
                "accessory": "证书、礼盒、保养配件",
                "size": "圈口按手围定制，常见52-58mm",
            }
        if "戒指" in normalized:
            return {
                "title": "潮流翡翠戒指",
                "short_description": "适合年轻表达与日常搭配的翡翠戒指需求",
                "category": "翡翠戒指",
                "shape": "蛋面或几何戒面",
                "quality": "糯冰种或冰种",
                "color": "阳绿、晴水或紫罗兰",
                "style": "年轻潮流",
                "use_case": "日常穿搭、聚会社交、个性表达",
                "audience": "年轻时尚人群",
                "selling_point": "小体量高辨识度，适合潮流搭配",
                "emotional_value": "个性与身份认同",
                "meaning": "自信表达、好运随行",
                "craft": "18K金镶嵌",
                "metal": "18K金",
                "accessory": "戒托、证书、礼盒",
                "size": "戒圈按手寸定制",
            }
        if "手串" in normalized:
            return {
                "title": "日常翡翠手串",
                "short_description": "适合轻松佩戴与生活方式升级的手串需求",
                "category": "翡翠手串",
                "shape": "圆珠手串",
                "quality": "细糯种或糯冰种",
                "color": "浅绿、晴水或多彩搭配",
                "style": "轻奢休闲",
                "use_case": "通勤、休闲、朋友聚会",
                "audience": "日常佩戴人群",
                "selling_point": "佩戴舒适，兼具装饰与轻收藏属性",
                "emotional_value": "生活品质升级",
                "meaning": "平安喜乐、日日顺遂",
                "craft": "弹力绳串珠或贵金属隔珠",
                "metal": "可选18K金隔珠",
                "accessory": "隔珠、吊牌、礼盒",
                "size": "珠径6-10mm，手围可调",
            }
        return {
            "title": "轻奢翡翠吊坠",
            "short_description": "适合日常佩戴与礼赠表达的翡翠吊坠需求",
            "category": "翡翠吊坠",
            "shape": "福豆、平安扣或葫芦",
            "quality": "糯冰种或冰种",
            "color": "阳绿、晴水或飘花",
            "style": "精致轻奢",
            "use_case": "日常佩戴、节日礼物、生活方式升级",
            "audience": "注重精致感人群",
            "selling_point": "小巧精致、寓意明确、佩戴门槛低",
            "emotional_value": "愉悦感与仪式感",
            "meaning": "平安纳福、福气常伴",
            "craft": "18K金扣头或简约镶嵌",
            "metal": "18K金或925银",
            "accessory": "扣头、项链、证书、礼盒",
            "size": "主石约10-25mm，链长约40-45cm",
        }

    def normalize_contract_response(self, response: dict[str, Any]) -> dict[str, Any]:
        raw_items = response.get("items", [])
        jade_items = [
            item
            for item in raw_items
            if isinstance(item, dict) and item.get("category") == "jade"
        ]
        items = [self.normalize_contract_item(item) for item in jade_items[: self.CARD_LIMIT]]
        response["query"] = response.get("query") or ""
        response["items"] = items
        response["suggestions"] = response.get("suggestions") or []
        response["count"] = len(items)
        response["all_jade"] = bool(items) and all(item.get("category") == "jade" for item in items)
        return response

    def normalize_contract_item(self, item: dict[str, Any]) -> dict[str, Any]:
        images = item.get("images") if isinstance(item.get("images"), list) else []
        image = item.get("image") or item.get("imageUrl") or (images[0] if images else None)
        final_score = float(item.get("final_score") or item.get("score") or 0.0)
        return {
            **item,
            "id": str(item.get("id")),
            "name": str(item.get("name") or ""),
            "price": self._numeric_price(item.get("price")),
            "image": image or "/assets/jade-bangle-1.png",
            "category": "jade",
            "embedding_similarity": float(item.get("embedding_similarity") or 0.0),
            "category_match_score": float(item.get("category_match_score") or 1.0),
            "business_score": float(item.get("business_score") or 0.0),
            "final_score": final_score,
            "score": final_score,
        }

    def _numeric_price(self, price: Any) -> float:
        try:
            return float(price)
        except (TypeError, ValueError):
            return 0.0

    def get_session_profile(self, session_id: str) -> dict[str, Any]:
        return dict(self._session_profiles[session_id])

    async def get_session_profile_async(self, session_id: str) -> dict[str, Any]:
        try:
            raw = await redis_client.get(self._session_profile_key(session_id))
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    self._session_profiles[session_id] = data
                    return dict(data)
        except Exception:
            pass
        return self.get_session_profile(session_id)

    def update_session_profile(self, session_id: str, query: str, intent: str) -> dict[str, Any]:
        profile = dict(self._session_profiles[session_id])
        profile["last_intent"] = intent
        profile["last_query"] = query
        budget = self._extract_budget(query)
        product_type = self._extract_product_type(query)
        quality = self._extract_quality(query)
        if budget is not None:
            profile["budget"] = budget
        if product_type:
            profile["type"] = product_type
        if quality:
            profile["quality"] = quality
        self._session_profiles[session_id] = profile
        return profile

    async def update_session_profile_async(self, session_id: str, query: str, intent: str) -> dict[str, Any]:
        profile = self.update_session_profile(session_id, query, intent)
        try:
            await redis_client.setex(
                self._session_profile_key(session_id),
                self.MEMORY_TTL_SECONDS,
                json.dumps(profile, ensure_ascii=False),
            )
        except Exception:
            pass
        return profile

    def _session_profile_key(self, session_id: str) -> str:
        return f"session:{session_id}:profile"

    def _extract_budget(self, query: str) -> float | None:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(万|w|W)?", query or "")
        if not match:
            return None
        value = float(match.group(1))
        return value * 10000 if match.group(2) else value

    def _extract_product_type(self, query: str) -> str | None:
        for value in ["手镯", "吊坠", "戒指", "手串", "平安扣"]:
            if value in (query or ""):
                return value
        return None

    def _extract_quality(self, query: str) -> str | None:
        for value in ["冰种", "糯种", "高冰", "玻璃种", "豆种"]:
            if value in (query or ""):
                return value
        return None

    def normalize_query(self, query: str) -> dict[str, Any]:
        normalized = (query or "").strip().lower()
        structured_query: dict[str, Any] = {
            "category": "jade",
            "type": None,
            "quality": None,
            "intent": "buy",
        }
        if "手镯" in normalized or "玉镯" in normalized or "bracelet" in normalized or "bangle" in normalized:
            structured_query["type"] = "bangle"
        if "冰种" in normalized:
            structured_query["quality"] = "ice"
        if "糯种" in normalized:
            structured_query["quality"] = "waxy"
        return structured_query

    def expand_query(self, query: str, understanding: QueryUnderstanding | None = None) -> list[str]:
        expanded = [query]
        normalized = (query or "").strip().lower()

        for keyword, expansions in self.EXPANSION_DICTIONARY.items():
            if keyword in normalized:
                expanded.extend(expansions)

        if understanding and understanding.category:
            expanded.append(understanding.category)
            expanded.extend(sorted(self.RELATED_CATEGORIES.get(understanding.category, set())))

        return self._expand_synonym_graph(expanded)

    def rerank(
        self,
        query: str,
        understanding: QueryUnderstanding,
        expanded_queries: list[str],
        candidates: list[dict[str, Any]],
        recent_queries: list[str],
        memory_hits: list[str],
        memory_profile: dict[str, Any],
        user_preference_summary: str,
    ) -> list[dict[str, Any]]:
        if not candidates:
            return []

        candidates = self._apply_domain_constraint(candidates, understanding.category)
        if not candidates:
            return []

        ranked_items = []
        memory_keywords = self._extract_keywords(" ".join([*memory_hits, user_preference_summary]))
        category_weights = memory_profile.get("category_weights", {})

        for candidate in candidates:
            item = dict(candidate)
            item["embedding_score"] = round(self._semantic_score(item.get("distance")), 6)
            item["embedding_similarity"] = self._candidate_embedding_similarity(item)
            item["category_match_score"] = self._candidate_category_match_score(item, understanding.category)
            item["price_score"] = self._price_score(item.get("price"))
            item["price_sort_value"] = self._price_sort_value(item.get("price"))
            item["popularity_score"] = self._popularity_score(item)
            item["business_score"] = self._candidate_business_score(item)
            item["llm_score"] = 0.0
            item["rank_score"] = item["embedding_similarity"]
            item["reason"] = self._structured_reason(item, understanding)
            item["memory_score"] = self._combined_memory_score(memory_keywords, category_weights, item)
            item["agent_score"] = self._business_score(
                item["embedding_similarity"],
                item["category_match_score"],
                item["business_score"],
            )
            item["final_score"] = item["agent_score"]
            item["score"] = item["final_score"]
            item["explanation"] = item["reason"]
            item["llm_fallback"] = False
            ranked_items.append(item)

        return sorted(
            ranked_items,
            key=lambda item: (
                item["final_score"],
                item["business_score"],
                item["embedding_similarity"],
            ),
            reverse=True,
        )

    def _llm_rerank(
        self,
        query: str,
        understanding: QueryUnderstanding,
        expanded_queries: list[str],
        candidates: list[dict[str, Any]],
        recent_queries: list[str],
        memory_hits: list[str],
        user_preference_summary: str,
    ) -> dict[str, Any]:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required for LLM rerank")

        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=3.5, max_retries=0)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=700,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": self._build_rerank_prompt(
                        query,
                        understanding,
                        expanded_queries,
                        candidates,
                        recent_queries,
                        memory_hits,
                        user_preference_summary,
                    ),
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)

    def _build_rerank_prompt(
        self,
        query: str,
        understanding: QueryUnderstanding,
        expanded_queries: list[str],
        candidates: list[dict[str, Any]],
        recent_queries: list[str],
        memory_hits: list[str],
        user_preference_summary: str,
    ) -> str:
        products = [
            {
                "id": candidate.get("id"),
                "name": candidate.get("name"),
                "description": self._truncate_text(candidate.get("description"), 80),
                "category": candidate.get("category"),
                "distance": round(float(candidate.get("distance") or 0.0), 4),
            }
            for candidate in candidates
        ]
        payload = {
            "task": "Return JSON only. Rank every product by query fit; lower distance is better.",
            "hard_rules": [
                "Do not recommend products outside the query category.",
                f"Only rank candidate products in category: {understanding.category}.",
                "Only sort the provided candidate set. Do not invent products.",
            ],
            "query": query,
            "intent": understanding.intent,
            "category": understanding.category,
            "structured_query": understanding.structured_query,
            "expanded": expanded_queries[:8],
            "memory_hits": memory_hits[:5],
            "preference": user_preference_summary,
            "products": products,
            "schema": {"results": [{"id": 1, "score": 0.92, "reason": "short reason"}]},
        }
        return json.dumps(payload, ensure_ascii=False)

    def _apply_domain_constraint(
        self,
        candidates: list[dict[str, Any]],
        category: str | None,
    ) -> list[dict[str, Any]]:
        constrained_category = category or "jade"
        return [
            candidate
            for candidate in candidates
            if candidate.get("category") == constrained_category
        ]

    def explain(
        self,
        query: str,
        candidate: dict[str, Any],
        understanding: QueryUnderstanding,
        category_score: float,
        name_score: float,
        memory_score: float,
    ) -> str:
        reasons = []
        if understanding.category and candidate.get("category") == understanding.category:
            reasons.append(f"商品类目与 query 判断的 {understanding.category} 场景匹配")
        elif category_score > 0:
            reasons.append(f"商品类目与 query 判断的 {understanding.category} 场景相关")
        if name_score > 0:
            reasons.append("商品名称或描述命中了用户需求关键词")
        if memory_score > 0:
            reasons.append("与最近查询偏好有轻量关联")
        if not reasons:
            reasons.append("向量距离较近，语义上与当前需求相关")

        distance = candidate.get("distance")
        if distance is not None:
            reasons.append(f"embedding distance={float(distance):.4f}")

        return "；".join(reasons)

    async def _remember(self, user_key: str, query: str) -> None:
        normalized = (query or "").strip()
        if not normalized:
            return

        self._memory[user_key].append(normalized)
        redis_key = self._memory_key(user_key)
        try:
            memory = await self._get_memory(user_key)
            memory = [normalized, *[item for item in memory if item != normalized]][: self.MEMORY_LIMIT]
            await redis_client.setex(
                redis_key,
                self.MEMORY_TTL_SECONDS,
                json.dumps(memory, ensure_ascii=False),
            )
        except Exception:
            return

    async def _get_memory(self, user_key: str) -> list[str]:
        redis_key = self._memory_key(user_key)
        try:
            raw_memory = await redis_client.get(redis_key)
            queries = json.loads(raw_memory) if raw_memory else []
        except Exception:
            return list(self._memory[user_key])
        if not isinstance(queries, list):
            return []
        return [str(query) for query in queries[: self.MEMORY_LIMIT] if query]

    def _memory_hits(self, query: str, expanded_queries: list[str], recent_queries: list[str]) -> list[str]:
        query_terms = set(self._extract_keywords(" ".join([query, *expanded_queries])))
        hits = []
        for recent_query in recent_queries:
            recent_terms = set(self._extract_keywords(recent_query))
            if query_terms & recent_terms:
                hits.append(recent_query)
        return hits

    def _response_memory_score(self, memory_hits: list[str], recent_queries: list[str]) -> float:
        if not recent_queries:
            return 0.0
        return round(min(len(memory_hits) / len(recent_queries), 1.0), 6)

    def _memory_key(self, user_key: str) -> str:
        return f"user:{user_key}:memory"

    def _expand_synonym_graph(self, seeds: list[str], max_depth: int = 5) -> list[str]:
        expanded = []
        queue = [(seed, 0, 1.0) for seed in seeds if seed]
        seen: dict[str, float] = {}

        while queue:
            term, depth, score = queue.pop(0)
            if seen.get(term, 0.0) >= score:
                continue
            seen[term] = score
            if score >= 0.2:
                expanded.append(term)

            if depth >= max_depth:
                continue
            for related_term in self.SYNONYM_GRAPH.get(term, []):
                edge_weight = self.SYNONYM_EDGE_WEIGHTS.get((term, related_term), 0.6)
                queue.append((related_term, depth + 1, score * edge_weight))

        return expanded

    def _memory_profile(self, recent_queries: list[str]) -> dict[str, Any]:
        category_counts = {category: 0.0 for category in self.CATEGORY_KEYWORDS}
        for index, query in enumerate(recent_queries):
            understanding = self.understand_query(query)
            if understanding.category:
                category_counts[understanding.category] += self._decay_weight(index)

        top_categories = [
            {"category": category, "weight": round(weight, 6)}
            for category, weight in sorted(category_counts.items(), key=lambda item: item[1], reverse=True)
            if weight > 0
        ][:5]
        total_weight = sum(category_counts.values()) or 1.0
        category_weights = {
            category: round(weight / total_weight, 6)
            for category, weight in category_counts.items()
            if weight > 0
        }
        return {
            "recent_query_count": len(recent_queries),
            "top_categories": top_categories,
            "category_weights": category_weights,
            "long_term_preference_vector": category_weights,
            "decay_function": "0.85 ** recency_index",
        }

    def _user_preference_summary(self, memory_profile: dict[str, Any]) -> str:
        top_categories = memory_profile.get("top_categories") or []
        if not top_categories:
            return "No stable user preference detected."

        preferences = ", ".join(
            f"{item['category']}({item['weight']})" for item in top_categories
        )
        return f"User recently prefers: {preferences}."

    def _decay_weight(self, recency_index: int) -> float:
        return 0.85 ** recency_index

    def _category_score(self, category: str | None, candidate: dict[str, Any]) -> float:
        if not category:
            return 0.0

        candidate_category = candidate.get("category")
        if candidate_category == category:
            return 1.0
        if candidate_category in self.RELATED_CATEGORIES.get(category, set()):
            return 0.6
        return 0.0

    def _text_match_score(self, keywords: list[str], candidate: dict[str, Any]) -> float:
        if not keywords:
            return 0.0

        text = " ".join(
            str(value or "").lower()
            for value in [candidate.get("name"), candidate.get("description"), candidate.get("category")]
        )
        matched = sum(1 for keyword in keywords if keyword and keyword in text)
        return min(matched / max(len(keywords), 1), 1.0)

    def _memory_score(self, memory_keywords: list[str], candidate: dict[str, Any]) -> float:
        return self._text_match_score(memory_keywords, candidate) if memory_keywords else 0.0

    def _combined_memory_score(
        self,
        memory_keywords: list[str],
        category_weights: dict[str, float],
        candidate: dict[str, Any],
    ) -> float:
        lexical_score = self._memory_score(memory_keywords, candidate)
        category_score = float(category_weights.get(str(candidate.get("category")), 0.0))
        return round(min(lexical_score * 0.6 + category_score * 0.4, 1.0), 6)

    def _hybrid_score(self, embedding_score: float, memory_score: float, llm_score: float) -> float:
        return round(
            min(embedding_score * 0.4 + memory_score * 0.3 + llm_score * 0.3, 1.0),
            6,
        )

    def _business_score(
        self,
        embedding_similarity: float,
        category_match_score: float,
        business_score: float,
    ) -> float:
        return round(
            min(category_match_score * 0.6 + embedding_similarity * 0.25 + business_score * 0.15, 1.0),
            6,
        )

    def _candidate_business_score(self, candidate: dict[str, Any]) -> float:
        price_score = candidate.get("price_score")
        if price_score is None:
            price_score = self._price_score(candidate.get("price"))
        popularity_score = self._popularity_score(candidate)
        return round(min(float(price_score) * 0.8 + popularity_score * 0.2, 1.0), 6)

    def _popularity_score(self, candidate: dict[str, Any]) -> float:
        for key in ("popularity", "sales", "sales_count"):
            value = candidate.get(key)
            if value is None:
                continue
            try:
                return round(min(max(float(value), 0.0) / 1000.0, 1.0), 6)
            except (TypeError, ValueError):
                continue
        return 0.0

    def _candidate_embedding_similarity(self, candidate: dict[str, Any]) -> float:
        if candidate.get("embedding_similarity") is not None:
            return float(candidate["embedding_similarity"])
        return round(self._semantic_score(candidate.get("distance")), 6)

    def _candidate_category_match_score(self, candidate: dict[str, Any], category: str | None) -> float:
        if candidate.get("category_match_score") is not None:
            return float(candidate["category_match_score"])
        return 1.0 if candidate.get("category") == (category or "jade") else 0.0

    def _price_sort_value(self, price: Any) -> float:
        try:
            return float(price)
        except (TypeError, ValueError):
            return float("inf")

    def _price_score(self, price: Any) -> float:
        try:
            value = float(price)
        except (TypeError, ValueError):
            return 0.0
        if value <= 0:
            return 0.0

        ceiling = 20000.0
        return round(max(0.0, 1.0 - min(value, ceiling) / ceiling), 6)

    def _structured_reason(self, item: dict[str, Any], understanding: QueryUnderstanding) -> str:
        structured_query = understanding.structured_query or {}
        parts = [f"商品属于{understanding.category}类目，符合翡翠需求"]
        if structured_query.get("type") == "bangle" and "手镯" in str(item.get("name", "")):
            parts.append("款式匹配手镯需求")
        if structured_query.get("quality") == "ice" and "冰种" in str(item.get("name", "")):
            parts.append("种水匹配冰种偏好")
        parts.append("按类目约束与向量相似度排序")
        return "；".join(parts)

    def _embedding_fallback_ranking(self, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = sorted(candidates, key=lambda item: self._semantic_score(item.get("distance")), reverse=True)
        return {
            "results": [
                {
                    "id": item.get("id"),
                    "score": self._semantic_score(item.get("distance")),
                    "reason": "LLM unavailable; fallback ranking used embedding similarity.",
                }
                for item in ranked
            ]
        }

    def evaluate_recall_at_k(
        self,
        ranked_items: list[dict[str, Any]],
        relevant_ids: set[int],
        k: int = 5,
    ) -> float:
        if not relevant_ids:
            return 0.0
        top_ids = {int(item["id"]) for item in ranked_items[:k] if "id" in item}
        return round(len(top_ids & relevant_ids) / len(relevant_ids), 6)

    def ranking_consistency_check(
        self,
        first_ranking: list[dict[str, Any]],
        second_ranking: list[dict[str, Any]],
        k: int = 5,
    ) -> bool:
        first_ids = [item.get("id") for item in first_ranking[:k]]
        second_ids = [item.get("id") for item in second_ranking[:k]]
        return first_ids == second_ids

    def _truncate_text(self, value: Any, max_length: int) -> str | None:
        if value is None:
            return None
        text = str(value)
        if len(text) <= max_length:
            return text
        return text[:max_length]

    def _semantic_score(self, distance: Any) -> float:
        if distance is None:
            return 0.0

        value = max(float(distance), 0.0)
        return max(0.0, 1.0 - min(value, 2.0) / 2.0)

    def _extract_keywords(self, text: str) -> list[str]:
        normalized = (text or "").strip().lower()
        if not normalized:
            return []

        compact = "".join(char for char in normalized if not char.isspace())
        tokens = normalized.split()
        tokens.extend(
            keyword
            for keywords in self.CATEGORY_KEYWORDS.values()
            for keyword in keywords
            if keyword in compact
        )
        return list(dict.fromkeys(token for token in tokens if token))
