"""
Vector search over Pinecone + respuesta con LLM (header_based index).

Usage:
  python -m src.query --question "¿Cuántos días de vacaciones tengo?"
  python -m src.query -q "..." --top-k 5 --retrieval-only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from ingest.chunking import STRATEGY_HEADER_BASED
from ingest.embeddings import embed_texts
from ingest.pinecone_setup import (
	connect_index,
	embedding_model,
	get_openai_client,
	get_pinecone_client,
	index_name_for_strategy,
)

DEFAULT_TOP_K = 3
DEFAULT_CHAT_MODEL = 'gpt-4o-mini'


def _chat_model() -> str:
	return os.getenv('OPENAI_MODEL', DEFAULT_CHAT_MODEL)


def retrieve_vector(
	question: str,
	*,
	top_k: int = DEFAULT_TOP_K,
	strategy: str = STRATEGY_HEADER_BASED,
) -> list[Any]:
	"""Embed the question and query Pinecone; returns match objects."""
	openai_client = get_openai_client()
	pc = get_pinecone_client()
	index = connect_index(pc, strategy)

	query_vector = embed_texts(openai_client, [question])[0]
	response = index.query(
		vector=query_vector,
		top_k=top_k,
		include_metadata=True,
	)
	return list(response.matches)


def match_to_chunk_related(match: Any) -> dict[str, Any]:
	meta = match.metadata or {}
	content = meta.get('texto') or meta.get('content') or ''
	return {
		'chunk_id': match.id,
		'source': meta.get('source', ''),
		'content': content,
		'score': float(match.score) if match.score is not None else 0.0,
	}


def format_context_chunks(matches: list[Any]) -> list[str]:
	"""Build context strings for the LLM (id + path + body)."""
	blocks: list[str] = []
	for match in matches:
		meta = match.metadata or {}
		texto = meta.get('texto') or ''
		path = meta.get('header_path', '')
		header = f"[{match.id}] {path}".strip()
		blocks.append(f'{header}\n{texto}'.strip())
	return blocks


def prompt_with_context_builder(question: str, docs: list[str]) -> str:
	delim = '\n\n---\n\n'
	rules = (
		'Sos Nubbix Assist. Respondé usando SOLO los fragmentos en Context.\n'
		'- Citá los chunk_id entre corchetes cuando uses un fragmento '
		'(ej. [hr_policies.md_0]).\n'
		'- Si la respuesta no está en Context, decilo claramente.\n'
	)
	prompt_start = f'{rules}\n\nContext (fragmentos oficiales):\n'
	prompt_end = f'\n\nPregunta del empleado: {question}\nRespuesta:'
	return prompt_start + delim.join(docs) + prompt_end


def generate_answer(question: str, matches: list[Any]) -> str:
	"""LLM answer grounded on retrieved chunks (optional step)."""
	if not matches:
		return (
			'No encontré fragmentos relevantes en la documentación '
			'para esta pregunta.'
		)

	client = get_openai_client()
	docs = format_context_chunks(matches)
	prompt = prompt_with_context_builder(question, docs)
	system = (
		'Asistente de conocimiento interno de Nubbix. '
		'Solo usá información del mensaje del usuario (Context). '
		'Cité chunk_id entre corchetes.'
	)
	res = client.chat.completions.create(
		model=_chat_model(),
		messages=[
			{'role': 'system', 'content': system},
			{'role': 'user', 'content': prompt},
		],
		temperature=0,
	)
	return (res.choices[0].message.content or '').strip()


def build_response(
	question: str,
	matches: list[Any],
	system_answer: str,
) -> dict[str, Any]:
	chunks_related = [match_to_chunk_related(m) for m in matches]
	return {
		'user_question': question,
		'system_answer': system_answer,
		'chunks_related': chunks_related,
	}


def run_query(
	question: str,
	*,
	top_k: int = DEFAULT_TOP_K,
	strategy: str = STRATEGY_HEADER_BASED,
	retrieval_only: bool = False,
) -> dict[str, Any]:
	matches = retrieve_vector(question, top_k=top_k, strategy=strategy)
	if retrieval_only:
		return {
			'user_question': question,
			'system_answer': '',
			'chunks_related': [match_to_chunk_related(m) for m in matches],
		}
	answer = generate_answer(question, matches)
	return build_response(question, matches, answer)


def main() -> None:
	parser = argparse.ArgumentParser(
		description='Consulta Nubbix Assist (búsqueda vectorial en Pinecone)',
	)
	parser.add_argument(
		'-q',
		'--question',
		required=True,
		help='Pregunta del empleado',
	)
	parser.add_argument(
		'--top-k',
		type=int,
		default=DEFAULT_TOP_K,
		help=f'Cantidad de chunks a recuperar (default {DEFAULT_TOP_K})',
	)
	parser.add_argument(
		'--strategy',
		default=STRATEGY_HEADER_BASED,
		choices=[STRATEGY_HEADER_BASED],
		help='Índice Pinecone según estrategia de chunking',
	)
	parser.add_argument(
		'--retrieval-only',
		action='store_true',
		help='Solo recuperar chunks (sin llamar al LLM)',
	)
	parser.add_argument(
		'--pretty',
		action='store_true',
		help='JSON indentado en stdout',
	)
	args = parser.parse_args()

	try:
		result = run_query(
			args.question,
			top_k=args.top_k,
			strategy=args.strategy,
			retrieval_only=args.retrieval_only,
		)
	except RuntimeError as err:
		print(err, file=sys.stderr)
		sys.exit(1)

	index_name = index_name_for_strategy(args.strategy)
	print(
		f'# index={index_name} | embedding={embedding_model()} | top_k={args.top_k}',
		file=sys.stderr,
	)

	indent = 2 if args.pretty else None
	print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == '__main__':
	main()