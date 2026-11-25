"""Pinecone + embedding settings shared by create_indexes and ingest."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from ingest.chunking import STRATEGY_HEADER_BASED

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STRATEGY_FIXED_OVERLAP = 'fixed_overlap'

STRATEGY_INDEX_ENV = {
	STRATEGY_HEADER_BASED: 'PINECONE_INDEX_HEADER_BASED',
	STRATEGY_FIXED_OVERLAP: 'PINECONE_INDEX_FIXED_OVERLAP',
}

DEFAULT_INDEX_NAMES = {
	STRATEGY_HEADER_BASED: 'nubbix-header-based',
	STRATEGY_FIXED_OVERLAP: 'nubbix-fixed-overlap',
}

EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_DIMENSION = 1536
PINECONE_CLOUD = 'aws'
PINECONE_REGION = 'us-east-1'


def load_project_env() -> None:
	load_dotenv(PROJECT_ROOT / '.env')


def index_name_for_strategy(strategy: str) -> str:
	env_key = STRATEGY_INDEX_ENV.get(strategy)
	if not env_key:
		raise ValueError(f'Estrategia desconocida: {strategy}')
	default = DEFAULT_INDEX_NAMES[strategy]
	return os.getenv(env_key, default)


def embedding_model() -> str:
	return os.getenv('EMBEDDING_MODEL', EMBEDDING_MODEL)


def embedding_dimension() -> int:
	return int(os.getenv('EMBEDDING_DIMENSION', str(EMBEDDING_DIMENSION)))


def pinecone_cloud() -> str:
	return os.getenv('PINECONE_CLOUD', PINECONE_CLOUD)


def pinecone_region() -> str:
	return os.getenv('PINECONE_REGION', PINECONE_REGION)


def get_pinecone_client() -> Pinecone:
	load_project_env()
	api_key = os.getenv('PINECONE_API_KEY')
	if not api_key:
		raise RuntimeError('Falta PINECONE_API_KEY en .env')
	return Pinecone(api_key=api_key)


def get_openai_client() -> OpenAI:
	load_project_env()
	api_key = os.getenv('OPENAI_API_KEY')
	if not api_key:
		raise RuntimeError('Falta OPENAI_API_KEY en .env')
	return OpenAI(api_key=api_key)


def list_existing_index_names(pc: Pinecone) -> set[str]:
	return {item.name for item in pc.list_indexes()}


def create_serverless_index(pc: Pinecone, name: str, *, dimension: int) -> None:
	pc.create_index(
		name=name,
		dimension=dimension,
		metric='cosine',
		spec=ServerlessSpec(cloud=pinecone_cloud(), region=pinecone_region()),
	)


def ensure_indexes(pc: Pinecone | None = None) -> dict[str, str]:
	"""Create both strategy indexes if they do not exist. Returns strategy → index name."""
	client = pc or get_pinecone_client()
	existing = list_existing_index_names(client)
	dim = embedding_dimension()
	result: dict[str, str] = {}

	for strategy in (STRATEGY_HEADER_BASED, STRATEGY_FIXED_OVERLAP):
		name = index_name_for_strategy(strategy)
		result[strategy] = name
		if name in existing:
			print(f'Index ya existe: {name} ({strategy})')
			continue
		print(f'Creando index: {name} ({strategy}), dim={dim}...')
		create_serverless_index(client, name, dimension=dim)
		print(f'  creado: {name}')

	return result


def connect_index(pc: Pinecone, strategy: str):
	name = index_name_for_strategy(strategy)
	return pc.Index(name)