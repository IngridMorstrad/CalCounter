#!/usr/bin/env python3
"""Inventory dependencies and verify repository resolution from isolated caches.

The report is intentionally safe to run before the Android build migration. It
parses the committed Gradle files and source imports, then runs the committed
wrapper twice with a fresh GRADLE_USER_HOME for each run. Resolution failures
and policy violations are retained as explicit blockers rather than being
hidden by the developer's existing Gradle cache.
"""

from __future__ import annotations

import argparse
import datetime as datetime_module
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

REPORT_DIR = Path("build/reports/android-upgrade")
INVENTORY_REPORT = REPORT_DIR / "dependency-inventory.json"
RESOLUTION_REPORT = REPORT_DIR / "dependency-resolution.json"

DECLARATION_RE = re.compile(
    r"^\s*(implementation|api|compileOnly|runtimeOnly|annotationProcessor|"
    r"testImplementation|testRuntimeOnly|androidTestImplementation|classpath)\s+"
    r"['\"]([^'\"]+)['\"]"
)
MAP_DECLARATION_RE = re.compile(
    r"^\s*(implementation|api|compileOnly|runtimeOnly|annotationProcessor|"
    r"testImplementation|testRuntimeOnly|androidTestImplementation|classpath)\s+"
    r"group:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*"
    r"version:\s*['\"]([^'\"]+)['\"]"
)
COORDINATE_RE = re.compile(r"^[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+:[^\s]+$")
GRAPH_COORDINATE_RE = re.compile(r"(?:\+---|\\---)\s+([^\s()]+)")
URL_HOST_RE = re.compile(r"https?://([^/\s\]>)]+)", re.IGNORECASE)
SECRET_RE = re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*[^\s]+")

REPOSITORY_PATTERNS = (
    (re.compile(r"\bgoogle\s*\(\s*\)", re.IGNORECASE), "google()"),
    (re.compile(r"\bmavenCentral\s*\(\s*\)", re.IGNORECASE), "mavenCentral()"),
    (re.compile(r"\bjcenter\s*\(\s*\)", re.IGNORECASE), "jcenter()"),
    (re.compile(r"https?://jitpack\.io", re.IGNORECASE), "https://jitpack.io"),
    (re.compile(r"https?://[^\s\"']+", re.IGNORECASE), "custom URL"),
)


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def redact(text: str, root: Path) -> str:
    value = text.replace(str(root), "<repo>").replace(str(Path.home()), "<home>")
    return SECRET_RE.sub(r"\1=<redacted>", value)


def git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def source_files(root: Path) -> list[Path]:
    source_roots = [
        root / "app" / "src" / "main",
        root / "app" / "src" / "test",
        root / "app" / "src" / "androidTest",
    ]
    return sorted(
        path
        for source_root in source_roots
        if source_root.exists()
        for path in source_root.rglob("*")
        if path.is_file() and path.suffix in {".java", ".kt"}
    )


def repository_declarations(root: Path) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.gradle")) + [root / "app" / "build.gradle"]:
        if not path.exists():
            continue
        for line_number, line in enumerate(read_text(path).splitlines(), 1):
            for pattern, repository in REPOSITORY_PATTERNS:
                if pattern.search(line):
                    if repository == "custom URL" and re.search(r"https?://jitpack\.io", line, re.IGNORECASE):
                        continue
                    declarations.append(
                        {
                            "file": relative(root, path),
                            "line": line_number,
                            "repository": repository,
                            "approved": repository in {"google()", "mavenCentral()", "https://jitpack.io"},
                            "jitpack_conditional": repository == "https://jitpack.io",
                        }
                    )
    return declarations


def dependency_family(group: str, name: str) -> str:
    if group == "androidx.room":
        return "room"
    if group == "androidx.appcompat":
        return "appcompat"
    if group == "com.google.android.material":
        return "material"
    if group == "commons-io":
        return "commons-io"
    if group == "com.github.PhilJay" and name == "MPAndroidChart":
        return "mpandroidchart"
    if group == "org.projectlombok":
        return "lombok"
    if group == "junit":
        return "junit"
    if group == "com.android.tools.build":
        return "android-gradle-plugin"
    return "other"


