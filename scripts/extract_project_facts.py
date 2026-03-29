#!/usr/bin/env python3
"""
Extract thesis-friendly project facts from repository files.
Safe by default: local files only, no network calls.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover
    tomllib = None


DEFAULT_README_NAMES = ("README.md", "readme.md", "README.MD")
DEFAULT_REQUIREMENTS = ("requirements.txt", "requirements-dev.txt", "requirements-prod.txt")


def read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    for enc in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_text(errors="ignore")


def iter_project_files(root: Path, pattern: str) -> list[Path]:
    results: list[Path] = []
    for p in root.rglob(pattern):
        norm = str(p).replace("\\", "/")
        if any(seg in norm for seg in ("/.venv/", "/venv/", "/site-packages/", "/node_modules/", "/.git/")):
            continue
        results.append(p)
    return results


def relpath(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def parse_requirements_lines(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith(("-r", "--requirement")):
            continue
        raw = raw.split(" #", 1)[0].strip()
        if raw:
            rows.append(raw)
    return rows


def parse_pyproject_dependencies(pyproject_path: Path) -> list[str]:
    if not pyproject_path.exists() or tomllib is None:
        return []
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    deps: list[str] = []
    project_deps = data.get("project", {}).get("dependencies", [])
    if isinstance(project_deps, list):
        deps.extend([str(d).strip() for d in project_deps if str(d).strip()])

    opt_deps = data.get("project", {}).get("optional-dependencies", {})
    if isinstance(opt_deps, dict):
        for _, items in opt_deps.items():
            if isinstance(items, list):
                deps.extend([str(d).strip() for d in items if str(d).strip()])

    return deps


def parse_routes(urls_text: str) -> dict[str, list[str]]:
    page_routes: list[str] = []
    api_routes: list[str] = []
    other_routes: list[str] = []

    for m in re.finditer(r"(?:path|re_path)\(\s*['\"]([^'\"]+)['\"]", urls_text):
        route = m.group(1).strip()
        if not route:
            continue
        if route.startswith("api/"):
            api_routes.append(route)
        elif route in ("", "/"):
            other_routes.append("<root>")
        else:
            page_routes.append(route)

    return {
        "page_routes": sorted(set(page_routes)),
        "api_routes": sorted(set(api_routes)),
        "other_routes": sorted(set(other_routes)),
    }


def parse_models(models_text: str) -> list[str]:
    return re.findall(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\(\s*models\.Model\s*\):", models_text, flags=re.M)


def parse_key_functions(py_text: str) -> list[str]:
    hits: list[str] = []
    candidates = re.findall(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\(", py_text, flags=re.M)
    keywords = ("rag", "retrieve", "rewrite", "metric", "index", "vector", "embed", "search")
    for fn in candidates:
        lower = fn.lower()
        if any(k in lower for k in keywords):
            hits.append(fn)
    return sorted(set(hits))


def parse_metric_rows(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    metric_name_keys = (
        "recall",
        "precision",
        "top1",
        "f1",
        "latency",
        "准确率",
        "召回",
        "精确",
        "时延",
    )

    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        metric_name = cells[0]
        lower_name = metric_name.lower()
        if not any(k in lower_name for k in metric_name_keys):
            continue
        metrics[metric_name] = {
            "before": cells[1],
            "after": cells[2],
            "delta": cells[3],
        }

    sample_patterns = (
        r"Sample\s*count\s*[:：]\s*([0-9]+)",
        r"样本数\s*[:：]\s*([0-9]+)",
        r"总样本\s*[:：]\s*([0-9]+)",
    )
    for p in sample_patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            metrics["sample_count"] = m.group(1)
            break

    return metrics


def parse_settings_flags(text: str) -> dict[str, bool]:
    checks = {
        "has_debug_flag": r"\bDEBUG\b",
        "has_allowed_hosts": r"\bALLOWED_HOSTS\b",
        "has_database_config": r"\bDATABASES\b",
        "has_sqlite": r"django\.db\.backends\.sqlite3",
        "has_postgresql": r"django\.db\.backends\.postgresql",
        "llm_model_configurable": r"\bLLM_MODEL\b",
        "llm_base_url_configurable": r"\bLLM_BASE_URL\b",
    }
    return {k: bool(re.search(p, text)) for k, p in checks.items()}


def detect_capabilities(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {
        "has_async_pool": "threadpoolexecutor" in lower or "asyncio" in lower,
        "has_local_ocr": any(k in lower for k in ("pytesseract", "easyocr", "paddleocr", "ocrmypdf")),
        "has_vision_fallback": "vision" in lower and "ocr" in lower,
        "has_query_rewrite": "rewrite" in lower and "query" in lower,
        "has_rag_retrieval": "rag" in lower and ("retrieve" in lower or "retrieval" in lower),
    }


def detect_runtime(readme_text: str, settings_text: str, pyproject_text: str) -> str:
    blob = f"{readme_text}\n{settings_text}\n{pyproject_text}".lower()
    if "django" in blob:
        return "django"
    if "fastapi" in blob:
        return "fastapi"
    if "flask" in blob:
        return "flask"
    if "spring" in blob:
        return "spring"
    if "next.js" in blob or '"next"' in blob:
        return "nextjs"
    return "unknown"


def find_keyword_lines(text: str, keywords: list[str], max_hits: int = 8) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {}
    lines = text.splitlines()
    for kw in keywords:
        kw_hits: list[int] = []
        pattern = re.compile(re.escape(kw), flags=re.I)
        for idx, line in enumerate(lines, start=1):
            if pattern.search(line):
                kw_hits.append(idx)
                if len(kw_hits) >= max_hits:
                    break
        if kw_hits:
            hits[kw] = kw_hits
    return hits


def discover_primary_file(root: Path, names: tuple[str, ...]) -> Path | None:
    for name in names:
        p = root / name
        if p.exists():
            return p
    return None


def collect_doc_candidates(root: Path, docs_dir: str) -> dict[str, list[Path]]:
    docs_root = root / docs_dir
    if not docs_root.exists() or not docs_root.is_dir():
        return {"eval_docs": [], "readiness_docs": []}

    eval_docs: list[Path] = []
    readiness_docs: list[Path] = []

    for p in docs_root.rglob("*.md"):
        name = p.name.lower()
        if any(k in name for k in ("eval", "evaluation", "benchmark", "metric", "评测", "测评")):
            eval_docs.append(p)
        if any(k in name for k in ("readiness", "gap", "上线", "生产", "发布准备", "风险")):
            readiness_docs.append(p)

    return {"eval_docs": sorted(eval_docs), "readiness_docs": sorted(readiness_docs)}


def dedupe_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[Path] = set()
    for p in paths:
        if p in seen:
            continue
        seen.add(p)
        unique.append(p)
    return unique


def build_dependencies(root: Path) -> list[str]:
    deps: list[str] = []

    for req_name in DEFAULT_REQUIREMENTS:
        req_path = root / req_name
        deps.extend(parse_requirements_lines(read_text(req_path)))

    deps.extend(parse_pyproject_dependencies(root / "pyproject.toml"))

    # Keep order while de-duplicating.
    unique: list[str] = []
    seen: set[str] = set()
    for d in deps:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract project facts for thesis drafting.")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output", default="docs/thesis_facts.json", help="Output JSON path")
    parser.add_argument("--docs-dir", default="docs", help="Docs directory (relative to project root)")
    parser.add_argument("--max-route-samples", type=int, default=50, help="Max routes to keep in each category")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output = (root / args.output).resolve() if not Path(args.output).is_absolute() else Path(args.output).resolve()

    readme_path = discover_primary_file(root, DEFAULT_README_NAMES)
    settings_files = iter_project_files(root, "settings.py")
    url_files = iter_project_files(root, "urls.py")
    all_python_files = iter_project_files(root, "*.py")
    model_files = [p for p in all_python_files if p.name == "models.py" or "/models/" in str(p).replace("\\", "/")]
    view_files = [p for p in all_python_files if "/views" in str(p).replace("\\", "/")]
    service_files = [p for p in all_python_files if "/services" in str(p).replace("\\", "/")]

    model_files = dedupe_paths(model_files)
    view_files = dedupe_paths(view_files)
    service_files = dedupe_paths(service_files)

    docs = collect_doc_candidates(root, args.docs_dir)
    eval_docs = docs["eval_docs"]
    readiness_docs = docs["readiness_docs"]

    readme_text = read_text(readme_path) if readme_path else ""
    settings_text = "\n".join(read_text(p) for p in settings_files)
    urls_text = "\n".join(read_text(p) for p in url_files)
    models_text = "\n".join(read_text(p) for p in model_files)
    views_text = "\n".join(read_text(p) for p in view_files)
    services_text = "\n".join(read_text(p) for p in service_files)
    eval_text = "\n".join(read_text(p) for p in eval_docs)
    readiness_text = "\n".join(read_text(p) for p in readiness_docs)
    pyproject_text = read_text(root / "pyproject.toml")

    routes = parse_routes(urls_text)
    for key in ("page_routes", "api_routes", "other_routes"):
        routes[key] = routes[key][: max(0, args.max_route_samples)]

    model_names = parse_models(models_text)
    key_functions = parse_key_functions(f"{views_text}\n{services_text}")
    eval_metrics = parse_metric_rows(eval_text)

    readiness_flags = {
        "has_p0": bool(re.search(r"\bP0\b|P0级|高优先级", readiness_text, flags=re.I)),
        "has_p1": bool(re.search(r"\bP1\b|P1级|中优先级", readiness_text, flags=re.I)),
        "has_p2": bool(re.search(r"\bP2\b|P2级|低优先级", readiness_text, flags=re.I)),
    }

    source_files: list[Path] = []
    for seq in (
        [readme_path] if readme_path else [],
        settings_files,
        url_files,
        model_files,
        view_files,
        service_files,
        eval_docs,
        readiness_docs,
    ):
        source_files.extend(seq)

    # De-duplicate while preserving order.
    uniq_paths = dedupe_paths(source_files)

    evidence_index: list[dict[str, Any]] = []
    for p in uniq_paths[:30]:
        text = read_text(p)
        evidence_index.append(
            {
                "path": relpath(p, root),
                "line_count": len(text.splitlines()),
                "keyword_hits": find_keyword_lines(
                    text,
                    ["TODO", "FIXME", "rag", "rewrite", "evaluate", "benchmark", "security", "风险"],
                    max_hits=5,
                ),
            }
        )

    expected_paths = [
        root / "README.md",
        root / "docs",
        root / "requirements.txt",
    ]
    missing_expected = [relpath(p, root) for p in expected_paths if not p.exists()]

    dependencies = build_dependencies(root)

    data: dict[str, Any] = {
        "generated_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "project_name": root.name,
        "project_root": str(root),
        "runtime_summary": detect_runtime(readme_text, settings_text, pyproject_text),
        "dependencies": dependencies,
        "dependency_count": len(dependencies),
        "settings_flags": parse_settings_flags(settings_text),
        "routes": routes,
        "route_counts": {
            "page_routes": len(routes["page_routes"]),
            "api_routes": len(routes["api_routes"]),
            "other_routes": len(routes["other_routes"]),
        },
        "models": {
            "names": model_names,
            "count": len(model_names),
            "source_count": len(model_files),
        },
        "key_functions": key_functions,
        "capabilities": detect_capabilities(f"{views_text}\n{services_text}"),
        "evaluation": {
            "docs": [relpath(p, root) for p in eval_docs],
            "metrics": eval_metrics,
        },
        "readiness": {
            "docs": [relpath(p, root) for p in readiness_docs],
            **readiness_flags,
        },
        "evidence_index": evidence_index,
        "missing_expected_files": missing_expected,
        "source_files": [relpath(p, root) for p in uniq_paths],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote project facts to: {output}")
    print(
        "Summary: "
        f"runtime={data['runtime_summary']}, "
        f"deps={data['dependency_count']}, "
        f"models={data['models']['count']}, "
        f"key_functions={len(data['key_functions'])}, "
        f"routes(page/api)={data['route_counts']['page_routes']}/{data['route_counts']['api_routes']}"
    )

    if missing_expected:
        print("Missing common files:", ", ".join(missing_expected))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
