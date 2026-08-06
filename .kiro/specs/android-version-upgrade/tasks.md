# Implementation Plan: Android Version Upgrade

## Overview

Upgrade the existing CalCounter repository from its legacy Android build to Android 16/API 36 while preserving the application identity, minimum API, Java compatibility, Room data, calorie-tracking behavior, and debug/release variant behavior.

Fixed decisions for every implementation task:

- `compileSdk 36` and `targetSdk 36`.
- `minSdk 27`.
- `applicationId com.ashwinmenon.www.calcounter` for debug and release.
- Java source and bytecode compatibility remain Java 8 unless an explicit, recorded approval and API 27 validation allow a change.
- The repository remains a single Java `:app` module.
- Release shrinking remains disabled for the initial upgrade.
- No production signing secrets or personal user data may be committed or emitted in logs.
- Exact AGP, Gradle, and Build JDK versions are discovery outputs; do not invent or prefill them. They must be selected from dated official compatibility evidence before build-file edits.

The implementation must work from the actual baseline: root `build.gradle`, `settings.gradle`, `gradle.properties`, `gradle/wrapper/gradle-wrapper.properties`, `app/build.gradle`, `app/src/main/AndroidManifest.xml`, Java sources under `app/src/main/java/com/ashwinmenon/www/calcounter`, Room classes under `.../calcounter/db`, the legacy `ApplicationTest`, and no visible CI workflow under `.github`.

Convert the feature design into a series of prompts for a code-generation LLM that will implement each step with incremental progress. Make sure that each prompt builds on the previous prompts, and ends with wiring things together. There should be no hanging or orphaned code that isn't integrated into a previous step. Focus ONLY on tasks that involve writing, modifying, or testing code.

## Tasks

- [ ] 1. Establish the immutable baseline and discovery evidence
  - [x] 1.1 Create a reproducible baseline collector under `tools/android-upgrade/` that records the source revision, complete working-tree state, Gradle/Java environment, module graph, build files, variants, versioning, signing configuration references, ABI configuration, local libraries, test roots, and visible CI state; write a machine-readable report to `build/reports/android-upgrade/baseline.json` and retain the command output as a CI artifact.
    - Record the current known values as unconfirmed until the collector verifies them: one Java/Room `:app` module; AGP `4.1.1`; Gradle wrapper `6.5`; compile/target/min SDK `30/30/27`; Build Tools `29.0.2`; Java 8; `google()`, JCenter, and JitPack; legacy dependency coordinates; obsolete ABI split entries; and no visible workflow.
    - Exclude database contents, food names, signing secrets, and other personal data from the report.
    - _Requirements: 1.1, 1.2, 1.4, 9.2_

  - [x] 1.2 Create a source/manifest/dependency discovery check under `tools/android-upgrade/` and record its output in `build/reports/android-upgrade/discovery.json`.
    - Inventory `MainActivity`, `MainActivityFragment`, `FoodFragment`, `ChartFragment`, `SettingsFragment`, adapters, Room entities/DAOs/database, resource preference keys, and test classes.
    - Confirm that `FoodFragment` and `ChartFragment` are fragments, determine whether a real `SettingsActivity` exists, inspect `app/libs`, and identify all manifest components, launcher filters, parent metadata, native libraries, and externally referenced entry points.
    - Record every discrepancy from the design’s previously observed baseline before any source or build-file edit.
    - _Requirements: 1.2, 1.3, 1.5, 4.2, 4.5, 5.1, 9.1_

  - [-] 1.3 Select and record exact `AGP_VERSION`, `GRADLE_VERSION`, and `BUILD_JDK` values before editing `build.gradle` or the wrapper.
    - Use dated official Android Gradle Plugin release notes and release-specific compatibility tables, the official Gradle compatibility matrix, and the Android 16/API 36 SDK setup guidance available on the implementation date.
    - Record URLs, publication/access dates, required Gradle/JDK ranges, selected versions, installed SDK/build-tool packages, rejection reasons for candidates, and the `./gradlew --version` result in `build/reports/android-upgrade/toolchain-selection.json` (or an equivalent checked-in machine-readable evidence file).
    - Reject any candidate that is not mutually compatible or that requires an unapproved Kotlin migration; do not substitute a cached or assumed future version.
    - _Requirements: 3.1, 3.2, 7.2, 8.1_

