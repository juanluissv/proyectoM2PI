"""OpenAI batch embeddings for ingest."""

from __future__ import annotations

from openai import OpenAI

from ingest.pinecone_setup import embedding_model


def embed_texts(
	client: OpenAI,
	texts: list[str],
	*,
	batch_size: int = 100,
	model: str | None = None,
) -> list[list[float]]:
	"""Embed texts in batches; output order matches input order."""
	if not texts:
		return []

	modelo = model or embedding_model()
	vectors: list[list[float]] = []

	for start in range(0, len(texts), batch_size):
		lote = texts[start : start + batch_size]
		response = client.embeddings.create(model=modelo, input=lote)
		data = sorted(response.data, key=lambda item: item.index)
		vectors.extend(item.embedding for item in data)

	if len(vectors) != len(texts):
		raise RuntimeError(
			f'Conteo de embeddings ({len(vectors)}) != textos ({len(texts)})'
		)

	return vectors