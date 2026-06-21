import type { MemoryProfile } from "../types";

export function MemoryPanel({
  expandedQueries,
  memoryProfile,
  summary
}: {
  expandedQueries: string[];
  memoryProfile?: MemoryProfile;
  summary?: string;
}) {
  const categories = memoryProfile?.top_categories || [];

  return (
    <section className="memory-panel">
      <div>
        <span className="panel-label">Redis memory personalization</span>
        <p>{summary || "暂无稳定偏好，系统会随多轮查询逐步学习预算、品类、种水和用途。"}</p>
      </div>
      <div>
        <span className="panel-label">Query expansion graph</span>
        <div className="query-chips">
          {(expandedQueries.length ? expandedQueries.slice(0, 8) : ["翡翠", "jade", "手镯", "冰种", "珠宝收藏"]).map((query) => (
            <span key={query}>{query}</span>
          ))}
        </div>
      </div>
      <div>
        <span className="panel-label">Memory profile</span>
        <div className="query-chips">
          {categories.length ? (
            categories.map((item) => (
              <span key={item.category}>
                {item.category} {(item.weight * 100).toFixed(0)}%
              </span>
            ))
          ) : (
            <>
              <span>预算偏好待学习</span>
              <span>种水偏好待学习</span>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
