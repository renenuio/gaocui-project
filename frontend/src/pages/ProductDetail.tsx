import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { MailIcon } from "../components/Icons";
import { MobileShell, TopBar } from "../components/Layout";
import { ScorePill, TagList } from "../components/ProductCard";
import { formatPrice, withJadePresentation } from "../data/jadeCatalog";
import type { Product } from "../types";
import { navigate } from "../utils/router";
import { useRecommendation } from "../context/RecommendationContext";

export function ProductDetail({ id }: { id?: string | null }) {
  const { items } = useRecommendation();
  const [product, setProduct] = useState<Product | null>(null);
  const [email, setEmail] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<string>("");

  const recommendation = useMemo(() => items.find((item) => String(item.id) === String(id)), [id, items]);

  useEffect(() => {
    let ignore = false;
    if (!id) {
      setProduct(null);
      return;
    }

    api
      .getProduct(id)
      .then((data) => {
        if (!ignore) setProduct(withJadePresentation({ ...data, explanation: recommendation?.explanation, agent_score: recommendation?.agent_score }));
      })
      .catch(() => {
        if (!ignore) setProduct(null);
        setStatus("商品不存在或已下架。");
      });

    return () => {
      ignore = true;
    };
  }, [id, recommendation]);

  async function submitLead() {
    if (!email.trim() || !note.trim()) {
      setStatus("请填写邮箱和留言，方便卖家联系。");
      return;
    }

    try {
      await api.createLead({
        email,
        product_id: product?.id || "",
        source: product?.name,
        note: `商品：${product?.name || ""}\n需求：${note}`
      });
      setStatus("已提交意向，卖家将通过邮件联系您。");
      setEmail("");
      setNote("");
    } catch (error) {
      setStatus(error instanceof Error ? `提交失败：${error.message}` : "提交失败，请稍后重试。");
    }
  }

  if (!product) {
    return (
      <MobileShell>
        <TopBar title="商品详情" onBack={() => navigate("feed")} />
        <p className="loading-page">{status || "正在读取商品信息..."}</p>
      </MobileShell>
    );
  }

  return (
    <MobileShell>
      <TopBar title="商品详情" onBack={() => navigate("feed")} right={<button className="text-button" onClick={() => setStatus("分享入口已响应，可接入 Web Share API。")}>分享</button>} />

      <section className="detail-hero">
        <img src={product.imageUrl} alt={product.name} />
        <span>1/5</span>
      </section>

      <section className="detail-main">
        <h1>{product.name}</h1>
        <div className="price-line">
          <strong>{formatPrice(product.price)}</strong>
          <span>预估价</span>
          <ScorePill score={product.agent_score} />
        </div>
        <TagList tags={product.tags} max={10} />

        <div className="detail-section">
          <h2>AI简介（50字）</h2>
          <p>{product.description || "天然翡翠货源，适合礼赠、佩戴与轻收藏，实际品相以商家图片和沟通为准。"}</p>
        </div>

        <div className="detail-section">
          <h2>AI推荐解释</h2>
          <p>
            {product.explanation ||
              "系统根据用户需求、商品语义向量、历史偏好记忆和 LLM rerank 分数判断该货源具备较高匹配度。"}
          </p>
        </div>

        <div className="detail-section">
          <h2>AI详情（300字）</h2>
          <p>
            本款翡翠商品以种水、颜色、器形与预算匹配为主要推荐依据。前端展示后端 explanation 字段，帮助买家理解
            为什么该商品被推荐，同时保留“仅供参考，不做鉴定与交易”的业务边界。
          </p>
        </div>
      </section>

      <section className="contact-box">
        <h2>联系卖家 <small>留下邮箱，卖家将通过邮件联系您</small></h2>
        <label>
          <MailIcon size={18} />
          <input value={email} placeholder="请输入您的联系邮箱" onChange={(event) => setEmail(event.target.value)} />
        </label>
        <textarea value={note} placeholder="请输入留言，如预算、场景等" onChange={(event) => setNote(event.target.value)} />
        <button className="primary-button" onClick={submitLead}>
          提交意向，等待卖家联系
        </button>
        {status ? <p className="form-status">{status}</p> : <p>我们尊重您的隐私，仅用于卖家联系您</p>}
      </section>
    </MobileShell>
  );
}

