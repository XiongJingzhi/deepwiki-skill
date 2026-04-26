# Deep Dive Navigation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merge capability and internal implementation documentation into a single `deep-dive` wiki section named `深入理解`.

**Architecture:** New generated module pages should use `wiki/deep-dive/*.md`. Existing `capabilities/` and `internals/` directories remain readable as legacy inputs during menu reconciliation so already generated projects do not lose navigation immediately.

**Tech Stack:** Python standard library, pytest, DeepWiki helper scripts.

---

### Task 1: Topology Output

**Files:**
- Modify: `scripts/plan_doc_topology.py`
- Test: `tests/test_plan_doc_topology.py`

**Steps:**
1. Add a failing test that module pages use `wiki/deep-dive/*.md` and group under `deep-dive`.
2. Update `_page_bucket()` and `groupings` to emit the new group.
3. Run `pytest tests/test_plan_doc_topology.py -q`.

### Task 2: Menu Generation

**Files:**
- Modify: `scripts/generate_menu.py`
- Test: `tests/test_generate_menu.py`

**Steps:**
1. Add failing tests for `wiki/deep-dive/*.md` producing a `深入理解` section.
2. Update labels, known directories, topology label mapping, directory scanning, and reconcile additions.
3. Keep legacy `capabilities/` and `internals/` files readable as `深入理解`.
4. Run `pytest tests/test_generate_menu.py -q`.

### Task 3: Init And Docs

**Files:**
- Modify: `scripts/init_wiki.py`
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `references/**/*.md`
- Test: `tests/test_init_wiki.py`

**Steps:**
1. Add a failing test for creating `.deepwiki/wiki/deep-dive`.
2. Update init scaffolding and documentation references.
3. Run targeted tests.

### Task 4: Verification

Run:

```bash
pytest tests/test_plan_doc_topology.py tests/test_generate_menu.py tests/test_init_wiki.py -q
```
