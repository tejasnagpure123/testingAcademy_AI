"""Small, dependency-free TF-IDF retriever for the local TTA Cart test corpus."""

import json
import math
import re
from collections import Counter
from pathlib import Path

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
VALIDITY_VALUES = {"valid", "invalid"}
IMPORTANCE_VALUES = {"high", "medium", "low"}
EVIDENCE_VALUES = {"observed", "design_reference", "synthetic_duplicate"}
POSSIBLE_DUPLICATE_THRESHOLD = 0.82
TEXT_FIELDS = ("title", "feature", "test_type", "description", "expected_result")


def _tokens(text: str) -> list[str]:
    tokens = TOKEN_PATTERN.findall(text.lower())
    normalized = []
    for token in tokens:
        normalized.append(token)
        if token in {"login", "logged"}:
            normalized.append("authentication")
        elif token in {"remember", "persistent", "persistence"}:
            normalized.append("session")
        elif token in {"cart", "basket"}:
            normalized.append("shopping")
        elif token in {"purchase", "order", "checkout"}:
            normalized.append("cart")
    return normalized


def load_test_cases(corpus_path: Path) -> list[dict]:
    try:
        raw_cases = json.loads(corpus_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise RuntimeError(f"TTA Cart RAG corpus not found: {corpus_path}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Invalid JSON in TTA Cart RAG corpus: {corpus_path}") from error
    if not isinstance(raw_cases, list) or not raw_cases:
        raise RuntimeError("TTA Cart RAG corpus must contain a non-empty JSON list.")

    seen_ids = set()
    for case in raw_cases:
        if not isinstance(case, dict):
            raise RuntimeError("Every TTA Cart RAG record must be a JSON object.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen_ids:
            raise RuntimeError(f"Missing or duplicate TTA Cart test-case ID: {case_id!r}")
        seen_ids.add(case_id)
        if case.get("validity") not in VALIDITY_VALUES:
            raise RuntimeError(
                f"{case_id} validity must be one of {sorted(VALIDITY_VALUES)}."
            )
        for field in (
            "title",
            "feature",
            "test_type",
            "description",
            "expected_result",
        ):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise RuntimeError(f"{case_id} requires a non-empty {field}.")
        if not isinstance(case.get("tags", []), list):
            raise RuntimeError(f"{case_id} tags must be a JSON list.")
        if case.get("importance", "medium") not in IMPORTANCE_VALUES:
            raise RuntimeError(
                f"{case_id} importance must be one of {sorted(IMPORTANCE_VALUES)}."
            )
        if case.get("evidence_status", "design_reference") not in EVIDENCE_VALUES:
            raise RuntimeError(
                f"{case_id} evidence_status must be one of {sorted(EVIDENCE_VALUES)}."
            )
    return raw_cases


def _weighted_term_counts(case: dict) -> Counter:
    counts = Counter()
    for field, weight in (
        ("title", 3),
        ("feature", 2),
        ("test_type", 1),
        ("description", 1),
        ("expected_result", 1),
    ):
        counts.update(
            {
                token: weight * count
                for token, count in Counter(_tokens(case[field])).items()
            }
        )
    for value in [*case.get("tags", []), *case.get("jira_keys", [])]:
        counts.update({token: 2 * count for token, count in Counter(_tokens(str(value))).items()})
    return counts


def _tfidf_vector(
    term_counts: Counter, document_count: int, document_frequency: Counter
) -> dict[str, float]:
    vector = {}
    for term, frequency in term_counts.items():
        inverse_frequency = math.log(
            (1 + document_count) / (1 + document_frequency[term])
        ) + 1
        vector[term] = (1 + math.log(frequency)) * inverse_frequency
    norm = math.sqrt(sum(weight * weight for weight in vector.values()))
    return {term: weight / norm for term, weight in vector.items()} if norm else {}


def _tfidf_vectors(documents: list[Counter]) -> list[dict[str, float]]:
    document_frequency = Counter(
        term for document in documents for term in document.keys()
    )
    return [
        _tfidf_vector(document, len(documents), document_frequency)
        for document in documents
    ]


def _cosine_similarity(
    left: dict[str, float], right: dict[str, float]
) -> float:
    return sum(weight * right.get(term, 0.0) for term, weight in left.items())


def retrieve_test_cases(
    query: str, corpus_path: Path, top_k: int = 5
) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("RAG query must contain non-whitespace text.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    cases = load_test_cases(corpus_path)
    document_counts = [_weighted_term_counts(case) for case in cases]
    vectors = _tfidf_vectors(document_counts)
    query_counts = Counter(_tokens(query))
    document_frequency = Counter(
        term for document in document_counts for term in document.keys()
    )
    query_vector = _tfidf_vector(
        query_counts, len(document_counts), document_frequency
    )
    ranked = []
    for index, (case, vector) in enumerate(zip(cases, vectors)):
        score = _cosine_similarity(query_vector, vector)
        if score > 0:
            duplicates = []
            for other_index, other_case in enumerate(cases):
                if other_index == index:
                    continue
                duplicate_score = _cosine_similarity(vector, vectors[other_index])
                if duplicate_score >= POSSIBLE_DUPLICATE_THRESHOLD:
                    duplicates.append(
                        {
                            "id": other_case["id"],
                            "title": other_case["title"],
                            "similarity": round(duplicate_score, 4),
                        }
                    )
            duplicates.sort(key=lambda result: (-result["similarity"], result["id"]))
            ranked.append(
                {
                    **case,
                    "score": round(score, 4),
                    "possible_duplicates": duplicates,
                    "importance": case.get("importance", "medium"),
                }
            )
    ranked.sort(key=lambda result: (-result["score"], result["id"]))
    return ranked[:top_k]


def format_retrieved_cases(results: list[dict]) -> str:
    if not results:
        return "No related TTA Cart test cases were retrieved."
    lines = []
    for rank, case in enumerate(results, start=1):
        lines.extend(
            [
                f"{rank}. [{case['validity'].upper()} | score={case['score']:.4f}] "
                f"{case['id']}: {case['title']}",
                f"   Importance: {case.get('importance', 'medium').upper()}",
                f"   Type: {case['test_type']}",
                f"   Evidence: {case.get('evidence_status', 'design_reference')}",
                f"   Rationale: {case.get('validity_rationale', 'Not provided.')}",
                f"   Steps: {case['description']}",
                f"   Expected: {case['expected_result']}",
                f"   Source: {case.get('source', 'Local TTA Cart corpus')}",
            ]
        )
        if case.get("possible_duplicates"):
            duplicates = ", ".join(
                f"{candidate['id']} ({candidate['similarity']:.4f})"
                for candidate in case["possible_duplicates"]
            )
            lines.append(f"   Possible duplicates: {duplicates}")
    return "\n".join(lines)
