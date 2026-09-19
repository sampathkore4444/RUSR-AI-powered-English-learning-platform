# SPEC.md — English Newspaper-Learning App

**Product Name:** Read → Understand → Save → Remember  
**Type:** AI Reading + Personal Vocabulary + Spaced Repetition Platform  
**Date:** 2026-09-19  

---

## 1. Product Vision

An application that helps English learners read newspaper articles, understand vocabulary in context, save new words to a personal vocabulary, and retain them through spaced repetition and quizzes. The app evolves from a dictionary into a **personal English learning engine built around the content the user actually reads**.

### Core User Flow

1. **Read** — User opens an article (via URL, pasted text, or screenshot/PDF).
2. **Understand** — User taps an unknown word; the app provides pronunciation, definition, part of speech, context-aware meaning, synonyms, and an AI-generated explanation.
3. **Save** — User saves the word to their personal vocabulary.
4. **Remember** — Spaced repetition reviews and quizzes ensure the word is retained.

---

## 2. High-Level Architecture

```
                    ┌─────────────────────────────┐
                    │       Mobile / Web App      │
                    │                             │
                    │  📰 Read Article             │
                    │  🔍 Tap Word                 │
                    │  🧠 Ask AI                  │
                    │  ⭐ Save Word                │
                    │  📚 My Vocabulary            │
                    │  🎯 Daily Review             │
                    └──────────────┬──────────────┘
                                   │
                              HTTPS / REST
                                   │
                    ┌──────────────▼──────────────┐
                    │        API Gateway           │
                    │      FastAPI / Nginx         │
                    └──────────────┬──────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
 ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
 │ Article Service │      │ Vocabulary      │      │ Learning        │
 │                 │      │ Service         │      │ Service         │
 │ URL extraction  │      │ words           │      │ SRS             │
 │ article parsing │      │ meanings        │      │ quizzes         │
 │ sentence split  │      │ examples        │      │ review schedule │
 └────────┬────────┘      └────────┬────────┘      └────────┬────────┘
          │                        │                        │
          └────────────────────────┼────────────────────────┘
                                   │
                         ┌─────────▼──────────┐
                         │    AI Orchestrator │
                         │                   │
                         │ Context Builder   │
                         │ Prompt Manager    │
                         │ Model Router      │
                         └─────────┬──────────┘
                                   │
                   ┌───────────────┼────────────────┐
                   │               │                │
                   ▼               ▼                ▼
             ┌──────────┐    ┌──────────┐    ┌────────────┐
             │ Local LLM│    │ OpenAI   │    │ Embedding  │
             │ Qwen etc.│    │ optional │    │ Model      │
             └──────────┘    └──────────┘    └────────────┘

                                   │
             ┌─────────────────────┼─────────────────────┐
             │                     │                     │
             ▼                     ▼                     ▼
       ┌────────────┐       ┌────────────┐       ┌─────────────┐
       │ PostgreSQL │       │ Redis      │       │ pgvector    │
       │            │       │            │       │             │
       │ Users      │       │ Cache      │       │ Embeddings  │
       │ Vocabulary │       │ Sessions   │       │ Semantic    │
       │ Reviews    │       │            │       │ Search      │
       └────────────┘       └────────────┘       └─────────────┘
```

### MVP Strategy

Start with a **modular monolith** (FastAPI) rather than microservices. Split into services only after product-market fit.

```
                    React / Mobile
                           │
                           ▼
                      Nginx
                           │
                           ▼
                       FastAPI
                           │
       ┌───────────────────┼────────────────────┐
       │                   │                    │
       ▼                   ▼                    ▼
 Article Module      Vocabulary Module     Learning Module
       │                   │                    │
       └───────────────────┼────────────────────┘
                           │
                           ▼
                     AI Orchestrator
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
          Ollama        Dictionary      Embeddings
             │
             ▼
        Local LLM
                           │
                           ▼
                    PostgreSQL + pgvector
                           │
                           ▼
                         Redis
```

---

## 3. Technology Stack

