# Requirements Document

## Introduction

This feature upgrades the existing CalCounter Android application to Android 16/API 36 without changing the product’s calorie-tracking behavior or existing app identity. The upgrade covers the actual one-module Java/Room repository, build-tool compatibility, dependency resolution, modern Android configuration, packaging, persistence, CI validation, and rollback evidence.

## Glossary

- **CalCounter App**: The existing Java Android application in the repository’s single `:app` module.
- **Upgrade Process**: The implementation and validation work that changes the CalCounter App for Android 16/API 36.
- **Baseline Record**: A source-revision-specific inventory of modules, build tools, dependencies, manifest components, variants, signing behavior, data contracts, and packaging settings.
- **Room Data Store**: The existing Room database named `cal_counter_database`, including the `Day` and `Food` entities, DAOs, schema, keys, and relationships.
- **Core Workflows**: Launch, existing-day display, food entry, food display, calorie and protein calculations, settings, chart display, navigation, relaunch, and process recreation.
- **Approved Repositories**: `google()` and `mavenCentral()`, plus JitPack only when a verified dependency requires JitPack.
- **Validation Record**: Reproducible results from configuration checks, dependency resolution, builds, tests, device checks, artifact inspection, and blocker decisions.
- **Build Configuration**: The repository’s Gradle files, wrapper settings, Android module settings, dependency declarations, and CI toolchain declarations.
- **Android Manifest**: The merged and source manifest declarations that define the CalCounter App’s Android components, intent filters, exported state, and application metadata.
- **CI Build**: The non-interactive continuous-integration workflow that resolves dependencies, builds artifacts, runs checks, and retains validation reports.
- **AGP**: Android Gradle Plugin, the Gradle plugin that builds the Android application.
- **Build JDK**: The Java Development Kit used to run Gradle and AGP.
- **ABI**: Android binary interface used to classify native libraries and device-specific packaging.

## Requirements

### Requirement 1: Establish an immutable implementation baseline

**User Story:** As an implementer, I want a source-specific baseline, so that the upgrade does not rely on stale or unconfirmed assumptions.

#### Acceptance Criteria

1. WHEN the Upgrade Process begins, THE Baseline Record SHALL record the immutable source revision identifier and the complete working-tree state before any edit.
2. WHEN the baseline inventory completes, THE Baseline Record SHALL identify exactly one `:app` module implemented with Java and Room, and SHALL inventory local libraries, dependency declarations, repository declarations, the Android Manifest, variants, signing behavior, ABI configuration, CI configuration, and existing tests.
3. WHEN the Room inventory completes, THE Baseline Record SHALL record the Room Data Store as schema version 1 with the `Day` and `Food` entities, their DAOs, keys, values, associations, and foreign-key relationship.
4. WHEN previously observed baseline values are recorded, THE Baseline Record SHALL mark each value as unconfirmed and SHALL include AGP 4.1.1, Gradle 6.5, build tools 29.0.2, compile SDK 30, target SDK 30, minimum SDK 27, Java 8, `google()`, JCenter, and JitPack, every previously observed dependency coordinate and version, and the previously observed manifest and ABI findings.
5. IF the inspected source revision or working-tree state differs from a previously observed baseline, THEN THE Upgrade Process SHALL record each discrepancy in the Baseline Record before editing build or source files.

### Requirement 2: Preserve fixed Android and application compatibility

**User Story:** As an existing user, I want the upgraded app to remain the same application, so that existing installs and workflows continue to work.

#### Acceptance Criteria

1. WHEN the Android build configuration is updated, THE CalCounter App SHALL use compile SDK 36 and target SDK 36.
2. WHEN the Android build configuration is updated, THE CalCounter App SHALL use minimum SDK 27.
3. WHEN debug and release application identities are evaluated, THE CalCounter App SHALL use application ID `com.ashwinmenon.www.calcounter` for both variants.
4. WHEN variants are evaluated, THE CalCounter App SHALL preserve the existing debug and release variants, versioning behavior, and signing behavior.
5. WHEN Java compilation is evaluated, THE CalCounter App SHALL use Java 8 source and bytecode compatibility.
6. IF an implementation change from Java 8 or another fixed compatibility decision is proposed, THEN THE Upgrade Process SHALL obtain explicit approval and SHALL validate the change on API 27 before acceptance.

