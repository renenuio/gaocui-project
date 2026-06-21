import json

from app.agent.recommendation_agent import RecommendationAgent


def jade_candidates():
    return [
        {
            "id": 1,
            "name": "冰种翡翠手镯",
            "description": "冰种正圈翡翠手镯",
            "category": "jade",
            "price": "12800",
            "distance": 0.1,
        },
        {
            "id": 2,
            "name": "糯种飘花翡翠手镯",
            "description": "飘花翡翠手镯",
            "category": "jade",
            "price": "6800",
            "distance": 0.25,
        },
        {
            "id": 3,
            "name": "翡翠福豆吊坠",
            "description": "天然翡翠福豆吊坠",
            "category": "jade",
            "price": "2600",
            "distance": 0.4,
        },
        {
            "id": 4,
            "name": "智能运动手表",
            "description": "电子产品",
            "category": "electronics",
            "price": "499",
            "distance": 0.02,
        },
    ]


def assert_contract(response):
    for key in ["intent", "query", "suggestions", "items", "all_jade", "count"]:
        assert key in response, key
    assert response["count"] == len(response["items"])


def run():
    agent = RecommendationAgent()
    understanding = agent.understand_query("翡翠手镯")
    jade_response = agent.normalize_contract_response(
        {
            "query": "翡翠手镯",
            "intent": "jade_query",
            "items": agent.rerank(
                "翡翠手镯",
                understanding,
                ["翡翠手镯", "jade", "bracelet"],
                jade_candidates(),
                [],
                [],
                {"category_weights": {}},
                "No stable user preference detected.",
            ),
        }
    )
    non_jade_response = agent.normalize_contract_response(agent.non_jade_requirement_response("我想买iPhone", "non_jade_query"))
    general_response = agent.normalize_contract_response(agent.non_jade_requirement_response("你好", "general_query"))
    session_id = "contract-session"
    agent.update_session_profile(session_id, "预算2万冰种翡翠手镯", "jade_query")
    followup_intent = agent.classify_intent_with_session("便宜点", agent.get_session_profile(session_id))

    assert_contract(jade_response)
    assert jade_response["intent"] == "jade_query"
    assert jade_response["count"] == 3
    assert jade_response["all_jade"] is True
    assert all(item["category"] == "jade" for item in jade_response["items"])

    assert_contract(non_jade_response)
    assert non_jade_response["intent"] == "non_jade_query"
    assert non_jade_response["items"] == []
    assert non_jade_response["jade_requirement_spec"]["title"]

    assert_contract(general_response)
    assert general_response["intent"] == "general_query"
    assert general_response["items"] == []
    assert general_response["jade_requirement_spec"]["title"]

    assert followup_intent == "jade_query"

    result = {
        "jade_query": {
            "count": jade_response["count"],
            "all_jade": jade_response["all_jade"],
            "top1": jade_response["items"][0]["name"],
        },
        "non_jade_query": {
            "items_empty": non_jade_response["items"] == [],
            "spec_present": bool(non_jade_response["jade_requirement_spec"]["title"]),
        },
        "general_query": {
            "items_empty": general_response["items"] == [],
            "spec_present": bool(general_response["jade_requirement_spec"]["title"]),
        },
        "session_carry_over": {
            "followup_intent": followup_intent,
            "profile": agent.get_session_profile(session_id),
        },
        "fallback_safety": {
            "non_jade_product_pollution": len(non_jade_response["items"]),
            "general_product_pollution": len(general_response["items"]),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run()
