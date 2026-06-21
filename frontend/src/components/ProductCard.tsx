import type { Product, RecommendationItem } from "../types";
import { formatPrice, withJadePresentation } from "../data/jadeCatalog";
import { navigate } from "../utils/router";

type ProductLike = Product | RecommendationItem;

export function TagList({ tags, max = 6 }: { tags?: string[]; max?: number }) {
  return (
    <div className="tag-list">
      {(tags || ["翡翠", "天然A货", "收藏价值"]).slice(0, max).map((tag) => (
        <span key={tag}>{tag}</span>
      ))}
    </div>
  );
}

export function ScorePill({ score }: { score?: number }) {
  if (score === undefined || score === null) return null;
  return <span className="score-pill">AI匹配 {Math.round(score * 100)}%</span>;
}

export function ProductCard({ product, index = 0, compact = false }: { product: ProductLike; index?: number; compact?: boolean }) {
  const item = withJadePresentation(product, index);
  const score = item.score ?? item.agent_score ?? item.final_score;
  return (
    <article
      className={`product-card ${compact ? "compact" : ""}`}
      role="button"
      tabIndex={0}
      onClick={() => navigate("product", { id: item.id })}
      onKeyDown={(event) => {
        if (event.key === "Enter") navigate("product", { id: item.id });
      }}
    >
      <img src={item.imageUrl} alt={item.name} />
      <div className="product-card-body">
        <h3>{item.name}</h3>
        <TagList tags={item.tags} max={compact ? 3 : 5} />
        <div className="card-footer">
          <strong>{formatPrice(item.price)}</strong>
          <ScorePill score={score} />
        </div>
        {!compact && item.explanation ? <p className="product-explain">{item.explanation}</p> : null}
      </div>
    </article>
  );
}
