# END-to-END-FLOW.md — RUSR Platform Complete Documentation

**Product:** Read → Understand → Save → Remember (RUSR)
**Type:** AI-Powered English Newspaper Learning Platform
**Date:** 2026-09-19

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Architecture at a Glance](#2-architecture-at-a-glance)
3. [Tech Stack](#3-tech-stack)
4. [Phase 1 — Authentication](#4-phase-1--authentication)
5. [Phase 2 — Article Ingestion](#5-phase-2--article-ingestion)
6. [Phase 3 — Tap-a-Word Intelligence](#6-phase-3--tap-a-word-intelligence)
7. [Phase 4 — AI Sentence Explanation](#7-phase-4--ai-sentence-explanation)
8. [Phase 5 — Personal Vocabulary](#8-phase-5--personal-vocabulary)
9. [Phase 6 — Spaced Repetition & Quizzes](#9-phase-6--spaced-repetition--quizzes)
10. [Phase 7 — Learning Events & Analytics](#10-phase-7--learning-events--analytics)
11. [Phase 8 — pgvector Semantic Search](#11-phase-8--pgvector-semantic-search)
12. [Phase 9 — Redis Caching Layer](#12-phase-9--redis-caching-layer)
13. [Frontend Architecture](#13-frontend-architecture)
14. [Frontend ↔ Backend Communication](#14-frontend--backend-communication)
15. [Complete API Reference](#15-complete-api-reference)
16. [Database Schema](#16-database-schema)
17. [Server Management — Without Docker](#17-server-management--without-docker)
18. [Server Management — With Docker](#18-server-management--with-docker)
19. [Troubleshooting](#19-troubleshooting)
20. [Project File Structure](#20-project-file-structure)

---

## 1. Platform Overview

RUSR is an AI-powered English learning platform built around newspaper reading. The core loop is:

```
Read → Understand → Save → Remember
```

1. **Read** — User ingests articles via URL or pasted text. The system extracts content, splits into paragraphs/sentences, and annotates every word with NLP data (lemma, POS).
2. **Understand** — User taps any word in the article. The system shows: dictionary definition, pronunciation (IPA), part of speech, context-aware meaning, synonyms, and an AI-generated example.
3. **Save** — User saves interesting words to a personal vocabulary with one click.
4. **Remember** — Spaced repetition reviews and quizzes ensure long-term retention.

### Key Differentiators

- **Deterministic-first** — Dictionary/NLP before LLM (keeps costs near zero)
- **Context-aware** — AI explains what a word means *in the specific sentence*
- **Personal vocabulary** — Words are stored with their original context
- **Spaced repetition** — Fixed-interval MVP, FSRS-ready architecture

---

## 2. Architecture at a Glance

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)               │
│                                                         │
│  Pages: Login │ Home │ Article Reader │ Vocabulary │ Review│
│  Hooks: useArticles │ useWordInspect │ useVocabulary    │
│  API Client: api.ts (all HTTP calls, JWT management)    │
└─────────────────────────┬───────────────────────────────┘
                          │  fetch() with Authorization header
                          │  Vite dev proxy: /api → localhost:8000
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)             │
│                                                         │
│  Routes (thin controllers):                             │
│    auth.py │ articles.py │ vocabulary.py │ words.py      │
│    review.py │ users.py                                  │
│                                                         │
│  Services (business logic):                             │
│    auth_service.py    │ article_service.py               │
│    nlp_service.py     │ dictionary_service.py            │
│    ai_service.py      │ word_intelligence_service.py     │
│    vocabulary_service.py │ review_service.py             │
│    learning_event_service.py                             │
│                                                         │
│  Core: config.py │ database.py │ redis.py │ auth.py      │
│  Cache: cache.py │ pgvector.py                          │
└──────────┬──────────────┬──────────────┬────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │PostgreSQL│   │  Redis   │   │  Ollama  │
    │+ pgvector│   │  Cache   │   │  + Qwen  │
    └──────────┘   └──────────┘   └──────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 19 + Vite 6 + Tailwind CSS 4 | SPA with hot reload |
| **Frontend Router** | React Router 7 | Client-side routing |
| **HTTP Client** | fetch API (native) | All backend communication |
| **Backend** | Python 3.12 + FastAPI | Async REST API |
| **ORM** | SQLAlchemy 2 (async) | Database queries |
| **Migrations** | Alembic | Schema versioning |
| **Database** | PostgreSQL 16 + pgvector | Relational data + vector search |
| **Cache** | Redis 7 | Dictionary, AI, pronunciation caching |
| **NLP** | spaCy + WordNet (NLTK) | Tokenization, POS, lemmatization |
| **Dictionary** | WordNet + eng-to-ipa | Definitions, synonyms, pronunciation |
| **AI/LLM** | Ollama + Qwen 2.5 (7B) | Context explanations, AI assistant |
| **Embeddings** | sentence-transformers (MiniLM-L6) | Semantic sentence search |
| **Auth** | JWT (python-jose) + bcrypt | Stateless authentication |
| **Deployment** | Docker Compose | Full stack orchestration |

---

## 4. Phase 1 — Authentication

### Flow

```
User opens /login
       │
       ▼
Enters email + password
       │
       ▼
Frontend: authApi.login({ email, password })
       │
       ▼
POST /api/auth/login
       │
       ▼
Backend: auth_service.login()
  ├── Find user by email (SQL SELECT)
  ├── Verify password (bcrypt check)
  ├── Create JWT token (HS256, 24h expiry)
  └── Return { access_token, token_type, user }
       │
       ▼
Frontend:
  ├── setToken(jwt) → localStorage "rusr_token"
  ├── store email → localStorage "rusr_user_email"
  └── navigate("/")
```

### Registration Flow

```
POST /api/auth/register
  ├── Check email uniqueness (ConflictError if exists)
  ├── Hash password (bcrypt)
  ├── Create user record
  ├── Generate JWT
  └── Return { access_token, token_type, user }
```

### How Auth Works on Every Subsequent Request

```
Frontend api.ts request() function:
  1. Read token from localStorage("rusr_token")
  2. Add header: Authorization: Bearer <token>
  3. Make fetch() call
  4. If response is 401:
     ├── clearToken() from localStorage
     ├── Redirect to /login
     └── Throw "Session expired" error
  5. If response is !ok:
     └── Parse error body, throw with message
  6. If response is 204:
     └── Return undefined (no body)
  7. Otherwise:
     └── Return res.json()
```

### Backend Auth Middleware

```
core/auth.py → get_current_user()
  1. Extract "Authorization" header (optional parameter)
  2. If missing → raise 400 "Missing authentication token"
  3. Strip "Bearer " prefix
  4. Decode JWT (verify signature + expiry)
  5. Extract user_id from "sub" claim
  6. Fetch user from database
  7. If not found → raise 404
  8. Return User object (injected into route via Depends)
```

### Protected vs Public Routes

| Route | Auth Required |
|-------|--------------|
| `POST /api/auth/register` | ❌ No |
| `POST /api/auth/login` | ❌ No |
| `GET /health` | ❌ No |
| `POST /api/articles/*` | ✅ Yes |
| `GET /api/articles/*` | ✅ Yes |
| `POST /api/vocabulary` | ✅ Yes |
| `GET/PUT/DELETE /api/vocabulary/*` | ✅ Yes |
| `POST /api/words/*` | ✅ Yes |
| `GET /api/review/*` | ✅ Yes |
| `POST /api/review/answer` | ✅ Yes |
| `GET /api/users/me` | ✅ Yes |
| `DELETE /api/users/me` | ✅ Yes |

---

## 5. Phase 2 — Article Ingestion

### 5.1 URL Ingestion Flow

```
User pastes URL in HomePage form
       │
       ▼
Frontend: articlesApi.ingestFromUrl(url)
       │
       ▼
POST /api/articles/url  { "url": "https://..." }
       │
       ▼
article_service.ingest_from_url()
  │
  ├── 1. FETCH HTML
  │     httpx.AsyncClient.get(url, timeout=15s)
  │     User-Agent: Chrome browser string
  │     Follows redirects
  │     Raises BadRequestError on HTTP errors
  │
  ├── 2. EXTRACT CONTENT
  │     readability-lxml extracts main article
  │     Falls back to BeautifulSoup if readability fails:
  │       soup.find("article") → soup.find("main") → body
  │     Removes: script, style, nav, footer, aside, form tags
  │     Extracts: title, author (meta tags), clean text
  │
  ├── 3. CREATE ARTICLE RECORD
  │     Article(user_id, title, source=domain, url, author)
  │     db.add() + db.flush() → gets UUID
  │
  ├── 4. SPLIT INTO PARAGRAPHS
  │     text.split("\n\n") → if empty, split("\n")
  │     Each paragraph → ArticleParagraph(article_id, sequence, text)
  │
  ├── 5. SPLIT INTO SENTENCES (spaCy)
  │     nlp_service.split_sentences(para_text)
  │     Uses spaCy sentencizer (not regex)
  │     Each sentence → ArticleSentence(paragraph_id, sequence, text)
  │
  ├── 6. TOKENIZE (spaCy)
  │     nlp_service.process_sentence(sent_text)
  │     For each token: text, lemma, POS tag
  │     Each token → SentenceToken(sentence_id, position, text, lemma, pos)
  │
  └── 7. RETURN ARTICLE
        Full Article object with relationships
```

### 5.2 Text Ingestion Flow

```
User pastes title + text in HomePage form
       │
       ▼
POST /api/articles/text  { "title": "...", "text": "..." }
       │
       ▼
article_service.ingest_from_text()
  ├── Create Article record (no URL)
  └── Same paragraph → sentence → token pipeline as URL ingestion
```

### 5.3 Frontend Ingestion UX

```
HomePage:
  ├── Click "Add Article" button
  ├── Toggle between "URL" and "Paste Text" modes
  ├── For URL: paste URL → click "Ingest"
  ├── For Text: enter title + paste text → click "Ingest"
  ├── Loading spinner while processing
  ├── Error banner if ingestion fails
  └── Article list refreshes automatically on success
```

### 5.4 NLP Processing Detail

```
nlp_service.py
  │
  ├── process_sentence(text)
  │     Uses spaCy nlp pipeline
  │     Returns: [{"text": "The", "lemma": "the", "pos": "DET"}, ...]
  │
  ├── split_sentences(text)
  │     Uses spaCy sentencizer
  │     Returns: ["First sentence.", "Second sentence."]
  │
  ├── get_lemma(word)
  │     Single word → lemma via spaCy
  │     "curbed" → "curb"
  │
  └── get_pos(word)
        Single word → POS tag via spaCy
        "curbed" → "VERB"
```

---

## 6. Phase 3 — Tap-a-Word Intelligence

This is the core differentiator of the app.

### 6.1 Flow

```
User taps a word in ArticleText component
       │
       ▼
ArticleText: onWordTap(tok.text, sent.text)
  └── e.stopPropagation() — prevents sentence click
       │
       ▼
ArticleReaderPage: handleWordTap(word, sentence)
  ├── inspect(word, sentence)  → useWordInspect hook
  ├── setSelectedWord(word)    → highlights word in text
  └── setSelectedSentence(sentence)
       │
       ▼
useWordInspect: inspect(word, sentence)
  ├── setLoading(true)
  ├── setError(null)
  ├── setData(null)
  └── wordsApi.inspect({ word, sentence })
       │
       ▼
POST /api/words/inspect  { "word": "curbed", "sentence": "The government curbed inflation." }
       │
       ▼
word_intelligence_service.inspect_word()
  │
  ├── Step 1: NLP
  │     lemma = get_lemma("curbed") → "curb"
  │     pos = get_pos("curbed") → "VERB"
  │
  ├── Step 2: Dictionary (Redis cached)
  │     lookup_word("curb")
  │     ├── Check Redis cache (7-day TTL)
  │     ├── Cache miss → WordNet query
  │     │   ├── synsets → definitions, synonyms, POS tags
  │     │   └── eng-to-ipa → IPA pronunciation
  │     ├── Store in Redis cache
  │     └── Return { definitions, synonyms, pronunciation }
  │     Pick definition matching POS → "to control or reduce"
  │
  ├── Step 3: AI Context Meaning (Ollama, Redis cached)
  │     generate_context_meaning("curbed", "The government curbed inflation.")
  │     Prompt: "A student tapped 'curbed'. Explain what it means in this context."
  │     Cache key: "context:curbed:The government..."
  │     Fallback: "Look up 'curb' in the dictionary..."
  │
  └── Step 4: AI Example (Ollama, Redis cached)
        generate_example("curb", "to control or reduce")
        Prompt: "Generate one sentence using 'curb' with meaning..."
        Fallback: "The teacher will help curb the students' behavior."
       │
       ▼
Response:
{
  "word": "curbed",
  "lemma": "curb",
  "dictionary": {
    "definition": "to control or reduce",
    "pos": "VERB",
    "pronunciation": "/kɜːrb/",
    "synonyms": ["reduce", "restrain", "control", "limit"]
  },
  "context_meaning": "In this sentence, 'curbed' means the government took action to reduce inflation.",
  "example": "The new policy aims to curb spending on unnecessary programs."
}
       │
       ▼
Frontend:
  ├── setData(result) → WordCard renders
  ├── Selected word highlighted in yellow in ArticleText
  └── WordCard slides in from right (300ms animation)
```

### 6.2 Word Card Display

```
┌─────────────────────────────────┐
│ CURBED                         │
│ curb · VERB           [⭐ Save] │
│─────────────────────────────────│
│ MEANING                        │
│ to control or reduce           │
│                                │
│ IN THIS SENTENCE               │
│ (AI context meaning)           │
│                                │
│ PRONUNCIATION                  │
│ /kɜːrb/                        │
│                                │
│ EXAMPLE                        │
│ (AI-generated sentence)        │
│                                │
│ SYNONYMS                       │
│ [reduce] [restrain] [control]  │
└─────────────────────────────────┘
```

### 6.3 Keyboard Shortcuts

While the word card is open:
- Click another word → new word card (previous aborted)
- Press Escape → not applicable (word card has no keyboard shortcuts)

---

## 7. Phase 4 — AI Sentence Explanation

### 7.1 Flow

```
User clicks a sentence in ArticleText
       │
       ▼
ArticleText: onSentenceTap(sent.text)
       │
       ▼
ArticleReaderPage: handleSentenceSelect(sentence)
  ├── setSelectedSentence(sentence)
  ├── setShowAiPanel(true)
  └── setAiMinimized(false)
       │
       ▼
AiExplanationPanel renders below the article text
  │
  ├── Shows selected sentence in a gray box
  ├── 6 action buttons: Simple English, Grammar, Vocabulary,
  │   Why this word?, Examples, Simplify
  ├── Keyboard shortcuts: press 1-6 to trigger
  ├── Minimize button (—) collapses to floating pill
  └── Close button (✕) closes panel
```

### 7.2 Action Trigger Flow

```
User clicks "Grammar" button (or presses 2)
       │
       ▼
handleExplain("grammar")
  ├── Check cache: cacheRef.current.get("grammar")
  │   ├── Cache hit → instant display (no spinner)
  │   └── Cache miss → proceed to API
  │
  ├── Cancel any previous in-flight request (AbortController)
  ├── Create new AbortController
  ├── setLoading(true)
  │
  └── wordsApi.explain({ sentence, action: "grammar" })
       │
       ▼
POST /api/words/explain  { "sentence": "...", "action": "grammar" }
       │
       ▼
word_intelligence_service.explain_sentence()
  │
  └── ai_service.generate_explanation(sentence, "grammar")
        │
        ├── Check Redis cache (1-day TTL)
        │   Key: "explain:grammar:The central bank..."
        │
        ├── Cache miss → Build prompt:
        │   "Explain the grammar of this sentence step by step: ..."
        │
        ├── Call Ollama API (httpx POST to /api/generate)
        │   ├── Model: qwen2.5:7b
        │   ├── Timeout: 30s
        │   ├── Retries: 2x with exponential backoff
        │   └── Options: temperature=0.7, top_p=0.9
        │
        ├── Store result in Redis cache
        └── Return explanation text
       │
       ▼
Frontend:
  ├── setExplanation(result.explanation)
  ├── cacheRef.current.set("grammar", explanation)
  └── Explanation renders in indigo box with copy button
```

### 7.3 AI Actions Reference

| Key | Action | Prompt Template |
|-----|--------|----------------|
| 1 | Simple English | "Rewrite this sentence in simpler English that a B1 learner would understand" |
| 2 | Grammar | "Explain the grammar of this sentence step by step" |
| 3 | Vocabulary | "Define the key vocabulary words and phrases in this sentence" |
| 4 | Why this word? | "Explain why each key word was chosen. Cover connotation, register, nuance" |
| 5 | Examples | "Generate 3 example sentences with similar vocabulary and structure" |
| 6 | Simplify | "Translate this sentence to simple English" |

### 7.4 AI Panel Features

| Feature | Detail |
|---------|--------|
| **Cache** | Same sentence + action = instant display (Map in component state) |
| **Abort** | Previous request cancelled when new action triggered or panel closed |
| **Retry** | Error state shows retry button, removes from cache, re-fetches |
| **Copy** | Copy-to-clipboard button on explanation result |
| **Minimize** | Collapse to floating pill at bottom-right |
| **Keyboard** | 1-6 triggers actions, Esc closes panel |
| **Loading** | Skeleton shimmer animation + "AI is thinking…" pulse |
| **Error handling** | Network error, timeout, generic — each with friendly message |

### 7.5 Minimize / Restore Flow

```
Click minimize (—)
  └── setAiMinimized(true)
      Panel unmounts, floating pill appears at bottom-right:
      ┌──────────────────────────────┐
      │ 💬 AI Assistant  [12 words]  │
      └──────────────────────────────┘

Click pill
  └── setAiMinimized(false)
      Panel re-renders with cached state intact
```

---

## 8. Phase 5 — Personal Vocabulary

### 8.1 Save Word Flow

```
User clicks "⭐ Save" on WordCard
       │
       ▼
useWordInspect: save()
  ├── setSaving(true)
  └── vocabularyApi.save({
        word: "curbed",
        lemma: "curb",
        meaning: "to control or reduce",
        context_sentence: "The government curbed inflation."
      })
       │
       ▼
POST /api/vocabulary
       │
       ▼
vocabulary_service.save_word()
  ├── Check for duplicate (same user + word)
  │   └── If exists → raise ConflictError
  ├── Create UserVocabulary record:
  │   ├── word, lemma, meaning
  │   ├── difficulty: "Medium" (default)
  │   ├── mastery_level: 0.0
  │   ├── times_seen: 1
  │   ├── times_reviewed: 0
  │   └── next_review_date: now + 1 day
  ├── Track learning event: WORD_SAVED
  └── Return VocabularyWord
       │
       ▼
Frontend:
  ├── setSaved(true)
  └── Shows "✅ Word saved to vocabulary!"
```

### 8.2 Vocabulary Page Flow

```
Navigate to /vocabulary
       │
       ▼
VocabularyPage mounts → useVocabulary()
  └── Fetches: GET /api/vocabulary?offset=0&limit=50
       │
       ▼
Response: { vocabulary: [...], total: 42 }
       │
       ▼
Renders:
  ├── Header: "My Vocabulary — 42 words saved"
  ├── Search bar (client-side filter):
  │   ├── Searches: word, lemma, meaning, personal_note
  │   ├── Debounced input
  │   └── Clear button (X)
  ├── Filter panel (toggle):
  │   ├── Difficulty: All | Easy | Medium | Hard
  │   └── Sort: Newest | Oldest | Mastery ↑↓ | A→Z | Difficulty
  ├── VocabularyRow for each word:
  │   ├── Word + difficulty badge
  │   ├── Meaning (truncated)
  │   ├── Mastery bar (0-100%)
  │   ├── Review count
  │   └── Delete button (🗑️)
  └── Empty state if no words
```

### 8.3 Delete Word Flow

```
Click 🗑️ on VocabularyRow
       │
       ▼
onDelete(word.id)
  └── vocabularyApi.delete(id)
       │
       ▼
DELETE /api/vocabulary/{id}
       │
       ▼
vocabulary_service.delete_vocabulary()
  └── DELETE FROM user_vocabulary WHERE id = ?
       │
       ▼
Frontend: Optimistic UI update
  └── setWords(prev => prev.filter(w => w.id !== id))
```

---

## 9. Phase 6 — Spaced Repetition & Quizzes

### 9.1 Review Page Flow

```
Navigate to /review
       │
       ▼
ReviewPage mounts → useReviews()
  ├── Fetch stats: GET /api/review/stats
  ├── Fetch due items: GET /api/review/due?limit=20
  └── Both in parallel
       │
       ▼
Response:
  stats: { total_words, words_mastered, words_learning, words_new, retention_rate, streak_days }
  items: [{ vocabulary_id, word, lemma, meaning, difficulty }, ...]
       │
       ▼
Renders:
  ├── Stats bar: Total Words | Mastered | Learning | Retention
  ├── QuizCard for current item (index 0)
  └── Progress: "1 / 12"
```

### 9.2 Quiz Flow

```
QuizCard renders with current word
       │
       ▼
Builds 4 options:
  ├── 1 correct answer (word's meaning)
  └── 3 random distractors from FAKE_OPTIONS pool
  Shuffled randomly
       │
       ▼
User clicks an option
       │
       ▼
handleSelect(idx)
  ├── setAnswered(true)
  ├── Check: idx === correctIdx?
  ├── onAnswer(vocabularyId, isCorrect)
  │
  ▼
useReviews: submitAnswer(vocabularyId, correct)
  └── reviewApi.submitAnswer({ vocabulary_id, answer_correct })
       │
       ▼
POST /api/review/answer
       │
       ▼
review_service.submit_answer()
  ├── Fetch UserVocabulary record
  ├── If correct:
  │   ├── mastery_level += 0.1 (capped at 1.0)
  │   ├── interval_days = next_interval(current_interval)
  │   │   Fixed intervals: 1 → 3 → 7 → 14 → 30 → 60 days
  │   └── next_review_date = now + interval_days
  ├── If wrong:
  │   ├── mastery_level = max(0, mastery_level - 0.15)
  │   ├── interval_days = 1 (reset to 1 day)
  │   └── next_review_date = now + 1 day
  ├── times_reviewed += 1
  ├── Track learning event: QUIZ_ANSWERED
  └── Return { vocabulary_id, correct, mastery_level, next_review_date, interval_days }
       │
       ▼
Frontend:
  ├── Shows ✓ Correct / ✗ Incorrect feedback
  ├── After 1.5s → auto-advance to next card
  └── If no more items → "All caught up!" empty state
```

### 9.3 Spaced Repetition Schedule

```
New word saved
       │
       ▼
next_review_date = now + 1 day
       │
       ▼
┌─ CORRECT ──────────────────────────────┐
│ 1 day → 3 days → 7 days → 14 days     │
│ → 30 days → 60 days → mastered        │
│                                        │
│ Each correct answer:                   │
│   mastery += 0.1, interval = next step │
└────────────────────────────────────────┘

┌─ WRONG ────────────────────────────────┐
│ Reset to 1 day                         │
│ mastery = max(0, mastery - 0.15)       │
└────────────────────────────────────────┘

Mastery levels:
  0.0 - 0.3 → "New"
  0.3 - 0.7 → "Learning"
  0.7 - 1.0 → "Mastered"
```

### 9.4 Stats Calculation

```
review_service.get_review_stats()
  │
  ├── total_words: COUNT(*) FROM user_vocabulary WHERE user_id = ?
  │
  ├── words_mastered: COUNT(*) WHERE mastery_level >= 0.7
  │
  ├── words_learning: COUNT(*) WHERE mastery_level >= 0.3 AND < 0.7
  │
  ├── words_new: COUNT(*) WHERE mastery_level < 0.3
  │
  ├── retention_rate:
  │   ├── total_reviews: SUM(times_reviewed) for all words
  │   └── rate = (total_words / total_reviews * 100) if reviews > 0 else 0
  │
  └── streak_days:
      ├── Check learning events for consecutive days with activity
      ├── Counts backwards from today (up to 365 days)
      └── Returns number of consecutive days with QUIZ_ANSWERED events
```

---

## 10. Phase 7 — Learning Events & Analytics

### 10.1 Event Types

| Event | When Triggered | Data Stored |
|-------|---------------|-------------|
| `WORD_VIEWED` | User taps a word | vocabulary_id, context_sentence |
| `WORD_SAVED` | User saves to vocabulary | vocabulary_id, context_sentence |
| `ARTICLE_READ` | User opens an article | article_id |
| `ARTICLE_COMPLETED` | User finishes reading | article_id |
| `AI_EXPLANATION_REQUESTED` | User requests AI explanation | context_sentence = "[action] sentence" |
| `QUIZ_STARTED` | User begins review session | vocabulary_id |
| `QUIZ_ANSWERED` | User submits quiz answer | vocabulary_id, correct/incorrect |

### 10.2 Event Tracking

```
learning_event_service.py
  │
  ├── track_event(db, user_id, event_type, ...)
  │     Creates LearningEvent record
  │
  └── Convenience functions:
        track_word_viewed()
        track_word_saved()
        track_article_read()
        track_article_completed()
        track_ai_explanation()
        track_quiz_started()
```

---

## 11. Phase 8 — pgvector Semantic Search

### 11.1 Setup

```
core/pgvector.py
  │
  ├── ensure_pgvector_extension(db)
  │     CREATE EXTENSION IF NOT EXISTS vector
  │
  ├── generate_embedding(text) → list[float]
  │     Uses sentence-transformers "all-MiniLM-L6-v2"
  │     Returns 384-dimensional normalized vector
  │
  ├── generate_embeddings_batch(texts) → list[list[float]]
  │     Batch processing (32 at a time) for efficiency
  │
  └── find_similar_sentences(db, query_embedding, user_id, limit=5, threshold=0.3)
        SQL query using cosine distance (<=> operator)
        Joins: sentence_embeddings → article_sentences → paragraphs → articles
        Filters: user_id, similarity > threshold
        Returns: [{ sentence_id, text, similarity }]
```

### 11.2 Model

```
models/embedding.py — SentenceEmbedding

┌─────────────────────────────────┐
│ sentence_embeddings             │
├─────────────────────────────────┤
│ id: UUID (PK)                   │
│ sentence_id: UUID (FK → sentences, unique)│
│ embedding: Vector(384)          │
│ model_name: VARCHAR(100)        │
│ created_at: TIMESTAMP           │
└─────────────────────────────────┘
```

---

## 12. Phase 9 — Redis Caching Layer

### 12.1 Cache Architecture

```
core/cache.py
  │
  ├── Generic: get_cached(prefix, *args) / set_cached(prefix, value, ttl, *args)
  │   Key format: "rusr:{prefix}:{md5(args)}"
  │
  ├── Dictionary cache (7-day TTL):
  │   cache_dictionary(word, data) / get_cached_dictionary(word)
  │
  ├── AI explanation cache (1-day TTL):
  │   cache_explanation(key_parts, data) / get_cached_explanation(key_parts)
  │
  └── Pronunciation cache (30-day TTL):
        cache_pronunciation(word, data) / get_cached_pronunciation(word)
```

### 12.2 What Gets Cached

| Data | TTL | Cache Key Pattern | Where Used |
|------|-----|-------------------|------------|
| WordNet definitions | 7 days | `rusr:dict:{md5(word)}` | dictionary_service.py |
| IPA pronunciation | 30 days | `rusr:pron:{md5(word)}` | dictionary_service.py |
| AI explanations | 1 day | `rusr:ai_explain:{md5(action+sentence)}` | ai_service.py |

### 12.3 Cache Flow

```
Dictionary lookup for "curb"
  │
  ├── Check Redis: GET rusr:dict:{md5("curb")}
  │   ├── HIT → return cached data (microseconds)
  │   └── MISS → proceed to WordNet
  │
  ├── WordNet query (slow, ~50ms)
  ├── eng-to-ipa conversion
  │
  ├── Store in Redis: SETEX rusr:dict:{md5("curb")} 604800 {json}
  └── Return result
```

---

## 13. Frontend Architecture

### 13.1 Page Structure

```
App.tsx (Routes)
  │
  ├── /login → LoginPage (public)
  │
  └── ProtectedRoute (checks isAuthenticated())
      │
      └── Layout (Navbar + Outlet)
          │
          ├── / → HomePage
          │     ├── DailySummary (greeting, stats, continue reading)
          │     ├── Add Article form (URL or text)
          │     └── ArticleCard list
          │
          ├── /article/:id → ArticleReaderPage
          │     ├── ArticleText (tappable words + sentences)
          │     ├── WordCard (sidebar, slide-in animation)
          │     ├── AiExplanationPanel (below article)
          │     └── Minimized AI pill (floating bottom-right)
          │
          ├── /vocabulary → VocabularyPage
          │     ├── Search bar
          │     ├── Filter panel (difficulty, sort)
          │     └── VocabularyRow list
          │
          └── /review → ReviewPage
                ├── Stats bar (4 cards)
                └── QuizCard (one at a time)
```

### 13.2 Component Hierarchy

```
Layout
├── Navbar
│   ├── Nav links (Home, Vocabulary, Review)
│   ├── Dark mode toggle (☀️/🌙)
│   ├── User email display
│   └── Logout button
│
├── HomePage
│   ├── DailySummary
│   │   ├── Time-based greeting
│   │   ├── Quick stats (new words, due reviews, streak)
│   │   └── "Continue Reading" link
│   ├── Add Article form
│   │   ├── URL/Text toggle
│   │   ├── Input fields
│   │   └── Ingest/Cancel buttons
│   └── ArticleCard (×N)
│
├── ArticleReaderPage
│   ├── ArticleText
│   │   ├── Paragraphs → Sentences → Tokens
│   │   ├── Word highlighting (yellow ring)
│   │   └── Hover effects (yellow bg for words, indigo for sentences)
│   ├── WordCard (sidebar)
│   │   ├── Slide-in animation
│   │   ├── Word + lemma + POS
│   │   ├── Save button
│   │   ├── Definition, pronunciation, example, synonyms
│   │   └── Context meaning
│   ├── AiExplanationPanel
│   │   ├── 6 action buttons (with keyboard shortcuts 1-6)
│   │   ├── Skeleton loading shimmer
│   │   ├── Error state with retry
│   │   ├── Explanation result with copy button
│   │   ├── "Try another action" link
│   │   ├── Explanation cache (Map)
│   │   └── Minimize button (→ floating pill)
│   └── ErrorBoundary (wraps AI panel + word card)
│
├── VocabularyPage
│   ├── Search bar (client-side filter)
│   ├── Filter panel (difficulty, sort)
│   └── VocabularyRow (×N)
│       ├── Word + difficulty badge
│       ├── Meaning
│       ├── Mastery bar
│       └── Delete button
│
└── ReviewPage
    ├── StatCard (×4)
    └── QuizCard
        ├── Word display
        ├── 4 options (1 correct + 3 fakes)
        └── Correct/Incorrect feedback
```

### 13.3 Custom Hooks

| Hook | State Managed | API Calls |
|------|--------------|-----------|
| `useArticles()` | articles[], loading, error | `articlesApi.list()`, `articlesApi.get()` |
| `useVocabulary()` | words[], total, loading, error | `vocabularyApi.list()`, `vocabularyApi.delete()` |
| `useWordInspect()` | data, loading, saving, saved, error | `wordsApi.inspect()`, `vocabularyApi.save()` |
| `useReviews()` | items[], totalDue, stats, loading, error | `reviewApi.getDue()`, `reviewApi.submitAnswer()`, `reviewApi.getStats()` |
| `useDarkMode()` | theme, isDark | localStorage read/write |

### 13.4 Dark Mode

```
useDarkMode() hook
  ├── Reads from localStorage("rusr_theme")
  ├── Falls back to prefers-color-scheme
  ├── Toggles .dark class on <html>
  ├── Custom Tailwind variant: @custom-variant dark (&:where(.dark, .dark *))
  └── Every component has dark: variants
```

---

## 14. Frontend ↔ Backend Communication

### 14.1 HTTP Request Lifecycle

```
1. Component calls hook function (e.g., inspect("curb", "sentence"))
2. Hook calls API function (e.g., wordsApi.inspect({ word, sentence }))
3. api.ts request() function:
   a. Reads JWT from localStorage("rusr_token")
   b. Builds headers: { Content-Type, Authorization: Bearer <token> }
   c. Makes fetch("/api/words/inspect", { method: "POST", body, headers })
   d. Vite dev server proxies /api → localhost:8000
   e. Receives response
   f. Handles 401 → clear token, redirect to /login
   g. Handles !ok → parse error JSON, throw Error
   h. Handles 204 → return undefined
   i. Otherwise → return res.json()
4. Hook receives result, updates state
5. Component re-renders with new data
```

### 14.2 Vite Proxy Configuration

```typescript
// frontend/vite.config.ts
server: {
  proxy: {
    "/api": {
      target: "http://localhost:8000",
      changeOrigin: true,
    },
  },
}
```

This means:
- Frontend dev server runs on `http://localhost:5173`
- Any `fetch("/api/...")` is proxied to `http://localhost:8000/api/...`
- No CORS issues in development
- In production, Nginx handles the proxy

### 14.3 Complete Request Map

```
FRONTEND                              BACKEND
────────                              ───────

authApi.login(data)
  → POST /api/auth/login                → auth_service.login()
  ← { access_token, user }             ← bcrypt verify + JWT create

authApi.register(data)
  → POST /api/auth/register             → auth_service.register()
  ← { access_token, user }             ← bcrypt hash + JWT create

articlesApi.ingestFromUrl(url)
  → POST /api/articles/url              → article_service.ingest_from_url()
  ← Article object                     ← httpx fetch + readability + spaCy NLP

articlesApi.ingestFromText(data)
  → POST /api/articles/text             → article_service.ingest_from_text()
  ← Article object                     ← spaCy paragraph/sentence/token split

articlesApi.list(offset, limit)
  → GET /api/articles?offset=0&limit=20 → article_service.list_articles()
  ← { articles: [...], total: N }      ← SQL SELECT with pagination

articlesApi.get(id)
  → GET /api/articles/{id}              → article_service.get_article()
  ← Article with paragraphs            ← SQLAlchemy relationship loading

wordsApi.inspect({ word, sentence })
  → POST /api/words/inspect             → word_intelligence_service.inspect_word()
  ← WordInspectResponse                ← NLP + Dictionary (Redis) + AI (Ollama)

wordsApi.explain({ sentence, action })
  → POST /api/words/explain             → word_intelligence_service.explain_sentence()
  ← ExplainResponse                    ← AI (Ollama, Redis cached)

vocabularyApi.save(data)
  → POST /api/vocabulary                → vocabulary_service.save_word()
  ← VocabularyWord                     ← Duplicate check + learning event

vocabularyApi.list(offset, limit)
  → GET /api/vocabulary                 → vocabulary_service.get_vocabulary()
  ← { vocabulary: [...], total: N }

vocabularyApi.delete(id)
  → DELETE /api/vocabulary/{id}         → vocabulary_service.delete_vocabulary()
  ← 204 No Content

reviewApi.getDue(limit)
  → GET /api/review/due                 → review_service.get_due_reviews()
  ← { items: [...], total_due: N }     ← WHERE next_review_date <= NOW()

reviewApi.submitAnswer(data)
  → POST /api/review/answer             → review_service.submit_answer()
  ← { mastery_level, interval_days }   ← SRS interval update

reviewApi.getStats()
  → GET /api/review/stats               → review_service.get_review_stats()
  ← { total_words, mastered, learning }← Aggregate queries

usersApi.getProfile()
  → GET /api/users/me                   → Direct return
  ← User object

usersApi.deleteAccount()
  → DELETE /api/users/me                → Cascading delete
  ← 204 No Content
```

---

## 15. Complete API Reference

### Auth

| Method | Endpoint | Body | Response | Status |
|--------|----------|------|----------|--------|
| POST | `/api/auth/register` | `{ email, password, full_name? }` | `{ access_token, token_type, user }` | 201 |
| POST | `/api/auth/login` | `{ email, password }` | `{ access_token, token_type, user }` | 200 |

### Articles

| Method | Endpoint | Body/Params | Response | Status |
|--------|----------|-------------|----------|--------|
| POST | `/api/articles/url` | `{ url }` | Article object | 201 |
| POST | `/api/articles/text` | `{ title, text, source?, author? }` | Article object | 201 |
| GET | `/api/articles` | `?offset=0&limit=20` | `{ articles: [...], total }` | 200 |
| GET | `/api/articles/{id}` | — | Article with paragraphs/sentences/tokens | 200 |

### Vocabulary

| Method | Endpoint | Body/Params | Response | Status |
|--------|----------|-------------|----------|--------|
| POST | `/api/vocabulary` | `{ word, lemma, meaning?, context_sentence?, difficulty? }` | VocabularyWord | 201 |
| GET | `/api/vocabulary` | `?offset=0&limit=50` | `{ vocabulary: [...], total }` | 200 |
| GET | `/api/vocabulary/{id}` | — | VocabularyWord | 200 |
| PUT | `/api/vocabulary/{id}` | `{ meaning?, personal_note?, difficulty? }` | VocabularyWord | 200 |
| DELETE | `/api/vocabulary/{id}` | — | — | 204 |

### Word Intelligence

| Method | Endpoint | Body | Response | Status |
|--------|----------|------|----------|--------|
| POST | `/api/words/inspect` | `{ word, sentence }` | WordInspectResponse | 200 |
| POST | `/api/words/explain` | `{ sentence, action? }` | ExplainResponse | 200 |

### Review

| Method | Endpoint | Params | Response | Status |
|--------|----------|--------|----------|--------|
| GET | `/api/review/due` | `?limit=20` | `{ items: [...], total_due }` | 200 |
| POST | `/api/review/answer` | `{ vocabulary_id, answer_correct }` | AnswerResult | 200 |
| GET | `/api/review/stats` | — | ReviewStats | 200 |

### Users

| Method | Endpoint | Response | Status |
|--------|----------|----------|--------|
| GET | `/api/users/me` | User object | 200 |
| DELETE | `/api/users/me` | — | 204 |

### Health

| Method | Endpoint | Response | Status |
|--------|----------|----------|--------|
| GET | `/health` | `{ status: "ok", version }` | 200 |

---

## 16. Database Schema

### Tables (8 total)

```
users
├── id: UUID (PK)
├── email: VARCHAR (unique)
├── hashed_password: VARCHAR
├── full_name: VARCHAR (nullable)
├── created_at: TIMESTAMP
└── updated_at: TIMESTAMP

articles
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── title: TEXT
├── source: TEXT (nullable)
├── url: TEXT (nullable)
├── author: TEXT (nullable)
├── published_at: TIMESTAMP (nullable)
└── created_at: TIMESTAMP

article_paragraphs
├── id: UUID (PK)
├── article_id: UUID (FK → articles)
├── sequence: INTEGER
└── text: TEXT

article_sentences
├── id: UUID (PK)
├── paragraph_id: UUID (FK → article_paragraphs)
├── sequence: INTEGER
└── text: TEXT

sentence_tokens
├── id: UUID (PK)
├── sentence_id: UUID (FK → article_sentences)
├── position: INTEGER
├── text: VARCHAR (surface form)
├── lemma: VARCHAR (base form)
└── pos: VARCHAR (part of speech)

user_vocabulary
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── word: VARCHAR
├── lemma: VARCHAR
├── meaning: TEXT (nullable)
├── first_seen: TIMESTAMP
├── times_seen: INTEGER (default 1)
├── times_reviewed: INTEGER (default 0)
├── mastery_level: FLOAT (default 0.0)
├── difficulty: VARCHAR (Easy/Medium/Hard)
├── personal_note: TEXT (nullable)
├── next_review_date: TIMESTAMP (nullable)
├── created_at: TIMESTAMP
└── updated_at: TIMESTAMP

learning_events
├── id: UUID (PK)
├── user_id: UUID (FK → users)
├── vocabulary_id: UUID (FK → user_vocabulary, nullable)
├── event_type: VARCHAR
├── context_sentence: TEXT (nullable)
└── created_at: TIMESTAMP

sentence_embeddings
├── id: UUID (PK)
├── sentence_id: UUID (FK → article_sentences, unique)
├── embedding: Vector(384)
├── model_name: VARCHAR(100)
└── created_at: TIMESTAMP
```

### Entity Relationships

```
users 1──N articles 1──N article_paragraphs 1──N article_sentences 1──N sentence_tokens
users 1──N user_vocabulary
users 1──N learning_events
user_vocabulary 1──N learning_events
article_sentences 1──1 sentence_embeddings
```

---

## 17. Server Management — Without Docker

### Prerequisites

```bash
# Required software
Python 3.12+
Node.js 20+
PostgreSQL 16+
Redis 7+
Ollama (for AI features)
```

### 17.1 Database Setup

```bash
# Create database
createdb rusr_db

# Or with psql
psql -U postgres -c "CREATE DATABASE rusr_db;"
```

### 17.2 Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

# Set up environment variables
cp .env.example .env
# Edit .env with your database/Redis credentials

# Initialize database tables
python -m scripts.init_db

# Run migrations (optional, for schema changes)
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 17.3 Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Runs on http://localhost:5173
# Proxies /api → localhost:8000
```

### 17.4 Ollama Setup (for AI features)

```bash
# Install Ollama
# macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: download from ollama.com

# Start Ollama
ollama serve

# Pull the model (in another terminal)
ollama pull qwen2.5:7b
```

### 17.5 Starting Everything

```bash
# Terminal 1: PostgreSQL (if not running as service)
pg_ctl start

# Terminal 2: Redis
redis-server

# Terminal 3: Ollama
ollama serve

# Terminal 4: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 5: Frontend
cd frontend
npm run dev
```

### 17.6 Stopping Everything

```bash
# Terminal 5: Frontend — Ctrl+C

# Terminal 4: Backend — Ctrl+C

# Terminal 3: Ollama — Ctrl+C

# Terminal 2: Redis
redis-cli shutdown

# Terminal 1: PostgreSQL
pg_ctl stop
```

---

## 18. Server Management — With Docker

### 18.1 Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgres:16-alpine | 5432 | Database |
| `redis` | redis:7-alpine | 6379 | Cache |
| `ollama` | ollama/ollama:latest | 11434 | Local LLM |
| `backend` | Custom (FastAPI) | 8000 | REST API |
| `frontend` | Custom (React + Nginx) | 3000 | Web app |

### 18.2 Start All Services

```bash
# From project root
docker-compose up --build

# Or in background
docker-compose up --build -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 18.3 First-Time Setup

```bash
# After docker-compose up, pull the LLM model
docker exec -it rusr-ollama ollama pull qwen2.5:7b

# The backend auto-creates tables on startup
# No manual migration needed
```

### 18.4 Stop All Services

```bash
# Stop containers (preserves data)
docker-compose down

# Stop and remove volumes (DELETES all data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### 18.5 Individual Service Management

```bash
# Restart one service
docker-compose restart backend

# Rebuild one service
docker-compose up --build backend

# View container status
docker-compose ps

# Execute command in running container
docker exec -it rusr-backend bash
docker exec -it rusr-postgres psql -U postgres rusr_db
```

### 18.6 Docker Compose Environment Variables

```yaml
# Backend environment (set in docker-compose.yml)
DATABASE_URL: postgresql+asyncpg://postgres:postgres@postgres:5432/rusr_db
REDIS_URL: redis://redis:6379/0
OLLAMA_BASE_URL: http://ollama:11434
OLLAMA_MODEL: qwen2.5:7b
SECRET_KEY: change-me-in-production
CORS_ORIGINS: '["http://localhost:3000"]'
```

### 18.7 Volumes

```yaml
volumes:
  pgdata:       # PostgreSQL data (persists across restarts)
  ollama_data:  # Ollama models (persists across restarts)
```

---

## 19. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Connection refused` on backend | PostgreSQL/Redis not running | Start them or use Docker |
| `401 Unauthorized` on all requests | JWT token expired or invalid | Re-login, clear localStorage |
| `AI service unavailable` | Ollama not running | Start Ollama, pull model |
| `Module not found` errors | Missing Python packages | `pip install -r requirements.txt` |
| `spacy` model not found | spaCy model not downloaded | `python -m spacy download en_core_web_sm` |
| Frontend can't reach backend | Vite proxy not configured | Check `vite.config.ts` proxy settings |
| Dark mode not persisting | localStorage blocked | Check browser settings |
| `pgvector` extension error | Extension not installed | `CREATE EXTENSION IF NOT EXISTS vector` |

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# PostgreSQL
psql -U postgres -d rusr_db -c "SELECT 1;"

# Redis
redis-cli ping

# Ollama
curl http://localhost:11434/api/tags

# Frontend
curl http://localhost:3000
```

### Logs

```bash
# Docker logs
docker-compose logs backend
docker-compose logs frontend

# Backend stdout (dev mode)
# Printed to terminal where uvicorn is running

# Check for errors in browser console
# Open DevTools → Console tab
```

---

## 20. Project File Structure

```
.
├── END-to-END-FLOW.md          # This document
├── SPEC.md                      # Technical specification
├── 1.Chatgpt_Details.md         # Original design notes
├── docker-compose.yml           # Full stack orchestration
│
├── backend/                     # Python + FastAPI
│   ├── main.py                  # Entry point (uvicorn)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example             # Environment template
│   ├── Dockerfile               # Backend container
│   ├── alembic.ini              # Alembic configuration
│   │
│   ├── alembic/                 # Database migrations
│   │   ├── env.py               # Async Alembic environment
│   │   ├── script.py.mako       # Migration template
│   │   └── versions/            # Migration files
│   │
│   ├── core/                    # Infrastructure
│   │   ├── config.py            # Pydantic settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── dependencies.py      # FastAPI dependency injection
│   │   ├── redis.py             # Redis connection
│   │   ├── auth.py              # JWT dependency (get_current_user)
│   │   ├── cache.py             # Redis caching layer
│   │   └── pgvector.py          # Vector search setup
│   │
│   ├── common/                  # Shared utilities
│   │   ├── exceptions.py        # AppError, NotFoundError, etc.
│   │   ├── middleware.py        # Request timing middleware
│   │   └── utils.py             # Helper functions
│   │
│   ├── models/                  # SQLAlchemy ORM
│   │   ├── user.py              # User model
│   │   ├── article.py           # Article + Paragraph + Sentence
│   │   ├── token.py             # SentenceToken (NLP-annotated)
│   │   ├── vocabulary.py        # UserVocabulary
│   │   ├── learning_event.py    # LearningEvent
│   │   └── embedding.py         # SentenceEmbedding (pgvector)
│   │
│   ├── schemas/                 # Pydantic request/response
│   │   ├── user.py              # UserCreate, UserLogin, TokenResponse
│   │   ├── article.py           # ArticleCreate, ArticleResponse
│   │   ├── vocabulary.py        # VocabularySave, VocabularyResponse
│   │   ├── word.py              # WordInspectRequest/Response, ExplainRequest/Response
│   │   └── review.py            # ReviewDueResponse, ReviewAnswerRequest
│   │
│   ├── services/                # ⭐ Business logic
│   │   ├── auth_service.py      # Register, login, JWT, bcrypt
│   │   ├── article_service.py   # URL/text ingestion, parsing
│   │   ├── nlp_service.py       # spaCy tokenization, POS, sentencizer
│   │   ├── dictionary_service.py# WordNet + IPA + Redis cache
│   │   ├── ai_service.py        # Ollama LLM with retries + Redis cache
│   │   ├── word_intelligence_service.py # Tap-to-lookup pipeline
│   │   ├── vocabulary_service.py# Personal vocabulary CRUD
│   │   ├── review_service.py    # Spaced repetition + quizzes
│   │   └── learning_event_service.py # Event tracking
│   │
│   ├── routes/                  # Thin API controllers
│   │   ├── auth.py              # POST /register, POST /login
│   │   ├── articles.py          # POST /url, POST /text, GET list, GET /{id}
│   │   ├── vocabulary.py        # CRUD endpoints
│   │   ├── words.py             # POST /inspect, POST /explain
│   │   ├── review.py            # GET /due, POST /answer, GET /stats
│   │   └── users.py             # GET /me, DELETE /me (GDPR)
│   │
│   └── scripts/
│       └── init_db.py           # Create tables + seed demo user
│
└── frontend/                    # React + Vite + Tailwind
    ├── index.html               # HTML entry point
    ├── package.json             # NPM dependencies
    ├── tsconfig.json            # TypeScript config
    ├── vite.config.ts           # Vite config (proxy to backend)
    ├── Dockerfile               # Multi-stage build
    ├── nginx.conf               # SPA + API proxy
    │
    └── src/
        ├── main.tsx             # React entry point
        ├── App.tsx              # Router + ProtectedRoute
        ├── index.css            # Tailwind + dark mode + animations
        │
        ├── lib/
        │   └── api.ts           # ⭐ All API calls + JWT management
        │
        ├── hooks/
        │   ├── useArticles.ts   # Article list + single article
        │   ├── useVocabulary.ts # Vocabulary list + delete
        │   ├── useWordInspect.ts# Inspect word + save to vocabulary
        │   ├── useReviews.ts    # Due reviews + submit + stats
        │   └── useDarkMode.ts   # Theme toggle + localStorage
        │
        ├── components/
        │   ├── layout/
        │   │   ├── Layout.tsx   # Navbar + Outlet + dark bg
        │   │   └── Navbar.tsx   # Nav links + dark toggle + logout
        │   │
        │   ├── article/
        │   │   ├── ArticleCard.tsx  # Article preview card
        │   │   └── ArticleText.tsx  # Tappable text with highlighting
        │   │
        │   ├── word/
        │   │   ├── WordCard.tsx          # Word details + save
        │   │   ├── AiExplanationPanel.tsx # AI assistant panel
        │   │   └── AiLoadingSkeleton.tsx  # Loading shimmer
        │   │
        │   ├── vocabulary/
        │   │   └── VocabularyRow.tsx     # Vocabulary list item
        │   │
        │   ├── review/
        │   │   └── QuizCard.tsx          # Quiz question card
        │   │
        │   ├── home/
        │   │   └── DailySummary.tsx      # Greeting + stats
        │   │
        │   └── common/
        │       ├── Spinner.tsx           # Loading spinner
        │       ├── EmptyState.tsx        # Empty state placeholder
        │       └── ErrorBoundary.tsx     # React error boundary
        │
        └── pages/
            ├── LoginPage.tsx         # Login/Register form
            ├── HomePage.tsx          # Article list + ingest form
            ├── ArticleReaderPage.tsx  # Full article reader
            ├── VocabularyPage.tsx     # Vocabulary with search/filter
            └── ReviewPage.tsx         # Daily review quiz
```
