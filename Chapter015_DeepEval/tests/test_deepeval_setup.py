from deepeval.test_case import LLMTestCase


def test_deepeval_llm_test_case_can_be_created():
    test_case = LLMTestCase(
        input="What is 2 + 2?",
        actual_output="4",
        expected_output="4",
    )

    assert test_case.input == "What is 2 + 2?"
    assert test_case.actual_output == "4"
    assert test_case.expected_output == "4"
