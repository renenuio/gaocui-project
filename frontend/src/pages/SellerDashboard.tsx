import { useEffect, useState } from "react";
import { api } from "../api/client";
import { BellIcon, BoxIcon, CrownIcon, HomeIcon, PlusIcon, UserIcon } from "../components/Icons";
import { MobileShell, SectionTitle, SellerTabBar, ToastBanner } from "../components/Layout";
import { formatPrice, maskEmail } from "../data/jadeCatalog";
import type { Product, SellerLead, ToastTone } from "../types";
import { navigate } from "../utils/router";

type Dashboard = {
  productCount: number;
  productLimit: number;
  todayLeadCount: number;
  totalLeadCount: number;
  recentLeads: SellerLead[];
  seller: { email: string; isVip: boolean };
};

export function SellerDashboard() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();

  useEffect(() => {
    api
      .sellerDashboard()
      .then(setDashboard)
      .catch((error) => {
        setNotice({ message: error instanceof Error ? error.message : "商家后台接口不可用", tone: "error" });
      });
    api.sellerProducts().then((data) => setProducts(data.slice(0, 3))).catch(() => undefined);
  }, []);

  const isVip = dashboard?.seller?.isVip || false;

  return (
    <MobileShell className="dashboard-page">
      <header className="dashboard-header">
        <button className="icon-button" onClick={() => navigate("chat")} aria-label="返回首页"><HomeIcon /></button>
        <h1>商家后台 {isVip ? <span className="vip-badge">VIP</span> : null}</h1>
        <button className="icon-button" aria-label="系统通知" onClick={() => navigate("seller-notifications")}><BellIcon /></button>
      </header>
      <ToastBanner message={notice?.message} tone={notice?.tone} />

      <section className="stats-panel">
        <div><span>商品数量</span><strong>{dashboard?.productCount ?? 0} <small>/ {dashboard?.productLimit ?? 0}</small></strong><p>已上架 / 上限</p></div>
        <div><span>今日客资</span><strong>{dashboard?.todayLeadCount ?? 0}</strong><p>条</p></div>
        <div><span>累计客资</span><strong>{dashboard?.totalLeadCount ?? 0}</strong><p>条</p></div>
      </section>

      <section className="action-grid">
        {[
          { label: "发布商品", icon: <PlusIcon />, tone: "green", action: () => navigate("seller-publish") },
          { label: "商品管理", icon: <BoxIcon />, tone: "blue", action: () => navigate("seller-products") },
          { label: "客资列表", icon: <UserIcon />, tone: "orange", action: () => navigate("seller-leads") },
          { label: "账户权限", icon: <CrownIcon />, tone: "purple", action: () => navigate("seller-entitlements") }
        ].map(({ label, icon, tone, action }) => (
          <button key={label} onClick={action}>
            <span className={`action-icon ${tone}`}>{icon}</span>
            {label}
          </button>
        ))}
      </section>

      <section className="seller-products">
        <SectionTitle title="推荐展示中的商品" action={<button className="text-button" onClick={() => navigate("seller-products")}>全部</button>} />
        {products.map((product) => (
          <div className="seller-product-row" key={product.id} onClick={() => navigate("product", { id: product.id })}>
            <img src={product.imageUrl || product.images?.[0]} alt={product.name} />
            <div><h3>{product.name}</h3><p>{formatPrice(product.price)} · 已上架</p></div>
            <span>{product.status === "active" ? "已上架" : "未上架"}</span>
          </div>
        ))}
        {!products.length ? <p className="empty-copy">暂无已发布商品。</p> : null}
      </section>

      <section className="lead-panel">
        <SectionTitle title="最近客资" action={<button className="text-button" onClick={() => navigate("seller-leads")}>全部</button>} />
        {(dashboard?.recentLeads || []).map((lead) => (
          <article className="lead-row" key={lead.id} onClick={() => navigate("seller-leads")}>
            <time>{formatLeadTime(lead.created_at)}</time>
            <div><h3>{lead.note || "客户提交了商品意向"}</h3><p>{lead.source || "关联商品"}</p></div>
            <span>{isVip ? lead.email || lead.buyerEmail : maskEmail(lead.email || lead.buyerEmail)}</span>
          </article>
        ))}
        {!(dashboard?.recentLeads || []).length ? <p className="empty-copy">暂无客资。</p> : null}
      </section>

      {!isVip ? <button className="primary-button sticky-upgrade" onClick={() => navigate("seller-entitlements")}>升级VIP，查看全部联系方式</button> : null}
      <SellerTabBar active="dashboard" />
      <p className="seller-email">当前商家账号：{dashboard?.seller?.email || "未登录"}</p>
    </MobileShell>
  );
}

function formatLeadTime(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
