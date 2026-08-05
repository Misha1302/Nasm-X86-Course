from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_ai_tutor_provider_eval.py"


class Handler(BaseHTTPRequestHandler):
    calls = 0

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        assert payload["messages"][0]["role"] == "system"
        Handler.calls += 1
        body = json.dumps(
            {
                "id": f"mock-{Handler.calls}",
                "created": 1,
                "model": payload["model"],
                "choices": [{"message": {"role": "assistant", "content": "Какой один точный факт нужно проверить?"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False, env=env)


def write_fixture(temp_path: Path) -> tuple[Path, Path, Path]:
    fixture = ROOT / "tests" / "_ai_tutor_fixture.md"
    fixture.write_text("# fixture\n", encoding="utf-8")
    headings = [f"Fixture {index}" for index in range(1, 11)]
    prompts = temp_path / "prompts.md"
    prompts.write_text(
        "\n\n".join(
            f"## {heading}\n\n```text\nInstruction {index}\n\n<task>\nOLD\n</task>\n\n<chapter>\nOLD\n</chapter>\n\n<answer>\nOLD\n</answer>\n```"
            for index, heading in enumerate(headings, start=1)
        )
        + "\n",
        encoding="utf-8",
    )
    cases = temp_path / "cases.json"
    cases.write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "provider_status": "NOT_RUN",
                "cases": [
                    {
                        "id": f"AI-{index:02d}",
                        "prompt_heading": heading,
                        "chapter_files": ["tests/_ai_tutor_fixture.md"],
                        "turns": [{"role": "user", "content": "EMPTY"}],
                        "must": ["ask_exactly_one_question"],
                        "must_not": ["ask_multiple_independent_questions"],
                        "input_contract": {"task": "task", "answer": "EMPTY"},
                    }
                    for index, heading in enumerate(headings, start=1)
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return cases, prompts, fixture


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    fixture: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="nasm-ai-eval-") as temp:
            temp_path = Path(temp)
            cases, prompts, fixture = write_fixture(temp_path)
            dry_output = temp_path / "dry.json"
            dry = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--cases",
                    str(cases),
                    "--prompts",
                    str(prompts),
                    "--provider",
                    "openai-compatible",
                    "--base-url",
                    "http://127.0.0.1:9/v1",
                    "--model",
                    "mock",
                    "--runs",
                    "3",
                    "--dry-run",
                    "--output",
                    str(dry_output),
                ]
            )
            if dry.returncode != 0:
                raise RuntimeError(dry.stdout + dry.stderr)
            dry_data = json.loads(dry_output.read_text(encoding="utf-8"))
            if dry_data["provider_execution_status"] != "DRY_RUN" or len(dry_data["results"]) != 30:
                raise RuntimeError("dry-run did not compile all 30 requests")

            output = temp_path / "evidence.json"
            env = os.environ.copy()
            env["MOCK_KEY"] = "not-a-secret"
            executed = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "run",
                    "--cases",
                    str(cases),
                    "--prompts",
                    str(prompts),
                    "--provider",
                    "openai-compatible",
                    "--base-url",
                    f"http://127.0.0.1:{server.server_port}/v1",
                    "--model",
                    "mock-model",
                    "--api-key-env",
                    "MOCK_KEY",
                    "--runs",
                    "3",
                    "--output",
                    str(output),
                    "--source-revision",
                    "a" * 40,
                ],
                env,
            )
            if executed.returncode != 0:
                raise RuntimeError(executed.stdout + executed.stderr)
            data = json.loads(output.read_text(encoding="utf-8"))
            if data["provider_execution_status"] != "COMPLETE":
                raise RuntimeError("provider execution did not complete")
            if data["semantic_adjudication_status"] != "NOT_RUN":
                raise RuntimeError("runner overclaimed semantic adjudication")
            if len(data["results"]) != 30 or Handler.calls != 30:
                raise RuntimeError(f"expected 30 calls/results, got {Handler.calls}/{len(data['results'])}")
            if any(item["request_messages"][0]["role"] != "system" for item in data["results"]):
                raise RuntimeError("prompt was not placed into the system message")
            validated = run([sys.executable, str(SCRIPT), "validate", str(output)], env)
            if validated.returncode != 0:
                raise RuntimeError(validated.stdout + validated.stderr)

            adjudication = temp_path / "adjudication.json"
            templated = run([
                sys.executable, str(SCRIPT), "template", str(output),
                "--cases", str(cases), "--output", str(adjudication),
            ], env)
            if templated.returncode != 0:
                raise RuntimeError(templated.stdout + templated.stderr)
            adjudication_data = json.loads(adjudication.read_text(encoding="utf-8"))
            adjudication_data["reviewer"] = {
                "kind": "manual", "id": "test-reviewer", "provider": None, "model": None
            }
            for result in adjudication_data["case_results"]:
                for check in result["checks"]:
                    check["verdict"] = "PASS"
                    check["evidence"] = "manually checked against the captured response"
            adjudication.write_text(json.dumps(adjudication_data), encoding="utf-8")
            behavior = temp_path / "behavior.json"
            scored = run([
                sys.executable, str(SCRIPT), "score", str(output), str(adjudication),
                "--cases", str(cases), "--output", str(behavior),
            ], env)
            if scored.returncode != 0:
                raise RuntimeError(scored.stdout + scored.stderr)
            behavior_data = json.loads(behavior.read_text(encoding="utf-8"))
            if behavior_data["behavioral_status"] != "PASS":
                raise RuntimeError("complete adjudication did not pass")

            bad_adjudication = json.loads(adjudication.read_text(encoding="utf-8"))
            bad_adjudication["case_results"][0]["checks"].pop()
            adjudication.write_text(json.dumps(bad_adjudication), encoding="utf-8")
            bad_score = run([
                sys.executable, str(SCRIPT), "score", str(output), str(adjudication),
                "--cases", str(cases), "--output", str(behavior),
            ], env)
            if bad_score.returncode == 0:
                raise RuntimeError("incomplete adjudication topology was accepted")

            data["results"][0]["request_messages"][0]["content"] += " forged"
            output.write_text(json.dumps(data), encoding="utf-8")
            forged = run([sys.executable, str(SCRIPT), "validate", str(output)], env)
            if forged.returncode == 0:
                raise RuntimeError("forged request transcript was accepted")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        if fixture is not None:
            fixture.unlink(missing_ok=True)

    print("AI_TUTOR_PROVIDER_DRY_RUN=PASS")
    print("AI_TUTOR_PROVIDER_MOCK_RUN=PASS")
    print("AI_TUTOR_PROVIDER_30_TRANSCRIPTS=PASS")
    print("AI_TUTOR_PROVIDER_PROVENANCE_FORGERY=BLOCKED")
    print("AI_TUTOR_PROVIDER_SEMANTIC_OVERCLAIM=BLOCKED")
    print("AI_TUTOR_ADJUDICATION_TOPOLOGY=PASS")
    print("AI_TUTOR_ADJUDICATION_INCOMPLETE=BLOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
