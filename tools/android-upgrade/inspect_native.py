#!/usr/bin/env python3
"""Inspect native libraries and ABIs used by the Android project.

The checker is intentionally independent of the Android/Gradle toolchain. It
scans local libraries, available Gradle dependency archives, and built APK/AAB
outputs. It never treats the ABI split list in app/build.gradle as evidence.
When any required evidence source is unavailable, the generated report is
blocked and the ABI split decision remains undetermined.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPORT_RELATIVE_PATH = Path("build/reports/android-upgrade/abi.json")
ARCHIVE_SUFFIXES = {".aar", ".apk", ".aab", ".jar", ".zip"}
NATIVE_SUFFIX = ".so"
OBSOLETE_ABIS = {"armeabi", "mips", "mips64"}
ABI_PATH_MARKERS = {"lib", "jni"}
MAX_HASH_BYTES = 1024 * 1024 * 1024


class NativeInspector:
    def __init__(self, root: Path, extra_cache_roots: Iterable[Path] = ()) -> None:
        self.root = root.resolve()
        self.extra_cache_roots = [path.expanduser().resolve() for path in extra_cache_roots]
        self.errors: list[dict[str, str]] = []
        self.blockers: list[dict[str, str]] = []
        self.observations: list[dict[str, Any]] = []
        self.archive_observations: list[dict[str, Any]] = []
        self._seen_paths: set[Path] = set()
        self._seen_archives: set[Path] = set()

    def display_path(self, path: Path, label: str | None = None, relative_to: Path | None = None) -> str:
        path = path.resolve()
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            pass
        if label:
            try:
                base = (relative_to or path.parent).resolve()
                relative_path = path.relative_to(base).as_posix()
                return f"<{label}>" if relative_path == "." else f"<{label}>/{relative_path}"
            except ValueError:
                return f"<{label}>"
        return str(path)

    @staticmethod
    def sha256_bytes(value: bytes) -> str:
        return hashlib.sha256(value).hexdigest()

    def sha256_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        total = 0
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                total += len(chunk)
                if total > MAX_HASH_BYTES:
                    raise ValueError(f"file exceeds safe hash limit of {MAX_HASH_BYTES} bytes")
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def abi_from_path(path: str, is_direct: bool = False) -> str | None:
        normalized = path.replace("\\", "/").strip("/")
        parts = normalized.split("/")
        if not parts or not parts[-1].lower().endswith(NATIVE_SUFFIX):
            return None
        if is_direct:
            return parts[-2] if len(parts) >= 2 else "unknown"
        for index, part in enumerate(parts[:-2]):
            if part in ABI_PATH_MARKERS:
                candidate = parts[index + 1]
                return candidate if candidate else "unknown"
        # A native entry without a conventional lib/<abi>/ or jni/<abi>/ path
        # is observed but cannot safely be attributed to an ABI.
        return "unknown"

    def record_direct_library(self, path: Path, source_kind: str, source_root: Path) -> None:
        if path in self._seen_paths:
            return
        self._seen_paths.add(path)
        try:
            digest = self.sha256_file(path)
            size = path.stat().st_size
        except (OSError, ValueError) as exc:
            message = f"Unable to hash native library {self.display_path(path)}: {exc}"
            self.errors.append({"path": self.display_path(path), "error": str(exc)})
            self.blockers.append({"type": "native-library-unreadable", "evidence": message})
            return
        relative = path.relative_to(source_root).as_posix() if path.is_relative_to(source_root) else path.name
        abi = self.abi_from_path(relative, is_direct=True)
        self.observations.append(
            {
                "source": source_kind,
                "path": self.display_path(path),
                "entry": None,
                "abi": abi,
                "bytes": size,
                "sha256": digest,
                "source_root": self.display_path(source_root),
            }
        )
        if abi == "unknown":
            self.blockers.append(
                {
                    "type": "unclassified-abi",
                    "evidence": f"Native library has no identifiable ABI directory: {self.display_path(path)}",
                }
            )

    def inspect_archive(self, path: Path, source_kind: str, source_root: Path) -> None:
        path = path.resolve()
        if path in self._seen_archives:
            return
        self._seen_archives.add(path)
        try:
            archive_hash = self.sha256_file(path)
            archive_size = path.stat().st_size
            with zipfile.ZipFile(path) as archive:
                entries = sorted(
                    info for info in archive.infolist() if not info.is_dir() and info.filename.lower().endswith(NATIVE_SUFFIX)
                )
                native_entries: list[dict[str, Any]] = []
                for info in entries:
                    try:
                        contents = archive.read(info)
                    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
                        self.errors.append({"path": self.display_path(path), "entry": info.filename, "error": str(exc)})
                        self.blockers.append(
                            {
                                "type": "native-entry-unreadable",
                                "evidence": f"Unable to read {info.filename} in {self.display_path(path)}: {exc}",
                            }
                        )
                        continue
                    abi = self.abi_from_path(info.filename)
                    native_entry = {
                        "entry": info.filename,
                        "abi": abi,
                        "bytes": len(contents),
                        "sha256": self.sha256_bytes(contents),
                    }
                    native_entries.append(native_entry)
                    self.observations.append(
                        {
                            "source": source_kind,
                            "path": self.display_path(path),
                            "entry": info.filename,
                            "abi": abi,
                            "bytes": len(contents),
                            "sha256": native_entry["sha256"],
                            "archive_sha256": archive_hash,
                            "source_root": self.display_path(source_root),
                        }
                    )
                    if abi == "unknown":
                        self.blockers.append(
                            {
                                "type": "unclassified-abi",
                                "evidence": f"Native archive entry has no identifiable ABI directory: {self.display_path(path)}!{info.filename}",
                            }
                        )
                self.archive_observations.append(
                    {
                        "source": source_kind,
                        "path": self.display_path(path),
                        "bytes": archive_size,
                        "sha256": archive_hash,
                        "native_entries": native_entries,
                        "source_root": self.display_path(source_root),
                    }
                )
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            self.errors.append({"path": self.display_path(path), "error": str(exc)})
            self.blockers.append(
                {
                    "type": "archive-unreadable",
                    "evidence": f"Unable to inspect dependency/build archive {self.display_path(path)}: {exc}",
                }
            )

    def scan_files(self, directory: Path, source_kind: str, source_root: Path) -> dict[str, Any]:
        if not directory.exists():
            return {"state": "absent", "file_count": 0, "archive_count": 0, "native_file_count": 0}
        if not directory.is_dir():
            self.blockers.append(
                {"type": "inspection-input-not-directory", "evidence": f"Expected directory is not a directory: {self.display_path(directory)}"}
            )
            return {"state": "invalid", "file_count": 0, "archive_count": 0, "native_file_count": 0}

        file_count = 0
        archive_count = 0
        native_file_count = 0
        try:
            paths = sorted(path for path in directory.rglob("*") if path.is_file())
        except OSError as exc:
            self.blockers.append({"type": "inspection-input-unreadable", "evidence": f"Unable to enumerate {self.display_path(directory)}: {exc}"})
            return {"state": "unreadable", "file_count": 0, "archive_count": 0, "native_file_count": 0}
        for path in paths:
            file_count += 1
            suffix = path.suffix.lower()
            if suffix == NATIVE_SUFFIX:
                native_file_count += 1
                self.record_direct_library(path, source_kind, source_root)
            elif suffix in ARCHIVE_SUFFIXES:
                archive_count += 1
                self.inspect_archive(path, source_kind, source_root)
        return {
            "state": "available",
            "file_count": file_count,
            "archive_count": archive_count,
            "native_file_count": native_file_count,
        }

    def gradle_cache_roots(self) -> list[Path]:
        candidates = list(self.extra_cache_roots)
        env_root = os.environ.get("GRADLE_USER_HOME")
        if env_root:
            candidates.append(Path(env_root))
        candidates.append(Path.home() / ".gradle")
        candidates.append(self.root / ".gradle")
        roots: list[Path] = []
        seen: set[Path] = set()
        for path in candidates:
            resolved = path.expanduser().resolve()
            if resolved not in seen:
                seen.add(resolved)
                roots.append(resolved)
        return roots

    def cache_artifact_directories(self) -> list[tuple[Path, str]]:
        directories: list[tuple[Path, str]] = []
        for index, cache_root in enumerate(self.gradle_cache_roots()):
            if not cache_root.exists():
                continue
            module_cache = cache_root / "caches" / "modules-2" / "files-2.1"
            if module_cache.exists():
                directories.append((module_cache, f"gradle-cache-{index}"))
            # Transformed or resolved artifacts can be present outside the
            # canonical files-2.1 store in older/newer Gradle versions.
            for candidate in (cache_root / "caches" / "transforms-1", cache_root / "caches" / "transforms-2", cache_root / "caches" / "transforms-3"):
                if candidate.exists():
                    directories.append((candidate, f"gradle-transform-cache-{index}"))
        return directories

    def inspect(self) -> dict[str, Any]:
        local_libs = self.root / "app" / "libs"
        build_root = self.root / "app" / "build"
        outputs = build_root / "outputs"

        local_state = self.scan_files(local_libs, "local-library", local_libs)
        local_state["path"] = self.display_path(local_libs)
        # An absent app/libs directory is an explicit finding that no local
        # libraries are configured, not a reason to invent ABI requirements.
        local_state["inventory_complete"] = True
        if not local_libs.exists():
            local_state["state"] = "absent-directory"
            local_state["note"] = "No app/libs directory is configured in this source revision; no local libraries were available to inspect."

        cache_states: list[dict[str, Any]] = []
        cache_dirs = self.cache_artifact_directories()
        for directory, source_kind in cache_dirs:
            state = self.scan_files(directory, "resolved-dependency", directory)
            state.update({"path": self.display_path(directory, source_kind, directory), "source_kind": source_kind})
            cache_states.append(state)
        dependency_available = bool(cache_states)
        dependency_artifact_count = sum(int(item["archive_count"]) + int(item["native_file_count"]) for item in cache_states)
        if not dependency_available:
            self.blockers.append(
                {
                    "type": "resolved-dependency-inventory-unavailable",
                    "evidence": "No Gradle cache artifact directory was available; resolved dependency archives and their native libraries could not be inspected.",
                }
            )
        elif dependency_artifact_count == 0:
            self.blockers.append(
                {
                    "type": "resolved-dependency-inventory-empty",
                    "evidence": "Gradle cache directories were present but contained no inspectable dependency archives or native files.",
                }
            )

        output_state = self.scan_files(outputs, "built-artifact", outputs)
        output_state["path"] = self.display_path(outputs)
        built_artifacts = [
            path for path in outputs.rglob("*")
            if path.is_file() and path.suffix.lower() in {".apk", ".aab"}
        ] if outputs.exists() else []
        output_state["artifacts"] = [self.display_path(path) for path in sorted(built_artifacts)]
        output_state["inventory_complete"] = bool(built_artifacts)
        if not outputs.exists():
            output_state["state"] = "absent-directory"
        if not built_artifacts:
            self.blockers.append(
                {
                    "type": "built-artifact-inventory-unavailable",
                    "evidence": "No APK or AAB output was available under app/build/outputs; final packaged native libraries and ABIs could not be inspected.",
                }
            )

        observed_abis = sorted({str(item["abi"]) for item in self.observations if item.get("abi") and item["abi"] != "unknown"})
        unknown_native_count = sum(1 for item in self.observations if item.get("abi") == "unknown")
        obsolete_observed = sorted(set(observed_abis) & OBSOLETE_ABIS)
        complete = bool(local_state["inventory_complete"] and dependency_available and output_state["inventory_complete"] and not self.errors)
        if unknown_native_count:
            complete = False
        if complete:
            decision = "no-native-splits-required" if not observed_abis else "splits-require-evidence-review"
        else:
            decision = "undetermined-blocked"

        return {
            "report_schema": "android-upgrade-abi/v1",
            "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "source_revision": self.git_revision(),
            "scope": {
                "packaging_configuration_changed": False,
                "legacy_abi_split_list_used_as_evidence": False,
                "personal_data_collected": False,
            },
            "inputs": {
                "local_libraries": local_state,
                "resolved_dependency_artifacts": {
                    "cache_roots_considered": [self.display_path(path, f"gradle-cache-{index}", path) for index, path in enumerate(self.gradle_cache_roots())],
                    "artifact_directories": cache_states,
                    "inventory_complete": dependency_available and dependency_artifact_count > 0,
                },
                "built_apk_aab_outputs": output_state,
            },
            "native_libraries": {
                "observed_count": len(self.observations),
                "observations": sorted(self.observations, key=lambda item: (str(item.get("path")), str(item.get("entry")), str(item.get("abi")))),
                "archives_inspected": sorted(self.archive_observations, key=lambda item: str(item["path"])),
                "observed_abis": observed_abis,
                "unknown_abi_count": unknown_native_count,
                "obsolete_abis_observed": obsolete_observed,
            },
            "decision": {
                "inventory_complete": complete,
                "status": "pass" if complete else "blocked",
                "abi_split_decision": decision,
                "evidence": [
                    "Only .so files in local libraries, resolved dependency archives, and APK/AAB archives are considered ABI evidence.",
                    "The legacy splits.abi include list is intentionally not used to infer native dependencies or required ABIs.",
                ],
            },
            "errors": sorted(self.errors, key=lambda item: (item.get("path", ""), item.get("entry", ""), item.get("error", ""))),
            "blockers": sorted(self.blockers, key=lambda item: (item.get("type", ""), item.get("evidence", ""))),
            "privacy": {
                "database_contents_included": False,
                "food_names_included": False,
                "signing_secrets_included": False,
                "personal_data_included": False,
                "recorded_values": "Paths, file sizes, SHA-256 hashes, archive entries, and ABI names only.",
            },
        }

    def git_revision(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=self.root, capture_output=True, text=True, check=False
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except OSError:
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_root", nargs="?", help="repository root; defaults to the parent of tools/android-upgrade")
    parser.add_argument(
        "--gradle-cache",
        action="append",
        default=[],
        metavar="PATH",
        help="additional Gradle user-home/cache root to inspect; may be repeated",
    )
    args = parser.parse_args(argv)
    script_root = Path(__file__).resolve().parents[2]
    root = Path(args.repo_root).expanduser().resolve() if args.repo_root else script_root
    report = NativeInspector(root, (Path(path) for path in args.gradle_cache)).inspect()
    output = root / REPORT_RELATIVE_PATH
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ABI report: {REPORT_RELATIVE_PATH.as_posix()}")
    print(f"Native libraries observed: {report['native_libraries']['observed_count']}")
    print(f"Observed ABIs: {', '.join(report['native_libraries']['observed_abis']) or 'none'}")
    print(f"Inventory complete: {report['decision']['inventory_complete']}")
    print(f"ABI split decision: {report['decision']['abi_split_decision']}")
    if report["blockers"]:
        print(f"Blockers: {len(report['blockers'])}")
    return 0 if report["decision"]["status"] == "pass" else 2


if __name__ == "__main__":
    sys.exit(main())
