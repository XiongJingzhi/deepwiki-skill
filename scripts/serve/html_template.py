"""DeepWiki wiki 预览页面的 HTML/CSS/JS 模板。"""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeepWiki</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github-dark.min.css">
<script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --sidebar-width: 260px;
  --toc-width: 200px;
  --source-width: 40vw;
  --header-height: 52px;
  --bg: #ffffff;
  --bg-sidebar: #ffffff;
  --bg-toc: #f6f8fa;
  --text: #1f2328;
  --text-secondary: #656d76;
  --border: #d1d9e0;
  --accent: #0969da;
  --accent-hover: #0550ae;
  --code-bg: #0d1117;
  --heading-color: #1f2328;
  --link-color: #0969da;
}

html, body { height: 100%; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
  background: var(--bg);
}

a { color: var(--link-color); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Header */
.header {
  position: fixed; top: 0; left: 0; right: 0;
  height: var(--header-height);
  background: var(--bg);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center;
  padding: 0 20px;
  z-index: 0;
  font-size: 16px; font-weight: 600;
}

.header .logo { margin-right: 12px; font-size: 20px; }
.header .title { color: var(--text); }
.header .title span { color: var(--text-secondary); font-weight: 400; margin-left: 8px; font-size: 14px; }

/* Layout */
.layout {
  position: fixed;
  top: var(--header-height);
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
}

/* Left Sidebar */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100%;
  overflow-y: auto;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border);
  padding: 16px 0 24px;
}

.sidebar::-webkit-scrollbar { width: 6px; }
.sidebar::-webkit-scrollbar-thumb { background: #c1c8cd; border-radius: 3px; }

.menu-group { margin-bottom: 8px; }
.menu-group-title {
  padding: 10px 20px 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0;
  text-transform: none;
}
.menu-group-title:hover { color: var(--accent); }
.menu-group-title .arrow {
  display: inline-block;
  transition: transform 0.2s;
  font-size: 9px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.menu-group.collapsed .arrow { transform: rotate(-90deg); }
.menu-group.collapsed .menu-items { display: none; }

.menu-items { list-style: none; }
.menu-item a {
  display: block;
  padding: 5px 20px 5px 20px;
  color: var(--text-secondary);
  font-size: 14px;
  text-decoration: none;
  border-radius: 6px;
  margin: 1px 8px;
  transition: background 0.15s, color 0.15s;
}
.menu-item a:hover { background: #f0f2f4; color: var(--text); text-decoration: none; }
.menu-item.active a {
  background: #eaeef2;
  color: var(--text);
  font-weight: 500;
}
.menu-sub-item a {
  padding-left: 32px;
  font-size: 13.5px;
  color: var(--text-secondary);
}
.menu-sub-item.active a { color: var(--text); background: #eaeef2; font-weight: 500; }

/* 3rd level: collapsible sub-group */
.menu-sub-group-title {
  padding: 6px 20px 4px 32px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-top: 8px;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  gap: 6px;
  text-transform: none;
  letter-spacing: 0;
}
.menu-sub-group-title:hover { color: var(--text); }
.menu-sub-group-title .arrow {
  display: inline-block;
  transition: transform 0.2s;
  font-size: 9px;
  color: var(--text-secondary);
}
.menu-sub-group.collapsed > .menu-sub-group-title .arrow { transform: rotate(-90deg); }
.menu-sub-group.collapsed > .menu-sub-items { display: none; }
.menu-sub-items { list-style: none; }
.menu-sub-sub-item a {
  padding-left: 44px;
  font-size: 13px;
  color: var(--text-secondary);
  border-radius: 6px;
  margin: 1px 8px;
  transition: background 0.15s, color 0.15s;
}
.menu-sub-sub-item a:hover { background: #f0f2f4; color: var(--text); text-decoration: none; }
.menu-sub-sub-item.active a { color: var(--text); background: #eaeef2; font-weight: 500; }

/* Main Content */
.content-wrapper {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 32px 48px 80px;
}

.content-wrapper::-webkit-scrollbar { width: 8px; }
.content-wrapper::-webkit-scrollbar-thumb { background: #c1c8cd; border-radius: 4px; }

#content { max-width: 860px; margin: 0 auto; }
#content h1 { font-size: 2em; margin: 0 0 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
#content h2 { font-size: 1.5em; margin: 32px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
#content h3 { font-size: 1.25em; margin: 24px 0 8px; }
#content h4 { font-size: 1.1em; margin: 20px 0 8px; font-weight: 600; }
#content p { margin: 0 0 12px; }
#content ul, #content ol { margin: 0 0 12px; padding-left: 24px; }
#content li { margin-bottom: 4px; }
#content strong { font-weight: 600; }

#content pre {
  position: relative;
  background: var(--code-bg);
  color: #e6edf3;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.5;
}
#content pre code.hljs {
  background: transparent;
  padding: 0;
}
#content code {
  font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  font-size: 0.9em;
}
#content :not(pre) > code {
  background: #eff1f3;
  color: var(--text);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.85em;
}
#content blockquote {
  border-left: 4px solid var(--border);
  padding: 8px 16px;
  margin: 0 0 16px;
  color: var(--text-secondary);
  background: var(--bg-sidebar);
  border-radius: 0 4px 4px 0;
}
#content table { border-collapse: collapse; margin: 0 0 16px; width: 100%; }
#content th, #content td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
#content th { background: var(--bg-sidebar); font-weight: 600; }
#content img { max-width: 100%; border-radius: 6px; margin: 8px 0; }

/* Source links */
#content details {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 0 0 18px;
  background: #fff;
}
#content summary {
  cursor: pointer;
  font-weight: 700;
  color: var(--text);
}
#content a.source-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  padding: 4px 8px;
  border-radius: 7px;
  background: #eaeef2;
  color: #24292f;
  font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  font-size: 0.88em;
  font-weight: 650;
  line-height: 1.4;
  vertical-align: baseline;
  text-decoration: none;
}
#content a.source-link:hover {
  background: #d8dee4;
  color: #0969da;
  text-decoration: none;
}
#content a.source-link.active {
  background: #ddf4ff;
  color: #0969da;
  box-shadow: inset 0 0 0 1px rgba(9, 105, 218, 0.18);
}
#content a.source-link::before {
  content: "{}";
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #f6f8fa;
  color: #6e7781;
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 9px;
  font-weight: 800;
  flex: 0 0 auto;
}
#content a.source-link .source-path {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
#content a.source-link .source-line-range {
  margin: -4px -8px -4px 0;
  padding: 4px 8px;
  border-left: 1px solid rgba(31, 35, 40, 0.08);
  border-radius: 0 7px 7px 0;
  background: rgba(208, 215, 222, 0.82);
  color: #57606a;
  font-weight: 700;
  white-space: nowrap;
}

