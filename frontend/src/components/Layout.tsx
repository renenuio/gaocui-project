import type { RouteName, ToastTone } from "../types";
import { navigate } from "../utils/router";
import { BackIcon, BoxIcon, HomeIcon, UserIcon } from "./Icons";

export function MobileShell({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <main className={`mobile-shell ${className}`}>{children}</main>;
}

export function LogoMark() {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden="true">
        <span />
      </span>
      <span className="brand-title">AI翡翠匹配</span>
    </div>
  );
}

export function TopBar({
  title,
  right,
  onBack
}: {
  title: string;
  right?: React.ReactNode;
  onBack?: () => void;
}) {
  return (
    <header className="top-bar">
      <button className="icon-button" aria-label="返回" onClick={onBack || (() => window.history.back())}>
        <BackIcon />
      </button>
      <h1>{title}</h1>
      <div className="top-right">{right}</div>
    </header>
  );
}

export function SectionTitle({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="section-title">
      <h2>{title}</h2>
      {action}
    </div>
  );
}

export function ToastBanner({ message, tone = "info" }: { message?: string; tone?: ToastTone }) {
  if (!message) return null;
  return <div className={`toast-banner ${tone}`}>{message}</div>;
}

export function SellerTabBar({ active }: { active: "home" | "products" | "dashboard" | "profile" }) {
  const tabs: Array<{ key: typeof active; label: string; icon: React.ReactNode; route: RouteName }> = [
    { key: "home", label: "首页", icon: <HomeIcon />, route: "chat" },
    { key: "products", label: "商品", icon: <BoxIcon />, route: "seller-products" },
    { key: "dashboard", label: "管理后台", icon: <BoxIcon />, route: "seller-dashboard" },
    { key: "profile", label: "我的", icon: <UserIcon />, route: "seller-profile" }
  ];

  return (
    <footer className="seller-tabbar">
      {tabs.map((tab) => (
        <button key={tab.key} className={active === tab.key ? "active" : ""} onClick={() => navigate(tab.route)}>
          {tab.icon}
          {tab.label}
        </button>
      ))}
    </footer>
  );
}
