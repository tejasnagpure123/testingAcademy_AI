import os
from pathlib import Path
import sys

import pytest
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from groq_model import create_groq_evaluation_model

PROJECT_ENV = PROJECT_ROOT / ".env"
load_dotenv(PROJECT_ENV)


def test_groq_model_uses_openai_compatible_configuration(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    model = create_groq_evaluation_model()

    assert model.get_model_name() == "openai/gpt-oss-120b"


@pytest.mark.skipif(
    not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not configured"
)
def test_groq_answer_relevancy():
    metric = AnswerRelevancyMetric(
        model=create_groq_evaluation_model(),
        include_reason=True,
    )
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="Paris is the capital of France.",
    )

    metric.measure(test_case)

    assert metric.score >= 0.5