def parse_coordinate(coordinate: str) -> tuple[str | None, str | None, str | None]:
    parts = coordinate.split(":", 2)
    return (parts + [None, None, None])[:3] if len(parts) >= 3 else (None, None, None)


def candidate_repositories(group: str | None) -> list[str]:
    if not group:
        return []
    if group.startswith("com.github."):
        return ["https://jitpack.io"]
    if group.startswith(("androidx.", "com.android.", "com.google.android.")):
        return ["google()"]
    if group in {"junit", "commons-io", "org.projectlombok"}:
        return ["mavenCentral()"]
    return ["google()", "mavenCentral()"]


def repository_verification_entries(dependencies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for dependency in dependencies:
        if dependency["declaration_kind"] != "coordinate":
            continue
        entries.append(
            {
                "coordinate": dependency["coordinate"],
                "family": dependency["family"],
                "candidate_repositories": dependency["candidate_repositories"],
                "status": "not_verified",
                "reason": "The legacy Gradle build could not produce a dependency graph; see dependency-resolution.json blockers.",
            }
        )
    return entries


def parse_dependencies(root: Path) -> list[dict[str, Any]]:
    declarations: list[dict[str, Any]] = []
    paths = [root / "build.gradle", root / "settings.gradle", root / "app" / "build.gradle"]
    for path in paths:
        if not path.exists():
            continue
        for line_number, line in enumerate(read_text(path).splitlines(), 1):
            map_match = MAP_DECLARATION_RE.match(line)
            quoted_match = DECLARATION_RE.match(line)
            if map_match:
                configuration, group, name, version = map_match.groups()
                coordinate = f"{group}:{name}:{version}"
            elif quoted_match:
                configuration, coordinate = quoted_match.groups()
                group, name, version = parse_coordinate(coordinate)
            elif re.search(r"\bimplementation\s+fileTree\s*\(", line):
                declarations.append(
                    {
                        "file": relative(root, path),
                        "line": line_number,
                        "configuration": "implementation",
                        "coordinate": "app/libs/*.jar",
                        "group": None,
                        "name": None,
                        "version": None,
                        "family": "local-library",
                        "candidate_repositories": [],
                        "declaration_kind": "fileTree",
                    }
                )
                continue
            else:
                continue
            group, name, version = parse_coordinate(coordinate)
            declarations.append(
                {
                    "file": relative(root, path),
                    "line": line_number,
                    "configuration": configuration,
                    "coordinate": coordinate,
                    "group": group,
                    "name": name,
                    "version": version,
                    "family": dependency_family(group or "", name or ""),
                    "candidate_repositories": candidate_repositories(group),
                    "declaration_kind": "coordinate",
                    "dynamic_or_placeholder": bool(
                        version and ("$" in version or "latest" in version.lower() or version in {"+", "*"})
                    ),
                }
            )
    return declarations


def source_usage(root: Path) -> dict[str, Any]:
    patterns = {
        "room_core": re.compile(r"androidx\.room\.", re.IGNORECASE),
        "room_rxjava2": re.compile(r"(?:androidx\.room\.rxjava2|io\.reactivex|rxjava)", re.IGNORECASE),
        "room_guava": re.compile(r"(?:androidx\.room\.guava|com\.google\.common\.util\.concurrent|ListenableFuture|Guava)", re.IGNORECASE),
        "lombok": re.compile(r"\blombok\.", re.IGNORECASE),
        "mpandroidchart": re.compile(r"com\.github\.mikephil\.charting", re.IGNORECASE),
        "commons_io": re.compile(r"org\.apache\.commons\.io|commons\.io", re.IGNORECASE),
        "appcompat": re.compile(r"androidx\.appcompat", re.IGNORECASE),
        "material": re.compile(r"com\.google\.android\.material", re.IGNORECASE),
    }
    result: dict[str, Any] = {}
    for usage_name, pattern in patterns.items():
        matches = []
        for path in source_files(root):
            for line_number, line in enumerate(read_text(path).splitlines(), 1):
                if pattern.search(line):
                    matches.append({"file": relative(root, path), "line": line_number})
        result[usage_name] = {"used": bool(matches), "references": matches}
    result["room_optional_module_decisions"] = {
        "room-rxjava2": {
            "used": result["room_rxjava2"]["used"],
            "decision": "retained-if-resolution-succeeds" if result["room_rxjava2"]["used"] else "source-usage-not-found; candidate-for-removal-after-approval",
        },
        "room-guava": {
            "used": result["room_guava"]["used"],
            "decision": "retained-if-resolution-succeeds" if result["room_guava"]["used"] else "source-usage-not-found; candidate-for-removal-after-approval",
        },
        "lombok": {
            "used": result["lombok"]["used"],
            "annotation_processing_required": result["lombok"]["used"],
            "decision": "annotationProcessor-required-by-source-imports" if result["lombok"]["used"] else "no-source-usage-found",
        },
    }
    return result


def inventory(root: Path) -> dict[str, Any]:
    dependencies = parse_dependencies(root)
    repositories = repository_declarations(root)
    usage = source_usage(root)
    blockers: list[dict[str, Any]] = []
    if any(item["repository"] == "jcenter()" for item in repositories):
        blockers.append(
            {
                "id": "unapproved-repository-jcenter",
                "severity": "release-blocker",
                "message": "jcenter() is declared and is not an approved repository for the upgrade.",
                "evidence": [item for item in repositories if item["repository"] == "jcenter()"],
            }
        )
    dynamic = [item for item in dependencies if item.get("dynamic_or_placeholder")]
    if dynamic:
        blockers.append(
            {
                "id": "dynamic-or-placeholder-dependency-version",
                "severity": "release-blocker",
                "message": "A dependency declaration uses a dynamic or unresolved version placeholder.",
                "evidence": dynamic,
            }
        )
    jitpack_dependencies = [item["coordinate"] for item in dependencies if (item.get("group") or "").startswith("com.github.")]
    return {
        "report_schema": "android-upgrade-dependency-inventory/v1",
        "generated_at_utc": datetime_module.datetime.now(datetime_module.timezone.utc).replace(microsecond=0).isoformat(),
        "source_revision": git_value(root, "rev-parse", "HEAD"),
        "scope": {
            "database_contents_read": False,
            "personal_data_collected": False,
            "generated_artifacts_read": False,
            "source_usage_roots": ["app/src/main", "app/src/test", "app/src/androidTest"],
        },
        "repositories": {
            "declarations": repositories,
            "approved_policy": ["google()", "mavenCentral()", "https://jitpack.io only when verified required"],
            "configured_jitpack_candidate_dependencies": jitpack_dependencies,
            "dependency_assignments": repository_verification_entries(dependencies),
        },
        "direct_dependencies": dependencies,
        "dependency_family_summary": {
            family: sorted({item["coordinate"] for item in dependencies if item["family"] == family})
            for family in sorted({str(item["family"]) for item in dependencies})
        },
        "source_usage": usage,
        "transitive_resolution": {
            "status": "pending-isolated-cache-runs",
            "report": RESOLUTION_REPORT.as_posix(),
        },
        "blockers": blockers,
    }


def normalized_graph(output: str) -> list[str]:
    coordinates = set()
    for match in GRAPH_COORDINATE_RE.finditer(output):
        coordinate = match.group(1).rstrip(",")
        if COORDINATE_RE.match(coordinate):
            coordinates.add(coordinate)
    return sorted(coordinates)


def observed_hosts(output: str) -> list[str]:
    return sorted({match.group(1).lower().rstrip(".,") for match in URL_HOST_RE.finditer(output)})


def repository_from_hosts(hosts: Iterable[str]) -> list[str]:
    repositories = set()
    tool_hosts = {"services.gradle.org", "docs.gradle.org", "help.gradle.org", "gnu.org"}
    for host in hosts:
        if host in tool_hosts:
            continue
        if "jitpack.io" in host:
            repositories.add("https://jitpack.io")
        elif "jcenter" in host or "bintray.com" in host:
            repositories.add("jcenter()")
        elif "google" in host or "dl.google.com" in host:
            repositories.add("google()")
        elif "maven.org" in host or "repo1.maven" in host:
            repositories.add("mavenCentral()")
        else:
            repositories.add(f"unclassified:{host}")
    return sorted(repositories)


def run_command(root: Path, cache: Path, command: list[str], output_path: Path, timeout: int) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["GRADLE_USER_HOME"] = str(cache)
    rendered = " ".join(command)
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=timeout,
        )
        output = redact(completed.stdout or "", root)
        exit_code = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        output = redact((exc.stdout or "") if isinstance(exc.stdout, str) else "", root)
        output += "\n[command timed out]\n"
        exit_code = 124
        timed_out = True
    except OSError as exc:
        output = redact(f"[command unavailable: {exc}]", root)
        exit_code = 127
        timed_out = False
    output_path.write_text(output, encoding="utf-8")
    graph = normalized_graph(output)
    hosts = observed_hosts(output)
    return {
        "command": rendered,
        "exit_code": exit_code,
        "succeeded": exit_code == 0,
        "timed_out": timed_out,
        "output_file": output_path.relative_to(root).as_posix(),
        "normalized_graph_count": len(graph),
        "normalized_graph_sha256": hashlib.sha256("\n".join(graph).encode()).hexdigest(),
        "normalized_graph": graph,
        "observed_url_hosts": hosts,
        "observed_repositories": repository_from_hosts(hosts),
    }


