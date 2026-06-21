import { MobileShell, TopBar } from "../components/Layout";
import { navigate } from "../utils/router";

export function LegalPage({ type }: { type: "terms" | "privacy" }) {
  const isTerms = type === "terms";
  return (
    <MobileShell>
      <TopBar title={isTerms ? "平台服务协议" : "隐私政策"} onBack={() => navigate("seller-login")} />
      <section className="legal-page">
        <h1>{isTerms ? "高翠网平台服务协议" : "高翠网隐私政策"}</h1>
        <p>{isTerms ? "商家入驻高翠网后，可使用 AI 翡翠匹配、商品展示和客资管理服务。平台不参与线下交易定价、鉴定和资金交割。" : "我们仅收集邮箱、留言、商品意向等完成买卖双方联系所需的信息，并仅用于卖家联系、客资管理和平台服务优化。"}</p>
        <p>当前为前端 PRD 收口版本的可点击协议页，后续可替换为正式法务文本。</p>
        <button className="primary-button" onClick={() => navigate("seller-login")}>返回入驻页</button>
      </section>
    </MobileShell>
  );
}