- [ ] 2. Apply the verified wrapper and Android build configuration
  - [~] 2.1 Update only `gradle/wrapper/gradle-wrapper.properties` and the wrapper distribution metadata needed for the selected Gradle version; include a distribution checksum when supported and verify the wrapper with an isolated Gradle user home.
    - Do not change the wrapper until task 1.3 has recorded the exact selected version.
    - _Requirements: 3.1, 3.2, 7.2, 8.1_

  - [~] 2.2 Modernize `build.gradle`, `settings.gradle`, and `gradle.properties` around the verified toolchain.
    - Retain only the `:app` module, centralize approved plugin/dependency repositories as appropriate, remove every `jcenter()` declaration, retain `google()` and `mavenCentral()`, and retain JitPack only when task 3.1 proves a required dependency has no approved alternative.
    - Remove obsolete root `java` and Lombok Gradle plugins only after source/dependency discovery proves no root Java project needs them; keep AndroidX/Jetifier settings until all dependencies are verified.
    - Preserve non-secret JVM and Android build settings unless the selected AGP requires a documented change.
    - _Requirements: 1.2, 3.2, 3.3, 3.4, 7.1, 8.1_

  - [~] 2.3 Update the Android block in `app/build.gradle` without changing product behavior.
    - Set compile SDK and target SDK to 36, keep min SDK 27, add namespace `com.ashwinmenon.www.calcounter`, preserve application ID `com.ashwinmenon.www.calcounter`, version code/name, debug/release variants, signing behavior, Java 8 compile options, and `minifyEnabled false`.
    - Remove the explicit Build Tools 29.0.2 pin unless the selected AGP/SDK evidence requires a literal verified Build Tools version.
    - Preserve the existing release ProGuard file reference and avoid introducing Kotlin or a Java source/target change.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 5.4, 5.5, 7.1_

- [ ] 3. Migrate and align repositories and dependencies
  - [x] 3.1 Extend the discovery tooling to produce a direct/transitive dependency inventory and repository-resolution report from empty isolated caches.
    - Identify all current coordinates, including AppCompat, Material, Commons IO, MPAndroidChart, Lombok, JUnit, and every Room runtime/compiler/optional/testing artifact.
    - Verify which dependencies require JitPack, which resolve from Google/Maven Central, whether optional Room RxJava2/Guava modules are used, and whether Lombok remains required by annotation processing.
    - Record unresolved or unapproved dependencies as release blockers rather than masking them with cached artifacts.
    - _Requirements: 1.2, 3.3, 3.4, 3.5, 7.2_

  - [~] 3.2 Update dependency declarations in `app/build.gradle` as aligned families.
    - Replace legacy AppCompat/Material/test versions with exact versions compatible with the selected AGP/API 36 toolchain; retain MPAndroidChart `v3.1.0` unless a tested approved replacement is required.
    - Use one exact Room version for runtime, compiler, retained optional modules, and Room testing; remove unused optional Room modules only after source inspection confirms they are unused.
    - Change Commons IO from `api` to `implementation`; use Lombok as `compileOnly` plus `annotationProcessor` when still needed; do not ship annotation-only tooling at runtime.
    - Ensure no dependency uses `latest`, a dynamic version, an unapproved repository, or a hidden local-cache fallback.
    - _Requirements: 3.3, 3.4, 3.5, 6.1_

  - [~] 3.3 Wire dependency resolution checks into `tools/android-upgrade/` and retain normalized dependency graphs and `dependencyInsight` output under `build/reports/android-upgrade/`.
    - Resolve from two empty isolated Gradle caches using the same source revision, wrapper, Build JDK, repositories, and pinned versions.
    - Compare the graphs and fail on any difference or any JCenter/unapproved repository resolution.
    - _Requirements: 3.4, 3.5, 6.1, 7.2_

