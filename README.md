# Nubbix Assist

Asistente de conocimiento interno para **Nubbix** (SaaS de gestión para pymes de LATAM). Responde preguntas de empleados sobre políticas y procesos oficiales usando **RAG** (Retrieval-Augmented Generation), con **búsqueda híbrida** (léxica + vectorial) y **citas rastreables** a los fragmentos del corpus.

**Proyecto Integrador — Módulo 2 (AI Engineering)**

---

## Contexto

Nubbix creció a ~350 empleados y el conocimiento interno quedó disperso en PDFs, wikis y correos. People e IT pierden horas respondiendo las mismas consultas, a veces con respuestas desalineadas de la política vigente.

**Nubbix Assist** centraliza ese conocimiento: un chatbot que responde solo a partir de documentación oficial y **cita siempre las fuentes** usadas.

### Objetivos del módulo

| Objetivo | Descripción |
|----------|-------------|
| Ingesta reproducible | Procesar el corpus, chunking justificado, embeddings; índice construido por comando, consulta separada |
| Índice + búsqueda híbrida | Vector DB con recuperación léxica + vectorial |
| Chunking con datos | Comparar **dos** estrategias sobre el mismo corpus y elegir una con métricas de retrieval |
| Evaluación por etapas | Retrieval (precision/recall) vs. generación (groundedness) con golden dataset propio |

---

## Corpus documental

El corpus son **tres archivos Markdown** (sin modificar), en `data/corpus/`:

| Archivo | Contenido |
|---------|-----------|
| `hr_policies.md` | HR: licencias, beneficios, home office |
| `it_manual.md` | IT: accesos, equipos, seguridad |
| `finance_processes.md` | Finance: reintegros, viáticos, compras |

Algunos temas cruzan documentos (p. ej. capacitación en HR y su rendición en Finance). Eso impacta el chunking y el golden dataset.

> Descargá los tres documentos desde el material del curso y colocalos en `data/corpus/`.

---

## Estructura del repositorio

```
proyectoM2PI/
├── data/
│   └── corpus/              # hr_policies.md, it_manual.md, finance_processes.md
├── ingest/                  # Pipeline de ingesta (chunking, embeddings, indexación)
├── src/                     # Consulta: búsqueda híbrida + generación + JSON de salida
├── evals/
│   ├── dataset.jsonl        # Golden dataset (≥25 preguntas)
│   └── runner.py            # Métricas retrieval + groundedness
├── prompts/                 # Prompts YAML (generación y juez)
├── .env.example
├── requirements.txt
└── README.md
```

- **Ingesta** y **consulta** son procesos separados: el índice se construye una vez; las consultas solo leen.
- Cada estrategia de chunking se indexa por separado (p. ej. una colección de Chroma por estrategia).

---

## Requisitos previos

- Python 3.10+ (recomendado)
- Cuenta y API key del proveedor de embeddings/LLM que elijas (vía variables de entorno)
- Git

---

## Instalación

```bash
git clone <url-de-tu-repo>
cd proyectoM2PI

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Completar .env con tus claves (nunca subir .env al repositorio)
```

Colocá el corpus en `data/corpus/` antes de indexar.

---

## Uso

### 1. Ingesta (construir el índice)

Ejecutá la ingesta **por estrategia** (parámetro documentado en tu CLI):

```bash
# Ejemplo — ajustá según tu implementación
python -m ingest.ingest --strategy fixed_overlap
python -m ingest.ingest --strategy header_based
```

La ingesta debe producir **al menos 20 chunks** por estrategia (como mínimo en una de las dos).

### 2. Consulta

```bash
# Ejemplo — CLI o endpoint según tu diseño
python -m src.query --question "¿Hasta qué día del mes puedo cargar una rendición de gastos?"
```

### 3. Evaluaciones

```bash
python -m evals.runner
```

El runner debe reportar retrieval (precision/recall) y generación (groundedness) **por separado**, para **cada** estrategia de chunking.

---

## Contrato de salida (JSON)

Cada respuesta del asistente debe ser JSON consumible sin transformaciones adicionales:

```json
{
  "user_question": "¿Hasta qué día del mes puedo cargar una rendición de gastos?",
  "system_answer": "Las rendiciones se cargan en ExpenseHub antes del día 25 de cada mes; las que se ingresan después se procesan en el ciclo de pagos del mes siguiente [finance_processes.md_0].",
  "chunks_related": [
    {
      "chunk_id": "finance_processes.md_0",
      "source": "finance_processes.md",
      "content": "## Reintegro de Gastos y Viáticos\n...",
      "score": 0.87
    }
  ]
}
```