/* Mermaid diagrams */
.mermaid-container {
  position: relative;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 52px 16px 16px;
  margin: 0 0 16px;
  text-align: center;
  overflow-x: auto;
}
.mermaid-container svg { max-width: 100%; height: auto; }
.mermaid-toolbar {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.16s ease, transform 0.16s ease;
  z-index: 2;
}
.mermaid-container:hover .mermaid-toolbar,
.mermaid-container:focus-within .mermaid-toolbar {
  opacity: 1;
  transform: translateY(0);
}
.mermaid-action {
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.92);
  color: var(--text);
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(31, 35, 40, 0.08);
}
.mermaid-action:hover {
  border-color: var(--accent);
  color: var(--accent);
}
.mermaid-action.copied {
  color: #1a7f37;
  border-color: #1a7f37;
}
.mermaid-modal {
  position: fixed;
  inset: 0;
  z-index: 500;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: rgba(13, 17, 23, 0.72);
  backdrop-filter: blur(8px);
}
.mermaid-modal.open { display: flex; }
.mermaid-modal-panel {
  width: min(1200px, 96vw);
  height: min(820px, 92vh);
  background: #fff;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.mermaid-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  background: #f6f8fa;
}
.mermaid-modal-title {
  font-weight: 700;
  color: var(--text);
}
.mermaid-modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.mermaid-zoom-value {
  min-width: 48px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 700;
}
.mermaid-modal-body {
  flex: 1;
  overflow: auto;
  padding: 28px;
  cursor: grab;
  user-select: none;
}
.mermaid-modal-body.dragging { cursor: grabbing; }
.mermaid-zoom-stage {
  min-width: 100%;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transform-origin: center center;
  transition: transform 0.12s ease;
  will-change: transform;
}
.mermaid-zoom-stage svg {
  max-width: none;
  width: auto;
  height: auto;
}

/* Right TOC Sidebar */
.toc {
  width: var(--toc-width);
  min-width: var(--toc-width);
  height: 100%;
  overflow-y: auto;
  background: var(--bg-toc);
  border-left: 1px solid var(--border);
  padding: 16px 0;
  position: sticky;
  top: var(--header-height);
}
.toc-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  padding: 0 16px 8px;
}
.toc-list { list-style: none; }
.toc-list li a {
  display: block;
  padding: 3px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: all 0.15s;
}
.toc-list li a:hover { color: var(--text); text-decoration: none; }
.toc-list li.active a {
  color: var(--accent);
  border-left-color: var(--accent);
}
.toc-list .toc-h3 a { padding-left: 28px; }

