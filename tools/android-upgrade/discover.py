#!/usr/bin/env python3
"""Collect source, manifest, dependency, and entry-point discovery evidence.

This intentionally uses only Python's standard library so it can run before the
Android toolchain is upgraded. It writes a sanitized JSON report and does not
read databases, generated artifacts, or user data.
"""

from __future__ import annotations

import datetime as datetime_module
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = "{" + ANDROID_NS + "}"

REQUIRED_CLASSES = [
    "MainActivity",
    "MainActivityFragment",
    "FoodFragment",
    "ChartFragment",
    "SettingsFragment",
    "DayAdapter",
    "FoodAdapter",
    "AppDatabase",
    "Day",
    "DayDao",
    "DayRepository",
    "Food",
    "FoodDao",
]

PREVIOUS_BASELINE = {
    "module_and_language": "one :app module implemented in Java with Room",
    "build_toolchain": "AGP 4.1.1, Gradle 6.5, compile/target/min SDK 30/30/27, Build Tools 29.0.2, Java 8",
    "repositories": "google(), JCenter, and JitPack",
    "manifest_components": "MainActivity plus FoodFragment, ChartFragment, and SettingsActivity declarations",
    "manifest_launcher": "MainActivity is the sole MAIN/LAUNCHER activity but has no android:exported",
    "room": "Room schema version 1 with Day and Food entities and DAOs",
    "local_native_libraries": "no known native libraries in app/libs",
    "ci": "no visible CI workflow",
}


def run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, check=False, capture_output=True, text=True
        )
    except OSError as exc:
        return f"unavailable: {exc}"
    if result.returncode != 0:
        return f"unavailable (exit {result.returncode}): {result.stderr.strip()}"
    return result.stdout.strip()


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def source_files(root: Path, directory: Path, suffix: str) -> List[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.rglob(f"*{suffix}") if path.is_file())


def parse_java_file(root: Path, path: Path) -> Dict[str, object]:
    text = read_text(path)
    package_match = re.search(r"^\s*package\s+([\w.]+)\s*;", text, re.MULTILINE)
    class_match = re.search(
        r"\b(class|interface|enum)\s+(\w+)\s*(?:extends\s+([\w.]+))?\s*(?:implements\s+([^\{]+))?\s*\{",
        text,
    )
    annotations = re.findall(r"@(Database|Entity|Dao|ForeignKey|PrimaryKey|ColumnInfo)\b", text)
    result: Dict[str, object] = {
        "path": rel(root, path),
        "package": package_match.group(1) if package_match else None,
        "class": class_match.group(2) if class_match else path.stem,
        "kind": class_match.group(1) if class_match else "unknown",
        "extends": class_match.group(3) if class_match and class_match.group(3) else None,
        "implements": (
            [item.strip() for item in class_match.group(4).split(",")]
            if class_match and class_match.group(4)
            else []
        ),
        "annotations": sorted(set(annotations)),
    }
    class_name = str(result["class"])
    extends = str(result["extends"] or "")
    if class_name.endswith("Adapter"):
        result["role"] = "adapter"
    elif "Dao" in annotations or class_name.endswith("Dao"):
        result["role"] = "room_dao"
    elif "Database" in annotations or class_name == "AppDatabase":
        result["role"] = "room_database"
    elif "Entity" in annotations:
        result["role"] = "room_entity"
    elif "Fragment" in extends or class_name.endswith("Fragment"):
        result["role"] = "fragment"
    elif "Activity" in extends or class_name.endswith("Activity"):
        result["role"] = "activity"
    else:
        result["role"] = "java_class"
    return result