- [ ] 4. Correct namespace, manifest contracts, and only-required Java compatibility
  - [~] 4.1 Update `app/src/main/AndroidManifest.xml` and any manifest placeholders/merge inputs.
    - Keep the namespace/application identity separate and unchanged; declare exactly one concrete `.MainActivity` launcher with `MAIN`/`LAUNCHER` and `android:exported="true"`.
    - Remove `.FoodFragment` and `.ChartFragment` activity declarations and remove `.SettingsActivity` unless task 1.2 proves a real activity exists and an approved wrapper is needed.
    - Give every retained activity an explicit `android:exported` value; remove/correct stale parent metadata and invalid parent references; preserve label, icon, theme, backup policy, and other unrelated metadata.
    - _Requirements: 2.3, 4.1, 4.2, 4.3, 4.4, 4.5, 7.1_

  - [~] 4.2 Modify only the affected Java files under `app/src/main/java/com/ashwinmenon/www/calcounter/` when the selected toolchain or lint requires it.
    - Prefer no source migration if the existing platform fragment/preference APIs compile and pass API 27/API 36 behavior checks; otherwise migrate the affected activity/fragment/preference classes consistently to AndroidX without changing preference keys (`days_to_query`, `days_to_average`), navigation, chart inputs, or calorie calculations.
    - Keep Java 8 source/bytecode compatibility. Any required move above Java 8 must be recorded with explicit approval and validated on API 27 before acceptance.
    - Do not combine unrelated fixes to static collections, deletion persistence, dates, invalid preference handling, or thread lifecycle unless a targeted compatibility failure requires the change and the blocker record explains it.
    - _Requirements: 2.4, 2.5, 6.4, 7.1, 8.3_

- [ ] 5. Inspect native libraries and make the packaging decision
  - [x] 5.1 Add an ABI/native-library inspection check under `tools/android-upgrade/` that scans `app/libs`, resolved dependency artifacts, and built APK/AAB contents for every `.so` and observed ABI.
    - Record the inspected inputs, hashes where useful, observed ABIs, and the decision evidence in `build/reports/android-upgrade/abi.json`.
    - Treat a missing or incomplete native-library inventory as a blocker; do not infer ABI requirements from the old split list.
    - _Requirements: 5.1, 5.3, 7.1_

  - [~] 5.2 Update the packaging section of `app/build.gradle` based only on task 5.1 evidence.
    - If no verified native dependency requires splits, remove manual ABI splits and configure universal APK output plus the normal release App Bundle path.
    - If splits are required, include only observed supported ABIs and exclude `armeabi`, `mips`, and `mips64`; preserve debug/release variant names, release signing behavior, and disabled shrinking.
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

  - [ ]* 5.3 Add automated packaging assertions under `tools/android-upgrade/` or the existing test harness for universal/split APK policy, obsolete ABI absence, release shrinking state, and AAB/APK artifact presence.
    - Validate the selected decision against generated artifacts rather than only checking Gradle source text.
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 6. Preserve Room schema and existing user data
  - [~] 6.1 Export the current Room version-1 schema and create a sanitized fixture/test resource for `cal_counter_database` without personal data.
    - Cover `Day`/`day` primary key `dayId`, `date`, `Food`/`food` auto-generated `food_id`, `name`, `calories`, `proteins`, `dayId`, the foreign key, and cascade-delete behavior.
    - Keep the database name and `@Database(version = 1)` if the upgraded entities/schema are identical; if a source change requires a version bump, add the explicit old-to-new migration before changing the version.
    - Do not use destructive migration, database recreation, or a committed real user database as a fallback.
    - _Requirements: 1.3, 6.1, 6.2, 6.3, 9.2_

  - [~] 6.2 Add Room unit/integration tests in `app/src/test/` and/or `app/src/androidTest/` for the approved schema path.
    - Verify opening the fixture preserves database identity, all rows/IDs/values, day associations, foreign-key behavior, and reopen behavior.
    - Verify insert, query-by-day/name, update, delete, and cascade behavior; if a migration exists, execute the exact migration and assert row-level preservation.
    - Ensure tests and diagnostics never print food names or full database contents.
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 8.4, 8.5_

  - [ ]* 6.3 Validate **Property 3: Room data preservation across the upgrade** with deterministic sanitized fixtures rather than arbitrary generated Android environments.
    - For each representative version-1 fixture, assert the filename/schema identity, every Day/Food field and key, relationships, and non-destructive behavior before and after opening or migrating.
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 8.5.**

