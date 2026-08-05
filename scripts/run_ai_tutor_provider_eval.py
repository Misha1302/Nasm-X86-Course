#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals/ai_tutor_cases.json"
PROMPTS = ROOT / "docs/ai_tutor_prompts.md"
BASE_URLS = {"openai": "https://api.openai.com/v1", "deepseek": "https://api.deepseek.com", "openai-compatible": None}
CRITICAL = {"AI-01-one-question", "AI-02-no-early-solution", "AI-03-ia32-boundary", "AI-06-third-failure-prerequisite", "AI-07-reverse-uncertainty", "AI-08-x87-order"}


class Error(RuntimeError):
    pass


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canon(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Error(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Error(f"expected JSON object: {path}")
    return value


def repo_file(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise Error(f"path escapes repository root: {relative}") from exc
    if not path.is_file():
        raise Error(f"missing fixture: {relative}")
    return path


def prompt_block(markdown: str, heading: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", markdown)
    if match is None:
        raise Error(f"missing prompt heading: {heading}")
    fence = re.search(r"(?s)```text\s*\n(.*?)\n```", match.group(1))
    if fence is None:
        raise Error(f"missing text fence under: {heading}")
    return fence.group(1).strip()


def replace_tag(text: str, tag: str, value: str) -> str:
    pattern = re.compile(rf"(?s)<{tag}>\s*.*?\s*</{tag}>")
    if len(pattern.findall(text)) != 1:
        raise Error(f"expected one <{tag}> block")
    return pattern.sub(f"<{tag}>\n{value}\n</{tag}>", text)


def compile_case(case: dict[str, Any], markdown: str) -> list[dict[str, str]]:
    block = prompt_block(markdown, str(case.get("prompt_heading")))
    chapters = case.get("chapter_files")
    if not isinstance(chapters, list) or not all(isinstance(item, str) for item in chapters):
        raise Error(f"invalid chapter_files: {case.get('id')}")
    chapter = "\n\n".join(f"<!-- source: {rel} -->\n{repo_file(rel).read_text(encoding='utf-8').strip()}" for rel in chapters) or "EMPTY"
    contract = case.get("input_contract")
    if not isinstance(contract, dict) or set(contract) != {"task", "answer"}:
        raise Error(f"invalid input_contract: {case.get('id')}")
    block = replace_tag(block, "task", str(contract["task"]))
    block = replace_tag(block, "chapter", chapter)
    block = replace_tag(block, "answer", str(contract["answer"]))
    turns = case.get("turns")
    if not isinstance(turns, list) or not turns:
        raise Error(f"missing turns: {case.get('id')}")
    messages = [{"role": "system", "content": block}]
    for index, turn in enumerate(turns):
        if not isinstance(turn, dict) or set(turn) != {"role", "content"} or turn["role"] not in {"user", "assistant"} or not isinstance(turn["content"], str):
            raise Error(f"invalid turn {index}: {case.get('id')}")
        messages.append({"role": turn["role"], "content": turn["content"]})
    return messages


def request(base_url: str, key: str, model: str, messages: list[dict[str, str]], args: argparse.Namespace, seed: int | None) -> dict[str, Any]:
    payload: dict[str, Any] = {"model": model, "messages": messages, args.token_limit_field: args.max_tokens}
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if seed is not None:
        payload["seed"] = seed
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=canon(payload),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Nasm-X86-Course-ai-eval/1.0"},
        method="POST",
    )
    last: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as response:
                body = json.loads(response.read().decode())
                status = response.status
            choices = body.get("choices") if isinstance(body, dict) else None
            message = choices[0].get("message") if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise Error("empty provider response")
            return {"http_status": status, "id": body.get("id"), "model": body.get("model"), "created": body.get("created"), "usage": body.get("usage"), "content": content}
        except urllib.error.HTTPError as exc:
            last = Error(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:1000]}")
            if exc.code not in {429, 500, 502, 503, 504}:
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, Error) as exc:
            last = exc
        if attempt < 3:
            time.sleep(attempt)
    raise Error(f"provider request failed: {last}")


def run_provider(args: argparse.Namespace) -> int:
    cases_path, prompts_path = Path(args.cases).resolve(), Path(args.prompts).resolve()
    cases_data = load(cases_path)
    cases = cases_data.get("cases")
    if not isinstance(cases, list) or len(cases) != 10:
        raise Error("exactly 10 cases are required")
    markdown = prompts_path.read_text(encoding="utf-8")
    base_url = args.base_url or BASE_URLS[args.provider]
    if not base_url:
        raise Error("--base-url is required")
    key = os.environ.get(args.api_key_env, "")
    if not key and not args.dry_run:
        raise Error(f"missing credential: {args.api_key_env}")
    report: dict[str, Any] = {
        "schema_version": "1.0", "run_id": str(uuid.uuid4()), "provider_execution_status": "DRY_RUN" if args.dry_run else "RUNNING",
        "semantic_adjudication_status": "NOT_RUN", "provider": args.provider, "model": args.model, "base_url": base_url,
        "source_revision": args.source_revision or os.getenv("SOURCE_HEAD_SHA") or os.getenv("GITHUB_SHA") or "UNKNOWN",
        "capture_started_at": now(), "capture_finished_at": None,
        "configuration": {"runs_per_case": args.runs, "temperature": args.temperature, "max_tokens": args.max_tokens, "token_limit_field": args.token_limit_field, "timeout_seconds": args.timeout, "seed_base": args.seed_base},
        "provenance": {"cases_path": str(cases_path), "cases_sha256": digest(cases_path), "prompts_path": str(prompts_path), "prompts_sha256": digest(prompts_path), "adapter_path": str(Path(__file__).resolve()), "adapter_sha256": digest(Path(__file__).resolve())},
        "results": [],
    }
    failures = 0
    for case in cases:
        case_id, messages = case.get("id"), compile_case(case, markdown)
        for index in range(args.runs):
            seed = args.seed_base + index if args.seed_base is not None else None
            item: dict[str, Any] = {"case_id": case_id, "run_index": index + 1, "seed": seed, "captured_at": now(), "request_messages": messages, "request_sha256": digest_bytes(canon(messages)), "response": None, "error": None}
            if args.dry_run:
                item["response"] = {"content": "DRY_RUN"}
            else:
                try:
                    item["response"] = request(base_url, key, args.model, messages, args, seed)
                except Error as exc:
                    failures += 1
                    item["error"] = str(exc)
            report["results"].append(item)
    report["capture_finished_at"] = now()
    report["provider_execution_status"] = "DRY_RUN" if args.dry_run else ("PARTIAL" if failures else "COMPLETE")
    output = Path(args.output).resolve()
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI_TUTOR_PROVIDER_EVIDENCE={output}")
    print(f"PROVIDER_EXECUTION_STATUS={report['provider_execution_status']}")
    print("SEMANTIC_ADJUDICATION_STATUS=NOT_RUN")
    return 1 if failures else 0


def validate_capture(args: argparse.Namespace) -> int:
    report = load(Path(args.evidence).resolve())
    errors: list[str] = []
    runs = report.get("configuration", {}).get("runs_per_case") if isinstance(report.get("configuration"), dict) else None
    results = report.get("results")
    if report.get("provider_execution_status") != "COMPLETE": errors.append("capture is not COMPLETE")
    if report.get("semantic_adjudication_status") != "NOT_RUN": errors.append("capture overclaims semantic adjudication")
    if not isinstance(runs, int) or runs < 1 or not isinstance(results, list) or len(results) != 10 * runs: errors.append("wrong result count")
    seen: set[tuple[Any, Any]] = set()
    for item in results if isinstance(results, list) else []:
        ident = (item.get("case_id"), item.get("run_index")) if isinstance(item, dict) else (None, None)
        if ident in seen: errors.append(f"duplicate result: {ident}")
        seen.add(ident)
        messages = item.get("request_messages") if isinstance(item, dict) else None
        content = item.get("response", {}).get("content") if isinstance(item, dict) and isinstance(item.get("response"), dict) else None
        if not isinstance(messages, list) or digest_bytes(canon(messages)) != item.get("request_sha256"): errors.append(f"request digest mismatch: {ident}")
        if not isinstance(content, str) or not content.strip() or content == "DRY_RUN": errors.append(f"missing live response: {ident}")
    if errors: raise Error("capture validation failed:\n- " + "\n- ".join(errors))
    print("AI_TUTOR_PROVIDER_CAPTURE=PASS")
    print("AI_TUTOR_SEMANTIC_ADJUDICATION=NOT_RUN")
    return 0


def template(args: argparse.Namespace) -> int:
    evidence_path = Path(args.evidence).resolve()
    evidence, cases_data = load(evidence_path), load(Path(args.cases).resolve())
    by_id = {case.get("id"): case for case in cases_data.get("cases", []) if isinstance(case, dict)}
    rows = []
    for item in evidence.get("results", []):
        case = by_id.get(item.get("case_id"))
        if not isinstance(case, dict): raise Error("evidence references unknown case")
        checks = [{"name": name, "polarity": "must", "verdict": "UNREVIEWED", "evidence": ""} for name in case.get("must", [])]
        checks += [{"name": name, "polarity": "must_not", "verdict": "UNREVIEWED", "evidence": ""} for name in case.get("must_not", [])]
        rows.append({"case_id": item.get("case_id"), "run_index": item.get("run_index"), "checks": checks, "notes": ""})
    value = {"schema_version": "1.0", "evidence_sha256": digest(evidence_path), "reviewer": {"kind": "UNSET", "id": "", "provider": None, "model": None}, "case_results": rows}
    output = Path(args.output).resolve(); output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI_TUTOR_ADJUDICATION_TEMPLATE={output}")
    return 0


def score(args: argparse.Namespace) -> int:
    evidence_path, adjudication_path = Path(args.evidence).resolve(), Path(args.adjudication).resolve()
    evidence, adjudication, cases_data = load(evidence_path), load(adjudication_path), load(Path(args.cases).resolve())
    if evidence.get("provider_execution_status") != "COMPLETE" or adjudication.get("evidence_sha256") != digest(evidence_path): raise Error("adjudication is not bound to complete evidence")
    reviewer = adjudication.get("reviewer")
    if not isinstance(reviewer, dict) or reviewer.get("kind") not in {"manual", "independent_model"} or not str(reviewer.get("id", "")).strip(): raise Error("invalid reviewer")
    if reviewer.get("kind") == "independent_model" and (not reviewer.get("provider") or not reviewer.get("model") or (reviewer.get("provider"), reviewer.get("model")) == (evidence.get("provider"), evidence.get("model"))): raise Error("independent reviewer must be a different identified model")
    cases = cases_data.get("cases"); by_id = {case.get("id"): case for case in cases if isinstance(case, dict)} if isinstance(cases, list) else {}
    expected = {(item.get("case_id"), item.get("run_index")) for item in evidence.get("results", []) if isinstance(item, dict)}
    rows = adjudication.get("case_results")
    actual = {(item.get("case_id"), item.get("run_index")) for item in rows if isinstance(item, dict)} if isinstance(rows, list) else set()
    if expected != actual or not isinstance(rows, list) or len(rows) != len(expected): raise Error("adjudication identities mismatch")
    per_case: dict[str, list[bool]] = {key: [] for key in by_id}; normalized = []
    for row in rows:
        case = by_id.get(row.get("case_id")); checks = row.get("checks")
        if not isinstance(case, dict) or not isinstance(checks, list): raise Error("invalid adjudication row")
        topology = [(name, "must") for name in case.get("must", [])] + [(name, "must_not") for name in case.get("must_not", [])]
        observed, verdicts = [], []
        for check in checks:
            observed.append((check.get("name"), check.get("polarity")))
            if check.get("verdict") not in {"PASS", "FAIL"} or len(str(check.get("evidence", "")).strip()) < 3: raise Error("unreviewed or unsupported check")
            verdicts.append(check["verdict"] == "PASS")
        if observed != topology: raise Error("check topology mismatch")
        passed = all(verdicts); per_case[row["case_id"]].append(passed); normalized.append({**row, "passed": passed})
    case_scores, overall = [], True
    for case_id, values in per_case.items():
        required = len(values) if case_id in CRITICAL else min(2, len(values)); passed = bool(values) and sum(values) >= required; overall &= passed
        case_scores.append({"case_id": case_id, "critical": case_id in CRITICAL, "passes": sum(values), "runs": len(values), "required_passes": required, "passed": passed})
    report = {"schema_version": "1.0", "behavioral_status": "PASS" if overall else "FAIL", "provider": evidence.get("provider"), "model": evidence.get("model"), "source_revision": evidence.get("source_revision"), "provider_evidence_sha256": digest(evidence_path), "adjudication_sha256": digest(adjudication_path), "reviewer": reviewer, "threshold": "critical 3/3; others at least 2/3", "case_scores": case_scores, "runs": normalized, "scored_at": now()}
    output = Path(args.output).resolve(); output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI_TUTOR_BEHAVIORAL_STATUS={report['behavioral_status']}")
    return 0 if overall else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run"); run.add_argument("--cases", default=str(CASES)); run.add_argument("--prompts", default=str(PROMPTS)); run.add_argument("--output", default="AI_TUTOR_PROVIDER_EVIDENCE.json"); run.add_argument("--provider", choices=sorted(BASE_URLS), required=True); run.add_argument("--model", required=True); run.add_argument("--base-url"); run.add_argument("--api-key-env", default="AI_TUTOR_API_KEY"); run.add_argument("--runs", type=int, default=3); run.add_argument("--temperature", type=float); run.add_argument("--max-tokens", type=int, default=700); run.add_argument("--token-limit-field", choices=("max_tokens", "max_completion_tokens"), default="max_tokens"); run.add_argument("--timeout", type=float, default=90); run.add_argument("--seed-base", type=int); run.add_argument("--source-revision"); run.add_argument("--dry-run", action="store_true"); run.set_defaults(handler=run_provider)
    validate = sub.add_parser("validate"); validate.add_argument("evidence"); validate.set_defaults(handler=validate_capture)
    make = sub.add_parser("template"); make.add_argument("evidence"); make.add_argument("--cases", default=str(CASES)); make.add_argument("--output", default="AI_TUTOR_ADJUDICATION.json"); make.set_defaults(handler=template)
    judge = sub.add_parser("score"); judge.add_argument("evidence"); judge.add_argument("adjudication"); judge.add_argument("--cases", default=str(CASES)); judge.add_argument("--output", default="AI_TUTOR_BEHAVIOR_REPORT.json"); judge.set_defaults(handler=score)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if getattr(args, "runs", 1) < 1: raise Error("--runs must be positive")
    return args.handler(args)


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Error as exc:
        print(str(exc), file=sys.stderr); raise SystemExit(2)