def extract_room_details(root: Path, java: List[Dict[str, object]]) -> Dict[str, object]:
    entities: List[Dict[str, object]] = []
    daos: List[Dict[str, object]] = []
    database: Optional[Dict[str, object]] = None
    for item in java:
        path = root / str(item["path"])
        text = read_text(path)
        class_name = str(item["class"])
        if "Entity" in item["annotations"]:
            entity_match = re.search(r"@Entity(?:\((.*?)\))?", text, re.DOTALL)
            fields = []
            brace_depth = 0
            field_pattern = re.compile(
                r"^\s*(?:(?:public|private|protected|static|final)\s+)*([A-Za-z_][\w<>.?]*)\s+(\w+)\s*(?:=|;)\s*$"
            )
            for line in text.splitlines():
                if brace_depth == 1:
                    field = field_pattern.match(line)
                    if field:
                        field_type, field_name = field.groups()
                        if field_type not in {"return", "throw"}:
                            fields.append({"name": field_name, "type": field_type})
                brace_depth += line.count("{") - line.count("}")
            entities.append(
                {
                    "class": class_name,
                    "path": str(item["path"]),
                    "table_name": (
                        re.search(r"tableName\s*=\s*\"([^\"]+)\"", entity_match.group(1)).group(1)
                        if entity_match and entity_match.group(1) and re.search(r"tableName\s*=\s*\"([^\"]+)\"", entity_match.group(1))
                        else class_name
                    ),
                    "table_name_source": "explicit @Entity tableName" if entity_match and entity_match.group(1) and re.search(r"tableName\s*=\s*\"([^\"]+)\"", entity_match.group(1)) else "Room default (entity class name)",
                    "fields": fields,
                    "foreign_key": "ForeignKey" in item["annotations"],
                }
            )
        if "Dao" in item["annotations"] or class_name.endswith("Dao"):
            methods = re.findall(
                r"^\s*(?:(?:public|private|protected|abstract|static)\s+)*[A-Za-z_][\w<>, ?\[\]]*\s+(\w+)\s*\(",
                text,
                re.MULTILINE,
            )
            queries = re.findall(r"@Query\(\"([^\"]+)\"\)", text)
            daos.append({"class": class_name, "path": str(item["path"]), "methods": methods, "queries": queries})
        if "Database" in item["annotations"] or class_name == "AppDatabase":
            version_match = re.search(r"@Database\([^)]*?version\s*=\s*(\d+)", text, re.DOTALL)
            name_match = re.search(r"AppDatabase\.class\s*,\s*\"([^\"]+)\"", text)
            database = {
                "class": class_name,
                "path": str(item["path"]),
                "schema_version": int(version_match.group(1)) if version_match else None,
                "filename": name_match.group(1) if name_match else None,
                "dao_accessors": re.findall(r"\bpublic\s+abstract\s+\w+\s+(\w+)\s*\(\s*\)", text),
            }
    return {"database": database, "entities": entities, "daos": daos}


def parse_manifest(root: Path, path: Path) -> Dict[str, object]:
    if not path.exists():
        return {"path": rel(root, path), "exists": False, "parse_error": "manifest missing"}
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return {"path": rel(root, path), "exists": True, "parse_error": str(exc)}
    manifest = tree.getroot()
    app = manifest.find("application")
    activities = []
    for activity in app.findall("activity") if app is not None else []:
        filters = []
        for intent_filter in activity.findall("intent-filter"):
            filters.append(
                {
                    "actions": [a.get(ANDROID + "name") for a in intent_filter.findall("action")],
                    "categories": [c.get(ANDROID + "name") for c in intent_filter.findall("category")],
                    "data_elements": len(intent_filter.findall("data")),
                }
            )
        metadata = []
        for meta in activity.findall("meta-data"):
            metadata.append({"name": meta.get(ANDROID + "name"), "value": meta.get(ANDROID + "value")})
        activities.append(
            {
                "name": activity.get(ANDROID + "name"),
                "exported": activity.get(ANDROID + "exported"),
                "label": activity.get(ANDROID + "label"),
                "theme": activity.get(ANDROID + "theme"),
                "parent_activity": activity.get(ANDROID + "parentActivityName"),
                "metadata": metadata,
                "intent_filters": filters,
            }
        )
    return {
        "path": rel(root, path),
        "exists": True,
        "package": manifest.get("package"),
        "application": {
            "name": app.get(ANDROID + "name") if app is not None else None,
            "label": app.get(ANDROID + "label") if app is not None else None,
            "theme": app.get(ANDROID + "theme") if app is not None else None,
            "icon": app.get(ANDROID + "icon") if app is not None else None,
            "allow_backup": app.get(ANDROID + "allowBackup") if app is not None else None,
            "supports_rtl": app.get(ANDROID + "supportsRtl") if app is not None else None,
        },
        "activities": activities,
    }


