"""Header-based chunking for the Nubbix corpus (strategy: header_based)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

STRATEGY_HEADER_BASED = 'header_based'

# Reserved for a future fixed-size strategy (not used by header_based).
DEFAULT_MAX_TOKENS = 115
CHARS_PER_TOKEN = 4

INGEST_DIR = Path(__file__).resolve().parent
CORPUS_DIR = INGEST_DIR.parent / 'data' / 'corpus'
CHUNKS_EXPORT_PATH = INGEST_DIR / 'chunks.md'
CHUNKS_JSONL_PATH = INGEST_DIR / 'chunks.jsonl'
CORPUS_FILES = (
	'hr_policies.md',
	'it_manual.md',
	'finance_processes.md',
)


@dataclass(frozen=True)
class Section:
	title: str
	header_path: str
	body: str


@dataclass(frozen=True)
class Chunk:
	chunk_id: str
	source: str
	doc: str
	titulo_doc: str
	section: str
	header_path: str
	content: str
	strategy: str
	part_index: int
	part_total: int

	def metadatos(self) -> dict[str, str]:
		"""Document/chunk metadata (not embedded; stored with the vector)."""
		parte = f'{self.part_index + 1}/{self.part_total}'
		return {
			'doc': self.doc,
			'titulo_doc': self.titulo_doc,
			'estrategia': self.strategy,
			'seccion': self.section,
			'titulo': self.section,
			'parte': parte,
			'source': self.source,
			'header_path': self.header_path,
		}

	def record(self) -> dict[str, Any]:
		"""Full chunk record: id + embeddable text + metadatos (for JSONL / debugging)."""
		return {
			'id': self.chunk_id,
			'texto': self.content,
			'metadatos': self.metadatos(),
		}

	def pinecone_metadata(self) -> dict[str, str]:
		"""Flat metadata dict for Pinecone upsert (strings only)."""
		meta = self.metadatos()
		# Text used at query time for citations / UI (embedded field is `texto`).
		meta['texto'] = self.content
		return meta


def contar_tokens(texto: str) -> int:
	"""Approximate token count (no extra deps; embedding step uses the API)."""
	texto = texto.strip()
	if not texto:
		return 0
	por_caracteres = len(texto) // CHARS_PER_TOKEN
	por_palabras = int(len(texto.split()) * 1.3)
	return max(por_caracteres, por_palabras)


def _desagregar_bloque(bloque: str) -> list[str]:
	"""Separate prose from a bullet/numbered list when there is no blank line."""
	partes = re.split(r'\n(?=-\s|\d+\.\s)', bloque, maxsplit=1)
	if len(partes) == 2 and partes[0].strip() and partes[1].strip():
		return [partes[0].strip(), partes[1].strip()]
	return [bloque.strip()]


def bloques_markdown(texto: str) -> list[str]:
	"""Paragraphs, lists, and numbered steps as atomic blocks (author units)."""
	bloques_gruesos = [b.strip() for b in re.split(r'\n\s*\n', texto) if b.strip()]
	bloques: list[str] = []
	for bloque in bloques_gruesos:
		bloques.extend(_desagregar_bloque(bloque))
	return bloques


def partir_por_bloques(texto: str, max_tokens: int) -> list[str]:
	"""Group whole blocks (paragraph, list, table) without exceeding max_tokens."""
	bloques = bloques_markdown(texto)
	partes: list[str] = []
	actual: list[str] = []

	for bloque in bloques:
		candidato = '\n\n'.join(actual + [bloque])
		if actual and contar_tokens(candidato) > max_tokens:
			partes.append('\n\n'.join(actual))
			actual = [bloque]
		else:
			actual.append(bloque)

	if actual:
		partes.append('\n\n'.join(actual))

	return partes


def _extraer_titulo_documento(lineas: list[str]) -> str:
	for linea in lineas:
		if linea.startswith('# '):
			return linea[2:].strip()
	return 'Documento sin título'


def secciones_por_encabezados(texto: str, titulo_doc: str) -> list[Section]:
	"""Split on ## headings; each section keeps title, header path, and body."""
	patron = re.compile(r'^## (.+)$', re.MULTILINE)
	partes = patron.split(texto)
	# split returns: [preamble, title1, body1, title2, body2, ...]
	if len(partes) < 3:
		return []

	secciones: list[Section] = []
	for i in range(1, len(partes), 2):
		titulo = partes[i].strip()
		cuerpo = partes[i + 1].strip() if i + 1 < len(partes) else ''
		if not cuerpo:
			continue
		ruta = f'{titulo_doc} > {titulo}'
		secciones.append(Section(title=titulo, header_path=ruta, body=cuerpo))

	return secciones


def chunk_por_seccion(
	doc_path: Path,
	con_ruta: bool = True,
	strategy: str = STRATEGY_HEADER_BASED,
) -> list[Chunk]:
	"""One chunk per ## section with the full section body (no sub-splitting)."""
	texto = doc_path.read_text(encoding='utf-8')
	lineas = texto.splitlines()
	titulo_doc = _extraer_titulo_documento(lineas)
	source = doc_path.name

	chunks: list[Chunk] = []
	idx = 0

	secciones = secciones_por_encabezados(texto, titulo_doc)
	doc_id = doc_path.stem

	for seccion in secciones:
		encabezado = seccion.header_path if con_ruta else seccion.title
		contenido = f'{encabezado}\n\n{seccion.body}'
		chunk_id = f'{source}_{idx}'
		chunks.append(
			Chunk(
				chunk_id=chunk_id,
				source=source,
				doc=doc_id,
				titulo_doc=titulo_doc,
				section=seccion.title,
				header_path=seccion.header_path,
				content=contenido,
				strategy=strategy,
				part_index=0,
				part_total=1,
			)
		)
		idx += 1

	return chunks