/* Source preview */
.source-backdrop {
  position: fixed;
  inset: 0;
  z-index: 650;
  display: none;
  background: transparent;
}
.source-backdrop.open { display: block; }
.source-panel {
  width: var(--source-width);
  min-width: min(520px, 100vw);
  max-width: 100vw;
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  z-index: 700;
  display: none;
  flex-direction: column;
  background: #0d1117;
  color: #e6edf3;
  border-left: 1px solid #30363d;
  box-shadow: -18px 0 42px rgba(13, 17, 23, 0.28);
}
.source-panel.open { display: flex; }
.source-panel.expanded {
  width: 100vw;
  min-width: 0;
  max-width: 100vw;
}
.source-panel-header {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 52px;
  padding: 10px 12px;
  border-bottom: 1px solid #30363d;
  background: #161b22;
}
.source-panel-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.source-panel-path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  font-size: 12px;
  font-weight: 700;
  color: #f0f6fc;
}
.source-panel-range {
  font-size: 11px;
  color: #8b949e;
}
.source-panel-actions {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
}
.source-panel-action {
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  border: 1px solid #30363d;
  border-radius: 6px;
  background: #21262d;
  color: #c9d1d9;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}
.source-panel-action:hover {
  border-color: #58a6ff;
  color: #58a6ff;
}
.source-panel-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.55;
}
.source-panel-empty,
.source-panel-error {
  padding: 24px;
  color: #8b949e;
}
.source-panel-error { color: #ffb4a8; }
.source-code-table {
  width: 100%;
  border-collapse: collapse;
}
.source-code-table td {
  padding: 0;
  vertical-align: top;
}
.source-code-table .source-line-number {
  width: 1%;
  min-width: 54px;
  padding: 0 24px 0 12px;
  color: #6e7681;
  text-align: right;
  user-select: none;
  border-right: 1px solid #21262d;
}
.source-code-table .source-line-code {
  padding: 0 16px 0 0;
  white-space: pre;
}
.source-line.highlight {
  background: rgba(187, 128, 9, 0.22);
}
.source-line.highlight .source-line-number {
  color: #d29922;
  border-right-color: rgba(210, 153, 34, 0.36);
}

/* Directory tree */
.dir-tree {
  padding: 16px 12px;
  font-family: "SF Mono", "Fira Code", "Fira Mono", Menlo, Consolas, monospace;
  font-size: 13px;
  color: #c9d1d9;
}
.dir-tree-list {
  list-style: none;
  padding-left: 16px;
  margin: 0;
}
.dir-tree > .dir-tree-list { padding-left: 4px; }
.dir-tree-dir > .dir-tree-list { display: none; }
.dir-tree-dir.open > .dir-tree-list { display: block; }
.dir-tree-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  user-select: none;
  color: #e6edf3;
  font-weight: 600;
}
.dir-tree-toggle:hover { background: rgba(255,255,255,0.08); }
.dir-tree-file {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 2px 4px;
  color: #8b949e;
}
.dir-tree-icon { font-size: 13px; flex-shrink: 0; }

