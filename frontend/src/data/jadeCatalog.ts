import type { Product, RecommendationItem } from "../types";

export const jadeImages = [
  "/assets/jade-bangle-hero.png",
  "/assets/jade-bangle-1.png",
  "/assets/jade-bangle-2.png",
  "/assets/jade-bangle-3.png",
  "/assets/jade-pendant.png"
];

export function withJadePresentation<T extends RecommendationItem | Product>(
  item: T,
  index = 0
): T {
  const existingTags = "tags" in item && Array.isArray(item.tags) ? item.tags : undefined;
  const category = item.category || "jade";
  const tags = existingTags || inferJadeTags(item.name, item.description, category);
  return {
    ...item,
    imageUrl: item.imageUrl || item.image || jadeImages[index % jadeImages.length],
    tags
  };
}

export function inferJadeTags(name?: string, description?: string | null, category?: string | null): string[] {
  const text = `${name || ""} ${description || ""} ${category || ""}`.toLowerCase();
  const tags = [
    text.includes("冰种") || text.includes("ice") ? "冰种" : "",
    text.includes("飘花") ? "飘花" : "",
    text.includes("紫罗兰") ? "紫罗兰" : "",
    text.includes("吊坠") || text.includes("项链") ? "吊坠" : "",
    text.includes("手镯") || text.includes("bracelet") ? "翡翠手镯" : "",
    text.includes("jade") || text.includes("翡翠") || category === "jade" ? "天然A货" : "",
    "收藏价值"
  ].filter(Boolean);
  return Array.from(new Set(tags)).slice(0, 6);
}

export function formatPrice(value?: string | number | null): string {
  const num = Number(value || 0);
  if (!Number.isFinite(num) || num <= 0) return "面议";
  return `¥${num.toLocaleString("zh-CN", { maximumFractionDigits: 0 })}`;
}

export function maskEmail(email?: string | null): string {
  if (!email || !email.includes("@")) return "****@***.com";
  const [, domain] = email.split("@");
  return `****@${domain.replace(/^[^.]*/, "***")}`;
}
