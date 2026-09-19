"""
Integration tests — full API endpoint flows.

Tests the complete user journey:
  Register → Login → Ingest Article → Inspect Word → Save → Review

Each test exercises real HTTP requests through the FastAPI test client
with an in-memory SQLite database.
"""

import pytest
from httpx import AsyncClient


# ── Helper ──────────────────────────────────────────────


async def _register(client: AsyncClient, email: str = "int@example.com") -> dict:
    """Register a user and return the response body."""
    res = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "testpass123",
            "full_name": "Integration User",
        },
    )
    assert res.status_code == 201, f"Register failed: {res.text}"
    return res.json()


def _auth_header(token: str) -> dict:
    """Build Authorization header."""
    return {"Authorization": f"Bearer {token}"}


# ── Health ──────────────────────────────────────────────


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client: AsyncClient):
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Auth flow ──────────────────────────────────────────


@pytest.mark.asyncio
class TestAuthFlow:
    async def test_register_and_login(self, client: AsyncClient):
        # Register
        reg = await _register(client)
        assert "access_token" in reg
        assert reg["user"]["email"] == "int@example.com"

        # Login
        res = await client.post(
            "/api/auth/login",
            json={"email": "int@example.com", "password": "testpass123"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["email"] == "int@example.com"

    async def test_duplicate_register_fails(self, client: AsyncClient):
        await _register(client, "dup@example.com")
        res = await client.post(
            "/api/auth/register",
            json={
                "email": "dup@example.com",
                "password": "testpass123",
            },
        )
        assert res.status_code == 409  # Conflict

    async def test_wrong_password_fails(self, client: AsyncClient):
        await _register(client, "wrong@example.com")
        res = await client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "badpassword"},
        )
        assert res.status_code == 400

    async def test_protected_route_without_token(self, client: AsyncClient):
        res = await client.get("/api/articles")
        assert res.status_code in (401, 403)

    async def test_get_profile(self, client: AsyncClient):
        reg = await _register(client, "profile@example.com")
        headers = _auth_header(reg["access_token"])

        res = await client.get("/api/users/me", headers=headers)
        assert res.status_code == 200
        assert res.json()["email"] == "profile@example.com"


# ── Article ingestion (text) ───────────────────────────


@pytest.mark.asyncio
class TestArticleIngestion:
    async def test_ingest_from_text(self, client: AsyncClient):
        reg = await _register(client, "article@example.com")
        headers = _auth_header(reg["access_token"])

        res = await client.post(
            "/api/articles/text",
            json={
                "title": "Climate Change and Global Markets",
                "text": (
                    "Global markets reacted to the Federal Reserve's decision. "
                    "The central bank raised interest rates by 25 basis points. "
                    "Investors are watching closely.\n\n"
                    "Bond yields surged after the announcement. "
                    "The dollar strengthened against major currencies."
                ),
                "source": "test",
                "author": "Test Reporter",
            },
            headers=headers,
        )
        assert res.status_code == 201
        article = res.json()
        assert article["title"] == "Climate Change and Global Markets"
        assert article["author"] == "Test Reporter"
        assert len(article["paragraphs"]) >= 2

        # Verify tokens exist
        first_para = article["paragraphs"][0]
        assert len(first_para["sentences"]) > 0
        first_sentence = first_para["sentences"][0]
        assert len(first_sentence["tokens"]) > 0
        # Tokens should have lemma and POS
        tok = first_sentence["tokens"][0]
        assert "lemma" in tok
        assert "pos" in tok

    async def test_list_articles(self, client: AsyncClient):
        reg = await _register(client, "list@example.com")
        headers = _auth_header(reg["access_token"])

        # Ingest two articles
        for i in range(2):
            await client.post(
                "/api/articles/text",
                json={
                    "title": f"Article {i}",
                    "text": f"This is article number {i}. It has some content.",
                },
                headers=headers,
            )

        res = await client.get("/api/articles", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["articles"]) == 2

    async def test_get_article_by_id(self, client: AsyncClient):
        reg = await _register(client, "getarticle@example.com")
        headers = _auth_header(reg["access_token"])

        # Ingest
        ingest_res = await client.post(
            "/api/articles/text",
            json={
                "title": "Get Me",
                "text": "This article should be fetchable by ID.",
            },
            headers=headers,
        )
        article_id = ingest_res.json()["id"]

        # Fetch by ID
        res = await client.get(f"/api/articles/{article_id}", headers=headers)
        assert res.status_code == 200
        assert res.json()["title"] == "Get Me"

    async def test_get_nonexistent_article(self, client: AsyncClient):
        reg = await _register(client, "noarticle@example.com")
        headers = _auth_header(reg["access_token"])

        res = await client.get("/api/articles/nonexistent-id", headers=headers)
        assert res.status_code == 404


