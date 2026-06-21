from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.recommendation_agent import RecommendationAgent
from app.db.session import get_db
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


class RecommendationRequest(BaseModel):
    query: str
    limit: int = 10
    sessionId: str | None = None


class SessionRequest(BaseModel):
    sessionId: str | None = None


class UploadRequest(BaseModel):
    image: str | None = None
    filename: str | None = None


class GenerateProductRequest(BaseModel):
    images: list[str]


@router.post("/recommendations")
async def recommend(payload: RecommendationRequest, db: AsyncSession = Depends(get_db)):
    session_id = payload.sessionId or "anonymous"
    try:
        return await AIService(db).recommend(payload.query, payload.limit, session_id=session_id)
    except Exception as exc:
        limit = 3
        agent = RecommendationAgent()
        intent = agent.classify_intent_with_session(payload.query, agent.get_session_profile(session_id))
        if intent != "jade_query":
            # PRD boundary: NON_JADE API fallback must not return jade products or enter recommendation fallback.
            return agent.normalize_contract_response({
                "embedding_enabled": False,
                "seed_created": False,
                "cache_hit": False,
                "fallback": False,
                "fallback_reason": f"api_boundary_failed: {type(exc).__name__}",
                "sessionId": session_id,
                **agent.non_jade_requirement_response(payload.query, intent),
            })

        jade_scene_query = payload.query
        return agent.normalize_contract_response({
            "sessionId": session_id,
            "query": payload.query,
            "intent": intent,
            "jade_scene_query": jade_scene_query,
            "jade_scene_mapping": agent.jade_scene_mapping(payload.query, jade_scene_query),
            "scene_mapping": agent.jade_scene_mapping(payload.query, jade_scene_query),
            "jade_requirement_spec": agent.generate_jade_requirement_spec(payload.query, jade_scene_query),
            "embedding_enabled": False,
            "seed_created": False,
            "cache_hit": False,
            "fallback": True,
            "fallback_reason": f"api_boundary_failed: {type(exc).__name__}",
            "agent_enabled": False,
            "query_intent": "fallback",
            "query_category": "jade",
            "expanded_queries": [jade_scene_query],
            "memory_hits": [],
            "memory_score": 0.0,
            "memory_profile": {
                "recent_query_count": 0,
                "top_categories": [],
                "category_weights": {},
                "long_term_preference_vector": {},
            },
            "user_preference_summary": "Fallback mode; AI service unavailable.",
            "memory": {"enabled": False, "recent_queries": []},
            "items": [],
            "count": 0,
            "all_jade": False,
        })


@router.post("/session")
async def session(payload: SessionRequest):
    session_id = payload.sessionId or "anonymous"
    agent = RecommendationAgent()
    return {
        "sessionId": session_id,
        "memory": await agent.get_session_profile_async(session_id),
    }


@router.post("/upload")
async def upload(payload: UploadRequest):
    return {
        "imageId": "ai-upload-image",
        "filename": payload.filename or "upload.jpg",
        "parsed": {
            "category": "jade",
            "quality": "unknown",
            "color": "unknown",
        },
    }


@router.post("/generate-product")
async def generate_product(payload: GenerateProductRequest):
    if not payload.images:
        return {"detail": "At least one image is required"}
    return {
        "name": "翡翠商品",
        "description": "根据上传图片生成的翡翠商品简介，请商家确认后发布。",
        "detail": "系统已接收商家上传图片，并生成可编辑商品详情。发布前请核对种水、颜色、瑕疵、尺寸和证书信息。",
        "category": "jade",
        "price": None,
        "imageUrl": payload.images[0],
        "images": payload.images,
        "tags": ["翡翠", "天然A货", "待商家确认"],
        "status": "active",
    }


def _is_jade_related(query: str) -> bool:
    terms = ["翡翠", "玉", "玉石", "玉镯", "手镯", "镯", "冰种", "糯种", "飘花", "紫罗兰", "a货", "A货", "jade", "bracelet", "bangle"]
    normalized = (query or "").strip().lower()
    return any(term.lower() in normalized for term in terms)