| Layer            | Technology                                        | Notes                              |
| ---------------- | ------------------------------------------------- | ---------------------------------- |
| **Frontend**     | React (web)                                   | MVP: Web first                     |
| **Backend**      | Python + FastAPI                                  | Modular monolith for MVP           |
| **Database**     | PostgreSQL + pgvector                             | Relational data + vector embeddings|
| **Cache**        | Redis                                             | Sessions, caching                  |
| **NLP**          | spaCy, WordNet                                    | Tokenization, POS, lemmatization   |
| **Local AI**     | Ollama (Qwen, Llama)                              | LLM runtime for explanations/quizzes|
| **Embeddings**   | sentence-transformers (via Ollama or standalone)   | Semantic search                    |
| **Dictionary**   | WordNet / dictionary API                          | Deterministic word data            |

### What is NOT needed for MVP

- **Hugging Face** — Optional; introduce later for specialized models (OCR, difficulty classification, advanced embeddings).
- **OpenAI API** — Optional; local LLM (Ollama + Qwen) handles explanation generation.
- **Separate Vector DB** — pgvector within PostgreSQL is sufficient.

---

## 4. Core Feature — "Tap a Word"

### 4.1 UI Behavior

When the user taps a word in an article:

```
CURB
━━━━━━━━━━━━━━━━━━━━

Meaning
→ to control, limit, or reduce something

Pronunciation
→ /kɜːrb/

Part of Speech
→ Verb

Meaning in this sentence
→ reduce/control inflationary pressures

Example
→ The government introduced measures to curb spending.

Synonyms
→ reduce
→ restrain
→ control

⭐ Save to My Vocabulary
```

### 4.2 Word Intelligence Pipeline

The app uses a **deterministic-first** approach: use linguistic resources where possible, LLMs only where they add value.

```
User taps "curb"
        │
        ▼
Vocabulary API
        │
        ├──────────────► Dictionary (WordNet / API)
        │                ├─ Definition
        │                ├─ POS
        │                ├─ Pronunciation
        │                └─ Synonyms
        │
        ├──────────────► NLP Engine (spaCy)
        │                ├─ Lemma
        │                ├─ POS
        │                └─ Sentence context
        │
        └──────────────► AI Orchestrator (Ollama)
                         ├─ Meaning in context
                         ├─ Simple explanation
                         └─ Example sentence
```

### 4.3 Lemmatization Example

```
"curbed"
    ↓
Lemma: "curb"
    ↓
Dictionary lookup: "to control/reduce"
    ↓
Context: "The government curbed inflation."
    ↓
AI: "In this sentence, curbed means reduced or controlled."
```

---

## 5. Article Ingestion

### Option A — Paste URL

```
Paste URL
   │
   ▼
Article Extraction
   │
   ▼
Clean HTML
   │
   ▼
Main article detection
   │
   ▼
Paragraph extraction
   │
   ▼
Sentence segmentation
   │
   ▼
Store article
```

### Option B — Upload Screenshot / PDF

```
Image/PDF
   │
   ▼
OCR
   │
   ▼
Text
   │
   ▼
Paragraph detection
   │
   ▼
Sentence segmentation
```

> **Note:** OCR is a post-MVP feature. Use Tesseract or PaddleOCR when needed.

### Option C — Paste Text

```
Text
 ↓
Sentence segmentation
 ↓
Article
```

**MVP scope:** URL + pasted text. OCR (Option B) added later.

---

## 6. Database Schema

### 6.1 Article Tables

```sql
-- Stores the article metadata
ARTICLE
──────────────────
article_id        UUID PRIMARY KEY
user_id           UUID REFERENCES users(id)
title             TEXT
source            TEXT
url               TEXT
author            TEXT
published_at      TIMESTAMP
created_at        TIMESTAMP DEFAULT NOW()

-- Stores paragraphs in order
ARTICLE_PARAGRAPH
──────────────────────
paragraph_id      UUID PRIMARY KEY
article_id        UUID REFERENCES articles(id)
sequence          INTEGER
text              TEXT

-- Stores sentences in order within paragraphs
ARTICLE_SENTENCE
─────────────────────
sentence_id       UUID PRIMARY KEY
paragraph_id      UUID REFERENCES paragraphs(id)
sequence          INTEGER
text              TEXT
```

### 6.2 Token Table (NLP-annotated words)

```sql
-- Each token (word) within a sentence, with linguistic annotations
SENTENCE_TOKEN
────────────────────
token_id          UUID PRIMARY KEY
sentence_id       UUID REFERENCES sentences(id)
position          INTEGER
text              TEXT        -- surface form: "curbed"
lemma             TEXT        -- base form: "curb"
pos               TEXT        -- part of speech: VERB
```

### 6.3 Personal Vocabulary

