import type { LeadPayload, LeadStatus, Product, ProductPayload, RecommendationResponse, SellerLead } from "../types";

const authTokenKey = "gaocui.demo.auth.token";
const sellerKey = "gaocui.demo.seller";
const productKey = "gaocui.demo.products";
const leadKey = "gaocui.demo.leads";
const notificationKey = "gaocui.demo.notifications";

const jadeImages = [
  "/assets/jade-bangle-hero.png",
  "/assets/jade-bangle-1.png",
  "/assets/jade-bangle-2.png",
  "/assets/jade-bangle-3.png",
  "/assets/jade-pendant.png"
];

type DemoSeller = {
  sellerId: string;
  email: string;
  membership: "free" | "vip";
  isVip: boolean;
};

type NotificationItem = { id: number; type: string; content: string; createdAt: string; readAt?: string };

function now() {
  return new Date().toISOString();
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value));
}

function demoSeller(): DemoSeller {
  return readJson<DemoSeller>(sellerKey, {
    sellerId: "seller-demo",
    email: "seller@email.com",
    membership: "free",
    isVip: false
  });
}

function productLimit() {
  return demoSeller().isVip ? 100 : 2;
}

function seedProducts(): Product[] {
  const existing = readJson<Product[] | null>(productKey, null);
  if (existing?.length) return existing;
  const products: Product[] = [
    {
      id: 101,
      name: "冰种晴底翡翠手镯",
      description: "冰种晴底，质地细腻通透，清新淡雅，佩戴显气质。",
      detail: "本款冰种晴底翡翠手镯，种水达到冰种级别，质地细腻，透光如水，底色清新淡雅。手镯为正圈设计，圈口55mm，佩戴舒适贴合。无纹裂，适合日常佩戴或收藏。",
      category: "jade",
      price: "48000",
      imageUrl: jadeImages[0],
      images: [jadeImages[0], jadeImages[2], jadeImages[3]],
      tags: ["冰种", "晴底色", "翡翠手镯", "正圈", "55圈口", "无纹裂"],
      status: "active",
      sellerId: "seller-demo",
      created_at: now(),
      score: 0.96
    },
    {
      id: 102,
      name: "冰种绿晴翡翠手镯",
      description: "水头足，底子清透，带淡绿晴色，适合日常佩戴与轻收藏。",
      detail: "绿晴色调清爽，整体光感柔和，适合预算较高的送礼与自戴场景。",
      category: "jade",
      price: "52000",
      imageUrl: jadeImages[1],
      images: [jadeImages[1], jadeImages[0]],
      tags: ["冰种", "55圈口", "微瑕", "收藏优选"],
      status: "active",
      sellerId: "seller-demo",
      created_at: now(),
      score: 0.92
    },
    {
      id: 103,
      name: "冰种飘花翡翠手镯",
      description: "飘花灵动，底色干净，适合偏好传统玉石韵味的买家。",
      detail: "飘花走势自然，底子干净，价格低于同等级满色手镯，适合日常佩戴。",
      category: "jade",
      price: "46800",
      imageUrl: jadeImages[3],
      images: [jadeImages[3], jadeImages[0]],
      tags: ["冰种", "飘花", "正圈", "天然A货"],
      status: "active",
      sellerId: "seller-demo",
      created_at: now(),
      score: 0.89
    },
    {
      id: 104,
      name: "帝王绿翡翠挂件",
      description: "高色高货，适合收藏与商务礼赠。",
      detail: "色泽浓郁，款式端正，适合作为高端收藏或重要礼物。",
      category: "jade",
      price: "88000",
      imageUrl: jadeImages[4],
      images: [jadeImages[4]],
      tags: ["帝王绿", "翡翠挂件", "收藏", "商务礼赠"],
      status: "active",
      sellerId: "seller-demo",
      created_at: now(),
      score: 0.84
    }
  ];
  writeJson(productKey, products);
  return products;
}

