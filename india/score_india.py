"""
Score India occupations for AI exposure using OpenRouter.

Reads markdown descriptions from india/output/pages/, sends each occupation to
an LLM, and writes cached results to india/output/scores_india.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    load_dotenv = None

INDIA_DIR = Path(__file__).resolve().parent

if load_dotenv is not None:
    load_dotenv()
else:
    env_path = INDIA_DIR.parent / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

OCCUPATIONS_PATH = INDIA_DIR / "output" / "occupations_india.json"
PAGES_DIR = INDIA_DIR / "output" / "pages"
OUTPUT_PATH = INDIA_DIR / "output" / "scores_india.json"
BUILD_SITE_DATA_PATH = INDIA_DIR / "build_site_data.py"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemini-3-flash-preview"
DEFAULT_MODEL_ENV = "OPENROUTER_MODEL"

SYSTEM_PROMPT = """\
You are an expert analyst evaluating how exposed Indian occupations are to AI.
You will be given a normalized occupation page derived from India's National
Career Service and supporting India labour-market metadata.

Rate the occupation's overall AI Exposure on a scale from 0 to 10.

AI Exposure measures how much AI will reshape this occupation. Consider both
direct automation of tasks and indirect effects where AI greatly amplifies the
productivity of fewer workers.

Use these anchors:
- 0-1: almost entirely physical or location-bound work with negligible AI impact
- 2-3: mostly physical or interpersonal work; AI only helps at the edges
- 4-5: mixed work; AI can assist with meaningful parts but not replace the core
- 6-7: mostly knowledge or workflow-heavy work; AI can materially change output
- 8-9: highly digital work; AI is likely to restructure the occupation
- 10: routine digital information processing with minimal physical component

Respond with ONLY a JSON object:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences>"
}\
"""


def parse_model_content(content: str) -> dict[str, object]:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    return json.loads(content)


def resolve_model_name(cli_model: str | None, env_model: str | None) -> str:
    return cli_model or env_model or DEFAULT_MODEL


def score_with_retries(callable_fn, max_retries: int, retry_delay: float) -> dict[str, object]:
    attempts = 0
    while True:
        try:
            return callable_fn()
        except Exception:
            if attempts >= max_retries:
                raise
            attempts += 1
            time.sleep(retry_delay)


def score_occupation(text: str, model: str) -> dict[str, object]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
    }
    request = Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    return parse_model_content(content)


def load_occupations() -> list[dict[str, object]]:
    return json.loads(OCCUPATIONS_PATH.read_text())


def load_scores(force: bool) -> dict[str, dict[str, object]]:
    if not OUTPUT_PATH.exists() or force:
        return {}
    rows = json.loads(OUTPUT_PATH.read_text())
    return {row["slug"]: row for row in rows}


def refresh_site_data() -> None:
    spec = importlib.util.spec_from_file_location("india_build_site_data", BUILD_SITE_DATA_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load build_site_data module from {BUILD_SITE_DATA_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    parser.add_argument("--max-retries", type=int, default=20)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    model = resolve_model_name(args.model, os.environ.get(DEFAULT_MODEL_ENV))
    occupations = load_occupations()[args.start : args.end]
    scores = load_scores(args.force)
    errors: list[str] = []

    print(f"Scoring {len(occupations)} India occupations with {model}")
    print(f"Already cached: {len(scores)}")

    for index, occupation in enumerate(occupations, start=1):
        slug = occupation["slug"]
        if slug in scores:
            continue

        page_path = PAGES_DIR / f"{slug}.md"
        if not page_path.exists():
            print(f"  [{index}] SKIP {slug} (no markdown)")
            continue

        text = page_path.read_text()
        print(f"  [{index}/{len(occupations)}] {occupation['title']}...", end=" ", flush=True)
        try:
            result = score_with_retries(
                lambda: score_occupation(text, model),
                max_retries=args.max_retries,
                retry_delay=args.retry_delay,
            )
            scores[slug] = {
                "slug": slug,
                "title": occupation["title"],
                **result,
            }
            print(f"exposure={result['exposure']}")
            OUTPUT_PATH.write_text(json.dumps(list(scores.values()), indent=2))
            refresh_site_data()
        except Exception as exc:
            print(f"ERROR: {exc}")
            errors.append(slug)

        if index < len(occupations):
            time.sleep(args.delay)

    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