### Requirement 3: Select a compatible, pinned toolchain and dependency set

**User Story:** As a maintainer, I want a supported and reproducible build toolchain, so that local and CI builds do not depend on obsolete or cached artifacts.

#### Acceptance Criteria

1. WHEN AGP, Gradle, and the Build JDK are selected, THE Upgrade Process SHALL select exact versions supported for Android 16/API 36 by dated official compatibility evidence that also verifies compatibility among the three versions.
2. WHEN the toolchain is committed, THE Build Configuration SHALL pin literal AGP, Gradle, Build JDK, and required Android build-tool versions and SHALL contain no `latest` or unresolved version placeholder.
3. WHEN repositories are configured, THE Build Configuration SHALL use `google()` and `mavenCentral()`, SHALL use JitPack only when a verified dependency requires JitPack, and SHALL contain no JCenter declaration.
4. IF a dependency cannot resolve from the configured Approved Repositories or lacks approval for the selected toolchain, THEN THE Upgrade Process SHALL record the dependency and block release acceptance until the dependency is replaced or explicitly approved.
5. WHEN Room dependencies are declared, THE Build Configuration SHALL use one exact compatible Room version across Room runtime, compiler, optional Room modules, and Room test helpers.
6. WHEN dependency determinism is validated, THE Upgrade Process SHALL resolve dependencies from two empty isolated caches using the same source revision, wrapper, Build JDK, repositories, and pinned versions, and SHALL prove that both resolutions produce the identical dependency graph.

### Requirement 4: Correct namespace and Android Manifest component contracts

**User Story:** As an Android user, I want the upgraded application to launch through valid Android components, so that target SDK enforcement does not break the app.

#### Acceptance Criteria

1. WHEN the Android namespace and application identity are configured, THE CalCounter App SHALL define namespace `com.ashwinmenon.www.calcounter` separately from application ID `com.ashwinmenon.www.calcounter`.
2. WHEN the Android Manifest is merged, THE Android Manifest SHALL declare exactly one concrete `MainActivity` activity and SHALL declare no `FoodFragment`, `ChartFragment`, or `SettingsActivity` component.
3. WHEN the launcher intent filter is merged, THE Android Manifest SHALL contain exactly one `MAIN`/`LAUNCHER` entry attached to `MainActivity`, and `MainActivity` SHALL have `android:exported="true"`.
4. WHEN any activity is declared, THE Android Manifest SHALL specify an explicit `android:exported` value for that activity.
5. IF the Android Manifest contains an invalid parent reference or stale component metadata, THEN THE Upgrade Process SHALL remove or correct the declaration and SHALL record the resulting manifest decision.

### Requirement 5: Validate native packaging and preserve release behavior

**User Story:** As a release maintainer, I want valid APK and App Bundle packaging, so that supported devices receive installable artifacts without obsolete ABI assumptions.

#### Acceptance Criteria

1. WHEN packaging configuration is reviewed, THE Upgrade Process SHALL inspect local libraries, resolved dependencies, and generated artifacts for native `.so` libraries and SHALL record every observed ABI.
2. WHEN no verified native dependency requires ABI splits, THE CalCounter App SHALL remove manual ABI splits and SHALL produce a universal APK and a release App Bundle without manual ABI filters.
3. IF verified native dependencies require ABI splits, THEN THE Upgrade Process SHALL include only observed, non-obsolete ABIs supplied by those dependencies and SHALL exclude `armeabi`, `mips`, and `mips64`.
4. WHEN artifact validation runs, THE CalCounter App SHALL produce debug and release APKs and a release AAB while preserving the existing debug and release variants.
5. WHEN release packaging is evaluated, THE CalCounter App SHALL preserve signing behavior and SHALL keep code shrinking disabled.

### Requirement 6: Preserve Room data and core calorie-tracking behavior

**User Story:** As an existing user, I want saved data and calorie-tracking workflows preserved, so that the Android upgrade does not change the app’s meaning or erase information.

#### Acceptance Criteria