```sql
-- The user's personal vocabulary store
USER_VOCABULARY
──────────────────────
vocabulary_id     UUID PRIMARY KEY
user_id           UUID REFERENCES users(id)
word              TEXT
lemma             TEXT
meaning           TEXT
first_seen        TIMESTAMP
times_seen        INTEGER DEFAULT 1
times_reviewed    INTEGER DEFAULT 0
mastery_level     FLOAT DEFAULT 0.0      -- 0.0 to 1.0
difficulty        TEXT                    -- Easy / Medium / Hard
personal_note     TEXT
next_review_date  TIMESTAMP
created_at        TIMESTAMP DEFAULT NOW()
updated_at        TIMESTAMP DEFAULT NOW()
```

### 6.4 Learning Events

```sql
-- Tracks every learning interaction for spaced repetition
LEARNING_EVENT
──────────────────────
event_id          UUID PRIMARY KEY
user_id           UUID REFERENCES users(id)
vocabulary_id     UUID REFERENCES user_vocabulary(id)
event_type        TEXT        -- DISCOVERED, SAVED, REVIEWED, QUIZ_CORRECT, QUIZ_WRONG
context_sentence  TEXT        -- the sentence where the word was encountered
created_at        TIMESTAMP DEFAULT NOW()
```

---

## 7. Spaced Repetition System

### 7.1 Learning Lifecycle

```
WORD DISCOVERED
       │
       ▼
USER READS MEANING
       │
       ▼
SAVE WORD
       │
       ▼
EXAMPLE
       │
       ▼
REVIEW
       │
       ▼
QUIZ
       │
       ├── Correct ──────► Increase interval
       │
       └── Wrong ────────► Review sooner
```

### 7.2 MVP Review Schedule (Fixed Intervals)

```
New word → 1 day → 3 days → 7 days → 14 days → 30 days → 60 days
```

### 7.3 Future: FSRS / Anki-style Algorithm

Evolve to a full spaced-repetition scheduler (FSRS) that adapts intervals based on:
- Recall accuracy
- Time since last review
- Word difficulty
- User's overall retention rate

---

## 8. Daily Learning Screen

```
━━━━━━━━━━━━━━━━━━━━━━━━
        GOOD MORNING
━━━━━━━━━━━━━━━━━━━━━━━━

Today's Reading

5 new words
12 words to review

━━━━━━━━━━━━━━━━━━━━━━━━

📖 Continue Reading

"Global markets react to
interest rate decision"

━━━━━━━━━━━━━━━━━━━━━━━━

VOCABULARY REVIEW

1 / 12

What does "curb" mean?

○ increase
○ control/reduce
○ announce
○ calculate

              [CHECK]
```

After answering:

```
✓ Correct

CURB = control or reduce

Example:
The policy was designed to
curb inflation.

Next review:
3 days
```

---

## 9. AI Assistant Features

When the user selects a sentence and requests help:

> "The central bank maintained a restrictive monetary stance despite signs of slowing growth."

### Available AI Actions

| Action                   | Description                                           |
| ------------------------ | ----------------------------------------------------- |
| **Simple English**       | Rewrite in simpler language                           |
| **Explain Grammar**      | Break down grammatical structure                      |
| **Explain Vocabulary**   | Define key words and phrases                          |
| **Why is this word used?** | Explain word choice / nuance                        |
| **Give me 3 examples**   | Generate additional example sentences                 |
| **Translate**            | Translate to the user's native language               |

---

## 10. AI Orchestrator

### 10.1 Architecture

```
                AI ORCHESTRATOR
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   Explanation     Vocabulary      Quiz
      Agent          Agent          Agent
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Model Router
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
          Local LLM          OpenAI (optional)
```

### 10.2 Model Routing

The Model Router selects the appropriate backend for each task:

| Task                  | Model / Backend              |
| --------------------- | ---------------------------- |
| Word definition       | Dictionary / WordNet         |
| POS tagging           | spaCy (NLP)                  |
| Lemmatization         | spaCy (NLP)                  |
| Sentence splitting    | spaCy (NLP)                  |
| Simple explanation    | Local LLM (Qwen via Ollama)  |
| Grammar explanation   | Local LLM (Qwen via Ollama)  |
| Complex explanation   | Larger LLM (fallback)        |
| Quiz generation       | Local LLM (Qwen via Ollama)  |
| Translation           | Translation model / API      |
| Embeddings            | sentence-transformers        |

