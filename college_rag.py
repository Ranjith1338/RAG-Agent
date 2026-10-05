
"""Small, dependency-free FAQ RAG agent for a college knowledge base.

Replace ``data/college_faq.csv`` with the college's exported FAQ data. The
expected columns are: id, category, question, answer, keywords.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "a", "an", "and", "are", "be", "for", "how", "i", "in", "is", "of",
    "on", "or", "the", "to", "what", "when", "where", "which", "who",
}


@dataclass(frozen=True)
class FAQ:
    id: str
    category: str
    question: str
    answer: str
    keywords: tuple[str, ...] = ()

    @property
    def searchable_text(self) -> str:
        return f"{self.question} {self.answer} {' '.join(self.keywords)}"


@dataclass(frozen=True)
class Retrieval:
    faq: FAQ
    score: float


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOP_WORDS
    }


def load_faqs(path: str | Path) -> list[FAQ]:
    """Load FAQ records from a CSV file and validate required fields."""
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"FAQ database not found: {csv_path}")

    required = {"id", "category", "question", "answer", "keywords"}
    faqs: list[FAQ] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or ()))
            raise ValueError(f"FAQ CSV is missing required columns: {', '.join(missing)}")
        for row_number, row in enumerate(reader, start=2):
            values = {key: (row.get(key) or "").strip() for key in required}
            if not values["id"] or not values["question"] or not values["answer"]:
                raise ValueError(f"FAQ CSV row {row_number} needs id, question, and answer")
            keywords = tuple(
                keyword.strip().lower()
                for keyword in values["keywords"].split("|")
                if keyword.strip()
            )
            faqs.append(FAQ(
                id=values["id"],
                category=values["category"],
                question=values["question"],
                answer=values["answer"],
                keywords=keywords,
            ))
    if not faqs:
        raise ValueError(f"FAQ database is empty: {csv_path}")
    return faqs


class FAQRetriever:
    def __init__(self, faqs: Iterable[FAQ]) -> None:
        self.faqs = tuple(faqs)

    def search(self, query: str, limit: int = 3) -> list[Retrieval]:
        if not query.strip():
            return []
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        results: list[Retrieval] = []
        query_lower = query.casefold()
        for faq in self.faqs:
            question_tokens = _tokens(faq.question)
            keyword_tokens = _tokens(" ".join(faq.keywords))
            answer_tokens = _tokens(faq.answer)
            overlap = len(query_tokens & question_tokens)
            keyword_overlap = len(query_tokens & keyword_tokens)
            answer_overlap = len(query_tokens & answer_tokens)
            phrase_bonus = 2.0 if query_lower in faq.question.casefold() else 0.0
            score = (overlap * 4.0) + (keyword_overlap * 3.0) + (
                answer_overlap * 0.5
            ) + phrase_bonus
            if score > 0:
                results.append(Retrieval(faq=faq, score=score))
        return sorted(results, key=lambda result: result.score, reverse=True)[:limit]


class CollegeRAGAgent:
    def __init__(self, retriever: FAQRetriever, min_score: float = 1.5) -> None:
        self.retriever = retriever
        self.min_score = min_score

    def answer(self, question: str) -> str:
        matches = self.retriever.search(question)
        if not matches or matches[0].score < self.min_score:
            return (
                "I could not find that in the college FAQ database. "
                "Please contact the college office for an official answer."
            )

        best = matches[0].faq
        sources = ", ".join(match.faq.id for match in matches if match.score >= self.min_score)
        return f"{best.answer}\n\nSource: {sources}"


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    database = base_dir / "data" / "college_faq.csv"
    try:
        agent = CollegeRAGAgent(FAQRetriever(load_faqs(database)))
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print("College FAQ RAG agent. Type 'exit' to quit.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.casefold() in {"exit", "quit"}:
            break
        if question:
            print(f"Agent: {agent.answer(question)}")


if __name__ == "__main__":
    main()
