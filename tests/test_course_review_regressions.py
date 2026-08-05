from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, diagnostic: str) -> None:
    if not condition:
        raise RuntimeError(diagnostic)


def main() -> int:
    day1 = read("docs/day_01.md")
    require("NASM source → assembler → object" in day1, "REVIEW-DAY01-NASM-PIPELINE")
    require("C++ source → compiler" in day1, "REVIEW-DAY01-CPP-COMPILER")
    require(
        "расположить этапы `source → assembler → object" not in day1,
        "REVIEW-DAY01-AMBIGUOUS-SOURCE-PIPELINE",
    )

    day13 = read("docs/day_13.md")
    require("uint32_t x" in day13, "REVIEW-DAY13-UNSIGNED-INPUT")
    require(
        "x = 0x80000000" in day13 and "x = 0xFFFFFFFF" in day13,
        "REVIEW-DAY13-BOUNDARIES",
    )
    require(
        "int result = 0;\nwhile (x != 0)" not in day13,
        "REVIEW-DAY13-SIGNED-POPCOUNT",
    )

    day19 = read("docs/day_19.md")
    require("unsigned short flags" in day19, "REVIEW-DAY19-UNSIGNED-FLAGS")
    require("movzx esi, word [eax+8]" in day19, "REVIEW-DAY19-MOVZX-PAIR")
    require(
        "struct SignedItem" in day19 and "movsx esi, word [eax+8]" in day19,
        "REVIEW-DAY19-SIGNED-PAIR",
    )
    require(
        "plain `char`" in day19 and "зависит от реализации" in day19,
        "REVIEW-DAY19-PLAIN-CHAR",
    )

    day21 = read("docs/day_21.md")
    require("R → чтение" in day21 and "X → исполнение" in day21, "REVIEW-DAY21-PERMISSIONS")
    require(
        "разрешение относится к конкретным страницам" in day21,
        "REVIEW-DAY21-MAPPING-BOUNDARY",
    )
    require(
        "куча или стек по своей природе никогда не могут исполняться" in day21,
        "REVIEW-DAY21-NEGATIVE-EXAMPLE",
    )

    day22 = read("docs/day_22.md")
    require("absoluteEpsilon" in day22 and "relativeEpsilon" in day22, "REVIEW-DAY22-SCALE")
    require(
        "std::max(std::abs(x), std::abs(y))" in day22,
        "REVIEW-DAY22-COMBINED-COMPARISON",
    )
    require("Когда точное равенство допустимо" in day22, "REVIEW-DAY22-EXACT-EQUALITY")

    day24 = read("docs/day_24.md")
    require("разрешение адреса цели" in day24.lower(), "REVIEW-DAY24-TARGET-RESOLUTION")
    require(
        "mov ecx, [p]" in day24 and "call dword [eax]" in day24,
        "REVIEW-DAY24-THIS-CALL",
    )
    require(
        "выбирать адрес функции и забывать передать `this`" in day24,
        "REVIEW-DAY24-MISSING-THIS",
    )

    manifest = read("scripts/course_manifest.py")
    require('"docs/sources.md"' in manifest, "REVIEW-MANIFEST-SOURCES")
    require('"docs/modern_x86_64_next.md"' in manifest, "REVIEW-MANIFEST-X86-64")

    cases = json.loads(read("evals/ai_tutor_cases.json"))
    serialized = json.dumps(cases, ensure_ascii=False)
    require("_placeholder" not in serialized, "REVIEW-AI-PLACEHOLDER-HISTORY")

    package = json.loads(read("package.json"))
    scripts = package.get("scripts", {})
    require("course:review-regressions" in scripts, "REVIEW-PACKAGE-REGRESSION-SCRIPT")
    require("course:score" in scripts, "REVIEW-PACKAGE-SCORE-SCRIPT")

    print("COURSE_REVIEW_DAY01_PIPELINES=PASS")
    print("COURSE_REVIEW_DAY13_SIGNEDNESS=PASS")
    print("COURSE_REVIEW_DAY19_FIELD_TYPES=PASS")
    print("COURSE_REVIEW_DAY21_NX_PERMISSIONS=PASS")
    print("COURSE_REVIEW_DAY22_FLOAT_COMPARISON=PASS")
    print("COURSE_REVIEW_DAY24_THIS_CONTRACT=PASS")
    print("COURSE_REVIEW_STANDALONE_MANIFEST=PASS")
    print("COURSE_REVIEW_AI_HISTORY=PASS")
    print("COURSE_REVIEW_COMMAND_SURFACE=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
