# Output Quality Standards

Use these rules when writing pages in `generate-pages`.

## Required Shape

Every generated Markdown page must:

- Start with one H1.
- Put `<details open><summary>Relevant source files</summary>` or `<summary>相关源文件</summary>` immediately after the H1.
- List relevant source files as a tree, not a table.
- Use `file:///path#Lx-Ly` source links with line ranges.
- Include at least one H2 section.
- Explain WHY and HOW, not only WHAT.
- Link to related wiki pages when relevant.

## Source Block Template

```markdown
<details open>
<summary>Relevant source files</summary>

- src/
  - [app.py](file:///src/app.py#L1-L40) `L1-L40` - runtime entry and dispatch

</details>
```

## Mermaid Rules

- Add a short paragraph before every Mermaid block explaining what the diagram shows.
- Prefer `flowchart TD` for workflows and architecture, `sequenceDiagram` for interactions, `classDiagram` for types, and `stateDiagram-v2` for state transitions.
- Use quoted labels for spaces, punctuation, and non-ASCII text.
- Run `deepwiki mermaid <project_path> --validate` before final delivery when `mmdc` is installed.

## Final Checks

Run:

```bash
deepwiki mermaid <project_path> --validate
deepwiki quality <project_path>
deepwiki finalize <project_path>
```

`finalize` already runs menu generation, Mermaid repair/validation, quality checks, and link checks.
