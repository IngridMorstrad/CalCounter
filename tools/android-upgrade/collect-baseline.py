#!/usr/bin/env python3
"""Collect a redacted, reproducible baseline for the Android upgrade.

The collector intentionally records metadata and hashes instead of source or
user data. Its JSON report and command log live below build/, so they can be
uploaded by CI without adding generated files to the repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPORT_RELATIVE_PATH = Path("build/reports/android-upgrade/baseline.json")
LOG_RELATIVE_PATH = Path("build/reports/android-upgrade/baseline-collector.log")
BUILD_FILE_PATHS = (
    "build.gradle",
    "settings.gradle",
    "gradle.properties",
    "gradle/wrapper/gradle-wrapper.properties",
    "gradle/wrapper/gradle-wrapper.jar",
    "gradlew",
    "gradlew.bat",
    "app/build.gradle",
    "app/proguard-rules.pro",
    "app/src/main/AndroidManifest.xml",
)


class Collector:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.log_lines: list[str] = []
        self.report_dir = self.root / REPORT_RELATIVE_PATH.parent
        self.report_path = self.root / REPORT_RELATIVE_PATH
        self.log_path = self.root / LOG_RELATIVE_PATH
        self._home = Path.home().resolve()

    def redact(self, value: str) -> str:
        """Remove absolute local paths and likely secret values from output."""
        result = value.replace(str(self.root), "<repo>")
        result = result.replace(str(self._home), "<home>")
        result = re.sub(r"(?i)(password|secret|token|api[_-]?key)\s*[=:]\s*[^\s]+", r"\1=<redacted>", result)
        return result

    def command(self, args: Iterable[str], cwd: Path | None = None) -> tuple[int, str]:
        command = [str(arg) for arg in args]
        rendered = " ".join(shlex.quote(arg) for arg in command)
        self.log_lines.append(f"$ {rendered}")
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd or self.root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            output = self.redact(completed.stdout or "")
            if output:
                self.log_lines.extend(output.rstrip("\n").splitlines())
            self.log_lines.append(f"[exit {completed.returncode}]")
            return completed.returncode, output
        except OSError as exc:
            output = self.redact(str(exc))
            self.log_lines.append(output)
            self.log_lines.append("[exit unavailable]")
            return 127, output

    def read(self, relative_path: str) -> str:
        path = self.root / relative_path
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def file_metadata(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        result: dict[str, Any] = {"path": relative_path, "exists": path.exists()}
        if not path.exists() or not path.is_file():
            return result
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
                size += len(chunk)
        result.update({"bytes": size, "sha256": digest.hexdigest()})
        try:
            result["lines"] = path.read_text(encoding="utf-8").count("\n")
        except (OSError, UnicodeDecodeError):
            pass
        return result

    def git(self, *args: str) -> tuple[int, str]:
        return self.command(["git", *args])

    def git_value(self, *args: str) -> str | None:
        code, output = self.git(*args)
        if code != 0:
            return None
        return output.strip()

    def parse_status(self, output: str) -> list[dict[str, str]]:
        entries = []
        for line in output.splitlines():
            if len(line) < 3:
                continue
            entries.append({"index": line[0], "worktree": line[1], "path": line[3:]})
        return entries

    def parse_dependencies(self, text: str) -> list[str]:
        dependencies: list[str] = []
        quoted_pattern = re.compile(
            r"^\s*(?:implementation|api|compileOnly|annotationProcessor|testImplementation|androidTestImplementation)\s+['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )
        for match in quoted_pattern.finditer(text):
            if match.group(1) not in dependencies:
                dependencies.append(match.group(1))

        # Also capture the legacy Groovy map notation used by Commons IO.
        map_pattern = re.compile(
            r"^\s*(?:implementation|api|compileOnly|annotationProcessor|testImplementation|androidTestImplementation)\s+"
            r"group:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*version:\s*['\"]([^'\"]+)['\"]",
            re.MULTILINE,
        )
        for match in map_pattern.finditer(text):
            coordinate = ":".join(match.groups())
            if coordinate not in dependencies:
                dependencies.append(coordinate)
        return dependencies

    def parse_repositories(self, *texts: str) -> list[str]:
        found: list[str] = []
        patterns = (
            (r"\bgoogle\s*\(\s*\)", "google()"),
            (r"\bmavenCentral\s*\(\s*\)", "mavenCentral()"),
            (r"\bjcenter\s*\(\s*\)", "jcenter()"),
            (r"https://jitpack\.io", "https://jitpack.io"),
        )
        for text in texts:
            for pattern, label in patterns:
                if re.search(pattern, text) and label not in found:
                    found.append(label)
        return found

    def parse_wrapper_version(self, text: str) -> str | None:
        match = re.search(r"distributionUrl=.*?/gradle-([^-/]+)-[^/]+\.zip", text)
        return match.group(1) if match else None

    def parse_abi(self, text: str) -> dict[str, Any]:
        block_match = re.search(r"splits\s*\{\s*abi\s*\{(.*?)\n\s*}\s*}\s*", text, re.DOTALL)
        block = block_match.group(1) if block_match else ""
        include_match = re.search(r"include\s+([^\n]+)", block)
        include_values = re.findall(r"['\"]([^'\"]+)['\"]", include_match.group(1)) if include_match else []
        universal_match = re.search(r"universalApk\s+(true|false)", block)
        return {
            "manual_splits_configured": bool(block_match),
            "included_abis": include_values,
            "universal_apk": universal_match.group(1) == "true" if universal_match else None,
            "obsolete_abis_present": sorted(set(include_values) & {"armeabi", "mips", "mips64"}),
        }

    def parse_manifest(self, text: str) -> dict[str, Any]:
        activities = []
        for match in re.finditer(r"<activity\b([^>]*)>", text, re.DOTALL):
            attrs = match.group(1)
            name = re.search(r'android:name\s*=\s*["\']([^"\']+)', attrs)
            exported = re.search(r'android:exported\s*=\s*["\']([^"\']+)', attrs)
            activities.append(
                {
                    "name": name.group(1) if name else None,
                    "exported": exported.group(1) if exported else None,
                    "has_launcher_filter": bool(
                        re.search(r"<intent-filter>.*?MAIN.*?LAUNCHER.*?</intent-filter>", text, re.DOTALL)
                    )
                    if name and name.group(1).endswith("MainActivity")
                    else False,
                }
            )
        return {
            "package_attribute": re.search(r'<manifest[^>]*\bpackage\s*=\s*["\']([^"\']+)', text).group(1)
            if re.search(r'<manifest[^>]*\bpackage\s*=\s*["\']([^"\']+)', text)
            else None,
            "activities": activities,
            "activity_count": len(activities),
        }

    def source_files(self, relative_root: str, suffixes: tuple[str, ...]) -> list[str]:
        root = self.root / relative_root
        if not root.exists():
            return []
        return sorted(
            path.relative_to(self.root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.suffix in suffixes
        )

    def directory_files(self, relative_root: str) -> list[str]:
        root = self.root / relative_root
        if not root.exists():
            return []
        return sorted(path.relative_to(self.root).as_posix() for path in root.rglob("*") if path.is_file())

    def collect(self) -> dict[str, Any]:
        # Capture the source state before creating the report or log files.
        revision = self.git_value("rev-parse", "HEAD")
        branch = self.git_value("branch", "--show-current")
        status_code, status_output = self.git("status", "--porcelain=v1", "--untracked-files=all")
        diff_code, diff_output = self.git("diff", "--stat")
        staged_code, staged_output = self.git("diff", "--cached", "--stat")
        tracked_code, tracked_output = self.git("ls-files")

        root_build = self.read("build.gradle")
        settings = self.read("settings.gradle")
        app_build = self.read("app/build.gradle")
        wrapper = self.read("gradle/wrapper/gradle-wrapper.properties")
        manifest = self.read("app/src/main/AndroidManifest.xml")
        gradle_version_code, gradle_version_output = self.command(["./gradlew", "--version"])
        java_version_code, java_version_output = self.command(["java", "-version"])

        build_files = [self.file_metadata(path) for path in BUILD_FILE_PATHS]
        dependencies = self.parse_dependencies(app_build)
        repositories = self.parse_repositories(root_build, settings, app_build)
        module_matches = re.findall(r"(?:include|project)\s+['\"](:[^'\"]+)", settings)
        modules = sorted(set(module_matches))
        if not modules and re.search(r"include\s+['\"]:app['\"]", settings):
            modules = [":app"]

        workflow_files = self.directory_files(".github/workflows")
        github_files = self.directory_files(".github")
        app_lib_files = self.directory_files("app/libs")
        test_roots = [
            relative
            for relative in ("app/src/test", "app/src/androidTest")
            if (self.root / relative).exists()
        ]
        test_files = self.source_files("app/src", (".java", ".kt"))
        test_files = [path for path in test_files if "/test/" in f"/{path}" or "/androidTest/" in f"/{path}"]

        build_tools_match = re.search(r"buildToolsVersion\s+['\"]([^'\"]+)", app_build)
        compile_sdk_match = re.search(r"compileSdk(?:Version)?\s+([^\s]+)", app_build)
        target_sdk_match = re.search(r"targetSdk(?:Version)?\s+([^\s]+)", app_build)
        min_sdk_match = re.search(r"minSdk(?:Version)?\s+([^\s]+)", app_build)
        app_id_match = re.search(r"applicationId\s+['\"]([^'\"]+)", app_build)
        version_code_match = re.search(r"versionCode\s+([^\s]+)", app_build)
        version_name_match = re.search(r"versionName\s+['\"]([^'\"]+)", app_build)
        java8 = bool(re.search(r"(?:sourceCompatibility|targetCompatibility)\s+JavaVersion\.VERSION_1_8", app_build))
        build_types = re.findall(r"^\s*(debug|release)\s*\{", app_build, re.MULTILINE)
        signing_refs = sorted(set(re.findall(r"signingConfig\s+([^\s]+)|signingConfigs\.([A-Za-z0-9_]+)", app_build)))
        signing_config_refs = [".".join(item) if isinstance(item, tuple) else item for item in signing_refs]
        signing_config_refs = [item.strip(".") for item in signing_config_refs if item.strip(".")]

        report: dict[str, Any] = {
            "schema_version": 1,
            "collector": {
                "name": "android-upgrade-baseline",
                "version": "1.0.0",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "report_path": REPORT_RELATIVE_PATH.as_posix(),
                "command_log_path": LOG_RELATIVE_PATH.as_posix(),
            },
            "source_revision": {
                "commit": revision,
                "branch": branch,
                "git_commands_succeeded": all(code == 0 for code in (status_code, diff_code, staged_code, tracked_code)),
                "tracked_file_count": len(tracked_output.splitlines()) if tracked_code == 0 else None,
            },
            "working_tree": {
                "captured_before_report_generation": True,
                "status_entries": self.parse_status(status_output),
                "status_command_succeeded": status_code == 0,
                "unstaged_diff_stat": diff_output.strip(),
                "staged_diff_stat": staged_output.strip(),
                "note": "File contents are intentionally not embedded; status paths and diff statistics provide the pre-collection state.",
            },
            "environment": {
                "os": platform.system(),
                "os_release": platform.release(),
                "machine": platform.machine(),
                "python": sys.version.split()[0],
                "java_command_exit_code": java_version_code,
                "java_version_output": java_version_output.strip(),
                "gradle_wrapper_command_exit_code": gradle_version_code,
                "gradle_wrapper_output": gradle_version_output.strip(),
                "gradle_wrapper_version_from_properties": self.parse_wrapper_version(wrapper),
                "android_sdk_variables_present": {
                    name: bool(os.environ.get(name)) for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT")
                },
            },
            "project": {
                "module_count": len(modules),
                "modules": modules,
                "application_language": "Java",
                "persistence": "Room",
                "java_source_files": self.source_files("app/src/main/java", (".java",)),
                "room_source_files": self.source_files("app/src/main/java/com/ashwinmenon/www/calcounter/db", (".java",)),
            },
            "build_files": build_files,
            "build_configuration": {
                "agp_version_observed": re.search(r"com\.android\.tools\.build:gradle:([^'\"]+)", root_build).group(1)
                if re.search(r"com\.android\.tools\.build:gradle:([^'\"]+)", root_build)
                else None,
                "compile_sdk_observed": compile_sdk_match.group(1) if compile_sdk_match else None,
                "target_sdk_observed": target_sdk_match.group(1) if target_sdk_match else None,
                "min_sdk_observed": min_sdk_match.group(1) if min_sdk_match else None,
                "build_tools_observed": build_tools_match.group(1) if build_tools_match else None,
                "application_id_observed": app_id_match.group(1) if app_id_match else None,
                "namespace_observed": re.search(r"namespace\s+['\"]([^'\"]+)", app_build).group(1)
                if re.search(r"namespace\s+['\"]([^'\"]+)", app_build)
                else None,
                "java8_compatibility_observed": java8,
                "repositories_observed": repositories,
                "dependencies_observed": dependencies,
                "room_versions_observed": sorted(set(re.findall(r"androidx\.room:[^:'\"]+:([^'\"]+)", app_build))),
            },
            "variants": {
                "build_types_observed": sorted(set(build_types)),
                "variants_observed": sorted(set(build_types) | {"debug"}),
                "expected_variants": ["debug", "release"],
                "application_id": app_id_match.group(1) if app_id_match else None,
                "version_code": version_code_match.group(1) if version_code_match else None,
                "version_name": version_name_match.group(1) if version_name_match else None,
                "signing_configuration_references": signing_config_refs,
                "release_shrinking_observed": re.search(r"release\s*\{.*?minifyEnabled\s+(true|false)", app_build, re.DOTALL).group(1)
                if re.search(r"release\s*\{.*?minifyEnabled\s+(true|false)", app_build, re.DOTALL)
                else None,
            },
            "manifest": self.parse_manifest(manifest),
            "abi_configuration": self.parse_abi(app_build),
            "local_libraries": {
                "directory_present": (self.root / "app/libs").exists(),
                "files": app_lib_files,
                "personal_data_excluded": True,
            },
            "tests": {
                "roots": test_roots,
                "source_files": test_files,
                "test_file_count": len(test_files),
            },
            "ci": {
                "github_directory_present": (self.root / ".github").exists(),
                "visible_github_files": github_files,
                "workflow_files": workflow_files,
                "workflow_present": bool(workflow_files),
                "note": "No workflow is reported when .github/workflows has no files; funding/configuration files are not treated as workflows.",
            },
            "prior_known_values_unconfirmed": [
                {"name": "module", "value": ":app (one Java/Room module)"},
                {"name": "agp", "value": "4.1.1"},
                {"name": "gradle_wrapper", "value": "6.5"},
                {"name": "sdk_versions", "value": "compile 30 / target 30 / min 27"},
                {"name": "build_tools", "value": "29.0.2"},
                {"name": "java_compatibility", "value": "Java 8"},
                {"name": "repositories", "value": "google(), jcenter(), JitPack"},
                {"name": "legacy_dependencies", "value": "AppCompat 1.0.0; Material 1.0.0; Room 2.0.0 family; Lombok 1.18.12; Commons IO 2.6; MPAndroidChart v3.1.0; JUnit 4.12"},
                {"name": "abi_splits", "value": "x86, x86_64, armeabi, armeabi-v7a, mips, mips64, arm64-v8a; universalApk false"},
                {"name": "ci_workflows", "value": "none visible"},
            ],
            "privacy": {
                "database_contents_included": False,
                "food_names_included": False,
                "signing_secrets_included": False,
                "personal_data_included": False,
                "redaction": "Only metadata, paths, hashes, parsed configuration values, and command diagnostics are recorded.",
            },
        }
        return report

    def write(self, report: dict[str, Any]) -> None:
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.log_path.write_text("\n".join(self.log_lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", help="repository root; defaults to the parent of tools/android-upgrade")
    args = parser.parse_args()
    script_root = Path(__file__).resolve().parents[2]
    root = Path(args.repo_root).resolve() if args.repo_root else script_root
    collector = Collector(root)
    report = collector.collect()
    collector.write(report)
    print(f"Baseline report: {REPORT_RELATIVE_PATH.as_posix()}")
    print(f"Command log: {LOG_RELATIVE_PATH.as_posix()}")
    print(f"Source revision: {report['source_revision']['commit'] or 'unavailable'}")
    print(f"Working-tree entries: {len(report['working_tree']['status_entries'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
