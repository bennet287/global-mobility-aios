from __future__ import annotations

import pytest

from app.core.config import settings
from app.services.docling_adapter import (
    STATUS_DISABLED,
    STATUS_ERROR,
    STATUS_SUCCESS,
    STATUS_UNAVAILABLE,
    DoclingResult,
    normalize_document_bytes,
)


class TestDoclingDisabled:
    def test_normalize_returns_disabled_when_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "docling_enabled", False)
        result = normalize_document_bytes(b"any content")
        assert result.status == STATUS_DISABLED


class TestDoclingMissingPackage:
    def test_normalize_returns_unavailable_when_docling_not_installed(self, monkeypatch):
        monkeypatch.setattr(settings, "docling_enabled", True)
        monkeypatch.setattr("app.services.docling_adapter.DocumentConverter", None)
        result = normalize_document_bytes(b"any content")
        assert result.status == STATUS_UNAVAILABLE
        assert "not installed" in result.error.lower()
        assert any("falling back" in w.lower() for w in result.warnings)


class TestDoclingEnabledConversions:
    def test_normalize_returns_success(self, monkeypatch):
        monkeypatch.setattr(settings, "docling_enabled", True)

        class FakeDocument:
            name = "fake-document"

            def export_to_markdown(self) -> str:
                return "# Extracted heading\n\nExtracted paragraph."

        class FakeInput:
            page_count = 2

        class FakeConversionResult:
            document = FakeDocument()
            input = FakeInput()

        class FakeConverter:
            def convert(self, _path: str) -> FakeConversionResult:
                return FakeConversionResult()

        monkeypatch.setattr(
            "app.services.docling_adapter.DocumentConverter",
            FakeConverter,
        )

        result = normalize_document_bytes(b"ignored bytes", mime_type="application/pdf", filename="sample.pdf")
        assert result.status == STATUS_SUCCESS
        assert "Extracted heading" in result.normalized_text
        assert result.page_count == 2
        assert result.title == "fake-document"

    def test_normalize_returns_error_on_conversion_failure(self, monkeypatch):
        monkeypatch.setattr(settings, "docling_enabled", True)

        class BrokenConverter:
            def convert(self, _path: str) -> None:
                raise RuntimeError("simulated conversion failure")

        monkeypatch.setattr(
            "app.services.docling_adapter.DocumentConverter",
            BrokenConverter,
        )

        result = normalize_document_bytes(b"any content", filename="sample.pdf")
        assert result.status == STATUS_ERROR
        assert "simulated conversion failure" in result.error


class TestDoclingResult:
    def test_to_dict_truncates_long_text(self):
        long_text = "x" * 1000
        result = DoclingResult(status=STATUS_SUCCESS, normalized_text=long_text)
        dumped = result.to_dict()
        assert dumped["status"] == STATUS_SUCCESS
        assert len(dumped["normalized_text"]) <= 500

    def test_to_dict_empty_text(self):
        result = DoclingResult(status=STATUS_DISABLED)
        dumped = result.to_dict()
        assert dumped["normalized_text"] == ""
        assert dumped["warnings"] == []
