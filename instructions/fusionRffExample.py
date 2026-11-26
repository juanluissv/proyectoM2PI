from collections import defaultdict

CANDIDATOS = 20                                   # cuántos resultados pide la híbrida a cada buscador


def buscar_bm25(pregunta, k=10):
    s = bm25.puntajes(pregunta)
    return [ids[i] for i in np.argsort(-s)[:k] if s[i] > 0]


def buscar_vectorial(pregunta, k=10, vector=None):
    if vector is None:
        vector = embeddear([pregunta])[0]
    return coleccion_h.query(query_embeddings=[vector], n_results=k, include=[])["ids"][0]


def fusion_rrf(rankings, k=60):
    """`rankings`: listas de ids. Devuelve [(id, puntaje RRF)] de mayor a menor."""
    puntajes = defaultdict(float)
    for ranking in rankings:
        for posicion, id_ in enumerate(ranking, 1):
            puntajes[id_] += 1 / (k + posicion)
    return sorted(puntajes.items(), key=lambda x: -x[1])


def buscar_hibrida(pregunta, k=10, vector=None, k_rrf=60):
    rankings = [buscar_vectorial(pregunta, CANDIDATOS, vector), buscar_bm25(pregunta, CANDIDATOS)]
    return [id_ for id_, _ in fusion_rrf(rankings, k_rrf)[:k]]


# La cuenta del pizarrón: "A" es 1° sólo en la lista 1; "C" es 3° en las dos
for id_, p in fusion_rrf([["A", "B", "C"], ["X", "Y", "C"]]):
    print(f"{id_}: {p:.4f}")