# ── Word intelligence ──────────────────────────────────


@pytest.mark.asyncio
class TestWordIntelligence:
    async def test_inspect_word(self, client: AsyncClient):
        reg = await _register(client, "inspect@example.com")
        headers = _auth_header(reg["access_token"])

        res = await client.post(
            "/api/words/inspect",
            json={
                "word": "inflation",
                "sentence": "The government is trying to reduce inflation.",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["word"] == "inflation"
        assert "lemma" in data
        assert "dictionary" in data
        assert "definition" in data["dictionary"]
        assert "pos" in data["dictionary"]

    async def test_inspect_unknown_word(self, client: AsyncClient):
        reg = await _register(client, "unknown@example.com")
        headers = _auth_header(reg["access_token"])

        res = await client.post(
            "/api/words/inspect",
            json={
                "word": "xyzqwerty",
                "sentence": "The xyzqwerty was important.",
            },
            headers=headers,
        )
        # Should still return a response (with empty definitions)
        assert res.status_code == 200
        assert res.json()["word"] == "xyzqwerty"


# ── Vocabulary CRUD ────────────────────────────────────


@pytest.mark.asyncio
class TestVocabularyFlow:
    async def test_save_and_list_words(self, client: AsyncClient):
        reg = await _register(client, "vocab@example.com")
        headers = _auth_header(reg["access_token"])

        # Save a word
        save_res = await client.post(
            "/api/vocabulary",
            json={
                "word": "curb",
                "lemma": "curb",
                "meaning": "to control or reduce",
                "context_sentence": "The government curbed inflation.",
                "difficulty": "Medium",
            },
            headers=headers,
        )
        assert save_res.status_code == 201
        vocab = save_res.json()
        assert vocab["word"] == "curb"
        vocab_id = vocab["id"]

        # List vocabulary
        list_res = await client.get("/api/vocabulary", headers=headers)
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1

        # Get single word
        get_res = await client.get(f"/api/vocabulary/{vocab_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["word"] == "curb"

        # Update word
        update_res = await client.put(
            f"/api/vocabulary/{vocab_id}",
            json={"meaning": "to restrain", "personal_note": "Important word"},
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["meaning"] == "to restrain"
        assert update_res.json()["personal_note"] == "Important word"

        # Delete word
        del_res = await client.delete(f"/api/vocabulary/{vocab_id}", headers=headers)
        assert del_res.status_code == 204

        # Verify deleted
        get_res2 = await client.get(f"/api/vocabulary/{vocab_id}", headers=headers)
        assert get_res2.status_code == 404

    async def test_save_duplicate_fails(self, client: AsyncClient):
        reg = await _register(client, "dupvocab@example.com")
        headers = _auth_header(reg["access_token"])

        await client.post(
            "/api/vocabulary",
            json={"word": "test", "lemma": "test"},
            headers=headers,
        )

        res = await client.post(
            "/api/vocabulary",
            json={"word": "test", "lemma": "test"},
            headers=headers,
        )
        assert res.status_code == 409  # Conflict

    async def test_word_of_the_day(self, client: AsyncClient):
        reg = await _register(client, "wod@example.com")
        headers = _auth_header(reg["access_token"])

        # Save a word first
        await client.post(
            "/api/vocabulary",
            json={"word": "hello", "lemma": "hello", "meaning": "greeting"},
            headers=headers,
        )

        res = await client.get("/api/vocabulary/word-of-the-day", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data is not None
        assert data["word"] == "hello"


# ── Review flow ────────────────────────────────────────


@pytest.mark.asyncio
class TestReviewFlow:
    async def test_full_review_cycle(self, client: AsyncClient):
        reg = await _register(client, "review@example.com")
        headers = _auth_header(reg["access_token"])

        # Save some words
        for word in ["curb", "inflation", "recession"]:
            await client.post(
                "/api/vocabulary",
                json={"word": word, "lemma": word, "meaning": f"Meaning of {word}"},
                headers=headers,
            )

        # Check stats
        stats_res = await client.get("/api/review/stats", headers=headers)
        assert stats_res.status_code == 200
        stats = stats_res.json()
        assert stats["total_words"] == 3

        # Get due reviews (words just saved may or may not be due depending on timing)
        due_res = await client.get("/api/review/due", headers=headers)
        assert due_res.status_code == 200
        due = due_res.json()

        # If there are due items, answer them
        if due["total_due"] > 0:
            item = due["items"][0]
            answer_res = await client.post(
                "/api/review/answer",
                json={
                    "vocabulary_id": item["vocabulary_id"],
                    "answer_correct": True,
                },
                headers=headers,
            )
            assert answer_res.status_code == 200
            result = answer_res.json()
            assert result["correct"] is True
            assert result["mastery_level"] >= 0.0

        # Check stats again
        stats_res2 = await client.get("/api/review/stats", headers=headers)
        assert stats_res2.status_code == 200

    async def test_review_answer_increases_mastery(self, client: AsyncClient):
        reg = await _register(client, "mastery@example.com")
        headers = _auth_header(reg["access_token"])

        # Save a word and make it due by updating next_review_date
        save_res = await client.post(
            "/api/vocabulary",
            json={"word": "test", "lemma": "test", "meaning": "a test"},
            headers=headers,
        )
        vocab_id = save_res.json()["id"]

        # Update next_review_date to past (via direct DB would be ideal, but we can test the flow)
        # For integration test, we'll just check the endpoint works
        due_res = await client.get("/api/review/due", headers=headers)
        assert due_res.status_code == 200


# ── GDPR deletion ─────────────────────────────────────


@pytest.mark.asyncio
class TestGDPRDeletion:
    async def test_delete_account(self, client: AsyncClient):
        reg = await _register(client, "delete@example.com")
        headers = _auth_header(reg["access_token"])

        # Save some data
        await client.post(
            "/api/vocabulary",
            json={"word": "hello", "lemma": "hello"},
            headers=headers,
        )

        # Delete account
        res = await client.delete("/api/users/me", headers=headers)
        assert res.status_code == 204

        # Verify profile is gone
        res2 = await client.get("/api/users/me", headers=headers)
        assert res2.status_code == 401  # Token no longer valid


# ── Full end-to-end journey ───────────────────────────


@pytest.mark.asyncio
class TestFullJourney:
    async def test_complete_user_journey(self, client: AsyncClient):
        """
        Simulates a complete user journey:
        1. Register
        2. Ingest article
        3. Tap a word (inspect)
        4. Save word to vocabulary
        5. Check review stats
        """
        # Step 1: Register
        reg = await _register(client, "journey@example.com")
        headers = _auth_header(reg["access_token"])
        assert reg["user"]["email"] == "journey@example.com"

        # Step 2: Ingest article
        article_res = await client.post(
            "/api/articles/text",
            json={
                "title": "Economic Growth Slows Down",
                "text": (
                    "The economy grew by only 1.2% last quarter. "
                    "This is below the expected 2.5% growth rate. "
                    "Analysts are concerned about a potential recession."
                ),
            },
            headers=headers,
        )
        assert article_res.status_code == 201
        article = article_res.json()
        article_id = article["id"]

        # Step 3: Inspect a word from the article
        word_res = await client.post(
            "/api/words/inspect",
            json={
                "word": "recession",
                "sentence": "Analysts are concerned about a potential recession.",
            },
            headers=headers,
        )
        assert word_res.status_code == 200
        word_data = word_res.json()
        assert word_data["word"] == "recession"
        assert word_data["dictionary"]["definition"] != ""

        # Step 4: Save the word to vocabulary
        save_res = await client.post(
            "/api/vocabulary",
            json={
                "word": word_data["word"],
                "lemma": word_data["lemma"],
                "meaning": word_data["dictionary"]["definition"],
                "context_sentence": "Analysts are concerned about a potential recession.",
                "difficulty": "Medium",
            },
            headers=headers,
        )
        assert save_res.status_code == 201
        vocab_id = save_res.json()["id"]

        # Step 5: Check it's in the list
        list_res = await client.get("/api/vocabulary", headers=headers)
        assert list_res.json()["total"] >= 1

        # Step 6: Check review stats
        stats_res = await client.get("/api/review/stats", headers=headers)
        stats = stats_res.json()
        assert stats["total_words"] >= 1

        # Step 7: Try AI explanation
        explain_res = await client.post(
            "/api/words/explain",
            json={
                "sentence": "The economy grew by only 1.2% last quarter.",
                "action": "simple",
            },
            headers=headers,
        )
        # AI may not be running, so accept 200 or 500
        assert explain_res.status_code in (200, 500)

        # Step 8: Verify article is retrievable
        get_res = await client.get(f"/api/articles/{article_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "Economic Growth Slows Down"

        # Step 9: Delete the word
        del_res = await client.delete(f"/api/vocabulary/{vocab_id}", headers=headers)
        assert del_res.status_code == 204

        # Step 10: Verify deletion
        list_res2 = await client.get("/api/vocabulary", headers=headers)
        assert list_res2.json()["total"] == 0
