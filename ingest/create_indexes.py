"""Create Pinecone serverless indexes for each chunking strategy (one-time setup)."""

from __future__ import annotations

import argparse

from ingest.pinecone_setup import (
	STRATEGY_FIXED_OVERLAP,
	STRATEGY_HEADER_BASED,
	embedding_dimension,
	embedding_model,
	ensure_indexes,
	get_pinecone_client,
)


def main() -> None:
	parser = argparse.ArgumentParser(
		description='Crea los índices Pinecone para header_based y fixed_overlap.',
	)
	parser.add_argument(
		'--dry-run',
		action='store_true',
		help='Solo muestra nombres y configuración, sin llamar a Pinecone.',
	)
	args = parser.parse_args()

	print(f'Embedding model: {embedding_model()}')
	print(f'Dimension: {embedding_dimension()}')

	if args.dry_run:
		from ingest.pinecone_setup import index_name_for_strategy

		for strategy in (STRATEGY_HEADER_BASED, STRATEGY_FIXED_OVERLAP):
			print(f'  {strategy} -> {index_name_for_strategy(strategy)}')
		return

	pc = get_pinecone_client()
	mapping = ensure_indexes(pc)
	print('Listo. Índices configurados:')
	for strategy, name in mapping.items():
		print(f'  {strategy}: {name}')


if __name__ == '__main__':
	main()