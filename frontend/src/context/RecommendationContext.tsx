import { createContext, useCallback, useContext, useEffect, useMemo, useReducer } from "react";
import { api } from "../api/client";
import { withJadePresentation } from "../data/jadeCatalog";
import type { ChatMessage, MemoryProfile, RecommendationItem, RecommendationResponse } from "../types";

type RecommendationState = {
  sessionId: string;
  query: string;
  messages: ChatMessage[];
  items: RecommendationItem[];
  latestResponse?: RecommendationResponse;
  memoryProfile?: MemoryProfile;
  userPreferenceSummary?: string;
  expandedQueries: string[];
  loading: boolean;
  error?: string;
};

type RecommendationContextValue = RecommendationState & {
  setQuery: (query: string) => void;
  submitQuery: (query: string) => Promise<void>;
  resetConversation: () => void;
};

type Action =
  | { type: "setQuery"; query: string }
  | { type: "request"; query: string; userMessage: ChatMessage }
  | { type: "success"; response: RecommendationResponse; assistantMessage: ChatMessage }
  | { type: "failure"; message: string; assistantMessage: ChatMessage }
  | { type: "reset" };

const storageKey = "gaocui.recommendation.state.v1";
const sessionStorageKey = "gaocui.recommendation.sessionId";

const welcomeMessage: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: "您好！\n请说出您的翡翠需求（预算、品类、尺寸、品相），我将为您精准匹配货源~",
  createdAt: new Date().toISOString(),
  status: "success"
};

const initialState: RecommendationState = {
  sessionId: getOrCreateSessionId(),
  query: "",
  messages: [welcomeMessage],
  items: [],
  expandedQueries: [],
  loading: false
};

function reducer(state: RecommendationState, action: Action): RecommendationState {
  switch (action.type) {
    case "setQuery":
      return { ...state, query: action.query };
    case "request":
      return {
        ...state,
        query: "",
        loading: true,
        error: undefined,
        messages: [...state.messages, action.userMessage]
      };
    case "success": {
      const items = action.response.intent === "jade_query" ? action.response.items.slice(0, 3).map(withJadePresentation) : [];
      return {
        ...state,
        sessionId: action.response.sessionId || state.sessionId,
        loading: false,
        latestResponse: action.response,
        items,
        expandedQueries: action.response.expanded_queries || [],
        memoryProfile: action.response.memory_profile,
        userPreferenceSummary: action.response.user_preference_summary,
        messages: [...state.messages, action.assistantMessage]
      };
    }
    case "failure":
      return {
        ...state,
        loading: false,
        error: action.message,
        items: [],
        messages: [...state.messages, action.assistantMessage]
      };
    case "reset":
      return initialState;
    default:
      return state;
  }
}

function getOrCreateSessionId() {
  const existing = localStorage.getItem(sessionStorageKey);
  if (existing) return existing;
  const next = `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  localStorage.setItem(sessionStorageKey, next);
  return next;
}

function loadStoredState(): RecommendationState {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return initialState;
    const parsed = JSON.parse(raw) as RecommendationState;
    return {
      ...initialState,
      ...parsed,
      sessionId: parsed.sessionId || getOrCreateSessionId(),
      messages: parsed.messages?.length ? parsed.messages : [welcomeMessage]
    };
  } catch {
    return initialState;
  }
}

const RecommendationContext = createContext<RecommendationContextValue | null>(null);

export function RecommendationProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadStoredState);

  useEffect(() => {
    const { loading, error: _error, ...persisted } = state;
    localStorage.setItem(storageKey, JSON.stringify(persisted));
  }, [state]);

  const submitQuery = useCallback(async (query: string) => {
    const normalized = query.trim();
    if (!normalized) return;

    const now = new Date().toISOString();
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: normalized,
      createdAt: now,
      status: "success"
    };

    dispatch({ type: "request", query: normalized, userMessage });

    try {
      const response = await api.recommend(normalized, 3, state.sessionId);
      const count = response.items?.length || 0;
      const summary = buildAssistantSummary(response, count);
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: summary,
        createdAt: new Date().toISOString(),
        status: "success"
      };
      dispatch({ type: "success", response: { ...response, items: response.items || [] }, assistantMessage });
    } catch (error) {
      const message = error instanceof Error ? error.message : "推荐接口暂不可用";
      const assistantMessage: ChatMessage = {
        id: `assistant-error-${Date.now()}`,
        role: "assistant",
        content: "推荐服务暂时不可用。为避免商品污染，本次不展示兜底商品，请稍后重试。",
        createdAt: new Date().toISOString(),
        status: "failed"
      };
      dispatch({ type: "failure", message, assistantMessage });
    }
  }, [state.sessionId]);

  function buildAssistantSummary(response: RecommendationResponse, count: number) {
    if (response.intent === "jade_query") {
      return `已按翡翠推荐链路匹配 ${count} 件货源，结果已限制为同类目 jade 商品。`;
    }
    const specTitle = response.jade_requirement_spec?.title;
    return specTitle
      ? `已生成“${specTitle}”消费场景需求，当前为需求结构化，不进入商品推荐链路。`
      : "已完成语义理解和翡翠消费场景整理，当前不进入商品推荐链路。";
  }

  const value = useMemo<RecommendationContextValue>(
    () => ({
      ...state,
      setQuery: (query: string) => dispatch({ type: "setQuery", query }),
      submitQuery,
      resetConversation: () => dispatch({ type: "reset" })
    }),
    [state, submitQuery]
  );

  return <RecommendationContext.Provider value={value}>{children}</RecommendationContext.Provider>;
}

export function useRecommendation() {
  const context = useContext(RecommendationContext);
  if (!context) {
    throw new Error("useRecommendation must be used inside RecommendationProvider");
  }
  return context;
}
