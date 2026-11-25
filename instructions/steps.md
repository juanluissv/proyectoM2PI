# Nubbix Assist — lista de tareas (Módulo 2)

Leyenda: **✅** hecho · **🔶** parcial / falta pulir · **⬜** pendiente · **⭐** bonus / extra credit

Última revisión: ingesta + consulta `header_based` (vector + LLM + JSON en `src/query.py`).

---

## 1. Setup del proyecto

| Estado | Tarea |
|--------|--------|
| ✅ | Repositorio Git + remote (`origin` GitHub) |
| ✅ | Entorno virtual (`.venv`) |
| ✅ | `requirements.txt` (OpenAI, Pinecone, etc.) |
| ✅ | `.gitignore` |
| ✅ | `.env.example` documentado |
| ✅ | `.env` local con API keys (no commitear) |
| ✅ | `README.md` inicial (setup, corpus, estructura) |
| 🔶 | `README.md` completo: comandos reales, Pinecone, **números de evals** y tabla comparativa de chunking |
| ⬜ | Push de todo el trabajo reciente a GitHub (repo público para entrega) |

---

## 2. Corpus y datos

| Estado | Tarea |
|--------|--------|
| ✅ | `data/corpus/` con `hr_policies.md`, `it_manual.md`, `finance_processes.md` |
| ⬜ | Revisión final: corpus sin modificaciones vs. material Henry |

---

## 3. Ingesta — chunking

| Estado | Tarea |
|--------|--------|
| ✅ | `ingest/chunking.py` — estrategia **`header_based`** (un chunk por `##`, texto completo) |
| ✅ | Ruta de headers en el texto a embeddear |
| ✅ | Metadatos por chunk (`doc`, `titulo_doc`, `estrategia`, `seccion`, `parte`, etc.) |
| ✅ | Export revisión: `ingest/chunks.md` + `ingest/chunks.jsonl` |
| ✅ | Helper `pinecone_upsert_record` (id + metadata para Pinecone) |
| ⬜ | Segunda estrategia **`fixed_overlap`** (tamaño fijo + overlap, ≥20 chunks en esa estrategia) |
| ⬜ | `chunk_corpus()` + CLI ingest con `--strategy` para ambas estrategias |

---

## 4. Ingesta — embeddings e índice (Pinecone)

| Estado | Tarea |
|--------|--------|
| ✅ | `ingest/embeddings.py` — OpenAI embeddings en batches |
| ✅ | `ingest/pinecone_setup.py` — config, nombres de índice por estrategia |
| ✅ | `ingest/create_indexes.py` — dos índices serverless (`nubbix-header-based`, `nubbix-fixed-overlap`) |
| ✅ | `ingest/ingest.py` — pipeline chunk → embed → upsert → verificación |
| ✅ | Ingesta ejecutada **`header_based`** → 18 vectores en `nubbix-header-based` |
| ⬜ | Ingesta **`fixed_overlap`** → índice `nubbix-fixed-overlap` |

**Comandos útiles**

```bash
python -m ingest.create_indexes
python -m ingest.chunking          # solo export chunks (opcional)
python -m ingest.ingest --strategy header_based
# python -m ingest.ingest --strategy fixed_overlap   # cuando exista chunking
```

---

## 5. Consulta (RAG) — `src/`

| Estado | Tarea |
|--------|--------|
| ✅ | `src/query.py` — CLI `python -m src.query -q "..."` |
| ✅ | Embed de la pregunta (mismo modelo que ingest) |
| ✅ | Búsqueda **vectorial** en Pinecone (`nubbix-header-based`) |
| ✅ | Generación con LLM sobre chunks recuperados (default; `--retrieval-only` opcional) |
| ✅ | Salida JSON: `{ user_question, system_answer, chunks_related }` |
| 🔶 | Cliente OpenAI en consulta (listo); Gemini fallback en query **no** implementado |
| 🔶 | Citas en `system_answer` + alineación estricta con `chunks_related` (revisar calidad) |
| ⬜ | **Búsqueda híbrida** (léxica + vectorial) + fusión documentada (RRF o ponderada) — **obligatorio consigna** |

**Comando consulta**

```bash
python -m src.query -q "¿Hasta qué día cargo rendiciones en ExpenseHub?" --pretty
```

---

## 6. Prompts

| Estado | Tarea |
|--------|--------|
| ⬜ | `prompts/` — prompt de generación en YAML |
| ⬜ | `prompts/` — prompt del juez de **groundedness** en YAML |
| ⬜ | Instrucciones en prompt: responder solo con contexto + citar `chunk_id` |

---

## 7. Evaluación

| Estado | Tarea |
|--------|--------|
| 🔶 | `evals/dataset.jsonl` — archivo existe, **vacío** |
| ⬜ | Golden dataset **≥25** preguntas (directas, sinónimos, cruzan docs, distractores) |
| ⬜ | Chunks esperados etiquetados **por estrategia de chunking** |
| 🔶 | `evals/runner.py` — archivo existe, **sin implementar** |
| ⬜ | Métricas **retrieval**: precision / recall (separado de generación) |
| ⬜ | Métricas **generación**: groundedness (LLM-as-judge) |
| ⬜ | Runner sobre **ambas** estrategias; mismos `top_k` y dataset para comparar chunking |

---

## 8. Comparación de chunking y documentación (entregable central)

| Estado | Tarea |
|--------|--------|
| ⬜ | Tabla en README: métricas retrieval estrategia A vs B |
| ⬜ | Decisión final de estrategia con trade-offs y números |
| ⬜ | README: modelo de embeddings, dimensión, Pinecone, método híbrido |
| ⬜ | README: resultados de evals (retrieval + groundedness) |
| ⬜ | README: limitaciones conocidas |
| ⬜ | Probar ingesta desde cero en clone limpio (checklist entrega) |

---

## 9. Bonus y extras (no obligatorio para aprobar)

| Estado | Tarea |
|--------|--------|
| ⬜ | ⭐ **Rechazo honesto** (preguntas fuera de corpus + métrica en runner + README) |
| ⬜ | ⭐ Re-ranking con cross-encoder (delta de métricas + latencia) |
| ⬜ | ⭐ Query rewriting / multi-query |
| ⬜ | ⭐ UI mínima (Streamlit) con citas navegables |
| ⬜ | Registro opcional `data/metrics.jsonl` por consulta (tokens, latencia, costo) — estilo M1 |

---

## 10. Checklist rápido de entrega (consigna)

| Estado | Ítem |
|--------|------|
| ✅ | API keys por entorno, no en código |
| 🔶 | Ingesta de cero con un comando **por estrategia** (solo `header_based` hoy) |
| 🔶 | Consulta con JSON válido y citas reales (`header_based` vector+LLM OK; híbrida falta) |
| ⬜ | Evals corridas ×2 estrategias → números en README |
| 🔶 | Repo autocontenido: clonar → instalar → indexar → consultar |

---

## Orden sugerido para lo que sigue

1. **Búsqueda híbrida** en `src/query.py` (obligatorio; vectorial ya está)
2. **`prompts/generation.yaml`** y cargar prompts desde YAML (sacar texto hardcodeado)
3. **`fixed_overlap`** + ingest al segundo índice
4. **`evals/dataset.jsonl`** (≥25) + **`evals/runner.py`**
5. README: Pinecone, query, híbrida, tabla chunking, métricas
6. Push a GitHub + prueba en clone limpio