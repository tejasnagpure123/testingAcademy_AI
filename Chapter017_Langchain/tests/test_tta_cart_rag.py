import asyncio
import contextlib
import importlib.util
import json
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "chapters"))

from tta_cart_rag import format_retrieved_cases, load_test_cases, retrieve_test_cases

ORCHESTRATOR_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "chapters"
    / "013_Fetch_Jira_Full_E2E_Playwright_Agent_Orcch_RAG.py"
)
CORPUS_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "tta_cart_test_cases.json"
)
SPEC = importlib.util.spec_from_file_location("tta_cart_rag_orchestrator", ORCHESTRATOR_PATH)
ORCHESTRATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORCHESTRATOR)


class TtaCartRagTests(unittest.TestCase):
    def test_remember_me_query_retrieves_invalid_unsupported_case(self):
        results = retrieve_test_cases(
            "KAN-4 verify Remember Me persistent login after browser restart",
            CORPUS_PATH,
            top_k=3,
        )

        self.assertTrue(results)
        self.assertEqual("TTA-AUTH-REMEMBER-001", results[0]["id"])
        self.assertEqual("invalid", results[0]["validity"])

    def test_cart_purchase_query_retrieves_observed_valid_checkout(self):
        results = retrieve_test_cases(
            "verify cart checkout price tax total and thank you order",
            CORPUS_PATH,
            top_k=3,
        )

        self.assertTrue(results)
        self.assertEqual("TTA-CHECKOUT-001", results[0]["id"])
        self.assertEqual("valid", results[0]["validity"])
        self.assertIn("$17.27", results[0]["expected_result"])

    def test_selected_case_has_retrieval_metadata_even_when_outside_top_results(self):
        selected = ORCHESTRATOR.select_retrieved_case("TTA-CHECKOUT-001", [])

        self.assertEqual("TTA-CHECKOUT-001", selected["id"])
        self.assertGreater(selected["score"], 0)
        self.assertIn("possible_duplicates", selected)

    def test_retrieval_scores_are_sorted_and_render_validity(self):
        results = retrieve_test_cases("login cart authentication", CORPUS_PATH, top_k=5)

        self.assertEqual(
            sorted((result["score"] for result in results), reverse=True),
            [result["score"] for result in results],
        )
        rendered = format_retrieved_cases(results)
        self.assertIn("[VALID", rendered)
        self.assertIn("[INVALID", rendered)
        self.assertIn("Importance:", rendered)
        login_case = next(
            result for result in results if result["id"] == "TTA-LOGIN-001"
        )
        self.assertIn(
            "TTA-LOGIN-004",
            {candidate["id"] for candidate in login_case["possible_duplicates"]},
        )

    def test_corpus_rejects_duplicate_ids(self):
        case = load_test_cases(CORPUS_PATH)[0]
        with tempfile.TemporaryDirectory() as temp_dir:
            corpus = Path(temp_dir) / "duplicate.json"
            corpus.write_text(json.dumps([case, case]), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "duplicate"):
                load_test_cases(corpus)

    def test_query_and_top_k_are_validated(self):
        with self.assertRaises(ValueError):
            retrieve_test_cases("  ", CORPUS_PATH)
        with self.assertRaises(ValueError):
            retrieve_test_cases("cart", CORPUS_PATH, top_k=0)

    def test_exact_duplicate_cases_are_flagged(self):
        cases = load_test_cases(CORPUS_PATH)
        duplicate = dict(cases[0])
        duplicate["id"] = "TTA-LOGIN-001-COPY"
        with tempfile.TemporaryDirectory() as temp_dir:
            corpus = Path(temp_dir) / "duplicates.json"
            corpus.write_text(json.dumps([cases[0], duplicate]), encoding="utf-8")
            results = retrieve_test_cases("successful standard user login", corpus)

        self.assertEqual(2, len(results))
        for result in results:
            duplicate_ids = {
                candidate["id"] for candidate in result["possible_duplicates"]
            }
            self.assertNotIn(result["id"], duplicate_ids)
            self.assertIn(
                "TTA-LOGIN-001-COPY" if result["id"] != "TTA-LOGIN-001-COPY" else "TTA-LOGIN-001",
                duplicate_ids,
            )

    def test_jira_and_retrieved_cases_are_in_both_generation_prompts(self):
        class FakeResponse:
            content = "Generated document"

        class FakeLLM:
            def __init__(self):
                self.messages = []

            async def ainvoke(self, messages):
                self.messages.append(messages)
                return FakeResponse()

        issue = {
            "key": "KAN-4",
            "summary": "Remember Me persistent login",
            "description": "No description provided.",
            "comments": "No comments provided.",
            "issue_type": "Bug",
            "status": "To Do",
            "priority": "Medium",
        }
        retrieved = retrieve_test_cases(
            "KAN-4 Remember Me persistent login TTA Cart",
            CORPUS_PATH,
            top_k=3,
        )
        llm = FakeLLM()
        plan, cases = asyncio.run(
            ORCHESTRATOR.generate_documents(llm, issue, retrieved)
        )

        self.assertEqual(("Generated document", "Generated document"), (plan, cases))
        self.assertEqual(2, len(llm.messages))
        for messages in llm.messages:
            prompt = messages[-1].content
            self.assertIn("KAN-4", prompt)
            self.assertIn("TTA-AUTH-REMEMBER-001", prompt)
            self.assertIn("[INVALID", prompt)

    def test_dummy_slack_notification_only_prints_and_does_not_send(self):
        issue = {"key": "KAN-4", "summary": "Remember Me"}
        retrieved = retrieve_test_cases("KAN-4 Remember Me", CORPUS_PATH, top_k=1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            response = asyncio.run(
                ORCHESTRATOR.DummySlackNotificationAgent().notify(
                    issue, "BLOCKED", Path("reports") / "KAN-4", retrieved
                )
            )

        self.assertFalse(response["sent"])
        self.assertIn("no message sent", output.getvalue())
        self.assertIn('"pipeline_status": "BLOCKED"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
