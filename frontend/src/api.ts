const BASE_URL = import.meta.env.VITE_API_URL ?? "";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface Stats {
  total_articles: number;
  last_collected_at: string | null;
}

export interface Keyword {
  keyword: string;
  count: number;
  source_count: number;
  summary: string;
}

export interface KeywordsResponse {
  period: string;
  keywords: Keyword[];
}

export interface Article {
  id: number;
  title: string;
  link: string;
  source: string;
  published_at: string | null;
  keywords: string;
}

export interface SourceCount {
  source: string;
  count: number;
}

export interface CollectResult {
  total_crawled: number;
  new_articles: number;
  collected_at: string;
}

export interface Fortune {
  date: string;
  천간: string;
  지지: string;
  element: string;
  element_hanja: string;
  element_emoji: string;
  fortune_message: string;
  cheer_message: string;
  money: { score: number; message: string };
  business: { score: number; message: string };
  lucky_color: string;
  lucky_number: number;
}

export const api = {
  getStats: () => fetchJson<Stats>("/api/stats"),
  getKeywords: (period: string) =>
    fetchJson<KeywordsResponse>(`/api/keywords/${period}`),
  getArticles: (params: { keyword?: string; source?: string; period?: string }) => {
    const sp = new URLSearchParams();
    if (params.keyword) sp.set("keyword", params.keyword);
    if (params.source) sp.set("source", params.source);
    if (params.period) sp.set("period", params.period);
    return fetchJson<Article[]>(`/api/articles?${sp.toString()}`);
  },
  getSources: () => fetchJson<SourceCount[]>("/api/sources"),
  collect: () => fetchJson<CollectResult>("/api/collect", { method: "POST" }),
  getFortune: () => fetchJson<Fortune>("/api/fortune"),
};