- [ ] 7. Add calculation and core workflow coverage
  - [~] 7.1 Add focused Java unit tests under `app/src/test/java/` for `Food.getRatio()`, zero-protein behavior, calorie/protein totals, averaging over empty/one/multiple days, preference parsing/defaults, and any pure helper extracted during compatibility work.
    - Keep assertions aligned with existing behavior unless an approved compatibility correction is recorded.
    - Replace or supplement the legacy shell test at `app/src/androidTest/java/.../ApplicationTest.java` only as needed; do not leave new behavior untested.
    - _Requirements: 6.4, 7.3_

  - [~] 7.2 Add instrumentation/UI workflow tests under `app/src/androidTest/java/` that use a sanitized pre-populated database and exercise launch, existing-day display, add/read/delete behavior as discovered, calorie/protein totals, settings persistence, chart rendering, navigation, relaunch, and process recreation.
    - Run the same suite against API 27 and API 36 for debug; add release-install smoke coverage where signing permits.
    - Record each artifact/API combination separately, including Room data-preservation results, and keep personal data out of screenshots, logs, fixtures, and reports.
    - _Requirements: 6.4, 6.5, 8.3, 8.4, 8.5_

  - [ ]* 7.3 Validate **Property 5: artifact and workflow equivalence on supported APIs** using the same sanitized fixture and workflow assertions for debug/release APKs on API 27 and API 36.
    - Allow only documented platform differences; fail on data loss, install failure, changed identity, changed totals/ratio behavior, broken settings/chart/navigation, or relaunch/process-recreation regressions.
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 7.1, 7.2, 7.3, 7.4, 7.5.**

- [ ] 8. Implement deterministic configuration and correctness-property gates
  - [~] 8.1 Create a configuration verifier under `tools/android-upgrade/` that evaluates built Gradle/manifest/artifact outputs rather than relying only on source grep.
    - Assert compile/target/min SDK 36/36/27, namespace and application ID for debug/release, Java 8, approved repositories/no JCenter, variant/version/signing behavior, explicit activity exported values, exactly one MainActivity launcher, absence of fragment/stale activity declarations, ABI policy, and disabled shrinking.
    - Emit separate pass/fail records and diagnostics for every gate to `build/reports/android-upgrade/configuration.json`.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.3, 4.1, 4.2, 4.3, 4.4, 4.5, 5.2, 5.5, 7.1_

  - [~] 8.2 Add the two-isolated-cache dependency/toolchain determinism command to `tools/android-upgrade/` and retain one dependency graph report plus one toolchain report per run.
    - Use the committed wrapper and selected Build JDK, `--refresh-dependencies`, approved repositories, normalized `:app:dependencies`, Room `dependencyInsight`, and `./gradlew --version` output.
    - Fail if graph/toolchain outputs differ or if resolution requires JCenter, an unapproved repository, an unresolved placeholder, or an unapproved dependency.
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 7.2, 8.1_

  - [ ]* 8.3 Validate **Property 1: target configuration and approved-value preservation** from evaluated Gradle models, merged manifests, and baseline snapshots.
    - Compare target SDK/namespace/application ID and require an explicit approval for every unrelated variant, versioning, signing, or compatibility difference.
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 4.1.**

  - [ ]* 8.4 Validate **Property 2: dependency and toolchain resolution determinism** by comparing the normalized outputs of the two clean isolated-cache runs.
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2.**

  - [ ]* 8.5 Validate **Property 4: manifest component contract** for every built variant using merged manifests or `apkanalyzer` output.
    - Assert exactly the approved activity set, one MainActivity launcher, explicit exported values, and no `FoodFragment`, `ChartFragment`, or stale/nonexistent `SettingsActivity` activity declaration.
    - **Validates: Requirements 5.4, 5.5.**