---

## Decisiones técnicas

> Completá esta sección a medida que implementes. Los números deben coincidir con lo que reporta `evals/runner.py`.

### Embeddings

| Campo | Valor |
|-------|--------|
| Modelo | _pendiente_ |
| Dimensiones | _pendiente_ |
| Métrica en vector DB | _pendiente_ |

### Vector database

| Campo | Valor |
|-------|--------|
| Motor | _ej. Chroma local persistente_ |
| Persistencia | _ruta / colecciones por estrategia_ |

### Búsqueda híbrida

| Campo | Valor |
|-------|--------|
| Método de fusión | _ej. RRF o suma ponderada_ |
| Parámetros | _pesos, top_k, etc._ |

### Estrategias de chunking

Documentá parámetros (tamaño, overlap, reglas por encabezados) y el **por qué** de cada una.

| Estrategia | Descripción breve | Parámetros |
|------------|-------------------|------------|
| A (_nombre_) | _pendiente_ | _pendiente_ |
| B (_nombre_) | _pendiente_ | _pendiente_ |

---

## Comparación de chunking (retrieval)

Mismas condiciones para ambas estrategias: **mismo** `dataset.jsonl`, **mismo** `top_k`, misma fórmula de métricas.

| Métrica | Estrategia A | Estrategia B |
|---------|--------------|--------------|
| Precision@k | _pendiente_ | _pendiente_ |
| Recall@k | _pendiente_ | _pendiente_ |
| _Otras (MRR, hit rate, …)_ | _pendiente_ | _pendiente_ |

**Decisión final:** _Qué estrategia elegiste, con trade-offs (una puede ganar en precision y perder en recall, etc.)._

**Estrategia en producción del asistente:** _nombre de la estrategia elegida_

---

## Resultados de evaluación

### Retrieval (estrategia elegida)

| Métrica | Valor |
|---------|-------|
| Precision@k | _pendiente_ |
| Recall@k | _pendiente_ |

### Generación (groundedness)

| Métrica | Valor |
|---------|-------|
| Groundedness (LLM-as-judge) | _pendiente_ |

### Bonus: rechazo honesto (opcional)

Preguntas fuera de alcance en `evals/dataset.jsonl`; el sistema debe declarar que no hay información en la base documental.

| Métrica | Valor |
|---------|-------|
| Tasa de rechazo correcto | _pendiente_ |

---

## Golden dataset

Archivo: `evals/dataset.jsonl`

- **≥25** preguntas con chunks esperados etiquetados **por estrategia de chunking**
- Incluir casos difíciles, no solo coincidencia léxica con el documento

Tipos de pregunta a cubrir (referencia, no copiar literalmente):

| Tipo | Ejemplo ilustrativo |
|------|---------------------|
| Directa | ¿Con cuánta anticipación tengo que pedir las vacaciones? |
| Sinónimos | ¿Cuánta plata me dan por mes para pagar internet en casa? |
| Cruza documentos | Robo de notebook en viaje de trabajo: pasos y reintegro |
| Distractor cercano | ¿Cuántos días por casamiento? (misma sección que otras licencias) |
| Fuera de alcance (bonus) | ¿Hay estacionamiento en la oficina? |

---

## Limitaciones conocidas

_Listá aquí límites de tu MVP: dominios no cubiertos, edge cases de retrieval, latencia, idioma, etc._

---

## Checklist de entrega

- [ ] API keys solo en `.env`, nunca en el código
- [ ] Ingesta de cero con un comando por estrategia → índice persistido
- [ ] Consulta con JSON válido y citas a chunks reales del índice
- [ ] Evals corridas sobre ambas estrategias; números reflejados en este README
- [ ] README y código alineados: clonar → instalar → indexar → consultar sin ayuda externa

---

## Criterios de evaluación (rúbrica)

Aprobación: **70/100**; destacado: **81–100**.

| Categoría | Qué se evalúa |
|-----------|----------------|
| Ingesta y reproducibilidad | Pipeline por comando, vector DB, híbrida léxica + vectorial |
| Chunking | Dos estrategias comparadas con decisión basada en números |
| Retrieval | Golden dataset ≥25, precision/recall separados de generación |
| Groundedness | JSON con citas + evaluación automatizada |
| Código y README | Modularidad (`/src`, `/ingest`, `/evals`), documentación completa |

**Extra credit (opcional):** re-ranking con cross-encoder, query rewriting, UI mínima (Streamlit) — documentar efecto medido.

---

## Licencia y autor

_Proyecto académico — Módulo 2 AI Engineering._