function seedLeads(): SellerLead[] {
  const existing = readJson<SellerLead[] | null>(leadKey, null);
  if (existing) return existing;
  const leads: SellerLead[] = [
    {
      id: 1,
      email: "buyer1@email.com",
      buyerEmail: displayEmail("buyer1@email.com"),
      source: "冰种晴底翡翠手镯",
      note: "预算5万左右，冰种手镯，55圈口，不要纹裂，颜色要清爽一点",
      status: "pending",
      product_id: 101,
      seller_id: "seller-demo",
      created_at: "2026-06-20T10:30:00"
    }
  ];
  writeJson(leadKey, leads);
  return leads;
}

function seedNotifications(): NotificationItem[] {
  const existing = readJson<NotificationItem[] | null>(notificationKey, null);
  if (existing) return existing;
  const items = [
    { id: 1, type: "new_lead", content: "有新客户留资：预算5万左右，冰种手镯，55圈口。", createdAt: "2026-06-20T10:30:00" },
    { id: 2, type: "vip_expiring", content: "VIP到期前30天提醒：请及时联系运营续费。", createdAt: "2026-06-18T09:00:00" }
  ];
  writeJson(notificationKey, items);
  return items;
}

function displayEmail(email?: string | null) {
  const seller = demoSeller();
  if (seller.isVip || !email || !email.includes("@")) return email || "";
  const [, domain] = email.split("@");
  return `****@${domain.replace(/^[^.]*/, "***")}`;
}

function storedLeadsForSeller() {
  return seedLeads().map((lead) => ({
    ...lead,
    email: displayEmail(lead.email),
    buyerEmail: displayEmail(lead.buyerEmail || lead.email)
  }));
}

function classifyIntent(query: string): "jade_query" | "non_jade_query" | "general_query" {
  const text = query.trim().toLowerCase();
  if (/(翡翠|玉|玉石|手镯|吊坠|平安扣|冰种|糯种|飘花|jade|bracelet|bangle)/i.test(text)) return "jade_query";
  if (!text || /(你好|hello|hi|天气|谢谢|帮助|怎么用)/i.test(text)) return "general_query";
  return "non_jade_query";
}

function requirementSpec(query: string) {
  const scene = query.includes("iPhone") || query.toLowerCase().includes("iphone")
    ? "商务高端翡翠手镯，用于身份展示与礼赠"
    : query.includes("辣条")
      ? "日常轻奢翡翠吊坠，用于生活方式升级"
      : "送礼收藏两用翡翠手镯";
  return {
    jade_scene_mapping: `基于“${query}”，转化为翡翠消费场景：${scene}。`,
    jade_requirement_spec: {
      title: "高翠消费需求",
      short_description: "将当前输入转为可沟通的翡翠购买需求。",
      detailed_description: `用户原始输入为“${query}”。Demo Agent 不直接推荐跨品类商品，而是生成一个翡翠消费场景：${scene}。该需求适合用于礼物、自戴、收藏或身份表达，可继续补充预算、佩戴对象、尺寸和种水偏好，帮助商家更准确地理解需求并提供对应货源。`,
      tags: ["翡翠", "礼赠", "轻奢", "收藏", "身份表达", "天然A货", "场景转译", "预算待定", "高翠AI", "需求结构化"],
      params: {
        产品品类: "翡翠饰品",
        核心卖点: "场景化需求转译",
        主石材质: "天然翡翠",
        适用场景: "礼赠、自戴、收藏",
        款式风格: "轻奢雅致"
      },
      parameters: {
        产品品类: "翡翠饰品",
        核心卖点: "场景化需求转译",
        主石材质: "天然翡翠",
        适用场景: "礼赠、自戴、收藏",
        款式风格: "轻奢雅致"
      }
    },
    suggestions: ["补充预算范围", "说明自戴或送礼", "选择手镯/吊坠/戒指"]
  };
}

function delay<T>(value: T, ms = 120): Promise<T> {
  return new Promise((resolve) => window.setTimeout(() => resolve(value), ms));
}

