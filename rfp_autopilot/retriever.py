"""Find the most similar approved answers for a new question.

Uses TF-IDF over word n-grams plus character n-grams, which handles
acronyms and phrasing variants ("SSO" vs "single sign-on", "encrypt" vs
"encryption") well enough for a library of a few thousand answers, with
no API key or vector database required.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .library import ApprovedAnswer

# Expand common security/compliance acronyms so "SSO" matches "single sign-on".
SYNONYMS = {
    r"\bsso\b": "sso single sign-on",
    r"\bsaml\b": "saml sso single sign-on",
    r"\bmfa\b": "mfa multi-factor authentication",
    r"\b2fa\b": "2fa multi-factor authentication",
    r"\bat rest\b": "at rest stored encryption",
    r"\bin transit\b": "in transit tls encryption",
    r"\bpen ?test(s|ing)?\b": "penetration test",
    r"\bdr\b": "disaster recovery",
    r"\bbcp\b": "business continuity",
    r"\bpii\b": "pii personal data",
    r"\bphi\b": "phi health data hipaa",
    r"\brbac\b": "rbac role-based access control",
    r"\bscim\b": "scim user provisioning",
    r"\brto\b": "rto recovery time objective",
    r"\brpo\b": "rpo recovery point objective",
    r"\bback(ed)? ?ups?\b": "backup",
    r"\bnotif(y|ied|ication)\b": "notify",
}


def normalize(text: str) -> str:
    text = text.lower()
    for pattern, replacement in SYNONYMS.items():
        text = re.sub(pattern, replacement, text)
    # Very light stemming: "keys" -> "key", "models" -> "model" (leaves "access", "this").
    return re.sub(r"\b\w+\b", _singular, text)


_KEEP = {"this", "does", "has", "was", "is", "its", "yes", "us", "always", "aws", "sms", "ops", "terms", "status"}


def _singular(m: re.Match) -> str:
    word = m.group(0)
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss") and word not in _KEEP:
        return word[:-1]
    return word


@dataclass(frozen=True)
class Match:
    entry: ApprovedAnswer
    score: float  # cosine similarity, 0..1


class Retriever:
    def __init__(self, library: list[ApprovedAnswer]):
        self.library = library
        # Index every phrasing (question + aliases) separately, remembering
        # which library entry it belongs to; an entry scores its best phrasing.
        self._owner: list[int] = []
        corpus: list[str] = []
        for idx, entry in enumerate(library):
            for phrasing in entry.phrasings:
                corpus.append(normalize(phrasing))
                self._owner.append(idx)
        self._word = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self._char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self._matrix = hstack([self._word.fit_transform(corpus), self._char.fit_transform(corpus)]).tocsr()

    def _vectorize(self, question: str):
        q = normalize(question)
        return hstack([self._word.transform([q]), self._char.transform([q])]).tocsr()

    def search(self, question: str, k: int = 3) -> list[Match]:
        if not question.strip():
            return []
        # Each block is L2-normalized, so cosine over the stacked vector is the
        # average of word-level and char-level similarity (range 0..1).
        sims = cosine_similarity(self._vectorize(question), self._matrix)[0]
        best: dict[int, float] = {}
        for owner, score in zip(self._owner, sims):
            if score > best.get(owner, -1.0):
                best[owner] = float(score)
        ranked = sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [Match(self.library[i], round(s, 4)) for i, s in ranked]
