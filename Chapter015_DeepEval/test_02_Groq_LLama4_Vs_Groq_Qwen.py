# Flow:
# 1. Send "What is 2+2?" to Groq Qwen3.8-27b (the model under test).
# 2. Capture the raw answer.
# 3. Hand input + answer + context to DeepEval.
# 4. openai/gpt-oss-120b as judge -> scores AnswerRelevancy + Hallucination.
#    Subject != judge on purpose: a judge scoring its own family inflates scores.

GROQ_MODEL = "qwen/qwen3.8-27b"
JUDGE_MODEL = "openai/gpt-oss-120b"

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from deepeval.models import OpenAIModel
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase

load_dotenv(Path(__file__).resolve().with_name(".env"))
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise RuntimeError("GROQ_API_KEY is missing from the .env file or environment.")

groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

groq = OpenAI(
    api_key=groq_api_key,
    base_url=groq_base_url,
)
judge_model = OpenAIModel(
    model=JUDGE_MODEL,
    api_key=groq_api_key,
    base_url=groq_base_url,
    temperature=0,
)


def llm_response(question):
    """Ask GROQ_MODEL one question and return its raw answer text."""
    response = groq.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": question}],
        # temperature=0 keeps the answer stable so the score below is
        # reproducible. The judge is still non-deterministic; this only
        # pins the thing under test.
        temperature=0,
    )
    return response.choices[0].message.content.strip()


question = "What is 2+2? Reply with just the number."
answer = llm_response(question)
print(f"\n[Groq {GROQ_MODEL}] → {answer!r}\n")


def test_l4_with_judge_qwen():
    case = LLMTestCase(
        input=question,
        actual_output=answer,
        expected_output="4",
        # HallucinationMetric scores actual_output against this grounding text.
        context=["Basic arithmetic fact: 2 + 2 = 4"],
    )

    metrics = [
        AnswerRelevancyMetric(threshold=0.8, model=judge_model),
        HallucinationMetric(threshold=0.8, model=judge_model),
    ]
    for metric in metrics:
        metric.measure(case)

    assert metrics[0].success, metrics[0].reason
    assert metrics[1].success, metrics[1].reason

    hallucination_rate = 1 - metrics[1].score
    print(
        f"Answer Relevancy: {metrics[0].score:.1f}; "
        f"Hallucination rate (1 - DeepEval score): {hallucination_rate:.1f}"
    )
