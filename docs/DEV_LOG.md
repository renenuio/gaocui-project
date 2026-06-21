# 开发日志

## 项目信息

- 项目名称：`gaocui-project`
- 项目类型：AI 商品推荐平台后端
- 技术栈：FastAPI、PostgreSQL、SQLAlchemy 2.0、Redis、pgvector

## 当前系统已完成

### 基础后端

- FastAPI 后端框架已完成。
- `/health` 健康检查接口已可用。
- API 分层已建立：
  - user
  - product
  - ai
  - vip
  - payment
  - lead

### 数据库与向量能力

- PostgreSQL 已部署。
- pgvector 已部署。
- 数据库 `gaocui_project` 已连接成功。
- `products` 表已创建。
- `users` 表已创建。
- `products` 表中已存在测试数据。

### AI 推荐链路

- mock embedding 生成逻辑已完成。
- product embedding 测试数据已生成。
- pgvector `cosine_distance` 检索已跑通。
- 推荐链路已完成：

```text
query -> embedding -> vector search -> product ranking -> API response
```

### FastAPI Recommendation API

- `/api/v1/ai/recommendations` 接口已可用。
- 接口可返回基于 embedding 相似度排序的商品结果。

## 当前未完成

### Agent 推荐层

- rerank 未完成。
- memory 未完成。
- explanation 未完成。

### 初始化工具

- 一键初始化脚本未完成。
- `init_db` 未完成。
- `rebuild_embeddings` 未完成。

## 当前目标

### 升级方向

- 将当前 AI 推荐能力升级为 AI Recommendation Agent 系统。
- 增加 rerank 能力。
- 增加 reasoning 能力。
- 增加 memory 能力。

## 下一步计划

1. 设计 Agent 推荐层输入输出结构。
2. 增加 rerank 逻辑。
3. 增加推荐 reasoning 输出。
4. 增加用户偏好 memory 存储与读取。
5. 增加 `init_db` 初始化脚本。
6. 增加 `rebuild_embeddings` 重建脚本。

## 本次执行记录：AI Recommendation Agent 增强

### 完成内容

- 新增 `backend/app/agent/recommendation_agent.py`。
- 新增 `backend/app/agent/__init__.py`。
- 增强 `backend/app/services/ai_service.py`：
  - 保留原有 query embedding 生成逻辑。
  - 保留原有 pgvector cosine_distance 候选检索逻辑。
  - 将 pgvector 检索结果交给 `RecommendationAgent` 做 rerank。
  - API 响应新增 Agent 字段：
    - `agent_enabled`
    - `query_intent`
    - `query_category`
    - `memory`
    - `agent_score`
    - `explanation`

### Agent 能力

- Query 理解：
  - 支持简单 intent 分类。
  - 支持基于关键词的 category 判断。
- Rerank：
  - 基于 embedding distance。
  - 基于 category 匹配。
  - 基于商品 name / description / category 关键词命中。
  - 基于轻量 user memory 的最近 query 关键词。
- Explanation：
  - 每个推荐结果都会返回 `explanation`。
  - explanation 包含类目匹配、关键词命中、memory 命中或 embedding distance 信息。
- Memory：
  - 当前为进程内轻量 memory。
  - 默认保存最近 5 条 query。
  - 不依赖数据库表结构变更。

### 执行脚本

- `python -m compileall app`
  - 结果：成功。
- `python -c "...RecommendationAgent self-check..."`
  - 结果：成功。
  - 验证内容：
    - `agent_enabled == True`
    - query category 可识别为 `office`
    - rerank 后办公椅优先于 embedding distance 更近但类目不匹配的商品
    - 每个推荐结果包含 `explanation`

### 是否成功

- 本次开发成功。
- 新增 Agent 模块可直接 import 和运行。
- 现有 FastAPI 主入口结构未修改。
- 现有数据库模型未修改。

### 数据库变化

- 表结构变化：无。
- 新增表：无。
- 删除表：无。
- 字段变化：无。
- 数据变化：无。
- embedding 数据变化：无。
- 本次未执行数据库写入脚本。

### pgvector 状态

- 原有 pgvector 检索链路未重构。
- `AIService.recommend()` 仍使用 `Product.embedding.cosine_distance(query_embedding)` 获取候选结果。
- 本次未连接数据库执行端到端 pgvector 查询。
- 本次自检确认 Agent 可处理 pgvector 返回格式的候选结果。

