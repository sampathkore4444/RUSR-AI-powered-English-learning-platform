/**
 * API client — single place for all backend communication.
 * Handles JWT auth tokens automatically.
 */

const API_BASE = "/api";

// ── Token management ─────────────────────────────────────

function getToken(): string | null {
  return localStorage.getItem("rusr_token");
}

export function setToken(token: string) {
  localStorage.setItem("rusr_token", token);
}

export function clearToken() {
  localStorage.removeItem("rusr_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

// ── Types ────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Article {
  id: string;
  title: string;
  source: string | null;
  url: string | null;
  author: string | null;
  published_at: string | null;
  created_at: string;
  paragraphs: Paragraph[];
}

export interface Paragraph {
  id: string;
  sequence: number;
  text: string;
  sentences: Sentence[];
}

export interface Sentence {
  id: string;
  sequence: number;
  text: string;
  tokens: Token[];
}

export interface Token {
  text: string;
  lemma: string;
  pos: string;
}

export interface VocabularyWord {
  id: string;
  word: string;
  lemma: string;
  meaning: string | null;
  first_seen: string;
  times_seen: number;
  times_reviewed: number;
  mastery_level: number;
  difficulty: string;
  personal_note: string | null;
  next_review_date: string | null;
}

export interface WordInspectResponse {
  word: string;
  lemma: string;
  dictionary: {
    definition: string;
    pos: string;
    pronunciation: string | null;
    synonyms: string[];
  };
  context_meaning: string | null;
  example: string | null;
}

export interface ReviewItem {
  vocabulary_id: string;
  word: string;
  lemma: string;
  meaning: string | null;
  difficulty: string;
}

export interface ReviewStats {
  total_words: number;
  words_mastered: number;
  words_learning: number;
  words_new: number;
  retention_rate: number;
  streak_days: number;
  reading_streak_days: number;
  quiz_streak_days: number;
}

export interface WordOfDay {
  id: string;
  word: string;
  lemma: string;
  meaning: string | null;
  difficulty: string;
  mastery_level: number;
  times_reviewed: number;
  next_review_date: string | null;
  reason: string;
}

// ── HTTP helper ──────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired. Please login again.");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `API error ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── File download helper ───────────────────────────────

async function fetchExport(path: string): Promise<Blob> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { headers });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired.");
  }

  if (!res.ok) {
    throw new Error("Export failed");
  }

  return res.blob();
}

// ── Auth ─────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ── Articles ─────────────────────────────────────────────

export const articlesApi = {
  ingestFromText: (data: { title: string; text: string; source?: string; author?: string }) =>
    request<Article>("/articles/text", { method: "POST", body: JSON.stringify(data) }),

  ingestFromUrl: (url: string) =>
    request<Article>("/articles/url", { method: "POST", body: JSON.stringify({ url }) }),

  list: (offset = 0, limit = 20) =>
    request<{ articles: Article[]; total: number }>(`/articles?offset=${offset}&limit=${limit}`),

  get: (id: string) => request<Article>(`/articles/${id}`),
};

// ── Vocabulary ───────────────────────────────────────────

export const vocabularyApi = {
  save: (data: { word: string; lemma: string; meaning?: string; context_sentence?: string; difficulty?: string }) =>
    request<VocabularyWord>("/vocabulary", { method: "POST", body: JSON.stringify(data) }),

  list: (offset = 0, limit = 50) =>
    request<{ vocabulary: VocabularyWord[]; total: number }>(`/vocabulary?offset=${offset}&limit=${limit}`),

  wordOfDay: () => request<WordOfDay | null>("/vocabulary/word-of-the-day"),

  get: (id: string) => request<VocabularyWord>(`/vocabulary/${id}`),

  update: (id: string, data: { meaning?: string; personal_note?: string; difficulty?: string }) =>
    request<VocabularyWord>(`/vocabulary/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  delete: (id: string) => request<void>(`/vocabulary/${id}`, { method: "DELETE" }),

  exportCsv: () => fetchExport("/vocabulary/export/csv"),
  exportAnki: () => fetchExport("/vocabulary/export/anki"),
};

// ── Word Intelligence ────────────────────────────────────

export const wordsApi = {
  inspect: (data: { word: string; sentence: string }) =>
    request<WordInspectResponse>("/words/inspect", { method: "POST", body: JSON.stringify(data) }),

  explain: (data: { sentence: string; action?: string }) =>
    request<{ original: string; explanation: string; action: string }>("/words/explain", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

// ── Reviews ──────────────────────────────────────────────

export const reviewApi = {
  getDue: (limit = 20) =>
    request<{ items: ReviewItem[]; total_due: number }>(`/review/due?limit=${limit}`),

  submitAnswer: (data: { vocabulary_id: string; answer_correct: boolean }) =>
    request<{
      vocabulary_id: string;
      correct: boolean;
      mastery_level: number;
      next_review_date: string;
      interval_days: number;
    }>("/review/answer", { method: "POST", body: JSON.stringify(data) }),

  getStats: () => request<ReviewStats>("/review/stats"),
};