def load_corpus(corpus_dir: Path | None = None) -> list[Path]:
	base = corpus_dir or CORPUS_DIR
	paths = [base / nombre for nombre in CORPUS_FILES]
	faltantes = [p for p in paths if not p.is_file()]
	if faltantes:
		raise FileNotFoundError(
			'Faltan archivos del corpus: ' + ', '.join(p.name for p in faltantes)
		)
	return paths


def chunk_corpus(
	corpus_dir: Path | None = None,
	strategy: Literal['header_based'] = STRATEGY_HEADER_BASED,
) -> list[Chunk]:
	"""Chunk all corpus files with the header-based strategy."""
	if strategy != STRATEGY_HEADER_BASED:
		raise ValueError(f'Estrategia no implementada aún: {strategy}')

	todos: list[Chunk] = []
	for ruta in load_corpus(corpus_dir):
		todos.extend(chunk_por_seccion(ruta, strategy=strategy))
	return todos


def _resumen_por_archivo(chunks: list[Chunk]) -> dict[str, int]:
	por_archivo: dict[str, int] = {}
	for chunk in chunks:
		por_archivo[chunk.source] = por_archivo.get(chunk.source, 0) + 1
	return por_archivo


def format_chunk_markdown(chunk: Chunk) -> str:
	"""Full chunk entry for human review (e.g. chunks.md)."""
	meta_json = json.dumps(chunk.metadatos(), ensure_ascii=False, indent=2)
	return (
		f'### `{chunk.chunk_id}`\n\n'
		f'- **id:** `{chunk.chunk_id}`\n'
		f'- **source:** `{chunk.source}`\n'
		f'- **header_path:** {chunk.header_path}\n\n'
		f'**metadatos:**\n\n'
		f'```json\n{meta_json}\n```\n\n'
		f'**texto** (lo que se embeddea):\n\n'
		f'```markdown\n{chunk.content}\n```\n'
	)


def save_chunks_jsonl(
	chunks: list[Chunk],
	path: Path | None = None,
) -> Path:
	"""Persist id, texto and metadatos (one JSON object per line)."""
	destino = path or CHUNKS_JSONL_PATH
	lineas = [json.dumps(chunk.record(), ensure_ascii=False) for chunk in chunks]
	destino.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
	return destino


def pinecone_upsert_record(
	chunk: Chunk,
	embedding: list[float],
) -> dict[str, Any]:
	"""Single vector payload for Pinecone (same shape as ingest1.py)."""
	return {
		'id': chunk.chunk_id,
		'values': embedding,
		'metadata': chunk.pinecone_metadata(),
	}


def save_chunks_markdown(
	chunks: list[Chunk],
	path: Path | None = None,
) -> Path:
	"""Write all chunks to a markdown file for visual inspection."""
	destino = path or CHUNKS_EXPORT_PATH
	por_archivo = _resumen_por_archivo(chunks)
	generado = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

	lineas = [
		'# Chunks export — header_based\n',
		f'- **Generado:** {generado}\n',
		f'- **Estrategia:** `{STRATEGY_HEADER_BASED}`\n',
		'- **Regla:** un chunk por cada sección `##` (cuerpo completo)\n',
		f'- **Total chunks:** {len(chunks)}\n',
		'- **Por archivo:** '
		+ ', '.join(f'`{k}`={v}' for k, v in sorted(por_archivo.items()))
		+ '\n',
		'\n---\n\n',
	]

	archivo_actual = ''
	for chunk in chunks:
		if chunk.source != archivo_actual:
			archivo_actual = chunk.source
			lineas.append(f'## {archivo_actual}\n\n')
		lineas.append(format_chunk_markdown(chunk))
		lineas.append('\n')

	destino.write_text(''.join(lineas), encoding='utf-8')
	return destino


def _format_chunk_preview(chunk: Chunk, max_body_chars: int = 280) -> str:
	cuerpo = chunk.content
	if len(cuerpo) > max_body_chars:
		cuerpo = cuerpo[: max_body_chars - 3].rstrip() + '...'
	sep = '=' * 72
	return (
		f'{sep}\n'
		f'id: {chunk.chunk_id} | source: {chunk.source} | '
		f'section: {chunk.section} | part: {chunk.part_index}\n'
		f'ruta: {chunk.header_path}\n'
		f'{sep}\n'
		f'{cuerpo}\n'
	)


def main() -> None:
	chunks = chunk_corpus()
	por_archivo = _resumen_por_archivo(chunks)
	export_md = save_chunks_markdown(chunks)
	export_jsonl = save_chunks_jsonl(chunks)

	print(f'Estrategia: {STRATEGY_HEADER_BASED}')
	print('Regla: un chunk por sección ## (texto completo)')
	print(f'Total chunks: {len(chunks)}')
	print('Por archivo:', ', '.join(f'{k}={v}' for k, v in sorted(por_archivo.items())))
	print(f'Exportado: {export_md}')
	print(f'Metadatos JSONL: {export_jsonl}')
	print()

	for chunk in chunks:
		print(_format_chunk_preview(chunk))
		print()


if __name__ == '__main__':
	main()