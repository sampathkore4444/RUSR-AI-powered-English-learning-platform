"""
Article service — ingestion (URL / text), parsing, and CRUD.

URL ingestion pipeline:
  URL → fetch HTML → readability extract → clean text → paragraphs → sentences → NLP tokens
"""

import re
from readability import Document
import httpx
from bs4 import BeautifulSoup

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import NotFoundError, BadRequestError
from models.article import Article, ArticleParagraph, ArticleSentence
from models.token import SentenceToken
from schemas.article import ArticleCreate, ArticleCreateFromURL
from services.nlp_service import process_sentence, split_sentences


# ── URL Ingestion ─────────────────────────────────────────


async def ingest_from_url(
    db: AsyncSession, user_id: str, payload: ArticleCreateFromURL
) -> Article:
    """Ingest an article by extracting content from a URL."""
    html = await _fetch_html(payload.url)
    extracted = _extract_article(html)

    article = Article(
        user_id=user_id,
        title=extracted["title"],
        source=_extract_domain(payload.url),
        url=payload.url,
        author=extracted.get("author"),
    )
    db.add(article)
    await db.flush()

    await _store_paragraphs(db, article.id, extracted["text"])
    await db.flush()
    return article


async def _fetch_html(url: str) -> str:
    """Fetch HTML content from a URL with timeout and user-agent."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        async with httpx.AsyncClient(
            timeout=15.0, follow_redirects=True, headers=headers
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPStatusError as e:
        raise BadRequestError(f"Failed to fetch URL: HTTP {e.response.status_code}")
    except httpx.RequestError as e:
        raise BadRequestError(f"Failed to fetch URL: {e}")


def _extract_article(html: str) -> dict:
    """Extract main article content using readability + BeautifulSoup."""
    try:
        doc = Document(html)
        title = doc.title()
        summary_html = doc.summary()
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string if soup.title else "Untitled Article"
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_=re.compile(r"article|content|post", re.I))
            or soup.body
        )
        summary_html = str(article) if article else ""

    soup = BeautifulSoup(summary_html, "html.parser")
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    author = _extract_author(soup)
    return {"title": title.strip(), "text": text.strip(), "author": author}


def _extract_author(soup: BeautifulSoup) -> str | None:
    """Try to extract author from common meta tags."""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name in ("author", "article:author"):
            content = meta.get("content", "").strip()
            if content:
                return content

    for cls in ["author", "byline", "writer", "journalist"]:
        el = soup.find(class_=re.compile(cls, re.I))
        if el:
            return el.get_text(strip=True)

    return None


def _extract_domain(url: str) -> str:
    """Extract domain name from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "")


# ── Text Ingestion ────────────────────────────────────────


async def ingest_from_text(
    db: AsyncSession, user_id: str, payload: ArticleCreate
) -> Article:
    """Ingest an article from pasted text."""
    article = Article(
        user_id=user_id,
        title=payload.title,
        source=payload.source,
        author=payload.author,
    )
    db.add(article)
    await db.flush()

    await _store_paragraphs(db, article.id, payload.text)
    await db.flush()
    return article


# ── Shared helpers ────────────────────────────────────────


async def _store_paragraphs(db: AsyncSession, article_id: str, text: str) -> None:
    """Split text into paragraphs → sentences (spaCy) → NLP tokens and store."""
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    for para_idx, para_text in enumerate(raw_paragraphs):
        paragraph = ArticleParagraph(
            article_id=article_id,
            sequence=para_idx,
            text=para_text,
        )
        db.add(paragraph)
        await db.flush()

        # Use spaCy sentencizer instead of regex
        sentences = await split_sentences(para_text)
        for sent_idx, sent_text in enumerate(sentences):
            sentence = ArticleSentence(
                paragraph_id=paragraph.id,
                sequence=sent_idx,
                text=sent_text,
            )
            db.add(sentence)
            await db.flush()

            tokens = await process_sentence(sent_text)
            for tok_idx, tok in enumerate(tokens):
                token = SentenceToken(
                    sentence_id=sentence.id,
                    position=tok_idx,
                    text=tok["text"],
                    lemma=tok["lemma"],
                    pos=tok["pos"],
                )
                db.add(token)


async def get_article(db: AsyncSession, article_id: str) -> Article:
    """Fetch a full article with paragraphs, sentences, and tokens."""
    result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise NotFoundError("Article", article_id)
    return article


async def list_articles(
    db: AsyncSession, user_id: str, offset: int = 0, limit: int = 20
) -> tuple[list[Article], int]:
    """List articles for a user with pagination."""
    count_result = await db.execute(
        select(func.count(Article.id)).where(Article.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Article)
        .where(Article.user_id == user_id)
        .order_by(Article.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    articles = list(result.scalars().all())
    return articles, total
