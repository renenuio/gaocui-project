import { useEffect, useState } from "react";
import { api } from "../api/client";
import { BellIcon, MailIcon, SparkIcon, UserIcon } from "../components/Icons";
import { LogoMark, MobileShell, ToastBanner, TopBar } from "../components/Layout";
import type { ToastTone } from "../types";
import { navigate } from "../utils/router";

export function SellerOnboarding() {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [agree, setAgree] = useState(false);
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();
  const [submitting, setSubmitting] = useState(false);

  async function sendCode() {
    if (!email.includes("@")) {
      setNotice({ message: "请输入有效邮箱地址。", tone: "error" });
      return;
    }
    setCode("123456");
    setNotice({ message: "Demo验证码已填入：123456。邮箱包含 vip 将进入 VIP 商家体验。", tone: "success" });
  }

  async function login() {
    if (!email.includes("@")) {
      setNotice({ message: "请填写有效邮箱。", tone: "error" });
      return;
    }
    if (!code.trim()) {
      setNotice({ message: "请填写验证码。", tone: "error" });
      return;
    }
    if (!agree) {
      setNotice({ message: "请先勾选同意平台服务协议与隐私政策。", tone: "warning" });
      return;
    }

    setSubmitting(true);
    try {
      const result = await api.loginOrRegister(email.trim(), code.trim());
      api.setAuthToken(result.access_token);
      setNotice({ message: "登录/注册成功，正在进入商家后台。", tone: "success" });
      setTimeout(() => navigate("seller-dashboard"), 500);
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "登录失败", tone: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <MobileShell className="seller-login">
      <TopBar title="" onBack={() => navigate("chat")} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="login-panel">
        <LogoMark />
        <h1>商家入驻</h1>
        <p>加入高翠网 · 获取精准买家线索</p>
        <label>
          <MailIcon />
          <input value={email} placeholder="请输入您的邮箱地址" onChange={(event) => setEmail(event.target.value)} />
        </label>
        <button className="primary-button" onClick={sendCode}>
          获取验证码
        </button>
        <label>
          <UserIcon />
          <input value={code} placeholder="请输入验证码" onChange={(event) => setCode(event.target.value)} />
        </label>
        <label className="agreement-row">
          <input type="checkbox" checked={agree} onChange={(event) => setAgree(event.target.checked)} />
          <span>
            我已阅读并同意
            <button type="button" onClick={() => navigate("legal", { type: "terms" })}>《平台服务协议》</button>
            与
            <button type="button" onClick={() => navigate("legal", { type: "privacy" })}>《隐私政策》</button>
          </span>
        </label>
        <button className="primary-button" disabled={submitting} onClick={login}>{submitting ? "提交中..." : "登录 / 注册"}</button>
      </section>

      <div className="seller-benefits">
        {[
          { text: "仅需邮箱", icon: <MailIcon />, action: () => setNotice({ message: "仅需邮箱即可入驻。", tone: "info" as const }) },
          { text: "验证码登录", icon: <UserIcon />, action: sendCode },
          { text: "快速入驻", icon: <SparkIcon />, action: () => { setEmail("vip-seller@email.com"); setCode("123456"); setAgree(true); setNotice({ message: "已填入 VIP Demo 账号。", tone: "success" as const }); } },
          { text: "免费试用", icon: <BellIcon />, action: () => { setEmail("seller@email.com"); setCode("123456"); setAgree(true); setNotice({ message: "已填入 FREE Demo 账号。", tone: "success" as const }); } }
        ].map(({ text, icon, action }) => (
          <button key={text} onClick={action}>
            <span>{icon}</span>
            <p>{text}</p>
          </button>
        ))}
      </div>
    </MobileShell>
  );
}