1. WHEN an existing Room Data Store is opened by the upgraded app, THE Room Data Store SHALL preserve the database filename and identity `cal_counter_database`, every `Day` and `Food` row, every primary key and field value, every day association, and the existing foreign-key behavior.
2. IF a schema change is required, THEN THE Upgrade Process SHALL provide an explicit tested Room migration from schema version 1 that preserves existing data before changing the database version.
3. IF a required Room migration cannot be proven with validation evidence, THEN THE Upgrade Process SHALL block release acceptance and SHALL preserve the existing data without using destructive database recreation as a fallback.
4. WHEN the Core Workflows run on API 27 and API 36, THE CalCounter App SHALL produce equivalent outcomes for launch, existing-day display, food entry, food display, calorie totals, protein calculations, settings, chart display, navigation, relaunch, and process recreation.
5. WHEN existing user data is used during validation, THE Upgrade Process SHALL keep personal data out of repository files and logs.

### Requirement 7: Execute deterministic configuration and compatibility gates

**User Story:** As a maintainer, I want deterministic checks, so that configuration regressions are detected before device testing or release.

#### Acceptance Criteria

1. WHEN configuration validation runs, THE Validation Record SHALL contain a separate pass or fail result for compile SDK 36, target SDK 36, minimum SDK 27, namespace, application ID in debug and release, Java 8, Approved Repositories, absence of JCenter, debug and release variants, versioning behavior, signing behavior, explicit activity exported values, the single `MainActivity` launcher contract, absence of `FoodFragment`, `ChartFragment`, and `SettingsActivity` declarations, the ABI decision, and disabled shrinking.
2. WHEN dependency determinism validation runs, THE Upgrade Process SHALL perform the two empty-isolated-cache resolutions and SHALL retain a separate dependency graph report and toolchain report for each run.
3. WHEN isolated clean validation runs, THE Upgrade Process SHALL execute dependency resolution, lint, unit tests, debug APK assembly, release APK assembly, and release AAB packaging, and SHALL retain diagnostics for each gate.
4. IF any configuration, dependency, manifest, packaging, or toolchain check produces an unapproved difference, THEN THE Upgrade Process SHALL record the difference and block release acceptance until the difference is resolved or explicitly approved.

### Requirement 8: Validate CI and artifacts on API 27 and API 36

**User Story:** As a contributor, I want CI and artifact checks to cover the supported API range, so that a successful local build is not the only evidence of compatibility.

#### Acceptance Criteria

1. WHEN the CI Build runs, THE CI Build SHALL use the committed Gradle wrapper, the selected Build JDK, and the pinned Android SDK and build-tool packages required for API 36 and minimum API 27.
2. WHEN the CI Build performs validation, THE CI Build SHALL run dependency resolution, lint, unit tests, debug APK assembly, release APK assembly, and release App Bundle packaging, and SHALL retain every artifact and validation report for at least 30 days.
3. WHEN device validation runs, THE Upgrade Process SHALL install and validate the debug APK on API 27, the release APK on API 27, the debug APK on API 36, and the release APK on API 36 as four separate checks.
4. WHEN the four artifact and API checks complete, THE Validation Record SHALL record Room data-preservation results separately for each artifact and API combination and SHALL record Core Workflows results separately for each artifact and API combination.

### Requirement 9: Record blockers and preserve rollback capability

**User Story:** As a release owner, I want explicit blocker and rollback reporting, so that an unsafe upgrade cannot be released and a known-good build remains recoverable.

#### Acceptance Criteria

1. IF toolchain compatibility, dependency resolution, manifest validity, artifact installability, API behavior, or Room data preservation fails, THEN THE Upgrade Process SHALL create a reproducible blocker record with the failing revision, command, diagnostics, and evidence, and SHALL stop release acceptance.
2. WHEN the upgrade record is finalized, THE Upgrade Process SHALL retain a retrievable last-known-good source revision, Build Configuration, toolchain, dependency graph, non-personal fixture, and artifact record.
3. WHEN rollback validation runs, THE Upgrade Process SHALL test the rollback identity, signing identity, version code, installation outcome, and Room data outcome against the retained last-known-good record.
4. WHEN final validation is complete, THE Validation Record SHALL provide an accepted-or-blocked summary containing baseline discrepancies, approved differences, gate results, unresolved risks, blocker records, and the rollback decision.
