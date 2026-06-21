import { useEffect, useMemo, useState } from "react";
import type { RouteName } from "../types";

export type AppRoute = {
  name: RouteName;
  params: URLSearchParams;
};

const validRoutes: RouteName[] = [
  "chat",
  "feed",
  "product",
  "seller-login",
  "seller-dashboard",
  "seller-products",
  "seller-publish",
  "seller-publish-review",
  "seller-leads",
  "seller-lead-detail",
  "seller-profile",
  "seller-entitlements",
  "seller-notifications",
  "legal"
];

export function parseRoute(): AppRoute {
  const hash = window.location.hash.replace(/^#\/?/, "");
  const [name = "chat", query = ""] = hash.split("?");
  return {
    name: validRoutes.includes(name as RouteName) ? (name as RouteName) : "chat",
    params: new URLSearchParams(query)
  };
}

export function navigate(name: RouteName, params?: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined) search.set(key, String(value));
  });
  window.location.hash = `/${name}${search.toString() ? `?${search.toString()}` : ""}`;
}

export function useHashRoute() {
  const [route, setRoute] = useState<AppRoute>(() => parseRoute());

  useEffect(() => {
    const sync = () => setRoute(parseRoute());
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return useMemo(() => route, [route]);
}