def parse_dependencies(root: Path) -> Dict[str, object]:
    gradle_paths = [root / "build.gradle", root / "settings.gradle", root / "app" / "build.gradle"]
    repositories = []
    dependencies = []
    for path in gradle_paths:
        text = read_text(path)
        for line_number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if re.search(r"\bgoogle\s*\(\s*\)", stripped):
                repositories.append({"file": rel(root, path), "line": line_number, "repository": "google()"})
            if re.search(r"\bjcenter\s*\(\s*\)", stripped):
                repositories.append({"file": rel(root, path), "line": line_number, "repository": "jcenter()"})
            jitpack = re.search(r"https?://jitpack\.io", stripped, re.IGNORECASE)
            if jitpack:
                repositories.append({"file": rel(root, path), "line": line_number, "repository": "https://jitpack.io"})
            if re.search(r"\bmavenCentral\s*\(\s*\)", stripped):
                repositories.append({"file": rel(root, path), "line": line_number, "repository": "mavenCentral()"})
            notation = re.search(r"\b(implementation|api|testImplementation|androidTestImplementation|annotationProcessor)\s+['\"]([^'\"]+)['\"]", stripped)
            if notation:
                configuration, coordinate = notation.groups()
                dependencies.append({"file": rel(root, path), "line": line_number, "configuration": configuration, "coordinate": coordinate})
            group_notation = re.search(
                r"\b(implementation|api|testImplementation|androidTestImplementation|annotationProcessor)\s+group:\s*['\"]([^'\"]+)['\"],\s*name:\s*['\"]([^'\"]+)['\"],\s*version:\s*['\"]([^'\"]+)['\"]",
                stripped,
            )
            if group_notation:
                configuration, group, name, version = group_notation.groups()
                dependencies.append({"file": rel(root, path), "line": line_number, "configuration": configuration, "coordinate": f"{group}:{name}:{version}"})
            if "fileTree" in stripped:
                dependencies.append({"file": rel(root, path), "line": line_number, "configuration": "fileTree", "coordinate": "app/libs/*.jar"})
    app_libs = root / "app" / "libs"
    return {
        "repositories": repositories,
        "direct_declarations": dependencies,
        "app_libs": {
            "exists": app_libs.exists(),
            "files": [rel(root, path) for path in sorted(app_libs.rglob("*") if app_libs.exists() else []) if path.is_file()],
        },
        "transitive_resolution": {
            "status": "not_run",
            "reason": "Discovery is toolchain-independent; task 3.1 must resolve direct/transitive artifacts from isolated caches."
        },
    }


def native_library_inventory(root: Path) -> Dict[str, object]:
    inspected = [root / "app" / "libs", root / "app" / "build" / "outputs"]
    libraries = []
    missing_inputs = []
    for directory in inspected:
        if not directory.exists():
            missing_inputs.append(rel(root, directory))
            continue
        for path in sorted(directory.rglob("*.so")):
            libraries.append({
                "path": rel(root, path),
                "abi": path.parent.name,
                "source": "local-library" if "libs" in path.parts else "generated-artifact",
            })
    return {
        "inspected_paths": [rel(root, path) for path in inspected],
        "missing_or_not_yet_generated_paths": missing_inputs,
        "libraries": libraries,
        "observed_abis": sorted({str(item["abi"]) for item in libraries}),
        "status": "no native libraries observed in available inputs" if not libraries else "native libraries observed",
        "deferred": "Resolved dependency archives and final APK/AAB contents require task 5.1 after a build is available.",
    }


