import importlib.util
import unittest
from pathlib import Path


THIS_DIR = Path(__file__).resolve().parent
MODULE_PATH = THIS_DIR / "score_india.py"
SPEC = importlib.util.spec_from_file_location("india_score_india", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

parse_model_content = MODULE.parse_model_content
resolve_model_name = MODULE.resolve_model_name
score_with_retries = MODULE.score_with_retries


class ScoreIndiaTests(unittest.TestCase):
    def test_parse_model_content_accepts_plain_json(self):
        parsed = parse_model_content('{"exposure": 7, "rationale": "Test"}')
        self.assertEqual(parsed["exposure"], 7)
        self.assertEqual(parsed["rationale"], "Test")

    def test_parse_model_content_strips_code_fences(self):
        parsed = parse_model_content(
            "```json\n{\"exposure\": 4, \"rationale\": \"Test\"}\n```"
        )
        self.assertEqual(parsed["exposure"], 4)

    def test_resolve_model_name_prefers_cli_then_env_then_default(self):
        self.assertEqual(resolve_model_name("cli-model", "env-model"), "cli-model")
        self.assertEqual(resolve_model_name(None, "env-model"), "env-model")
        self.assertEqual(
            resolve_model_name(None, None),
            "google/gemini-3-flash-preview",
        )

    def test_score_with_retries_eventually_returns_success(self):
        state = {"calls": 0}

        def flaky():
            state["calls"] += 1
            if state["calls"] < 3:
                raise RuntimeError("temporary")
            return {"exposure": 5, "rationale": "ok"}

        result = score_with_retries(flaky, max_retries=3, retry_delay=0)
        self.assertEqual(result["exposure"], 5)
        self.assertEqual(state["calls"], 3)

    def test_score_with_retries_raises_after_limit(self):
        state = {"calls": 0}

        def always_fail():
            state["calls"] += 1
            raise RuntimeError("temporary")

        with self.assertRaises(RuntimeError):
            score_with_retries(always_fail, max_retries=2, retry_delay=0)
        self.assertEqual(state["calls"], 3)


if __name__ == "__main__":
    unittest.main()
