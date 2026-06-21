import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CrownIcon } from "../components/Icons";
import { MobileShell, SellerTabBar, ToastBanner, TopBar } from "../components/Layout";
import type { ToastTone } from "../types";
import { navigate } from "../utils/router";

type Entitlements = {
  membership: "free" | "vip";
  isVip: boolean;
  productLimit: number;
  todayPublishedCount: number;
  leadVisibility: "masked" | "full";
  priorityWeight: "low" | "high";
  plans: Array<{ code: string; name: string; price: number }>;
};

export function EntitlementsPage() {
  const [data, setData] = useState<Entitlements | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<Entitlements["plans"][number]>();
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    api
      .sellerEntitlements()
      .then((result) => {
        setData(result);
        setSelectedPlan(result.plans?.[0]);
      })
      .catch((error) => setNotice({ message: error instanceof Error ? error.message : "账户权限接口不可用", tone: "error" }));
  }, []);

  const isVip = data?.isVip || false;

  return (
    <MobileShell className="dashboard-page">
      <TopBar title="账户权限" onBack={() => navigate("seller-profile")} right={isVip ? <span className="vip-badge">VIP</span> : null} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className={`entitlement-card ${isVip ? "vip" : "free"}`}>
        <CrownIcon />
        <div>
          <h2>{isVip ? "VIP会员" : "普通会员"}</h2>
          <p>{isVip ? "有效期至 2026-12-31" : "有效期至 永久"}</p>
        </div>
      </section>
      <section className="entitlement-table">
        <h2>当前权限</h2>
        <p><span>商品发布上限</span><strong>{data?.productLimit ?? 0}件</strong></p>
        <p><span>今日已发布</span><strong>{data?.todayPublishedCount ?? 0}件</strong></p>
        <p><span>客资查看权限</span><strong>{data?.leadVisibility === "full" ? "无限查看全部" : "无查看权限"}</strong></p>
        <p><span>优先展示权重</span><strong>{data?.priorityWeight === "high" ? "高" : "低"}</strong></p>
      </section>
      <section className="plan-list">
        <h2>升级/续费</h2>
        {(data?.plans || []).map((plan) => (
          <button key={plan.code} className={selectedPlan?.code === plan.code ? "selected-plan" : ""} onClick={() => setSelectedPlan(plan)}>
            <span>{plan.name}</span>
            <strong>¥{plan.price}</strong>
          </button>
        ))}
      </section>
      <button className="primary-button sticky-upgrade" onClick={() => setModalOpen(true)}>{isVip ? "联系运营续费" : "联系运营升级"}</button>
      {modalOpen ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <section className="confirm-modal ops-modal">
            <h2>{isVip ? "联系运营续费" : "联系运营升级"}</h2>
            <p>已选择{selectedPlan?.name || "会员套餐"}，运营将通过商家邮箱联系您。</p>
            <div className="modal-actions">
              <button onClick={() => setModalOpen(false)}>我知道了</button>
            </div>
          </section>
        </div>
      ) : null}
      <SellerTabBar active="profile" />
    </MobileShell>
  );
}
