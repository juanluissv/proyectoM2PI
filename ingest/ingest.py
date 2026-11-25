"""
Ingest pipeline: chunk → embed (OpenAI) → upsert (Pinecone).

Uso:
  python -m ingest.create_indexes
  python -m ingest.ingest --strategy header_based
"""

from __future__ import annotations

import argparse
import sys

from ingest.chunking import (
	STRATEGY_HEADER_BASED,
	chunk_corpus,
	pinecone_upsert_record,
	save_chunks_jsonl,
	save_chunks_markdown,
)
from ingest.embeddings import embed_texts
from ingest.pinecone_setup import (
	STRATEGY_FIXED_OVERLAP,
	connect_index,
	embedding_dimension,
	embedding_model,
	ensure_indexes,
	get_openai_client,
	get_pinecone_client,
	index_name_for_strategy,
)

UPSERT_BATCH_SIZE = 100


def _chunk_for_strategy(strategy: str):
	if strategy == STRATEGY_HEADER_BASED:
		return chunk_corpus(strategy=STRATEGY_HEADER_BASED)
	if strategy == STRATEGY_FIXED_OVERLAP:
		raise NotImplementedError(
			'fixed_overlap aún no está implementado en chunking.py'
		)
	raise ValueError(f'Estrategia desconocida: {strategy}')


def run_ingest(
	strategy: str,
	*,
	export_artifacts: bool = True,
	verify: bool = True,
	ensure_index: bool = True,
) -> int:
	if ensure_index:
		ensure_indexes()

	pc = get_pinecone_client()
	openai_client = get_openai_client()
	index = connect_index(pc, strategy)
	index_name = index_name_for_strategy(strategy)

	print(f'Estrategia: {strategy}')
	print(f'Pinecone index: {index_name}')
	print(f'Embedding: {embedding_model()} (dim={embedding_dimension()})')

	chunks = _chunk_for_strategy(strategy)
	if not chunks:
		print('No hay chunks para ingestar.', file=sys.stderr)
		return 1

	print(f'Chunks: {len(chunks)}')

	if export_artifacts:
		md_path = save_chunks_markdown(chunks)
		jsonl_path = save_chunks_jsonl(chunks)
		print(f'Exportado: {md_path}')
		print(f'Exportado: {jsonl_path}')

	textos = [chunk.content for chunk in chunks]
	print('Generando embeddings...')
	embeddings = embed_texts(openai_client, textos)

	dim_ok = all(len(v) == embedding_dimension() for v in embeddings)
	if not dim_ok:
		print(
			'Dimensión de embedding distinta a la del índice.',
			file=sys.stderr,
		)
		return 1

	vectors = [
		pinecone_upsert_record(chunk, vector)
		for chunk, vector in zip(chunks, embeddings)
	]

	print('Upsert a Pinecone...')
	total_upserted = 0
	for start in range(0, len(vectors), UPSERT_BATCH_SIZE):
		batch = vectors[start : start + UPSERT_BATCH_SIZE]
		response = index.upsert(vectors=batch)
		total_upserted += response.upserted_count

	print(f'Vectores upserted (reportados): {total_upserted}')

	if verify:
		sample_ids = [chunks[0].chunk_id, chunks[-1].chunk_id]
		fetched = index.fetch(ids=sample_ids)
		print(f'Verificación fetch: {len(fetched.vectors)}/{len(sample_ids)} ids')
		for chunk_id in sample_ids:
			if chunk_id not in fetched.vectors:
				print(f'  FALTA: {chunk_id}')
				continue
			meta = fetched.vectors[chunk_id].metadata
			titulo = meta.get('titulo', meta.get('seccion', chunk_id))
			print(f'  OK {chunk_id}: {titulo}')

		stats = index.describe_index_stats()
		print(f'Index stats: {stats}')

	return 0


def main() -> None:
	parser = argparse.ArgumentParser(description='Ingesta corpus → Pinecone')
	parser.add_argument(
		'--strategy',
		default=STRATEGY_HEADER_BASED,
		choices=[STRATEGY_HEADER_BASED, STRATEGY_FIXED_OVERLAP],
		help='Estrategia de chunking (fixed_overlap cuando esté implementada)',
	)
	parser.add_argument(
		'--no-export',
		action='store_true',
		help='No regenerar chunks.md / chunks.jsonl',
	)
	parser.add_argument(
		'--no-verify',
		action='store_true',
		help='Omitir fetch de verificación post-upsert',
	)
	parser.add_argument(
		'--skip-ensure-index',
		action='store_true',
		help='No intentar crear índices antes de ingestar',
	)
	args = parser.parse_args()

	try:
		code = run_ingest(
			args.strategy,
			export_artifacts=not args.no_export,
			verify=not args.no_verify,
			ensure_index=not args.skip_ensure_index,
		)
	except NotImplementedError as err:
		print(err, file=sys.stderr)
		code = 1
	except RuntimeError as err:
		print(err, file=sys.stderr)
		code = 1

	sys.exit(code)


if __name__ == '__main__':
	main()