#!/usr/bin/env python3
"""Unit tests for the ABI/native-library inspection checker."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from inspect_native import NativeInspector


class NativeInspectorTest(unittest.TestCase):
    def write_archive(self, path: Path, entries: dict[str, bytes]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w") as archive:
            for name, contents in entries.items():
                archive.writestr(name, contents)

    def test_scans_local_dependency_and_built_artifact_native_libraries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "app/libs/arm64-v8a").mkdir(parents=True)
            (root / "app/libs/arm64-v8a/liblocal.so").write_bytes(b"local")
            self.write_archive(
                root / "gradle-home/caches/modules-2/files-2.1/example/native/1.0/hash/native.aar",
                {"jni/x86_64/libdependency.so": b"dependency"},
            )
            self.write_archive(
                root / "app/build/outputs/apk/debug/app-debug.apk",
                {"lib/armeabi-v7a/libpackaged.so": b"packaged"},
            )

            report = NativeInspector(root, [root / "gradle-home"]).inspect()

            self.assertTrue(report["decision"]["inventory_complete"])
            self.assertEqual(report["decision"]["status"], "pass")
            self.assertEqual(
                report["native_libraries"]["observed_abis"],
                ["arm64-v8a", "armeabi-v7a", "x86_64"],
            )
            self.assertEqual(report["native_libraries"]["observed_count"], 3)
            self.assertEqual(report["native_libraries"]["unknown_abi_count"], 0)
            self.assertTrue(all(item["sha256"] for item in report["native_libraries"]["observations"]))

    def test_blocks_when_dependency_or_built_artifact_evidence_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = NativeInspector(Path(temporary_directory)).inspect()

            self.assertFalse(report["decision"]["inventory_complete"])
            self.assertEqual(report["decision"]["status"], "blocked")
            self.assertEqual(report["decision"]["abi_split_decision"], "undetermined-blocked")
            blocker_types = {item["type"] for item in report["blockers"]}
            self.assertIn("resolved-dependency-inventory-unavailable", blocker_types)
            self.assertIn("built-artifact-inventory-unavailable", blocker_types)
            self.assertFalse(report["scope"]["legacy_abi_split_list_used_as_evidence"])

    def test_blocks_unclassified_native_archive_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "app/libs").mkdir(parents=True)
            self.write_archive(
                root / "gradle-home/caches/modules-2/files-2.1/example/native/1.0/hash/native.aar",
                {"assets/libunclassified.so": b"native"},
            )
            self.write_archive(root / "app/build/outputs/apk/debug/app-debug.apk", {})

            report = NativeInspector(root, [root / "gradle-home"]).inspect()

            self.assertEqual(report["native_libraries"]["unknown_abi_count"], 1)
            self.assertFalse(report["decision"]["inventory_complete"])
            self.assertIn("unclassified-abi", {item["type"] for item in report["blockers"]})


if __name__ == "__main__":
    unittest.main()
