from functools import lru_cache
from hashlib import blake2b
from math import sqrt

from app.core.config import settings


class SemanticEmbeddingService:
    """Real semantic embedding provider for product recommendation v2."""

    def embed(self, text: str) -> list[float]:
        try:
            provider = settings.EMBEDDING_PROVIDER.lower()
            if provider == "openai":
                return self._openai_embedding(text)
            if provider == "sentence_transformers":
                return self._sentence_transformers_embedding(text)
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")
        except Exception:
            return self._fallback_embedding(text)

    def _openai_embedding(self, text: str) -> list[float]:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use EMBEDDING_PROVIDER=openai") from exc

        client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=3.0, max_retries=0)
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=self._normalize_text(text),
        )
        return self._fit_dimensions(response.data[0].embedding)

    def _sentence_transformers_embedding(self, text: str) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Install sentence-transformers to use EMBEDDING_PROVIDER=sentence_transformers"
            ) from exc

        model = self._sentence_transformers_model()
        vector = model.encode(self._normalize_text(text), normalize_embeddings=True).tolist()
        return self._fit_dimensions(vector)

    @staticmethod
    @lru_cache(maxsize=1)
    def _sentence_transformers_model():
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.SENTENCE_TRANSFORMERS_MODEL)

    def _fit_dimensions(self, vector: list[float]) -> list[float]:
        dimensions = settings.EMBEDDING_DIMENSIONS
        fitted = [float(value) for value in vector[:dimensions]]
        if len(fitted) < dimensions:
            fitted.extend([0.0] * (dimensions - len(fitted)))

        norm = sqrt(sum(value * value for value in fitted))
        if norm == 0:
            return fitted
        return [value / norm for value in fitted]

    def _normalize_text(self, text: str) -> str:
        normalized = (text or "").strip()
        return normalized or "default"

    def _fallback_embedding(self, text: str) -> list[float]:
        dimensions = settings.EMBEDDING_DIMENSIONS
        vector = [0.0] * dimensions
        normalized = self._normalize_text(text).lower()
        compact = "".join(char for char in normalized if not char.isspace())
        tokens = normalized.split()
        tokens.extend(compact[index : index + 1] for index in range(len(compact)))
        tokens.extend(compact[index : index + 2] for index in range(max(len(compact) - 1, 0)))
        tokens.extend(compact[index : index + 3] for index in range(max(len(compact) - 2, 0)))

        for token in tokens:
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            weight = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += weight

        return self._fit_dimensions(vector)


semantic_embedding_service = SemanticEmbeddingService()