### 错误记录

- 当前工作区 `docs/dev_log.md` 小写路径不存在。
- 实际项目日志文件为 `docs/DEV_LOG.md`，本次按已有事实来源文件追加记录。
- 当前环境中 `git` 命令不可用，未执行 `git diff` 或 `git status`。

## 当前项目状态同步：AI Recommendation Engine v2

### 1. 当前已完成系统（事实级）

- PostgreSQL + pgvector 已运行。
- embedding 召回链路已跑通：
  - 使用 `Product.embedding.cosine_distance`。
- `RecommendationAgent` 已实现 rule-based rerank。
- query intent 已支持。
- query category 已支持。
- memory 已支持：
  - 当前为进程内 memory。
- explanation 已支持。
- FastAPI recommendation API 已可用。
- seed 数据已自动初始化：
  - 测试商品。
  - 翡翠 / 玉石 / 珠宝类商品。

### 2. 当前系统能力总结

- embedding retrieval。
- rule-based rerank。
- category boost。
- keyword boost。
- memory boost。
- basic agent pipeline：
  - 当前为非 LLM pipeline。

### 3. 当前未完成（关键差距）

- LLM rerank 未完成：
  - 当前仍为 rule-based。
- Redis persistent memory 未完成：
  - 当前为内存版 memory。
- query expansion 未完成：
  - 例如 `翡翠 -> jade / jewelry` 未做。
- multi-agent reasoning pipeline 未完善。

### 4. 当前系统定位

- AI Recommendation Engine v2。
- rule-based agent。
- 非 LLM Agent system。

### 5. 下一步目标

- 升级为 LLM-based Recommendation Agent。
- 引入 query expansion。
- 引入 Redis memory。
- 引入 LLM rerank。
- 引入 LLM explanation generation。

## 当前系统状态（v2 - LLM Recommendation Agent）

### 已完成模块

#### 1. 推荐系统核心链路

- pgvector embedding retrieval 已完成。
- cosine distance TopK 检索已完成。
- FastAPI recommendation API 已稳定运行。

#### 2. Agent 能力（已完成）

- LLM rerank 已完成：
  - model: `gpt-4o-mini`
  - temperature: `0.2`
- query intent classification 已支持。
- query category 已支持：
  - `jade`
  - `jewelry`
  - `gemstone`
  - `accessory`
- explanation 生成已支持：
  - 当前由 LLM 生成。
- agent_score 排序系统已支持。

#### 3. embedding 系统

- OpenAI embedding 已接入：
  - model: `text-embedding-3-small`
- sentence-transformers fallback 已支持。
- 商品 embedding 自动生成机制已支持。

#### 4. 数据层

- `products` 表已有 20 条测试数据。
- 已包含类别：
  - `jade`
  - `jewelry`
  - `bag`
  - `home`
  - 其他测试类别。
- 支持翡翠 / 玉石测试场景。

#### 5. 当前系统能力总结

- 支持语义检索 + LLM rerank。
- 支持基础商品推荐。
- 支持 explanation 输出。

### 当前已知问题（重要）

- memory 未持久化：
  - 当前为空 / 进程内状态。
- query expansion 仅为弱规则：
  - 例如 `翡翠 -> jade`。
- 未引入 Redis。
- 未构建知识图谱 / 同义词体系。
- 未拆分 multi-agent architecture。

### 当前系统阶段

- v2: LLM-enhanced Recommendation Agent。
- prototype stage。

### 下一步目标（v3）

#### 1. Redis Memory System

- 用户 query memory 持久化。
- session-level preference tracking。

#### 2. Query Expansion System

- `翡翠 -> jade / jewelry / gemstone / accessory`。
- 建立 synonym graph。
- embedding-based expansion。

#### 3. Agent Architecture Upgrade

- QueryAgent。
- RetrievalAgent。
- RerankAgent。
- MemoryAgent。
- ExplanationAgent。

## 当前系统状态（v3 - LLM Recommendation Agent）

### 已完成能力

#### 1. 推荐系统核心链路

- pgvector retrieval。
- LLM rerank。
- query expansion：
  - `翡翠 -> jade / jewelry / gemstone / accessory`。