def resolution_run(root: Path, report_root: Path, run_number: int, timeout: int) -> dict[str, Any]:
    run_root = report_root / f"resolution-run-{run_number}"
    cache = run_root / "gradle-user-home"
    if run_root.exists():
        shutil.rmtree(run_root)
    run_root.mkdir(parents=True)
    cache.mkdir()
    initial_cache_entries = sorted(path.name for path in cache.iterdir())
    wrapper = root / "gradlew"
    wrapper_command = ["./gradlew"] if os.access(wrapper, os.X_OK) else ["bash", "./gradlew"]
    command_prefix = wrapper_command + [
        "--no-daemon",
        "--refresh-dependencies",
        "--console=plain",
        "--stacktrace",
        "--warning-mode",
        "all",
    ]
    commands = [
        wrapper_command + ["--version"],
        command_prefix + [":app:dependencies", "--configuration", "debugRuntimeClasspath"],
        command_prefix + [":app:dependencies", "--configuration", "debugCompileClasspath"],
        command_prefix + [":app:dependencies", "--configuration", "annotationProcessor"],
        command_prefix + [":app:dependencyInsight", "--dependency", "androidx.room", "--configuration", "debugRuntimeClasspath"],
        command_prefix + [":app:dependencyInsight", "--dependency", "com.github.PhilJay:MPAndroidChart", "--configuration", "debugRuntimeClasspath"],
    ]
    commands_report = []
    for index, command in enumerate(commands, 1):
        output_path = run_root / f"command-{index}.log"
        commands_report.append(run_command(root, cache, command, output_path, timeout))
    graph_commands = [item for item in commands_report if item["normalized_graph"]]
    combined_graph = sorted({coordinate for item in graph_commands for coordinate in item["normalized_graph"]})
    return {
        "run": run_number,
        "wrapper_command": wrapper_command,
        "cache": {
            "path": str(cache.relative_to(root)),
            "was_empty_before_resolution": not initial_cache_entries,
            "initial_entries": initial_cache_entries,
        },
        "commands": commands_report,
        "combined_normalized_graph": combined_graph,
        "combined_graph_count": len(combined_graph),
        "combined_graph_sha256": hashlib.sha256("\n".join(combined_graph).encode()).hexdigest(),
        "observed_repositories": sorted({repository for item in commands_report for repository in item["observed_repositories"]}),
        "successful_resolution_commands": sum(1 for item in commands_report if item["succeeded"]),
        "failed_resolution_commands": sum(1 for item in commands_report if not item["succeeded"]),
    }


