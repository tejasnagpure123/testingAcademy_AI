# Exercise 1 (Basic): Answer Relevancy
# Level Basic : chatbot anwsers

# Exercise 1 (Basic): Answer Relevancy & Hallucination Detection
# Level Basic : chatbot anwsers

# Goal:
#     Learn the two most fundamental LLM evaluation metrics:
#     1. Answer Relevancy  — Does the chatbot answer the question asked?


# Run from this folder: .\venv\Scripts\deepeval.exe test run .\test_01_AnswerRelevancy.py

from deepeval.test_case import LLMTestCase
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric

from groq_model import create_groq_evaluation_model


def test_answer_relevancy_with_groq():
    test = LLMTestCase(
        input="What is 2+2?",
        actual_output="4",
        expected_output="4",
        context=["Basic arithmatic perform and give result"],
    )
    metric = [
        AnswerRelevancyMetric(
            threshold=0.9,
            model=create_groq_evaluation_model(),
        )
    ]
    assert_test(test, metric)
