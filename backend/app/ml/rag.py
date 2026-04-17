"""
RAG Enrichment for Transaction Categorization.

Provides local retrieval from the merchant dictionary and optional
web-based retrieval for improved classification accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional
import logging

import httpx

from app.config import settings
from app.ml.categories import CATEGORY_HIERARCHY
from app.ml.merchant_dict import MerchantDictionary, MerchantEntry

logger = logging.getLogger(__name__)


@dataclass
class RagCandidate:
    category: str
    subcategory: str
    confidence: float
    source: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "evidence": self.evidence,
        }


class LocalMerchantRetriever:
    def __init__(self, merchant_dict: Optional[MerchantDictionary] = None):
        self.merchant_dict = merchant_dict or MerchantDictionary()
        self.available = True
        self.vectorizer = None
        self.matrix = None
        self.entries: List[MerchantEntry] = []
        self._build_index()

    def _build_index(self) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except Exception as exc:
            logger.warning(f"TF-IDF not available for RAG: {exc}")
            self.available = False
            return

        self.entries = list(self.merchant_dict.merchants.values())
        documents = []
        for entry in self.entries:
            tokens = [entry.name] + entry.keywords + entry.aliases + [entry.category, entry.subcategory]
            documents.append(" ".join(tokens).lower())

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.matrix = self.vectorizer.fit_transform(documents)

    def retrieve(self, query: str, top_k: int = 5) -> List[tuple[MerchantEntry, float]]:
        if not self.available or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query.lower()])
        scores = (self.matrix @ query_vec.T).toarray().ravel()
        if scores.size == 0:
            return []

        top_indices = scores.argsort()[-top_k:][::-1]
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            results.append((self.entries[idx], score))
        return results


class WebSearchRetriever:
    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        self.endpoint = endpoint
        self.api_key = api_key

    def retrieve(self, query: str, top_k: int = 3) -> List[dict[str, Any]]:
        if not self.endpoint:
            return []

        params = {"q": query, "limit": top_k}
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            with httpx.Client(timeout=settings.rag_web_timeout_seconds) as client:
                response = client.get(self.endpoint, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning(f"Web RAG request failed: {exc}")
            return []
        except ValueError as exc:
            logger.warning(f"Web RAG response invalid JSON: {exc}")
            return []

        results = payload.get("results") or payload.get("data") or []
        parsed = []
        for item in results[:top_k]:
            parsed.append(
                {
                    "title": item.get("title") or item.get("name"),
                    "snippet": item.get("snippet") or item.get("description") or "",
                    "url": item.get("url") or item.get("link"),
                }
            )
        return parsed


class RagEnricher:
    def __init__(self):
        self.local_retriever = LocalMerchantRetriever()
        self.web_retriever = None

        if settings.rag_web_enabled and settings.rag_web_endpoint:
            self.web_retriever = WebSearchRetriever(
                endpoint=settings.rag_web_endpoint,
                api_key=settings.rag_web_api_key,
            )

    def suggest(self, description: str, merchant_name: Optional[str] = None) -> List[RagCandidate]:
        query = " ".join([merchant_name or "", description]).strip()
        if not query:
            return []

        candidates: List[RagCandidate] = []

        for entry, score in self.local_retriever.retrieve(query, top_k=settings.rag_top_k):
            if score < settings.rag_min_score:
                continue
            confidence = min(1.0, score * 1.15)
            candidates.append(
                RagCandidate(
                    category=entry.category,
                    subcategory=entry.subcategory,
                    confidence=confidence,
                    source="local",
                    evidence={
                        "merchant": entry.name,
                        "keywords": entry.keywords[:5],
                    },
                )
            )

        if self.web_retriever:
            for result in self.web_retriever.retrieve(query, top_k=settings.rag_top_k):
                category, subcategory, confidence = self._infer_from_text(
                    f"{result.get('title', '')} {result.get('snippet', '')}"
                )
                if category:
                    candidates.append(
                        RagCandidate(
                            category=category,
                            subcategory=subcategory,
                            confidence=confidence,
                            source="web",
                            evidence=result,
                        )
                    )

        return candidates

    def _infer_from_text(self, text: str) -> tuple[Optional[str], Optional[str], float]:
        text_lower = text.lower()
        best_category = None
        best_subcategory = None
        best_score = 0

        for category, definition in CATEGORY_HIERARCHY.items():
            for subcategory in definition.subcategories:
                if subcategory.lower() in text_lower:
                    return category, subcategory, 0.8

            score = 0
            for keyword in definition.keywords:
                if keyword.lower() in text_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_category = category
                best_subcategory = definition.subcategories[0] if definition.subcategories else category

        if best_category and best_score > 0:
            confidence = min(0.85, 0.6 + best_score * 0.05)
            return best_category, best_subcategory, confidence

        return None, None, 0.0