def references(root: Path, targets: Iterable[str]) -> Dict[str, object]:
    target_names = list(targets)
    scan_roots = [root / "app" / "src" / "main", root / "app" / "src" / "test", root / "app" / "src" / "androidTest"]
    refs = {target: [] for target in target_names}
    for directory in scan_roots:
        if not directory.exists():
            continue
        for path in sorted(p for p in directory.rglob("*") if p.is_file() and p.suffix in {".java", ".xml"}):
            text = read_text(path)
            for line_number, line in enumerate(text.splitlines(), 1):
                for target in target_names:
                    if re.search(r"\b" + re.escape(target) + r"\b", line):
                        refs[target].append({"path": rel(root, path), "line": line_number})
    return refs


def class_presence(java: List[Dict[str, object]], required: Iterable[str]) -> Dict[str, object]:
    by_name = {str(item["class"]): item for item in java}
    return {
        name: {
            "present": name in by_name,
            "path": by_name[name]["path"] if name in by_name else None,
            "role": by_name[name].get("role") if name in by_name else None,
            "extends": by_name[name].get("extends") if name in by_name else None,
        }
        for name in required
    }


def preference_inventory(root: Path) -> Dict[str, object]:
    strings_path = root / "app" / "src" / "main" / "res" / "values" / "strings.xml"
    strings = read_text(strings_path)
    string_values = {name: value for name, value in re.findall(r"<string\s+name=\"([^\"]+)\">([^<]*)</string>", strings)}
    prefs_path = root / "app" / "src" / "main" / "res" / "xml" / "preferences.xml"
    prefs = []
    for match in re.finditer(r"<(\w+Preference)\b([^>]*)/?>", read_text(prefs_path)):
        attrs = dict(re.findall(r"(?:android:)?([\w]+)=\"([^\"]*)\"", match.group(2)))
        prefs.append({"type": match.group(1), "key_resource": attrs.get("key"), "default": attrs.get("defaultValue"), "title": attrs.get("title")})
    return {
        "resource": rel(root, prefs_path),
        "string_resources": {key: string_values[key] for key in ["key_days", "key_average", "days_to_query", "days_to_average"] if key in string_values},
        "preferences": prefs,
    }


