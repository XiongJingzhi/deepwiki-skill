# TODO: Known Limitations and Planned Improvements

## P1 - File Importance Scoring Lacks Relative Normalization

**Status**: Fixed — percentile-based normalization (`normalize_path_scores()`) now applied intra-module; single-file module branch recalculates `importance_score`/`is_core`/`is_high_priority`; module importance recalculated after file normalization in `analyze_project()`. See commit `fix: recalculate module importance scores after file-level path score normalization`.

**Problem**: `calculate_file_importance()` uses absolute scoring thresholds. All files under `src/` receive `path_score=1.0` (30% weight), which means a trivial `src/constants.py` can score similarly to `src/engine/core.py`. When module importance is computed as the average of file scores (`discover_modules()`), low-value modules like `src/config/` can rank alongside high-value modules like `src/core/`, causing incorrect prioritization during documentation generation.

**Affected functions**:
- `scripts/analyze_project.py`: `calculate_file_importance()` (L536), `discover_modules()` (L321)

**Proposed approach**: Introduce percentile-based normalization within each module's sibling group, or compute module importance relative to the project's score distribution rather than absolute thresholds.

---

## P2 - Monorepo Package Structure Not Fully Supported

**Status**: Partially working (root-level `packages/*/` and `apps/*/` are detected, but nested `packages/*/src/` patterns are not individually analyzed)

**Problem**: `detect_monorepo_tools()` detects monorepo tooling but does not influence module discovery behavior. `discover_modules()` finds direct children of `packages/` and `apps/` directories, but does not:
1. Read `pnpm-workspace.yaml` glob patterns to discover all workspace packages
2. Handle deeply nested structures like `packages/libs/utils/src/`
3. Detect inter-package dependency relationships

**Affected functions**:
- `scripts/analyze_project.py`: `discover_modules()` (L321), `detect_monorepo_tools()` (L140)

**Proposed approach**: When monorepo is detected, read workspace configuration files and use their glob patterns as additional source directories for module discovery.

---

## P2 - No Module Grouping / Hierarchy Support

**Status**: Not started

**Problem**: `discover_modules()` returns a flat list. There is no concept of parent-child relationships or logical grouping. In real projects, `src/components/`, `src/pages/`, and `src/layouts/` may all belong to a "frontend" group, while `src/services/`, `src/repositories/`, and `src/models/` belong to a "backend" group. The menu generator (`generate_menu.py`) and quality checker (`check_quality.py`) cannot leverage grouping information.

**Affected functions**:
- `scripts/analyze_project.py`: `discover_modules()` (L321) -- needs to return group metadata
- `scripts/generate_menu.py`: `build_menu()` (L30) -- needs to render grouped modules
- `scripts/check_quality.py`: `calculate_expected_metrics()` (L222) -- could use group-level expectations

**Proposed approach**: Add an optional `group` field to module output. Grouping can be inferred from common parent directories (e.g., all modules under `src/` with type "ui" form a "UI" group), or from an explicit `deepwiki.groups` config in `config.yaml`.
