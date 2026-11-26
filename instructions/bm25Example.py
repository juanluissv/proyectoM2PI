import math
import unicodedata
from collections import Counter


STOP = set("""a al algo como con cual cuales cuando cuanto cuanta cuantos de del desde donde el ella
ellos en entre era es esa ese eso esta estas este esto estos fue ha hay la las le les lo los me mi mis
muy mas me nos o para pero por porque que se si sin sobre su sus te tengo tiene tu un una uno unos unas
y ya yo e u puedo puede hace tan the of to and or is my it on for in an""".split())


def tokenizar(texto):

    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP]



class BM25:
    def __init__(self, textos, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenizar(t)) for t in textos]#cuntas veces esta la palabra en el CH self.docs[1] = {"cambio": 2, "clase": 1, "k": 1, "fecha": 1, "destino": 1}
        self.largos = np.array([sum(d.values()) for d in self.docs], dtype=float)#suma los valores de self.docs para saber cuantas palabra tiene el chunk
        self.avgdl = self.largos.mean()#el promedios de los chunks
        self.df = Counter(t for d in self.docs for t in d)#calculamos el df, es decir en cuantos chumks aprecio una palabra
        self.N = len(self.docs)#cuantos chunks hay

    def idf(self, t):#cuanto vale la palabra
        df = self.df.get(t, 0)
        return math.log(1 + (self.N - df + 0.5) / (df + 0.5))


    def aporte(self, t, i):#cuantos puntos le da una palabra aun chunk

        tf = self.docs[i].get(t, 0)
        if tf == 0:
            return 0.0
        return self.idf(t) * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * self.largos[i] / self.avgdl))

    def puntajes(self, consulta):#calulca el puntaje de una pregunta en los 88 chunks

        terminos = set(tokenizar(consulta))
        return np.array([sum(self.aporte(t, i) for t in terminos) for i in range(self.N)])


bm25 = BM25(textos)
print(f"{bm25.N} chunks · largo promedio {bm25.avgdl:.0f} palabras\n")
for t in ["k", "pasaje", "equipaje","maleta"]:
    print(f"{t:<10} aparece en {bm25.df[t]:>2} de {bm25.N} chunks → idf {bm25.idf(t):.2f}")