def resolution_report(root: Path, report_root: Path, inventory_report: dict[str, Any], timeout: int) -> dict[str, Any]:
    run_one = resolution_run(root, report_root, 1, timeout)
    run_two = resolution_run(root, report_root, 2, timeout)
    blockers: list[dict[str, Any]] = list(inventory_report["blockers"])
    for run in (run_one, run_two):
        for command in run["commands"]:
            if not command["succeeded"]:
                blockers.append(
                    {
                        "id": "isolated-dependency-resolution-failed",
                        "severity": "release-blocker",
                        "message": "A dependency/toolchain resolution command failed in an empty isolated Gradle cache.",
                        "run": run["run"],
                        "command": command["command"],
                        "exit_code": command["exit_code"],
                        "diagnostics": command["output_file"],
                    }
                )
    if run_one["combined_graph_sha256"] != run_two["combined_graph_sha256"]:
        blockers.append(
            {
                "id": "isolated-dependency-graphs-differ",
                "severity": "release-blocker",
                "message": "The two isolated-cache dependency graphs are not identical.",
                "run_one_graph_sha256": run_one["combined_graph_sha256"],
                "run_two_graph_sha256": run_two["combined_graph_sha256"],
            }
        )
    observed = sorted(set(run_one["observed_repositories"] + run_two["observed_repositories"]))
    unapproved_observed = [item for item in observed if item.startswith("unclassified:") or item == "jcenter()"]
    if unapproved_observed:
        blockers.append(
            {
                "id": "unapproved-resolution-repository",
                "severity": "release-blocker",
                "message": "Dependency resolution observed an unapproved or unclassified repository host.",
                "repositories": unapproved_observed,
            }
        )
    return {
        "report_schema": "android-upgrade-dependency-resolution/v1",
        "generated_at_utc": datetime_module.datetime.now(datetime_module.timezone.utc).replace(microsecond=0).isoformat(),
        "source_revision": git_value(root, "rev-parse", "HEAD"),
        "wrapper": run_one["wrapper_command"],
        "isolation": {
            "runs": 2,
            "refresh_dependencies": True,
            "cache_policy": "each run starts with a newly-created empty GRADLE_USER_HOME",
            "personal_data_collected": False,
        },
        "runs": [run_one, run_two],
        "comparison": {
            "graphs_identical": run_one["combined_graph_sha256"] == run_two["combined_graph_sha256"],
            "run_one_graph_sha256": run_one["combined_graph_sha256"],
            "run_two_graph_sha256": run_two["combined_graph_sha256"],
            "observed_repositories": observed,
        },
        "blockers": blockers,
        "status": "blocked" if blockers else "passed",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", help="repository root; defaults to the parent of tools/android-upgrade")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="timeout for each Gradle command")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    report_root = root / REPORT_DIR
    report_root.mkdir(parents=True, exist_ok=True)

    inventory_report = inventory(root)
    (root / INVENTORY_REPORT).write_text(json.dumps(inventory_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    resolution = resolution_report(root, report_root, inventory_report, args.timeout_seconds)
    (root / RESOLUTION_REPORT).write_text(json.dumps(resolution, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {INVENTORY_REPORT}")
    print(f"Wrote {RESOLUTION_REPORT}")
    print(f"Direct coordinate declarations: {len(inventory_report['direct_dependencies'])}")
    print(f"Source-used Room RxJava2: {inventory_report['source_usage']['room_rxjava2']['used']}")
    print(f"Source-used Room Guava: {inventory_report['source_usage']['room_guava']['used']}")
    print(f"Lombok annotation processing required: {inventory_report['source_usage']['room_optional_module_decisions']['lombok']['annotation_processing_required']}")
    print(f"Resolution status: {resolution['status']}; blockers: {len(resolution['blockers'])}")
    return 0 if resolution["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