export const api = {
  setAuthToken(token: string) {
    localStorage.setItem(authTokenKey, token);
  },

  clearAuthToken() {
    localStorage.removeItem(authTokenKey);
  },

  hasAuthToken() {
    return Boolean(localStorage.getItem(authTokenKey));
  },

  recommend(query: string, limit = 3, sessionId = "anonymous") {
    const intent = classifyIntent(query);
    if (intent !== "jade_query") {
      const spec = requirementSpec(query);
      return delay<RecommendationResponse>({
        sessionId,
        query,
        intent,
        ...spec,
        suggestions: spec.suggestions,
        all_jade: false,
        count: 0,
        items: []
      });
    }
    const items = seedProducts()
      .filter((product) => product.category === "jade" && product.status === "active")
      .slice(0, limit)
      .map((product, index) => ({
        ...product,
        category: "jade",
        score: product.score || 0.9 - index * 0.04,
        final_score: product.score || 0.9 - index * 0.04,
        embedding_similarity: 0.95 - index * 0.04,
        category_match_score: 1,
        business_score: 0.88 - index * 0.03,
        explanation: "Demo Agent 根据翡翠品类、预算语义和商品标签进行规则排序。"
      }));
    return delay<RecommendationResponse>({
      sessionId,
      query,
      intent,
      suggestions: [],
      expanded_queries: ["jade", "bracelet", "jewelry"],
      memory_profile: { recent_query_count: 1, top_categories: [{ category: "jade", weight: 1 }] },
      user_preference_summary: "Demo memory: 当前偏好翡翠手镯。",
      all_jade: true,
      count: items.length,
      items
    });
  },

  session(sessionId = "anonymous") {
    return delay({ sessionId, memory: { recent_queries: [] } });
  },

  me() {
    return delay(demoSeller());
  },

  sellerProfile() {
    const seller = demoSeller();
    return delay({
      ...seller,
      vipEndAt: seller.isVip ? "2026-12-31" : null,
      notificationSettings: { web: true, email: true }
    });
  },

  sellerDashboard() {
    const seller = demoSeller();
    const products = seedProducts().filter((item) => item.status === "active");
    const leads = storedLeadsForSeller();
    return delay({
      productCount: products.length,
      productLimit: productLimit(),
      todayLeadCount: leads.length,
      totalLeadCount: leads.length,
      recentLeads: leads.slice(0, 4),
      seller
    });
  },

  sellerEntitlements() {
    const seller = demoSeller();
    return delay({
      ...seller,
      productLimit: productLimit(),
      todayPublishedCount: seedProducts().filter((item) => item.status === "active").length,
      activeProductCount: seedProducts().filter((item) => item.status === "active").length,
      leadVisibility: seller.isVip ? ("full" as const) : ("masked" as const),
      priorityWeight: seller.isVip ? ("high" as const) : ("low" as const),
      plans: [
        { code: "vip_12m", name: "VIP会员（12个月）", price: 2999 },
        { code: "vip_6m", name: "VIP会员（6个月）", price: 1688 }
      ]
    });
  },

  sellerQuota() {
    const activeProductCount = seedProducts().filter((item) => item.status === "active").length;
    const limit = productLimit();
    return delay({ productLimit: limit, activeProductCount, remaining: Math.max(limit - activeProductCount, 0) });
  },

  sellerProducts() {
    return delay(seedProducts());
  },

  getProduct(id: string | number) {
    const product = seedProducts().find((item) => String(item.id) === String(id));
    return product ? delay(product) : Promise.reject(new Error("商品不存在"));
  },

  createProduct(payload: ProductPayload) {
    const products = seedProducts();
    const product: Product = {
      id: Date.now(),
      name: payload.name,
      description: payload.description || "",
      detail: payload.detail || "",
      category: "jade",
      price: payload.price || "",
      imageUrl: payload.imageUrl || payload.images?.[0] || jadeImages[0],
      images: payload.images?.length ? payload.images : [payload.imageUrl || jadeImages[0]],
      tags: payload.tags || ["翡翠", "天然A货"],
      status: payload.status || "active",
      sellerId: demoSeller().sellerId,
      created_at: now()
    };
    writeJson(productKey, [product, ...products]);
    return delay(product);
  },

  updateProduct(id: string | number, payload: Partial<ProductPayload>) {
    const products = seedProducts();
    const next = products.map((product) =>
      String(product.id) === String(id)
        ? {
            ...product,
            ...payload,
            imageUrl: payload.imageUrl || payload.images?.[0] || product.imageUrl,
            updated_at: now()
          }
        : product
    );
    writeJson(productKey, next);
    const updated = next.find((product) => String(product.id) === String(id));
    return updated ? delay(updated) : Promise.reject(new Error("商品不存在"));
  },

  async deleteProduct(id: string | number) {
    writeJson(productKey, seedProducts().filter((product) => String(product.id) !== String(id)));
    return delay({ ok: true });
  },

  uploadSellerProductImage(payload: { image: string; filename?: string }) {
    return delay({ imageId: `demo-image-${Date.now()}`, imageUrl: payload.image, filename: payload.filename || "upload.jpg" });
  },

  generateSellerProduct(payload: { images: string[] }) {
    return delay<ProductPayload>({
      name: "冰种晴底翡翠手镯",
      description: "冰种晴底，质地细腻通透，清新淡雅，佩戴显气质。",
      detail: "本款冰种晴底翡翠手镯，种水达到冰种级别，底色清爽柔和，适合日常佩戴、收藏或送礼。",
      category: "jade",
      price: "48000",
      imageUrl: payload.images[0],
      images: payload.images,
      tags: ["冰种", "晴底色", "翡翠手镯", "正圈", "天然A货"],
      status: "active"
    });
  },

  createLead(payload: LeadPayload) {
    const product = seedProducts().find((item) => String(item.id) === String(payload.product_id));
    const leads = seedLeads();
    const email = payload.email || "";
    const lead: SellerLead = {
      id: Date.now(),
      email,
      buyerEmail: displayEmail(email),
      source: payload.source || product?.name || "翡翠商品",
      note: payload.note,
      status: "pending",
      product_id: payload.product_id,
      seller_id: demoSeller().sellerId,
      created_at: now()
    };
    writeJson(leadKey, [lead, ...leads]);
    const notifications = seedNotifications();
    writeJson(notificationKey, [
      { id: Date.now(), type: "new_lead", content: `有新客户留资：${payload.note || product?.name || "翡翠商品"}`, createdAt: now() },
      ...notifications
    ]);
    return delay({ ...lead, email: displayEmail(email), buyerEmail: displayEmail(email) });
  },

  listLeads() {
    return delay(storedLeadsForSeller());
  },

  getLead(id: string | number) {
    const lead = storedLeadsForSeller().find((item) => String(item.id) === String(id));
    return lead ? delay(lead) : Promise.reject(new Error("客资不存在"));
  },

  updateLeadStatus(id: string | number, status: LeadStatus) {
    const leads = seedLeads().map((lead) => (String(lead.id) === String(id) ? { ...lead, status } : lead));
    writeJson(leadKey, leads);
    const updated = storedLeadsForSeller().find((lead) => String(lead.id) === String(id));
    return updated ? delay(updated) : Promise.reject(new Error("客资不存在"));
  },

  notifications() {
    return delay(seedNotifications());
  },

  markNotificationRead(id: string | number) {
    const items = seedNotifications().map((item) => (String(item.id) === String(id) ? { ...item, readAt: now() } : item));
    writeJson(notificationKey, items);
    return delay({ ok: true });
  },

  async loginOrRegister(email: string, code: string) {
    if (code !== "123456") throw new Error("Demo验证码固定为 123456");
    const seller: DemoSeller = {
      sellerId: "seller-demo",
      email,
      membership: email.toLowerCase().includes("vip") ? "vip" : "free",
      isVip: email.toLowerCase().includes("vip")
    };
    writeJson(sellerKey, seller);
    const token = `demo-token-${seller.membership}-${Date.now()}`;
    this.setAuthToken(token);
    seedProducts();
    seedLeads();
    seedNotifications();
    return delay({ access_token: token, token_type: "bearer", email, membership: seller.membership, isVip: seller.isVip });
  }
};