- explanation generation。

#### 2. Agent能力

- query intent classification。
- query category detection。
- LLM rerank scoring。
- reasoning explanation。

#### 3. memory系统（当前状态）

- memory 逻辑已实现。
- `memory_hits` 已存在字段。
- `memory_score` 已存在字段。
- 但未接入 Redis：
  - 当前为非持久化状态。

### 当前系统问题（关键）

- memory 未持久化：
  - 无 Redis。
- personalization 无法跨 session。
- query expansion 未图谱化。
- 无 user-level profiling。

### 当前系统阶段

- v3: LLM-enhanced Recommendation System。
- partial memory。

### 下一步目标（v4）

#### 1. Redis Memory System（关键升级）

- 引入 Redis。
- `user:{id}:memory`。
- 最近 20 条 query。
- TTL = 7 days。
- memory 注入 rerank prompt。

#### 2. Memory-aware ranking

- `memory_score` 影响 rerank。
- 用户偏好 bias。

#### 3. Query Expansion Graph升级

- 从 dictionary 升级为 semantic graph。
- 支持 multi-hop expansion。

## 当前系统状态（v4 - Personalized AI Recommendation System）

### v4 已完成

- Redis memory 已启用。
- query expansion graph 已启用。
- memory-aware rerank 已启用。
- API 已支持 personalization 字段。

### Redis Memory System

- Redis: 本地 `6379`。
- key: `user:{user_id}:memory`。
- value: JSON list。
- 保存最近 20 条 query。
- TTL: 7 days。
- 每次 recommendation request 读取 memory。
- 每次 recommendation request 写入 memory。
- memory 注入 LLM rerank prompt。

### Memory-aware Ranking

- 已增加 `memory_score`。
- 已增加 user preference boost。
- rerank 后 `agent_score` 会融合 LLM score 与 memory score。

### Query Expansion Graph

- 已从 dictionary 升级为 synonym graph。
- 支持 multi-hop expansion。
- 当前链路示例：
  - `翡翠 -> jade -> jewelry -> gemstone -> bracelet -> luxury accessory`
- `expanded_queries` 已返回到 API response。

### LLM Rerank Prompt 增强

- prompt 已包含：
  - `expanded_queries`
  - memory history
  - `memory_hits`
  - user preference summary

### API 新增字段

- `expanded_queries`
- `memory_hits`
- `memory_score`
- `memory_profile`
- `user_preference_summary`

### 自测结果

- Redis 写入：通过。
- Redis JSON list 读取：通过。
- 最近 20 条 query 限制：通过。
- TTL 7 days：通过。
- Query expansion 测试：通过。
  - 输入：`翡翠手镯`
  - 命中：`jade / jewelry / gemstone / bracelet`
- Memory 测试：通过。
  - 连续请求 2 次后出现 `memory_hits`
  - 第二次 `memory_score = 1.0`
- Rerank 测试：通过。
  - jade 类商品优先于非 jade 类商品。

## V4 System Spec 文档落地

### 文档文件

- 新增 `docs/V4_SYSTEM_SPEC.md`。

### 摘要

- V4 system completed:
  - memory
  - expansion
  - rerank
- Redis integration enabled。
- query expansion graph implemented。
- LLM rerank enhanced with memory context。

## 当前系统状态（V4.5 - Production Grade Recommendation System）

### 已完成能力

- User Profile Engine 已实现：
  - long-term preference vector。
  - category weighting。
  - decay function: `0.85 ** recency_index`。
- Graph-based Expansion Engine 已增强：
  - weighted edges。
  - multi-hop scoring。
  - low-score expansion filter。
- Hybrid Ranker 已实现：
  - `final_score = 0.4 embedding_score + 0.3 memory_score + 0.3 llm_score`
- Evaluation Layer 已实现：
  - `recall@k`。
  - ranking consistency check。
  - test dataset support helper。
- Safety fallback 已实现：
  - LLM failure fallback to embedding ranking。

### V4.5 自测结果

- Redis write/read test：通过。
- TTL check：通过。
- expansion correctness：通过。
- memory influence correctness：通过。
- hybrid ranker check：通过。
- preference vector check：通过。
- ranking consistency check：通过。
- recall@2：通过。
- LLM failure fallback check：通过。
