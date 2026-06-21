import { ChatHome } from "./pages/ChatHome";
import { EntitlementsPage } from "./pages/EntitlementsPage";
import { LeadDetail, LeadList } from "./pages/LeadList";
import { LegalPage } from "./pages/LegalPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { ProductDetail } from "./pages/ProductDetail";
import { ProductManagement, ProductPublish, ProductPublishReview } from "./pages/ProductManagement";
import { RecommendationFeed } from "./pages/RecommendationFeed";
import { SellerDashboard } from "./pages/SellerDashboard";
import { SellerOnboarding } from "./pages/SellerOnboarding";
import { SellerProfile } from "./pages/SellerProfile";
import { useHashRoute } from "./utils/router";

export function App() {
  const route = useHashRoute();

  if (route.name === "feed") return <RecommendationFeed />;
  if (route.name === "product") return <ProductDetail id={route.params.get("id")} />;
  if (route.name === "seller-login") return <SellerOnboarding />;
  if (route.name === "seller-dashboard") return <SellerDashboard />;
  if (route.name === "seller-products") return <ProductManagement />;
  if (route.name === "seller-publish") return <ProductPublish />;
  if (route.name === "seller-publish-review") return <ProductPublishReview id={route.params.get("id")} mode={route.params.get("mode")} />;
  if (route.name === "seller-leads") return <LeadList />;
  if (route.name === "seller-lead-detail") return <LeadDetail id={route.params.get("id")} />;
  if (route.name === "seller-profile") return <SellerProfile />;
  if (route.name === "seller-entitlements") return <EntitlementsPage />;
  if (route.name === "seller-notifications") return <NotificationsPage />;
  if (route.name === "legal") return <LegalPage type={route.params.get("type") === "privacy" ? "privacy" : "terms"} />;
  return <ChatHome />;
}
