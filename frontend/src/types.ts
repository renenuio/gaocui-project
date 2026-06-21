export type RouteName =
  | "chat"
  | "feed"
  | "product"
  | "seller-login"
  | "seller-dashboard"
  | "seller-products"
  | "seller-publish"
  | "seller-publish-review"
  | "seller-leads"
  | "seller-lead-detail"
  | "seller-profile"
  | "seller-entitlements"
  | "seller-notifications"
  | "legal";

export type MemoryProfile = {
  recent_query_count?: number;
  top_categories?: Array<{ category: string; weight: number }>;
  category_weights?: Record<string, number>;
  long_term_preference_vector?: Record<string, number>;
  decay_function?: string;
};

export type RecommendationItem = {
  id: number | string;
  name: string;
  description?: string | null;
  category?: "jade" | string | null;
  price?: string | number | null;
  distance?: number;
  score?: number;
  embedding_score?: number;
  embedding_similarity?: number;
  category_match_score?: number;
  business_score?: number;
  llm_score?: number;
  memory_score?: number;
  agent_score?: number;
  final_score?: number;
  explanation?: string;
  reason?: string;
  image?: string;
  imageUrl?: string;
  images?: string[];
  tags?: string[];
};

export type JadeRequirementSpec = {
  title: string;
  short_description: string;
  detailed_description: string;
  tags?: string[];
  parameters?: Record<string, string>;
  top_10_tags_table?: Array<Record<string, string>>;
  product_parameter_table?: Record<string, string>;
};

export type RecommendationResponse = {
  sessionId?: string;
  intent: "jade_query" | "non_jade_query" | "general_query" | string;
  query: string;
  jade_scene_mapping?: string;
  jade_requirement_spec?: JadeRequirementSpec;
  suggestions: string[];
  all_jade: boolean;
  count: number;
  embedding_enabled?: boolean;
  agent_enabled?: boolean;
  query_intent?: string;
  query_category?: string | null;
  expanded_queries?: string[];
  memory_hits?: string[];
  memory_score?: number;
  memory_profile?: MemoryProfile;
  user_preference_summary?: string;
  memory?: {
    enabled?: boolean;
    recent_queries?: string[];
  };
  items: RecommendationItem[];
};

export type ProductStatus = "active" | "draft" | "inactive";

export type Product = {
  id: number | string;
  name: string;
  description?: string | null;
  detail?: string | null;
  category?: string | null;
  price?: string | number | null;
  created_at?: string;
  updated_at?: string;
  image?: string;
  imageUrl?: string;
  images?: string[];
  tags?: string[];
  explanation?: string;
  score?: number;
  agent_score?: number;
  final_score?: number;
  status?: ProductStatus;
  sellerId?: string | number;
};

export type ProductPayload = {
  name: string;
  description?: string;
  detail?: string;
  category?: string;
  price?: string | number;
  imageUrl?: string;
  images?: string[];
  tags?: string[];
  status?: ProductStatus;
  sellerId?: string | number;
};

export type LeadPayload = {
  name?: string;
  phone?: string;
  email?: string;
  source?: string;
  note?: string;
  product_id: string | number;
  seller_id?: string | number;
};

export type ChatMessage = {
  id: string;
  role: "assistant" | "user";
  content: string;
  createdAt: string;
  status?: "sending" | "success" | "failed";
};

export type LeadStatus = "pending" | "contacted";

export type SellerLead = {
  id: number | string;
  email?: string | null;
  buyerEmail?: string | null;
  note?: string | null;
  source?: string | null;
  created_at?: string;
  status?: LeadStatus;
  product_id?: string | number;
  seller_id?: string | number;
};

export type SellerStats = {
  productCount: number;
  productLimit: number;
  todayLeadCount: number;
  totalLeadCount: number;
};

export type ToastTone = "success" | "warning" | "error" | "info";