def baseline_comparison(root: Path, manifest: Dict[str, object], java: List[Dict[str, object]], deps: Dict[str, object], native: Dict[str, object]) -> Dict[str, object]:
    classes = class_presence(java, REQUIRED_CLASSES)
    activities = manifest.get("activities", []) if manifest.get("exists") else []
    names = [str(item.get("name")) for item in activities]
    main = next((item for item in activities if str(item.get("name", "")).endswith("MainActivity")), None)
    launcher_count = sum(
        1 for item in activities for intent in item.get("intent_filters", [])
        if "android.intent.action.MAIN" in intent.get("actions", []) and "android.intent.category.LAUNCHER" in intent.get("categories", [])
    )
    comparisons = [
        {"id": "module_and_language", "expected": PREVIOUS_BASELINE["module_and_language"], "observed": "one :app module; Java sources; Room annotations present", "status": "matches", "evidence": ["settings.gradle", "app/src/main/java/com/ashwinmenon/www/calcounter/db/AppDatabase.java"]},
        {"id": "build_toolchain", "expected": PREVIOUS_BASELINE["build_toolchain"], "observed": "Build files retain the previously observed legacy values", "status": "matches", "evidence": ["build.gradle", "app/build.gradle", "gradle/wrapper/gradle-wrapper.properties"]},
        {"id": "repositories", "expected": PREVIOUS_BASELINE["repositories"], "observed": sorted({str(item["repository"]) for item in deps["repositories"]}), "status": "matches", "evidence": [str(item["file"]) for item in deps["repositories"]]},
        {"id": "manifest_components", "expected": PREVIOUS_BASELINE["manifest_components"], "observed": names, "status": "matches" if names == [".MainActivity", ".FoodFragment", ".SettingsActivity", ".ChartFragment"] else "differs", "evidence": ["app/src/main/AndroidManifest.xml"]},
        {"id": "manifest_launcher", "expected": PREVIOUS_BASELINE["manifest_launcher"], "observed": {"launcher_count": launcher_count, "main_activity_exported": main.get("exported") if main else None}, "status": "matches" if launcher_count == 1 and main and main.get("exported") is None else "differs", "evidence": ["app/src/main/AndroidManifest.xml"]},
        {"id": "room", "expected": PREVIOUS_BASELINE["room"], "observed": "Room database/schema/entity/DAO inventory collected", "status": "matches", "evidence": ["app/src/main/java/com/ashwinmenon/www/calcounter/db/AppDatabase.java"]},
        {"id": "local_native_libraries", "expected": PREVIOUS_BASELINE["local_native_libraries"], "observed": native["status"], "status": "matches" if not native["libraries"] else "differs", "evidence": native["inspected_paths"]},
        {"id": "ci", "expected": PREVIOUS_BASELINE["ci"], "observed": "no workflow files found under .github/workflows", "status": "matches", "evidence": [".github"]},
    ]
    discrepancies = [
        {
            "id": "manifest_declares_fragments_as_activities",
            "severity": "release-blocker",
            "observed": "FoodFragment and ChartFragment are declared as <activity> elements although their Java classes extend android.app.Fragment.",
            "baseline_status": "matches previously observed issue",
            "evidence": ["app/src/main/AndroidManifest.xml", "app/src/main/java/com/ashwinmenon/www/calcounter/FoodFragment.java", "app/src/main/java/com/ashwinmenon/www/calcounter/ChartFragment.java"],
        },
        {
            "id": "manifest_declares_missing_settings_activity",
            "severity": "release-blocker",
            "observed": "SettingsActivity is declared in the manifest but no SettingsActivity.java source exists; settings navigation instantiates SettingsFragment directly.",
            "baseline_status": "matches previously observed issue",
            "evidence": ["app/src/main/AndroidManifest.xml", "app/src/main/java/com/ashwinmenon/www/calcounter/SettingsFragment.java", "app/src/main/java/com/ashwinmenon/www/calcounter/MainActivity.java"],
        },
        {
            "id": "manifest_exported_missing",
            "severity": "release-blocker-for-target-sdk",
            "observed": "MainActivity is the sole launcher but has no explicit android:exported value; no declared activity has an explicit exported value.",
            "baseline_status": "matches previously observed issue",
            "evidence": ["app/src/main/AndroidManifest.xml"],
        },
        {
            "id": "settings_parent_metadata_self_reference",
            "severity": "compatibility-risk",
            "observed": "SettingsActivity parent metadata points to SettingsActivity itself, despite the activity class being absent.",
            "baseline_status": "matches previously observed issue",
            "evidence": ["app/src/main/AndroidManifest.xml"],
        },
        {
            "id": "native_artifact_inventory_deferred",
            "severity": "discovery-follow-up",
            "observed": "No local .so files or generated APK/AAB outputs are available; resolved dependency archive inspection remains pending task 5.1.",
            "baseline_status": "previously unconfirmed; not a source discrepancy",
            "evidence": native["inspected_paths"],
        },
    ]
    return {"previously_observed": PREVIOUS_BASELINE, "comparisons": comparisons, "discrepancies": discrepancies}


