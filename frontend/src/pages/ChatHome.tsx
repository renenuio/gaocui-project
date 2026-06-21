import { LogoMark, MobileShell } from "../components/Layout";
import { ProductCard } from "../components/ProductCard";
import { SendIcon, SparkIcon, UserIcon } from "../components/Icons";
import { api } from "../api/client";
import { useRecommendation } from "../context/RecommendationContext";
import { navigate } from "../utils/router";

const prompts = ["10万预算 帝王绿手镯 55圈口 微瑕", "冰种平安扣 预算2万 无纹无裂", "冰种翡翠吊坠 送礼自用均可"];

export function ChatHome() {
  const { query, setQuery, submitQuery, messages, items, latestResponse, loading, error, resetConversation } = useRecommendation();
  const hasRecommendations = items.length > 0;
  const spec = latestResponse?.intent !== "jade_query" ? latestResponse?.jade_requirement_spec : undefined;
  const sellerLoggedIn = api.hasAuthToken();

  return (
    <MobileShell className="chat-page">
      <header className="chat-header">
        <LogoMark />
        <button className="merchant-button" onClick={() => navigate(sellerLoggedIn ? "seller-dashboard" : "seller-login")}>
          {sellerLoggedIn ? "商家后台" : "商家入驻"}
        </button>
      </header>

      <section className="chat-scroll" aria-label="AI翡翠匹配聊天">
        {messages.map((message) => (
          <div className={`message-row ${message.role}`} key={message.id}>
            {message.role === "assistant" ? (
              <div className="bot-avatar">
                <SparkIcon size={18} />
              </div>
            ) : null}
            <div className="message-bubble">
              {message.content.split("\n").map((line) => (
                <p key={line}>{line}</p>
              ))}
              <time>{new Date(message.createdAt).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}</time>
            </div>
            {message.role === "user" ? (
              <div className="user-avatar">
                <UserIcon size={18} />
              </div>
            ) : null}
          </div>
        ))}

        {messages.length <= 1 ? (
          <div className="prompt-list">
            {prompts.map((prompt) => (
              <button key={prompt} onClick={() => submitQuery(prompt)}>
                <SparkIcon size={15} />
                {prompt}
              </button>
            ))}
          </div>
        ) : null}

        {loading ? (
          <div className="message-row assistant">
            <div className="bot-avatar">
              <SparkIcon size={18} />
            </div>
            <div className="message-bubble loading-bubble">
              已为您解析需求，正在调用 embedding retrieval、Redis memory 和 LLM rerank 匹配货源...
            </div>
          </div>
        ) : null}

        {hasRecommendations ? (
          <section className="recommendation-block">
            <div className="recommendation-heading">
              <h2>为您找到以下优质货源</h2>
              <button onClick={() => navigate("feed")}>查看全部</button>
            </div>
            <div className="chat-card-grid">
              {items.slice(0, 3).map((item, index) => (
                <ProductCard key={item.id} product={item} index={index} compact />
              ))}
            </div>
          </section>
        ) : null}

        {spec ? (
          <section className="recommendation-block">
            <div className="recommendation-heading">
              <h2>{spec.title}</h2>
            </div>
            <p className="small-muted">{spec.short_description}</p>
            <p>{spec.detailed_description}</p>
            <div className="tag-list">
              {(spec.tags || []).slice(0, 10).map((tag) => (
                <span key={tag}>{tag}</span>
              ))}
            </div>
            <div className="chip-row">
              {(latestResponse?.suggestions || []).map((suggestion) => (
                <button key={suggestion} onClick={() => setQuery(suggestion)}>
                  {suggestion}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {error ? <p className="inline-error">接口提示：{error}</p> : null}
      </section>

      <footer className="chat-input-area">
        <div className="input-row">
          <textarea
            value={query}
            rows={2}
            placeholder={"请输入您的翡翠需求...\n支持中文英文等多语言"}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="send-button" disabled={!query.trim() || loading} onClick={() => submitQuery(query)}>
            <SendIcon size={18} />
            AI匹配
          </button>
        </div>
        <div className="chat-actions">
          <button onClick={() => navigate("feed")}>推荐流</button>
          <button onClick={resetConversation}>清空对话</button>
        </div>
        <p>AI智能匹配，仅供参考，不做鉴定与交易</p>
      </footer>
    </MobileShell>
  );
}