This approach **keeps operating costs low** by routing simple tasks to deterministic tools and only using LLMs where they add genuine value.

---

## 11. Event System (Post-MVP)

Track user interactions for analytics and personalization:

```
WORD_VIEWED
WORD_SAVED
WORD_REVIEWED
QUIZ_STARTED
QUIZ_ANSWERED
ARTICLE_READ
ARTICLE_COMPLETED
AI_EXPLANATION_REQUESTED
```

---

## 12. Personal Learning Analytics (Post-MVP)

### Vocabulary by Category

```
Finance:      142 words
Technology:    87 words
Economics:     63 words
Politics:      51 words
General:      213 words
```

### Learning Metrics

- **Reading Level** — Estimated CEFR level (A1–C2)
- **Vocabulary Growth** — Words learned over time
- **Retention Rate** — Quiz accuracy over time
- **Weak Words** — Words with low mastery or repeated failures
- **Personalized Articles** — Recommend articles targeting weak areas

---

## 13. Long-Term Vision — Personalized Mini-Lessons

The app detects patterns in what the user struggles with and auto-generates lessons:

```
You know: INFLATION
    │
    ├── inflationary        ← you struggle with this
    ├── deflationary        ← you struggle with this
    ├── monetary policy
    ├── monetary tightening ← you struggle with this
    ├── restrictive stance  ← you struggle with this
    └── interest-rate hike
```

This transforms the app from a dictionary into a **personal English learning engine**.

---

## 14. API Endpoints (MVP)

### Articles

| Method | Endpoint                  | Description                    |
| ------ | ------------------------- | ------------------------------ |
| POST   | `/api/articles/url`       | Ingest article from URL        |
| POST   | `/api/articles/text`      | Ingest article from pasted text|
| GET    | `/api/articles`           | List user's articles           |
| GET    | `/api/articles/{id}`      | Get article with paragraphs    |

### Vocabulary

| Method | Endpoint                          | Description                |
| ------ | --------------------------------- | -------------------------- |
| POST   | `/api/vocabulary`                 | Save a word                |
| GET    | `/api/vocabulary`                 | List saved words           |
| GET    | `/api/vocabulary/{id}`            | Get word details           |
| PUT    | `/api/vocabulary/{id}`            | Update note / difficulty   |
| DELETE | `/api/vocabulary/{id}`            | Remove from vocabulary     |

### Word Intelligence

| Method | Endpoint                              | Description                      |
| ------ | ------------------------------------- | -------------------------------- |
| POST   | `/api/words/inspect`                  | Tap-to-lookup (lemma + dict + AI)|
| POST   | `/api/words/explain`                  | AI explanation of a sentence     |

### Learning

| Method | Endpoint                              | Description                  |
| ------ | ------------------------------------- | ---------------------------- |
| GET    | `/api/review/due`                     | Get words due for review     |
| POST   | `/api/review/answer`                  | Submit quiz answer           |
| GET    | `/api/review/stats`                   | User's learning statistics   |

---

## 15. Non-Functional Requirements

| Requirement          | Target                                      |
| -------------------- | ------------------------------------------- |
| Word tap response    | < 500ms (deterministic parts cached)        |
| Article ingestion    | < 5s for URL; < 2s for pasted text          |
| AI explanation       | < 3s (local LLM)                            |
| Uptime               | 99.5% (MVP acceptable)                      |
| Data retention       | User data retained indefinitely; GDPR-compliant deletion |
| Offline support      | Saved vocabulary accessible offline (post-MVP)|

---

## 16. Deployment

### MVP

- **Single server** or small VM
- Docker Compose: FastAPI + PostgreSQL + Redis + Ollama
- Nginx reverse proxy
- SSL via Let's Encrypt

### Scale-up Path

- Container orchestration (Kubernetes / ECS)
- Dedicated AI inference endpoints
- Event bus (Kafka / RabbitMQ) for analytics pipeline
- Separate microservices for Article, Vocabulary, and Learning

---

## 17. Open Questions

1. **Target audience CEFR level** — Should the app adapt difficulty based on the user's level (B1, B2, C1, C2)?
2. **Multi-language support** — Will the user's native language affect translation/explanation features?
3. **Offline-first** — Is offline vocabulary access a hard requirement for MVP?
4. **Social features** — Will users share vocabulary lists or articles?
5. **Monetization** — Free tier limits, premium features, or subscription model?