- [ ] 9. Build, inspect, and validate distribution artifacts
  - [~] 9.1 Add a repeatable validation command under `tools/android-upgrade/` that runs clean dependency resolution, lint, unit tests, debug APK assembly, release APK assembly, and release AAB packaging with `--no-daemon`, stack traces, and warning output retained.
    - Keep diagnostics separate per gate and fail fast on an unapproved configuration, dependency, manifest, packaging, or toolchain difference.
    - _Requirements: 7.2, 7.3, 7.4, 8.2_

  - [~] 9.2 Add artifact inspection checks for debug/release APK identity, version code/name, signing behavior, manifest, installability, universal/split ABI contents, release shrink state, and release AAB metadata.
    - Produce debug and release APKs and a release AAB while preserving the existing variants; do not commit signed production artifacts or credentials.
    - _Requirements: 2.3, 2.4, 5.2, 5.4, 5.5, 7.1, 7.3, 8.2_

- [ ] 10. Add CI validation and retained evidence
  - [~] 10.1 Create `.github/workflows/android-version-upgrade.yml` using the committed Gradle wrapper, selected Build JDK, platform/API 36 SDK packages, and required Build Tools.
    - Run isolated dependency resolution, lint, unit tests, debug/release APK assembly, and release AAB packaging; avoid signing production artifacts or exposing secrets on pull requests.
    - Pin action/tool versions according to the implementation-date discovery evidence; do not add a workflow that depends on runner-global Gradle.
    - _Requirements: 3.1, 7.2, 7.3, 8.1, 8.2_

  - [~] 10.2 Add API 27/API 36 instrumentation jobs or a documented emulator matrix to the same workflow and upload all artifacts, test/lint reports, dependency/toolchain/configuration reports, blocker records, and sanitized fixture results with retention of at least 30 days.
    - Keep debug and release API/artifact checks separate and record Room preservation and Core Workflow outcomes separately for all four combinations.
    - _Requirements: 6.4, 6.5, 7.3, 7.4, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Record blockers, validate rollback, and close the release gate
  - [~] 11.1 Create a blocker-record command/schema under `tools/android-upgrade/` that captures blocker type, source revision, exact command, selected toolchain, failing gate, diagnostics path, reproduction steps, and evidence links.
    - Invoke it for toolchain incompatibility, unresolved dependency, manifest invalidity, artifact/install failure, API behavior regression, schema/migration failure, data loss, or missing retention evidence; stop release acceptance while any blocker is unresolved.
    - _Requirements: 3.4, 6.3, 7.4, 9.1, 9.4_

  - [~] 11.2 Add rollback validation under `tools/android-upgrade/` and automated checks for the retained last-known-good revision/configuration/toolchain/dependency graph/fixture/artifact record.
    - Verify rollback identity, signing identity, version code policy, installation outcome, database filename/schema/row outcome, and the ability to restore the known-good build without destructive migration.
    - Preserve the pre-upgrade wrapper/build files and sanitized fixture until all target gates pass; do not lower a store version code without an explicitly recorded release decision.
    - _Requirements: 6.1, 6.2, 6.3, 9.2, 9.3_

  - [~] 11.3 Generate the final accepted-or-blocked validation summary under `build/reports/android-upgrade/final-summary.json` and wire it into CI artifact upload.
    - Include baseline discrepancies, approved differences, gate results, unresolved risks, blocker records, retained rollback evidence, and the final release decision; fail the workflow if the summary is blocked or incomplete.
    - _Requirements: 1.5, 7.4, 9.1, 9.2, 9.3, 9.4_

