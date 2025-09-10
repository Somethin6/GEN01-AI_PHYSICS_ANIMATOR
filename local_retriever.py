from pathlib import Path
import math, re, unicodedata


def _tok(s):
    s = unicodedata.normalize("NFKC", s.lower())
    return re.findall(r"[a-z0-9_]+", s)


class LocalRetriever:
    def __init__(self, roots, max_files=200, max_chars=250_000):
        self.docs = []
        for root in roots:
            root = Path(root)
            if not root.exists():
                continue
            for p in list(root.rglob("*.*"))[:max_files]:
                try:
                    t = p.read_text(encoding="utf-8")
                except Exception:
                    continue
                if not t:
                    continue
                self.docs.append((p, t[:max_chars]))
        self.df = {}
        self.tfs = []
        for _, text in self.docs:
            tokens = _tok(text)
            tf = {}
            for w in tokens:
                tf[w] = tf.get(w, 0) + 1
            self.tfs.append(tf)
            for w in tf:
                self.df[w] = self.df.get(w, 0) + 1
        self.N = max(1, len(self.docs))

    def search(self, query, k=6):
        q = _tok(query)
        scores = []
        for i, (p, text) in enumerate(self.docs):
            score = 0.0
            for w in q:
                if w in self.tfs[i]:
                    tf = 1 + math.log(self.tfs[i][w])
                    idf = math.log((self.N + 1) / (1 + self.df.get(w, 0)))
                    score += tf * idf
            if score > 0:
                scores.append((score, p, text))
        scores.sort(reverse=True, key=lambda x: x[0])
        return [
            {"path": str(p), "score": float(s), "snippet": text[:1200]}
            for s, p, text in scores[:k]
        ]