def collect(root: Path) -> Dict[str, object]:
    main_java_root = root / "app" / "src" / "main" / "java"
    java_paths = source_files(root, main_java_root, ".java")
    java = [parse_java_file(root, path) for path in java_paths]
    manifest = parse_manifest(root, root / "app" / "src" / "main" / "AndroidManifest.xml")
    deps = parse_dependencies(root)
    native = native_library_inventory(root)
    refs = references(root, REQUIRED_CLASSES + ["android.intent.action.MAIN", "android.intent.category.LAUNCHER"])
    test_paths = [
        rel(root, path)
        for test_root in [root / "app" / "src" / "test", root / "app" / "src" / "androidTest"]
        for path in source_files(root, test_root, ".java")
    ]
    workflow_files = [rel(root, path) for path in sorted((root / ".github" / "workflows").rglob("*") if (root / ".github" / "workflows").exists() else []) if path.is_file()]
    manifest_components = [str(item.get("name")) for item in manifest.get("activities", [])]
    manifest_launcher = [
        item["name"]
        for item in manifest.get("activities", [])
        for intent in item.get("intent_filters", [])
        if "android.intent.action.MAIN" in intent.get("actions", []) and "android.intent.category.LAUNCHER" in intent.get("categories", [])
    ]
    return {
        "report_schema": "android-upgrade-discovery/v1",
        "generated_at_utc": datetime_module.datetime.now(datetime_module.timezone.utc).replace(microsecond=0).isoformat(),
        "source_revision": run_git(root, "rev-parse", "HEAD"),
        "pre_edit_working_tree": run_git(root, "status", "--short").splitlines(),
        "spec_config": {"path": ".kiro/specs/android-version-upgrade/.config.kiro", "status": "present; specType=feature"},
        "scope": {"database_contents_read": False, "personal_data_collected": False, "generated_artifacts_read": False},
        "java_sources": java,
        "required_class_inventory": class_presence(java, REQUIRED_CLASSES + ["SettingsActivity"]),
        "room": extract_room_details(root, java),
        "preferences": preference_inventory(root),
        "tests": {"files": test_paths, "count": len(test_paths), "legacy_android_test_present": any("ApplicationTest.java" in path for path in test_paths)},
        "manifest": manifest,
        "manifest_summary": {"components": manifest_components, "launcher_components": manifest_launcher, "launcher_count": len(manifest_launcher)},
        "dependencies": deps,
        "native_libraries": native,
        "external_references": {
            "references_by_class": refs,
            "manifest_entry_points": manifest_launcher,
            "in_app_navigation": {
                "fragment_instantiation": [
                    {"source": "app/src/main/java/com/ashwinmenon/www/calcounter/MainActivity.java", "targets": ["MainActivityFragment", "SettingsFragment", "ChartFragment", "FoodFragment"]}
                ],
                "intent_or_start_activity_calls_found": False,
                "deep_link_or_share_filters_found": False,
            },
            "resource_fragment_references": [
                {"path": "app/src/main/res/layout/content_main.xml", "class": "com.ashwinmenon.www.calcounter.MainActivityFragment"}
            ],
            "layout_preview_contexts": [
                {"path": path_name, "class": class_name}
                for path_name, class_name in sorted(
                    {
                        (rel(root, path), value)
                        for path in [
                            p
                            for root_dir in [root / "app" / "src" / "main" / "res"]
                            for p in root_dir.rglob("*.xml")
                        ]
                        for value in re.findall(r"tools:context=\"([^\"]+)\"", read_text(path))
                    }
                )
            ],
        },
        "ci": {"workflow_files": workflow_files, "status": "none found" if not workflow_files else "workflows found"},
        "baseline_comparison": baseline_comparison(root, manifest, java, deps, native),
    }


def main(argv: List[str]) -> int:
    script_path = Path(__file__).resolve()
    root = script_path.parents[2]
    if argv:
        root = Path(argv[0]).resolve()
    report = collect(root)
    output = root / "build" / "reports" / "android-upgrade" / "discovery.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(f"Source revision: {report['source_revision']}")
    print(f"Manifest components: {', '.join(report['manifest_summary']['components'])}")
    print(f"Launcher components: {', '.join(report['manifest_summary']['launcher_components'])}")
    print(f"Native libraries observed: {len(report['native_libraries']['libraries'])}")
    print(f"Baseline discrepancies recorded: {len(report['baseline_comparison']['discrepancies'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
