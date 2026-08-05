from __future__ import annotations

import hashlib
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
PRODUCTION_CASES = ROOT / "evals" / "ai_tutor_cases.json"


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
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Какой один точный факт нужно проверить?",
                        }
                    }
                ],
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
    return subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fixture(temp_path: Path) -> tuple[Path, Path, Path]:
    fixture = ROOT / "tests" / "_ai_tutor_fixture.md"
    fixture.write_text("# fixture\n", encoding="utf-8")
    headings = [f"Fixture {index}" for index in range(1, 11)]
    prompts = temp_path / "prompts.md"
    prompts.write_text(
        "\n\n".join(
            f"## {heading}\n\n```text\nInstruction {index}\n\n"
            "<task>\nOLD\n</task>\n\n<chapter>\nOLD\n</chapter>\n\n"
            "<answer>\nOLD\n</answer>\n```"
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


def score_command(
    output: Path,
    adjudication: Path,
    behavior: Path,
    cases: Path,
    prompts: Path,
    *extra: str,
) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "score",
        str(output),
        str(adjudication),
        "--cases",
        str(cases),
        "--prompts",
        str(prompts),
        "--output",
        str(behavior),
        *extra,
    ]


def main() -> int:
    production_text = PRODUCTION_CASES.read_text(encoding="utf-8")
    require("_placeholder" not in production_text, "production AI histories still contain placeholders")

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    fixture: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="nasm-ai-eval-") as temp:
            temp_path = Path(temp)
            cases, prompts, fixture = write_fixture(temp_path)

            rejected_four = run(
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
                    "4",
                    "--dry-run",
                    "--output",
                    str(temp_path / "four.json"),
                ]
            )
            require(rejected_four.returncode != 0, "four provider runs were accepted")

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
            require(dry.returncode == 0, dry.stdout + dry.stderr)
            dry_data = json.loads(dry_output.read_text(encoding="utf-8"))
            require(
                dry_data["provider_execution_status"] == "DRY_RUN"
                and len(dry_data["results"]) == 30,
                "dry-run did not compile all 30 requests",
            )

            output = temp_path / "evidence.json"
            env = os.environ.copy()
            env["MOCK_KEY"] = "not-a-secret"
            revision = env.get("SOURCE_HEAD_SHA") or env.get("GITHUB_SHA") or "a" * 40
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
                    revision,
                ],
                env,
            )
            require(executed.returncode == 0, executed.stdout + executed.stderr)
            original_data = json.loads(output.read_text(encoding="utf-8"))
            require(original_data["provider_execution_status"] == "COMPLETE", "provider incomplete")
            require(original_data["semantic_adjudication_status"] == "NOT_RUN", "semantic overclaim")
            require(
                len(original_data["results"]) == 30 and Handler.calls == 30,
                f"expected 30 calls/results, got {Handler.calls}/{len(original_data['results'])}",
            )
            require(
                all(item["request_messages"][0]["role"] == "system" for item in original_data["results"]),
                "prompt was not placed into the system message",
            )

            validate_command = [
                sys.executable,
                str(SCRIPT),
                "validate",
                str(output),
                "--cases",
                str(cases),
                "--prompts",
                str(prompts),
            ]
            validated = run(validate_command, env)
            require(validated.returncode == 0, validated.stdout + validated.stderr)

            adjudication = temp_path / "adjudication.json"
            templated = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "template",
                    str(output),
                    "--cases",
                    str(cases),
                    "--prompts",
                    str(prompts),
                    "--output",
                    str(adjudication),
                ],
                env,
            )
            require(templated.returncode == 0, templated.stdout + templated.stderr)
            adjudication_data = json.loads(adjudication.read_text(encoding="utf-8"))
            for result in adjudication_data["case_results"]:
                for check in result["checks"]:
                    check["verdict"] = "PASS"
                    check["evidence"] = "checked against the captured response"

            adjudication_data["reviewer"] = {
                "kind": "manual",
                "id": "test-reviewer",
                "provider": None,
                "model": None,
                "evidence_sha256": None,
            }
            adjudication.write_text(json.dumps(adjudication_data), encoding="utf-8")
            behavior = temp_path / "behavior.json"
            scored = run(score_command(output, adjudication, behavior, cases, prompts), env)
            require(scored.returncode == 0, scored.stdout + scored.stderr)
            behavior_data = json.loads(behavior.read_text(encoding="utf-8"))
            require(behavior_data["behavioral_status"] == "PASS", "manual adjudication did not pass")
            require(
                behavior_data["threshold"] == "critical 3/3; others at least 2/3; exactly 3 runs per case",
                "reported threshold drifted from executable policy",
            )

            judge_evidence = temp_path / "judge-evidence.json"
            judge_evidence.write_text(
                json.dumps(
                    {
                        "provider": "judge-provider",
                        "model": "judge-model",
                        "judgments": [{"case_id": "AI-01", "result": "reviewed"}],
                    }
                ),
                encoding="utf-8",
            )
            independent = json.loads(json.dumps(adjudication_data))
            independent["reviewer"] = {
                "kind": "independent_model",
                "id": "judge-run-1",
                "provider": "judge-provider",
                "model": "judge-model",
                "evidence_sha256": sha256(judge_evidence),
            }
            adjudication.write_text(json.dumps(independent), encoding="utf-8")
            independent_score = run(
                score_command(
                    output,
                    adjudication,
                    behavior,
                    cases,
                    prompts,
                    "--judge-evidence",
                    str(judge_evidence),
                ),
                env,
            )
            require(independent_score.returncode == 0, independent_score.stdout + independent_score.stderr)
            require(
                json.loads(behavior.read_text(encoding="utf-8"))["judge_evidence_sha256"]
                == sha256(judge_evidence),
                "judge evidence digest was not preserved",
            )

            forged_judge = json.loads(json.dumps(independent))
            forged_judge["reviewer"]["evidence_sha256"] = "b" * 64
            adjudication.write_text(json.dumps(forged_judge), encoding="utf-8")
            forged_judge_score = run(
                score_command(
                    output,
                    adjudication,
                    behavior,
                    cases,
                    prompts,
                    "--judge-evidence",
                    str(judge_evidence),
                ),
                env,
            )
            require(forged_judge_score.returncode != 0, "forged judge digest was accepted")

            missing_judge = run(
                score_command(output, adjudication, behavior, cases, prompts),
                env,
            )
            require(missing_judge.returncode != 0, "independent score without judge file was accepted")

            self_judge = json.loads(json.dumps(independent))
            self_judge["reviewer"].update(
                {"provider": "openai-compatible", "model": "mock-model"}
            )
            adjudication.write_text(json.dumps(self_judge), encoding="utf-8")
            self_judged = run(
                score_command(
                    output,
                    adjudication,
                    behavior,
                    cases,
                    prompts,
                    "--judge-evidence",
                    str(judge_evidence),
                ),
                env,
            )
            require(self_judged.returncode != 0, "candidate model judged itself")

            incomplete = json.loads(json.dumps(adjudication_data))
            incomplete["case_results"][0]["checks"].pop()
            adjudication.write_text(json.dumps(incomplete), encoding="utf-8")
            incomplete_score = run(score_command(output, adjudication, behavior, cases, prompts), env)
            require(incomplete_score.returncode != 0, "incomplete adjudication topology was accepted")

            forged_data = json.loads(json.dumps(original_data))
            forged_data["results"][0]["request_messages"][0]["content"] += " forged"
            output.write_text(json.dumps(forged_data), encoding="utf-8")
            forged = run(validate_command, env)
            require(forged.returncode != 0, "forged request transcript was accepted")

            wrong_topology = json.loads(json.dumps(original_data))
            wrong_topology["results"][0]["case_id"] = "AI-UNKNOWN"
            output.write_text(json.dumps(wrong_topology), encoding="utf-8")
            topology = run(validate_command, env)
            require(topology.returncode != 0, "wrong case/run identity topology was accepted")

            too_many = json.loads(json.dumps(original_data))
            too_many["configuration"]["runs_per_case"] = 4
            output.write_text(json.dumps(too_many), encoding="utf-8")
            excessive = run(validate_command, env)
            require(excessive.returncode != 0, "more than three runs per case were accepted")

            too_few = json.loads(json.dumps(original_data))
            too_few["configuration"]["runs_per_case"] = 1
            too_few["results"] = [
                item for item in too_few["results"] if item["run_index"] == 1
            ]
            output.write_text(json.dumps(too_few), encoding="utf-8")
            insufficient = run(validate_command, env)
            require(insufficient.returncode != 0, "fewer than three runs per case were accepted")

            bad_provenance = json.loads(json.dumps(original_data))
            bad_provenance["provenance"]["adapter_sha256"] = "0" * 64
            output.write_text(json.dumps(bad_provenance), encoding="utf-8")
            provenance = run(validate_command, env)
            require(provenance.returncode != 0, "forged adapter provenance was accepted")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        if fixture is not None:
            fixture.unlink(missing_ok=True)

    print("AI_TUTOR_PROVIDER_DRY_RUN=PASS")
    print("AI_TUTOR_PROVIDER_MOCK_RUN=PASS")
    print("AI_TUTOR_PROVIDER_30_TRANSCRIPTS=PASS")
    print("AI_TUTOR_PROVIDER_EXACTLY_THREE_RUNS=ENFORCED")
    print("AI_TUTOR_PROVIDER_PROVENANCE_FORGERY=BLOCKED")
    print("AI_TUTOR_PROVIDER_SEMANTIC_OVERCLAIM=BLOCKED")
    print("AI_TUTOR_PROVIDER_IDENTITY_TOPOLOGY=PASS")
    print("AI_TUTOR_PROVIDER_ADAPTER_PROVENANCE=BOUND")
    print("AI_TUTOR_ADJUDICATION_TOPOLOGY=PASS")
    print("AI_TUTOR_ADJUDICATION_INCOMPLETE=BLOCKED")
    print("AI_TUTOR_SELF_JUDGE=BLOCKED")
    print("AI_TUTOR_JUDGE_FILE_DIGEST=BOUND")
    print("AI_TUTOR_PLACEHOLDER_HISTORY=BLOCKED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
