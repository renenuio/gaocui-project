import { useEffect, useState } from "react";
import { api } from "../api/client";
import { BellIcon, MailIcon, UserIcon } from "../components/Icons";
import { MobileShell, SellerTabBar, ToastBanner, TopBar } from "../components/Layout";
import type { ToastTone } from "../types";
import { navigate } from "../utils/router";

export function SellerProfile() {
  const [profile, setProfile] = useState<{ email: string; isVip: boolean; vipEndAt?: string | null }>();
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();

  useEffect(() => {
    api.sellerProfile().then(setProfile).catch((error) => setNotice({ message: error instanceof Error ? error.message : "个人中心接口不可用", tone: "error" }));
  }, []);

  function logout() {
    api.clearAuthToken();
    setNotice({ message: "已退出登录，即将返回首页。", tone: "success" });
    setTimeout(() => navigate("chat"), 500);
  }

  const isVip = profile?.isVip || false;

  return (
    <MobileShell className="dashboard-page">
      <TopBar title="个人中心" onBack={() => navigate("seller-dashboard")} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="profile-card" onClick={() => navigate("seller-entitlements")}>
        <div className="profile-avatar"><UserIcon /></div>
        <div>
          <h2>{profile?.email || "未登录"} {isVip ? <span className="vip-badge">VIP会员</span> : null}</h2>
          <p>{isVip ? `有效期至 ${profile?.vipEndAt || "2026-12-31"}` : "有效期至 永久"}</p>
        </div>
        <span>›</span>
      </section>
      <section className="profile-menu">
        <button onClick={() => navigate("seller-entitlements")}><UserIcon />账户信息<span>›</span></button>
        <button onClick={() => setNotice({ message: "修改邮箱需接入后端 PATCH /seller/email。", tone: "info" })}><MailIcon />修改邮箱<span>›</span></button>
        <button onClick={() => setNotice({ message: "通知设置由后端 profile 返回。", tone: "info" })}><BellIcon />通知设置<span>›</span></button>
        <button onClick={() => setNotice({ message: "帮助中心页面暂未设计，当前保留入口反馈。", tone: "info" })}>帮助中心<span>›</span></button>
        <button onClick={() => setNotice({ message: "高翠网：AI翡翠匹配与商家客资平台。", tone: "info" })}>关于我们<span>›</span></button>
        <button className="danger-text" onClick={logout}>退出登录<span>›</span></button>
      </section>
      <SellerTabBar active="profile" />
    </MobileShell>
  );
}