/* Loading */
.loading {
  display: flex; align-items: center; justify-content: center;
  height: 200px; color: var(--text-secondary);
}
.spinner {
  width: 24px; height: 24px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 12px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Responsive */
@media (max-width: 1200px) {
  .toc { display: none; }
  .source-panel { min-width: min(72vw, 520px); }
}
@media (max-width: 768px) {
  .sidebar { width: 220px; min-width: 220px; }
  .content-wrapper { padding: 24px 20px 60px; }
  .source-panel {
    width: 94vw;
    min-width: 0;
  }
}

/* Page navigation (prev / next) */
.page-nav {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 12px;
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  max-width: 860px;
  margin-left: auto;
  margin-right: auto;
}
.page-nav-btn {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  text-decoration: none;
  color: var(--text);
  background: var(--bg-sidebar);
  min-width: 0;
  max-width: 48%;
  transition: border-color 0.15s, background 0.15s;
  cursor: pointer;
  font-size: 14px;
}
.page-nav-btn:hover { border-color: var(--accent); background: var(--bg); text-decoration: none; }
.page-nav-btn.prev { justify-content: flex-start; }
.page-nav-btn.next { justify-content: flex-end; margin-left: auto; }
.page-nav-arrow { font-size: 16px; color: var(--text-secondary); flex-shrink: 0; }
.page-nav-title { font-weight: 500; color: var(--accent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
</head>
<body>
<div class="header">
  <div class="logo">&#128218;</div>
  <div class="title" id="header-title">DeepWiki</div>
</div>
<div class="layout">
  <nav class="sidebar" id="sidebar"></nav>
  <main class="content-wrapper">
    <div id="content">
      <div class="loading"><div class="spinner"></div>Loading...</div>
    </div>
  </main>
<aside class="toc" id="toc">
    <div class="toc-title">On this page</div>
    <ul class="toc-list" id="toc-list"></ul>
  </aside>
  <div class="source-backdrop" id="source-backdrop" onclick="closeSourcePanel()" aria-hidden="true"></div>
  <aside class="source-panel" id="source-panel" aria-label="Source preview">
    <div class="source-panel-header">
      <div class="source-panel-title">
        <div class="source-panel-path" id="source-panel-path">Source</div>
        <div class="source-panel-range" id="source-panel-range"></div>
      </div>
      <div class="source-panel-actions">
        <button class="source-panel-action" id="source-panel-expand" type="button" aria-label="Expand source preview" title="Expand source preview" onclick="toggleSourcePanelSize()">&#x26F6;</button>
        <button class="source-panel-action" type="button" aria-label="Close source preview" title="Close source preview" onclick="closeSourcePanel()">&times;</button>
      </div>
    </div>
    <div class="source-panel-body" id="source-panel-body">
      <div class="source-panel-empty">Click a source reference to inspect code.</div>
    </div>
  </aside>
</div>
<div class="mermaid-modal" id="mermaid-modal" aria-hidden="true" onclick="onMermaidModalBackdrop(event)">
  <div class="mermaid-modal-panel" role="dialog" aria-modal="true" aria-label="Mermaid diagram preview">
    <div class="mermaid-modal-header">
      <div class="mermaid-modal-title">Mermaid 图表预览</div>
      <div class="mermaid-modal-actions">
        <button class="mermaid-action" type="button" onclick="zoomMermaidModal(-0.1)">缩小</button>
        <span class="mermaid-zoom-value" id="mermaid-zoom-value">100%</span>
        <button class="mermaid-action" type="button" onclick="zoomMermaidModal(0.1)">放大</button>
        <button class="mermaid-action" type="button" onclick="resetMermaidZoom()">重置</button>
        <button class="mermaid-action" type="button" onclick="copyMermaidFromModal(this)">复制源码</button>
        <button class="mermaid-action" type="button" onclick="copyMermaidImageFromModal(this)">复制图片</button>
        <button class="mermaid-action" type="button" onclick="closeMermaidModal()">关闭</button>
      </div>
    </div>
    <div class="mermaid-modal-body" id="mermaid-modal-body"></div>
  </div>
</div>

<script>
let menuData = null;
let currentPath = "";
let wikiDir = "";
let activeMermaidSource = "";
let mermaidZoom = 1;
let mermaidPanX = 0;
let mermaidPanY = 0;
let mermaidDragging = false;
let mermaidDragStartX = 0;
let mermaidDragStartY = 0;
let mermaidDragOriginX = 0;
let mermaidDragOriginY = 0;

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });

marked.setOptions({
  highlight: function(code, lang) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
  breaks: true,
  gfm: true,
});

function escHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function decodeHtml(s) {
  const textarea = document.createElement("textarea");
  textarea.innerHTML = s;
  return textarea.value;
}

async function init() {
  try {
    menuData = await fetch("/api/menu").then(r => r.json());
  } catch(e) {
    menuData = { title: "Wiki", menu: [] };
  }
  document.getElementById("header-title").innerHTML =
    escHtml(menuData.title || "DeepWiki") + '<span>DeepWiki</span>';
  renderSidebar();
  const hashPath = parseHashPath(location.hash);
  if (hashPath) {
    navigateTo(hashPath, false);
  } else {
    navigateToDefault();
  }
}

function parseHashPath(hash) {
  if (!hash) return "";
  const raw = hash.startsWith("#/") ? hash.slice(2) : hash.replace(/^#/, "");
  return raw ? decodeURIComponent(raw.replace(/^\/+/, "")) : "";
}

function navigateToDefault() {
  for (const group of menuData.items || []) {
    for (const item of group.items || []) {
      if (item.path) { navigateTo(item.path, false); return; }
    }
  }
  document.getElementById("content").innerHTML =
    '<div style="padding:40px;text-align:center;color:#656d76;">No pages found in menu.json</div>';
}

function renderSidebar() {
  document.getElementById("sidebar").innerHTML = buildSidebarHTML();
}

function buildSidebarHTML() {
  let html = "";
  for (const group of menuData.items || []) {
    html += `<div class="menu-group"><div class="menu-group-title" onclick="toggleGroup(this)"><span class="arrow">&#9660;</span>${escHtml(group.title)}</div><ul class="menu-items">`;
    html += buildMenuItemsHTML(group.items || [], 0);
    html += "</ul></div>";
  }
  return html;
}

function buildMenuItemsHTML(items, level) {
  let html = "";
  for (const item of items) {
    if (item.path) {
      let cls = "menu-item";
      if (level === 1) cls += " menu-sub-item";
      else if (level >= 2) cls += " menu-sub-sub-item";
      const dataPath = ' data-path="' + escHtml(item.path) + '"';
      html += `<li class="${cls}"${dataPath}><a href="#/${encodeURIComponent(item.path)}" onclick="onNavClick(event, '${escAttr(item.path)}')">${escHtml(item.title)}</a></li>`;
      if (item.items && item.items.length) {
        html += buildMenuItemsHTML(item.items, level + 1);
      }
    } else if (item.items && item.items.length) {
      html += `<li class="menu-sub-group"><div class="menu-sub-group-title" onclick="toggleSubGroup(this)"><span class="arrow">&#9660;</span>${escHtml(item.title)}</div><ul class="menu-sub-items">`;
      html += buildMenuItemsHTML(item.items, level + 1);
      html += "</ul></li>";
    }
  }
  return html;
}

function escAttr(s) {
  return s.replace(/'/g, "\\'").replace(/\\/g, "\\\\");
}

function toggleGroup(el) {
  el.parentElement.classList.toggle("collapsed");
}

function toggleSubGroup(el) {
  el.parentElement.classList.toggle("collapsed");
}

async function onNavClick(e, path) {
  e.preventDefault();
  navigateTo(path, true);
}

async function navigateTo(path, pushState = true) {
  currentPath = path;
  updateActiveItem();
  const contentEl = document.getElementById("content");
  contentEl.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';

  try {
    const md = await fetch("/api/page/" + encodeURIComponent(path)).then(r => {
      if (!r.ok) throw new Error("Not found: " + path);
      return r.text();
    });
    renderMarkdown(md);
    if (pushState) history.pushState({ path }, "", "#/" + path);
    document.title = (menuData.title || "DeepWiki") + " - " + path.replace(/\.md$/, "").replace(/\//g, " / ");
  } catch(e) {
    contentEl.innerHTML = `<div style="padding:40px;text-align:center;color:#656d76;">Page not found: ${escHtml(path)}</div>`;
  }
}

function updateActiveItem() {
  document.querySelectorAll(".menu-item").forEach(el => {
    el.classList.toggle("active", el.dataset.path === currentPath);
  });
}

function renderMarkdown(md) {
  const contentEl = document.getElementById("content");
  let html = marked.parse(md);

  // Process mermaid code blocks: ```mermaid ... ```
  html = html.replace(/<pre><code class="language-mermaid">([\s\S]*?)<\/code><\/pre>/g,
    (match, code) => {
      const id = "mermaid-" + Math.random().toString(36).substr(2, 9);
      const source = decodeHtml(code).trim();
      return `<div class="mermaid-container" data-mermaid-source="${escHtml(encodeURIComponent(source))}">
        <div class="mermaid-toolbar">
          <button class="mermaid-action" type="button" onclick="openMermaidModal(this)">放大</button>
          <button class="mermaid-action" type="button" onclick="copyMermaidSource(this)">复制</button>
        </div>
        <div class="mermaid" id="${id}">${escHtml(source)}</div>
      </div>`;
    }
  );

  contentEl.innerHTML = html;
  // Collapse all <details> elements by default
  contentEl.querySelectorAll('details[open]').forEach(d => d.removeAttribute('open'));
  linkifyPlainSourceReferences(contentEl);
  setupSourceLinks(contentEl);
  highlightCodeBlocks(contentEl);
  mermaid.run({ nodes: contentEl.querySelectorAll(".mermaid") }).then(() => {
    setupMermaidInteractions();
  }).catch((err) => {
    console.error("Mermaid render failed", err);
    setupMermaidInteractions();
  });
  generateTOC();
  setupLinkInterception();
  renderPageNav();
}

function highlightCodeBlocks(root) {
  root.querySelectorAll("pre code").forEach((block) => {
    if (block.classList.contains("language-mermaid")) return;
    if (block.dataset.highlighted === "yes") return;

    const languageClass = Array.from(block.classList).find(cls => cls.startsWith("language-"));
    const language = languageClass ? languageClass.replace("language-", "") : "";

    try {
      if (language && hljs.getLanguage(language)) {
        block.innerHTML = hljs.highlight(block.textContent, { language }).value;
        block.classList.add("hljs");
        block.dataset.highlighted = "yes";
      } else {
        hljs.highlightElement(block);
      }
    } catch(e) {
      console.warn("Code highlight failed", e);
    }
  });
}

function parseSourceHref(href) {
  if (!href || !href.startsWith("file://")) return null;
  try {
    const url = new URL(href);
    const startEnd = (url.hash || "").match(/^#L(\d+)(?:-L(\d+))?/);
    let path = decodeURIComponent(url.pathname || "");
    if (url.host) {
      path = "/" + decodeURIComponent(url.host) + path;
    }
    const start = startEnd ? Number(startEnd[1]) : null;
    const end = startEnd && startEnd[2] ? Number(startEnd[2]) : start;
    return {
      path,
      start,
      end,
      range: start ? "L" + start + (end && end !== start ? "-L" + end : "") : "",
    };
  } catch(e) {
    return null;
  }
}

function linkifyPlainSourceReferences(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest("a, code, pre, script, style")) return NodeFilter.FILTER_REJECT;
      return node.nodeValue && node.nodeValue.includes("file://")
        ? NodeFilter.FILTER_ACCEPT
        : NodeFilter.FILTER_REJECT;
    }
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  const pattern = /\[?(file:\/\/[^\]\s)]+(?:#L\d+(?:-L\d+)?)?)\]?/g;
  nodes.forEach(node => {
    const text = node.nodeValue || "";
    if (!pattern.test(text)) return;
    pattern.lastIndex = 0;
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      fragment.appendChild(document.createTextNode(text.slice(lastIndex, match.index)));
      const link = document.createElement("a");
      link.href = match[1];
      link.textContent = match[1];
      fragment.appendChild(link);
      lastIndex = match.index + match[0].length;
    }
    fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    node.parentNode.replaceChild(fragment, node);
  });
}

function setupSourceLinks(root) {
  root.querySelectorAll('a[href^="file://"]').forEach((link) => {
    const parsed = parseSourceHref(link.getAttribute("href") || "");
    if (!parsed) return;

    const pathParts = parsed.path.split("/");
    const filename = pathParts[pathParts.length - 1] || parsed.path;

    link.classList.add("source-link");
    link.dataset.sourcePath = parsed.path;
    if (parsed.start) link.dataset.sourceStart = String(parsed.start);
    if (parsed.end) link.dataset.sourceEnd = String(parsed.end);
    link.setAttribute("title", parsed.range ? `${parsed.path} ${parsed.range}` : parsed.path);
    link.addEventListener("click", onSourceLinkClick);

    link.textContent = "";
    const pathEl = document.createElement("span");
    pathEl.className = "source-path";
    pathEl.textContent = filename;
    link.appendChild(pathEl);

    if (parsed.range) {
      const rangeEl = document.createElement("span");
      rangeEl.className = "source-line-range";
      rangeEl.textContent = parsed.range;
      link.appendChild(rangeEl);
    }
  });
}

async function onSourceLinkClick(event) {
  event.preventDefault();
  const link = event.currentTarget;
  document.querySelectorAll("a.source-link.active").forEach(el => el.classList.remove("active"));
  link.classList.add("active");
  await openSourcePanel(link.dataset.sourcePath || "", link.dataset.sourceStart || "", link.dataset.sourceEnd || "");
}

function closeSourcePanel() {
  const panel = document.getElementById("source-panel");
  const backdrop = document.getElementById("source-backdrop");
  panel.classList.remove("open");
  panel.classList.remove("expanded");
  backdrop.classList.remove("open");
  updateSourcePanelExpandButton();
  document.querySelectorAll("a.source-link.active").forEach(el => el.classList.remove("active"));
}

function toggleSourcePanelSize() {
  const panel = document.getElementById("source-panel");
  panel.classList.toggle("expanded");
  updateSourcePanelExpandButton();
}

function updateSourcePanelExpandButton() {
  const panel = document.getElementById("source-panel");
  const button = document.getElementById("source-panel-expand");
  if (!button) return;
  const expanded = panel.classList.contains("expanded");
  button.setAttribute("aria-label", expanded ? "Restore source preview" : "Expand source preview");
  button.setAttribute("title", expanded ? "Restore source preview" : "Expand source preview");
  button.innerHTML = expanded ? "&#x25F1;" : "&#x26F6;";
}

async function openSourcePanel(path, start, end) {
  const panel = document.getElementById("source-panel");
  const backdrop = document.getElementById("source-backdrop");
  const body = document.getElementById("source-panel-body");
  const pathEl = document.getElementById("source-panel-path");
  const rangeEl = document.getElementById("source-panel-range");

  panel.classList.add("open");
  backdrop.classList.add("open");
  pathEl.textContent = path || "Source";
  rangeEl.textContent = start ? "Lines " + start + (end && end !== start ? "-" + end : "") : "";
  body.innerHTML = '<div class="source-panel-empty">Loading source...</div>';

  const params = new URLSearchParams({ path });
  if (start) params.set("start", start);
  if (end) params.set("end", end);

  try {
    const response = await fetch("/api/source?" + params.toString());
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to load source");
    pathEl.textContent = data.relative_path || data.path || path;
    if (data.type === "directory") {
      rangeEl.textContent = "directory";
      renderDirTree(data);
    } else {
      rangeEl.textContent = start ? "Lines " + start + (end && end !== start ? "-" + end : "") : "";
      renderSourceCode(data);
    }
  } catch(e) {
    body.innerHTML = `<div class="source-panel-error">${escHtml(e.message || String(e))}</div>`;
  }
}

function renderSourceCode(data) {
  const body = document.getElementById("source-panel-body");
  const language = data.language || "";
  const rows = (data.lines || []).map(line => {
    let code = escHtml(line.text || "");
    if (language && hljs.getLanguage(language)) {
      try {
        code = hljs.highlight(line.text || "", { language }).value;
      } catch(e) {}
    }
    const cls = line.highlight ? "source-line highlight" : "source-line";
    return `<tr class="${cls}" id="source-line-${line.number}">
      <td class="source-line-number">${line.number}</td>
      <td class="source-line-code">${code || " "}</td>
    </tr>`;
  }).join("");
  body.innerHTML = `<table class="source-code-table"><tbody>${rows}</tbody></table>`;
  const firstHighlight = body.querySelector(".source-line.highlight");
  if (firstHighlight) {
    firstHighlight.scrollIntoView({ block: "center" });
  }
}

function renderDirTree(data) {
  const body = document.getElementById("source-panel-body");

  function buildNodes(items) {
    if (!items || !items.length) return "";
    let html = '<ul class="dir-tree-list">';
    for (const item of items) {
      if (item.type === "dir") {
        html += `<li class="dir-tree-dir open">
          <span class="dir-tree-toggle" onclick="this.closest('li').classList.toggle('open')">
            <span class="dir-tree-icon">&#128193;</span>${escHtml(item.name)}
          </span>
          ${buildNodes(item.children)}
        </li>`;
      } else {
        html += `<li class="dir-tree-file">
          <span class="dir-tree-icon">&#128196;</span>${escHtml(item.name)}
        </li>`;
      }
    }
    html += "</ul>";
    return html;
  }

  const tree = data.tree || [];
  body.innerHTML = `<div class="dir-tree">${buildNodes(tree) || '<div class="source-panel-empty">Empty directory</div>'}</div>`;
}

function getMermaidContainer(trigger) {
  return trigger.closest(".mermaid-container");
}

function getMermaidSource(container) {
  if (!container) return "";
  const encoded = container.getAttribute("data-mermaid-source") || "";
  try {
    return decodeURIComponent(encoded);
  } catch(e) {
    return encoded;
  }
}

function setupMermaidInteractions() {
  document.querySelectorAll(".mermaid-container svg").forEach(svg => {
    svg.style.cursor = "zoom-in";
    svg.addEventListener("click", () => openMermaidModal(svg));
  });
}

async function writeClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

async function copyMermaidSource(button) {
  const container = getMermaidContainer(button);
  const source = getMermaidSource(container);
  if (!source) return;
  await writeClipboard(source);
  const original = button.textContent;
  button.textContent = "已复制";
  button.classList.add("copied");
  setTimeout(() => {
    button.textContent = original;
    button.classList.remove("copied");
  }, 1200);
}

function openMermaidModal(trigger) {
  const container = getMermaidContainer(trigger);
  if (!container) return;
  const svg = container.querySelector("svg");
  const body = document.getElementById("mermaid-modal-body");
  activeMermaidSource = getMermaidSource(container);
  body.innerHTML = '<div class="mermaid-zoom-stage" id="mermaid-zoom-stage"></div>';
  const stage = document.getElementById("mermaid-zoom-stage");
  if (svg) {
    stage.appendChild(svg.cloneNode(true));
  } else {
    stage.textContent = "图表尚未渲染完成";
  }
  const modal = document.getElementById("mermaid-modal");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  setMermaidPan(0, 0);
  setMermaidZoom(1);
}

function closeMermaidModal() {
  const modal = document.getElementById("mermaid-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
  document.getElementById("mermaid-modal-body").innerHTML = "";
  activeMermaidSource = "";
  setMermaidPan(0, 0);
  setMermaidZoom(1);
}

function onMermaidModalBackdrop(event) {
  if (event.target.id === "mermaid-modal") closeMermaidModal();
}

async function copyMermaidFromModal(button) {
  if (!activeMermaidSource) return;
  await writeClipboard(activeMermaidSource);
  const original = button.textContent;
  button.textContent = "已复制";
  button.classList.add("copied");
  setTimeout(() => {
    button.textContent = original;
    button.classList.remove("copied");
  }, 1200);
}

function svgToPngBlob(svg) {
  return new Promise((resolve, reject) => {
    const clone = svg.cloneNode(true);
    clone.removeAttribute("style");
    if (!clone.getAttribute("xmlns")) {
      clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    }
    const viewBox = svg.viewBox && svg.viewBox.baseVal;
    const box = svg.getBoundingClientRect();
    const width = Math.max(1, Math.ceil(viewBox?.width || box.width || 1200));
    const height = Math.max(1, Math.ceil(viewBox?.height || box.height || 800));
    clone.setAttribute("width", String(width));
    clone.setAttribute("height", String(height));

    const svgText = new XMLSerializer().serializeToString(clone);
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svgText);
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob(blob => {
        if (blob) resolve(blob);
        else reject(new Error("图片生成失败"));
      }, "image/png");
    };
    img.onerror = () => {
      reject(new Error("图片生成失败"));
    };
    img.src = url;
  });
}

async function copyMermaidImageFromModal(button) {
  const svg = document.querySelector("#mermaid-modal-body svg");
  if (!svg) return;
  const original = button.textContent;
  try {
    if (!navigator.clipboard || typeof ClipboardItem === "undefined") {
      throw new Error("当前浏览器不支持复制图片");
    }
    if (ClipboardItem.supports && !ClipboardItem.supports("image/png")) {
      throw new Error("当前浏览器不支持复制 PNG 图片");
    }
    await navigator.clipboard.write([
      new ClipboardItem({ "image/png": svgToPngBlob(svg) })
    ]);
    button.textContent = "已复制";
    button.classList.add("copied");
  } catch(e) {
    console.warn("Copy Mermaid image failed", e);
    button.textContent = e.message || "复制失败";
  }
  setTimeout(() => {
    button.textContent = original;
    button.classList.remove("copied");
  }, 1600);
}

function setMermaidZoom(value) {
  mermaidZoom = Math.min(4, Math.max(0.25, value));
  const label = document.getElementById("mermaid-zoom-value");
  updateMermaidTransform();
  if (label) {
    label.textContent = Math.round(mermaidZoom * 100) + "%";
  }
}

function setMermaidPan(x, y) {
  mermaidPanX = x;
  mermaidPanY = y;
  updateMermaidTransform();
}

function updateMermaidTransform() {
  const stage = document.getElementById("mermaid-zoom-stage");
  if (stage) {
    stage.style.transform = `translate(${mermaidPanX}px, ${mermaidPanY}px) scale(${mermaidZoom})`;
  }
}

function zoomMermaidModal(delta) {
  setMermaidZoom(mermaidZoom + delta);
}

function resetMermaidZoom() {
  setMermaidPan(0, 0);
  setMermaidZoom(1);
}

function startMermaidDrag(event) {
  const modal = document.getElementById("mermaid-modal");
  if (!modal.classList.contains("open")) return;
  if (event.button !== 0) return;
  if (event.target.closest(".mermaid-modal-actions")) return;
  mermaidDragging = true;
  mermaidDragStartX = event.clientX;
  mermaidDragStartY = event.clientY;
  mermaidDragOriginX = mermaidPanX;
  mermaidDragOriginY = mermaidPanY;
  document.getElementById("mermaid-modal-body").classList.add("dragging");
  event.currentTarget.setPointerCapture?.(event.pointerId);
}

function moveMermaidDrag(event) {
  if (!mermaidDragging) return;
  event.preventDefault();
  setMermaidPan(
    mermaidDragOriginX + event.clientX - mermaidDragStartX,
    mermaidDragOriginY + event.clientY - mermaidDragStartY
  );
}

function endMermaidDrag(event) {
  if (!mermaidDragging) return;
  mermaidDragging = false;
  document.getElementById("mermaid-modal-body").classList.remove("dragging");
  event.currentTarget.releasePointerCapture?.(event.pointerId);
}

document.getElementById("mermaid-modal-body").addEventListener("wheel", (event) => {
  const modal = document.getElementById("mermaid-modal");
  if (!modal.classList.contains("open")) return;
  if (!event.ctrlKey && !event.metaKey) return;
  event.preventDefault();
  zoomMermaidModal(event.deltaY < 0 ? 0.1 : -0.1);
}, { passive: false });

document.getElementById("mermaid-modal-body").addEventListener("pointerdown", startMermaidDrag);
document.getElementById("mermaid-modal-body").addEventListener("pointermove", moveMermaidDrag);
document.getElementById("mermaid-modal-body").addEventListener("pointerup", endMermaidDrag);
document.getElementById("mermaid-modal-body").addEventListener("pointercancel", endMermaidDrag);

function generateTOC() {
  const tocList = document.getElementById("toc-list");
  const headings = document.querySelectorAll("#content h2, #content h3");
  let html = "";
  headings.forEach((h, i) => {
    const id = "heading-" + i;
    h.id = id;
    const cls = h.tagName === "H3" ? "toc-h3" : "";
    html += `<li class="${cls}"><a href="#${id}" onclick="scrollToHeading(event, '${id}')">${escHtml(h.textContent)}</a></li>`;
  });
  tocList.innerHTML = html;

  if (!html) {
    tocList.innerHTML = '<li style="padding:8px 16px;font-size:13px;color:#656d76;">No sections</li>';
  }
}

function scrollToHeading(e, id) {
  e.preventDefault();
  document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
}


function flattenMenuLeaves() {
  const leaves = [];
  function walk(items) {
    for (const item of items || []) {
      if (item.path && !item.planned) leaves.push(item);
      if (item.items && item.items.length) walk(item.items);
    }
  }
  for (const group of menuData.items || []) walk(group.items || []);
  return leaves;
}

function renderPageNav() {
  const existing = document.getElementById('page-nav');
  if (existing) existing.remove();

  const leaves = flattenMenuLeaves();
  const idx = leaves.findIndex(l => l.path === currentPath);
  if (idx < 0 || leaves.length < 2) return;

  const prev = idx > 0 ? leaves[idx - 1] : null;
  const next = idx < leaves.length - 1 ? leaves[idx + 1] : null;

  const nav = document.createElement('nav');
  nav.id = 'page-nav';
  nav.className = 'page-nav';

  if (prev) {
    const btn = document.createElement('button');
    btn.className = 'page-nav-btn prev';
    btn.innerHTML = '<span class="page-nav-arrow">\u2190</span><span class="page-nav-title">' + escHtml(prev.title) + '</span>';
    btn.addEventListener('click', () => navigateTo(prev.path));
    nav.appendChild(btn);
  } else {
    nav.appendChild(document.createElement('span'));
  }

  if (next) {
    const btn = document.createElement('button');
    btn.className = 'page-nav-btn next';
    btn.innerHTML = '<span class="page-nav-title">' + escHtml(next.title) + '</span><span class="page-nav-arrow">\u2192</span>';
    btn.addEventListener('click', () => navigateTo(next.path));
    nav.appendChild(btn);
  }

  document.getElementById('content').appendChild(nav);
}

function setupLinkInterception() {
  document.querySelectorAll("#content a").forEach(a => {
    const href = a.getAttribute("href");
    if (href && href.endsWith(".md")) {
      a.addEventListener("click", function(e) {
        e.preventDefault();
        const linkPath = href;
        if (linkPath.startsWith("http://") || linkPath.startsWith("https://")) return;
        // Resolve relative path based on current page location
        let resolved = linkPath;
        if (linkPath.startsWith("./") || linkPath.startsWith("../") || !linkPath.startsWith("/")) {
          const base = currentPath.includes("/") ? currentPath.substring(0, currentPath.lastIndexOf("/") + 1) : "";
          resolved = new URL(linkPath, "http://x/" + base).pathname.slice(1);
        }
        navigateTo(resolved);
      });
    }
  });
}

window.addEventListener("popstate", (e) => {
  if (e.state && e.state.path) {
    navigateTo(e.state.path, false);
  }
});

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeMermaidModal();
});

init();
</script>
</body>
</html>
"""
