import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { MobileShell, SectionTitle, ToastBanner, TopBar } from "../components/Layout";
import { formatPrice } from "../data/jadeCatalog";
import type { LeadStatus, Product, SellerLead, ToastTone } from "../types";
import { navigate } from "../utils/router";

type LeadTab = "all" | LeadStatus;

function statusText(status?: LeadStatus) {
  return status === "contacted" ? "已联系" : "待联系";
}

export function LeadList() {
  const [leads, setLeads] = useState<SellerLead[]>([]);
  const [profile, setProfile] = useState<{ isVip: boolean }>();
  const [activeTab, setActiveTab] = useState<LeadTab>("all");
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();

  useEffect(() => {
    Promise.all([api.listLeads(), api.sellerProfile()])
      .then(([leadData, profileData]) => {
        setLeads(leadData);
        setProfile(profileData);
      })
      .catch((error) => setNotice({ message: error instanceof Error ? error.message : "客资接口不可用", tone: "error" }));
  }, []);

  const counts = useMemo(() => {
    return leads.reduce(
      (result, lead) => {
        const status = lead.status || "pending";
        result.all += 1;
        result[status] += 1;
        return result;
      },
      { all: 0, pending: 0, contacted: 0 }
    );
  }, [leads]);

  const filteredLeads = activeTab === "all" ? leads : leads.filter((lead) => (lead.status || "pending") === activeTab);

  return (
    <MobileShell className="dashboard-page">
      <TopBar title="客资列表" onBack={() => navigate("seller-dashboard")} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="management-tabs three-tabs">
        <button className={activeTab === "all" ? "active" : ""} onClick={() => setActiveTab("all")}>全部({counts.all})</button>
        <button className={activeTab === "pending" ? "active" : ""} onClick={() => setActiveTab("pending")}>待联系({counts.pending})</button>
        <button className={activeTab === "contacted" ? "active" : ""} onClick={() => setActiveTab("contacted")}>已联系({counts.contacted})</button>
      </section>
      <SectionTitle title="买家意向" />
      <section className="lead-panel standalone">
        {filteredLeads.map((lead) => (
          <article className="lead-row clickable" key={lead.id} onClick={() => navigate("seller-lead-detail", { id: lead.id })}>
            <time>{formatLeadTime(lead.created_at)}</time>
            <div>
              <h3>{lead.source || "关联商品"}</h3>
              <p>{lead.note || "客户提交了商品意向"}</p>
            </div>
            <span><em>{statusText(lead.status)}</em>{lead.email || lead.buyerEmail || "未留邮箱"}</span>
          </article>
        ))}
        {!filteredLeads.length ? <p className="empty-copy">当前分类暂无客资。</p> : null}
      </section>
      {profile && !profile.isVip ? <button className="primary-button sticky-upgrade" onClick={() => navigate("seller-entitlements")}>升级VIP，查看全部联系方式</button> : null}
    </MobileShell>
  );
}

export function LeadDetail({ id }: { id?: string | null }) {
  const [lead, setLead] = useState<SellerLead | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [profile, setProfile] = useState<{ email: string; isVip: boolean }>();
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();

  useEffect(() => {
    if (!id) return;
    Promise.all([api.getLead(id), api.sellerProfile()])
      .then(async ([leadData, profileData]) => {
        setLead(leadData);
        setProfile(profileData);
        if (leadData.product_id) {
          setProduct(await api.getProduct(leadData.product_id));
        }
      })
      .catch((error) => setNotice({ message: error instanceof Error ? error.message : "客资详情接口不可用", tone: "error" }));
  }, [id]);

  async function copyEmail() {
    const email = lead?.email || lead?.buyerEmail;
    if (!email) return;
    await navigator.clipboard.writeText(email);
    setNotice({ message: "买家邮箱已复制。", tone: "success" });
  }

  async function markContacted() {
    if (!lead) return;
    const updated = await api.updateLeadStatus(lead.id, "contacted");
    setLead(updated);
    setNotice({ message: "已标记为已联系。", tone: "success" });
  }

  if (!lead) {
    return (
      <MobileShell>
        <TopBar title="客资详情" onBack={() => navigate("seller-leads")} />
        <ToastBanner message={notice?.message} tone={notice?.tone} />
        <p className="loading-page">正在读取客资详情...</p>
      </MobileShell>
    );
  }

  const isVip = profile?.isVip || false;

  return (
    <MobileShell>
      <TopBar title="客资详情" onBack={() => navigate("seller-leads")} right={isVip ? <button className="text-button" onClick={markContacted}>标记已联系</button> : null} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="lead-detail-card">
        <p><span>留言时间</span><strong>{formatLeadTime(lead.created_at)}</strong></p>
        <p><span>用户需求</span><strong>{lead.note || "客户提交了商品意向"}</strong></p>
        <div className="related-product">
          <span>关联商品</span>
          <div><img src={product?.imageUrl || product?.images?.[0]} alt={product?.name || "关联商品"} /><strong>{lead.source || product?.name || "关联商品"}<small>{formatPrice(product?.price)}</small></strong></div>
        </div>
        <p><span>用户邮箱</span><strong>{lead.email || lead.buyerEmail || "未留邮箱"}</strong></p>
        <p><span>商家账号</span><strong>{profile?.email || "--"}</strong></p>
      </section>
      {isVip ? (
        <div className="bottom-action-row">
          <button className="secondary-button" onClick={copyEmail}>复制邮箱</button>
          <button className="primary-button" onClick={markContacted}>标记已联系</button>
        </div>
      ) : (
        <button className="primary-button sticky-upgrade" onClick={() => navigate("seller-entitlements")}>升级VIP，查看完整联系方式</button>
      )}
    </MobileShell>
  );
}

function formatLeadTime(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
