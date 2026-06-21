import { MemoryPanel } from "../components/MemoryPanel";
import { ProductCard } from "../components/ProductCard";
import { TopBar, MobileShell, SectionTitle } from "../components/Layout";
import { useRecommendation } from "../context/RecommendationContext";
import { navigate } from "../utils/router";

export function RecommendationFeed() {
  const { items, latestResponse, expandedQueries, memoryProfile, userPreferenceSummary, loading } = useRecommendation();
  const isJadeChannel = latestResponse?.intent === "jade_query";

  return (
    <MobileShell>
      <TopBar title="商品推荐流" onBack={() => navigate("chat")} />
      <section className="feed-hero">
        <span>AI + 翡翠电商</span>
        <h1>按种水、预算、圈口和收藏价值重排货源</h1>
        <p>
          系统综合 embedding retrieval、query expansion graph、Redis memory personalization 与 LLM rerank，
          将翡翠语义需求转化为可比较的商品候选。
        </p>
      </section>

      <MemoryPanel expandedQueries={expandedQueries} memoryProfile={memoryProfile} summary={userPreferenceSummary} />

      <SectionTitle
        title={isJadeChannel && latestResponse?.query ? `“${latestResponse.query}” 的推荐` : "需求结构化结果"}
        action={loading ? <span className="small-muted">匹配中</span> : null}
      />
      {isJadeChannel && items.length ? (
        <div className="feed-list">
          {items.map((item, index) => (
            <ProductCard key={item.id} product={item} index={index} />
          ))}
        </div>
      ) : (
        <section className="empty-panel">
          <h2>{latestResponse?.jade_requirement_spec?.title || "暂无商品推荐"}</h2>
          <p>{latestResponse?.jade_requirement_spec?.short_description || "当前输入未进入翡翠商品推荐链路，不展示兜底商品。"}</p>
          <div className="chip-row">
            {(latestResponse?.suggestions || []).map((suggestion) => (
              <span key={suggestion}>{suggestion}</span>
            ))}
          </div>
        </section>
      )}
    </MobileShell>
  );
}