## Checkpoints

- [~] 12. Checkpoint after baseline/toolchain discovery
  - Ensure the baseline, source discovery, and dated official AGP/Gradle/Build JDK evidence are complete before changing any wrapper, repository, dependency, manifest, or source file.
  - If the actual revision differs from the design’s observed baseline, record every discrepancy and ask for approval where a fixed compatibility decision would change.

- [~] 13. Checkpoint after build, dependency, manifest, and packaging migration
  - Ensure isolated-cache resolution, lint, unit tests, merged-manifest checks, native-library inspection, and packaging policy checks pass before proceeding to device workflows.
  - Create a blocker record and stop release acceptance for any unapproved repository, dependency, manifest, ABI, signing, or shrink-state difference.

- [~] 14. Checkpoint after persistence and workflow validation
  - Ensure Room fixture preservation and core workflow tests pass separately for debug/release artifacts on API 27/API 36 before declaring compatibility.
  - Do not approve a schema bump, destructive fallback, or behavior change without explicit migration/compatibility evidence.

- [~] 15. Final checkpoint - Ensure all tests pass and rollback is proven
  - Ensure all configuration, dependency, build, lint, unit, Room, instrumentation, artifact, CI-retention, blocker, and rollback checks pass; ask the user if questions arise.
  - The workflow is blocked until the final summary is accepted and the last-known-good record remains retrievable.

## Notes

- Tasks marked with `*` are optional test/validation subtasks and may be skipped only for a documented reason; the mandatory build, data, API, and release gates still need evidence.
- The design contains a **Correctness Properties** section, so each property is represented by a dedicated practical validation task. These are deterministic configuration comparisons, sanitized Room fixtures, manifest inspection, and API workflow checks—not arbitrary 100-case Android environment generation.
- No exact AGP, Gradle, Build JDK, dependency, CI action, emulator image, or Build Tools patch version is invented here. Task 1.3 must record exact versions and dated official evidence before task 2 changes the wrapper/build configuration.
- The current manifest declares fragment classes as activities and declares a stale/missing settings activity; task 1.2 must confirm external references before task 4.1 removes or retains declarations.
- The current app uses Java platform fragments/preferences, Room schema version 1, database name `cal_counter_database`, static mutable collections, raw background threads, and verbose food/database logging. Only compatibility-required source changes belong in task 4.2; user-data logging must not remain in validation or release diagnostics.
- The current `FoodFragment` removes a food from the adapter without visibly deleting it through `FoodDao`; task 7.2 must characterize that existing behavior before changing it, and any intentional correction must be recorded separately from the SDK migration.
- The current root/app files contain JCenter, JitPack, legacy dependency versions, an unused Room version variable, explicit Build Tools 29.0.2, and obsolete ABI values. All must be verified against the baseline and dependency inventory rather than changed blindly.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "3.1", "5.1"] },
    { "id": 2, "tasks": ["2.1", "2.2", "6.1"] },
    { "id": 3, "tasks": ["2.3", "4.1", "4.2"] },
    { "id": 4, "tasks": ["3.2", "6.2", "7.1", "8.1"] },
    { "id": 5, "tasks": ["3.3", "5.2", "6.3", "7.2", "8.2", "8.3", "8.4", "8.5"] },
    { "id": 6, "tasks": ["5.3", "9.1", "10.1", "11.1"] },
    { "id": 7, "tasks": ["7.3", "9.2", "10.2", "11.2"] },
    { "id": 8, "tasks": ["11.3"] }
  ]
}
```
