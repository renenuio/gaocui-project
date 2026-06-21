# V4 Recommendation System（Personalized AI Recommendation System）

## 1. Redis Memory System（核心能力）

- 使用 Redis（docker localhost:6379）
- key format:
  - `user:{user_id}:memory`
- value:
  - JSON list（最多20条 recent queries）
- TTL:
  - 7天（604800秒）

### Memory Write Logic

- 每次 request 写入 query
- 自动 truncate 只保留最近20条

### Memory Read Logic

- 每次 request 读取 memory
- 注入 LLM rerank prompt

---

## 2. Memory Influence on Ranking

新增：

- `memory_score`（0~1）
- `memory_hits`（匹配历史query）
- user preference boost

最终 ranking：

```text
final_score =
    embedding_score +
    memory_score +
    llm_rerank_score
```

---

## 3. Query Expansion System（升级版）

从 dict -> synonym graph

### expansion graph example:

```text
翡翠
-> jade
-> jewelry
-> gemstone
-> accessory
-> bracelet
-> jade bracelet

玉石
-> jade
-> stone
-> luxury jewelry

手镯
-> bracelet
-> jade bracelet
```

### 输出：

- `expanded_queries` (multi-hop list)

---

## 4. LLM Rerank Input

prompt 必须包含：

- original query
- `expanded_queries`
- memory history (`recent_queries`)
- `memory_hits`
- `memory_score`
- `user_preference_summary`

---

## 5. AI Response Fields（API新增）

必须返回：

- `memory_profile`
- `user_preference_summary`
- `expanded_queries`
- `memory_hits`
- `memory_score`

---

## 6. AIService Changes

- embedding input = expanded_queries joined text
- pgvector search unchanged
- retrieval before rerank

---

## 7. Agent Architecture

pipeline:

```text
query
 -> expansion
 -> retrieval (pgvector)
 -> memory load
 -> LLM rerank
 -> final ranking
```

---

## 8. Constraints

- 不修改 FastAPI entry
- 不修改 database schema
- 最小侵入式修改
- 优先复用现有 agent
- Redis 为唯一新增依赖
