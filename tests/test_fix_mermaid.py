"""Tests for scripts/fix_mermaid.py"""

import json
import pytest
import fix_mermaid


class TestFixFlowchart:
    """Tests for fix_flowchart()."""

    def test_label_with_spaces_gets_quoted(self):
        text = 'A[Data Processing] --> B\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count >= 1
        assert '"Data Processing"' in fixed

    def test_chinese_label_gets_quoted(self):
        text = 'A[数据处理] --> B\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count >= 1
        assert '"数据处理"' in fixed

    def test_already_quoted_label_unchanged(self):
        text = 'A["Data Processing"] --> B\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count == 0

    def test_simple_label_unchanged(self):
        text = 'A[Process] --> B\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count == 0

    def test_edge_label_with_spaces(self):
        text = 'A -->|error handler| B\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count >= 1

    def test_hyphenated_node_id_label_gets_quoted(self):
        text = 'api-gw[HTTP 请求] --> chat-service[POST /api/chat]\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count == 2
        assert 'api-gw["HTTP 请求"]' in fixed
        assert 'chat-service["POST /api/chat"]' in fixed

    def test_chat_routes_example_gets_quoted(self):
        text = """flowchart TB
    Client[客户端] --> HTTP[POST /api/chat]
    Client --> SSE[POST /api/chat/stream]
    Client --> WS[WS /ws/chat/{session_id}]

    HTTP --> RunChat[run_chat]
    SSE --> RunChat
    WS --> RunChat

    RunChat --> Pre[PreProcessor.process]
    Pre --> WF[workflow_app.ainvoke]
    WF --> Resp[ChatResponse]

    HTTP --> SyncResp[同步 JSON 响应]
    SSE --> StreamResp[SSE 事件流]
    WS --> WsResp[WebSocket 消息]
"""
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count >= 9
        assert 'HTTP["POST /api/chat"]' in fixed
        assert 'WS["WS /ws/chat/{session_id}"]' in fixed
        assert 'SyncResp["同步 JSON 响应"]' in fixed

    def test_middleware_routes_example_gets_quoted(self):
        text = """graph TD
    REQ[HTTP 请求] --> MW[RequestLoggingMiddleware]
    MW --> CHAT[POST /chat]
    MW --> SSE[GET /chat/stream]
    MW --> WS[/ws/chat]
    MW --> HLTH[GET /health]
    MW --> SKILLS[POST /skills/reload]
"""
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count >= 6
        assert 'REQ["HTTP 请求"]' in fixed
        assert 'WS["/ws/chat"]' in fixed
        assert 'SKILLS["POST /skills/reload"]' in fixed

    def test_common_node_shapes_get_quoted(self):
        text = 'Start(HTTP 请求) --> Decision{是否成功?}\nDecision --> Store[(SQLite DB)]\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count == 3
        assert 'Start("HTTP 请求")' in fixed
        assert 'Decision{"是否成功?"}' in fixed
        assert 'Store[("SQLite DB")]' in fixed


class TestFixClassDiagram:
    """Tests for fix_class_diagram()."""

    def test_member_with_spaces(self):
        text = '  class MyClass {\n    +process data()\n  }\n'
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count >= 1
        assert '"process data"' in fixed

    def test_relationship_label_quoted(self):
        text = 'ClassA --|> ClassB : extends relationship\n'
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count >= 1

    def test_simple_class_unchanged(self):
        text = 'class MyClass {\n    +process()\n    -helper()\n}\n'
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count == 0


class TestFixSequenceDiagram:
    """Tests for fix_sequence_diagram()."""

    def test_message_label_with_spaces(self):
        text = 'A->>B:send request\n'
        fixed, count = fix_mermaid.fix_sequence_diagram(text)
        assert count >= 1

    def test_participant_with_spaces(self):
        text = 'participant P as My Service\n'
        fixed, count = fix_mermaid.fix_sequence_diagram(text)
        assert count >= 1

    def test_simple_message_unchanged(self):
        text = 'A->>B:hello\n'
        fixed, count = fix_mermaid.fix_sequence_diagram(text)
        assert count == 0


class TestFixDuplicateNodeIds:
    """Tests for fix_duplicate_node_ids()."""

    def test_duplicate_id_renamed(self):
        text = 'A[First] --> B\nA[Second] --> C\n'
        fixed, count = fix_mermaid.fix_duplicate_node_ids(text)
        assert count >= 1
        assert 'A_2' in fixed

    def test_no_duplicate_unchanged(self):
        text = 'A[First] --> B\nC[Second] --> D\n'
        fixed, count = fix_mermaid.fix_duplicate_node_ids(text)
        assert count == 0


class TestFixMermaidBlock:
    """Tests for fix_mermaid_block() dispatcher."""

    def test_flowchart_block(self):
        text = 'flowchart LR\nA[数据处理] --> B\n'
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count >= 1

    def test_class_diagram_block(self):
        text = 'classDiagram\n    class MyClass {\n    +process data()\n    }\n'
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count >= 1

    def test_sequence_diagram_block(self):
        text = 'sequenceDiagram\nA->>B:send request\n'
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count >= 1

    def test_unknown_type_unchanged(self):
        text = 'pie title Languages\n"Python" : 40\n'
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        assert count == 0


class TestStateDiagram:
    def test_state_diagram_preserved(self):
        block = 'stateDiagram-v2\n    [*] --> Idle\n    Idle --> Processing : start\n    Processing --> Idle : done'
        result, count = fix_mermaid.fix_mermaid_block(block)
        assert 'stateDiagram-v2' in result

    def test_er_diagram_safe_id(self):
        block = 'erDiagram\nUSER ||--o{ ORDER : places\nORDER ||--|{ LINE_ITEM : contains'
        result, count = fix_mermaid.fix_mermaid_block(block)
        assert 'erDiagram' in result
        assert 'USER' in result


class TestHyphenatedIds:
    def test_hyphenated_id_not_quoted(self):
        """IDs with hyphens like auth-service should be treated as safe."""
        assert fix_mermaid._needs_quoting('auth-service') == False
        assert fix_mermaid._needs_quoting('user-controller') == False
        assert fix_mermaid._needs_quoting('my_component') == False  # underscore is in \w, safe ID


class TestFixMermaidInFile:
    """Tests for fix_mermaid_in_file()."""

    def test_fixes_mermaid_block_in_md(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text(
            '# Title\n\n'
            '```mermaid\nflowchart LR\nA[数据处理] --> B\n```\n',
            encoding="utf-8",
        )
        result = fix_mermaid.fix_mermaid_in_file(f)
        assert result["total_fixes"] >= 1
        assert result["changes_made"]

        content = f.read_text(encoding="utf-8")
        assert '"数据处理"' in content

    def test_dry_run_does_not_modify(self, tmp_path):
        f = tmp_path / "doc.md"
        original = '# Title\n\n```mermaid\nflowchart LR\nA[处理] --> B\n```\n'
        f.write_text(original, encoding="utf-8")

        result = fix_mermaid.fix_mermaid_in_file(f, dry_run=True)
        assert result["total_fixes"] >= 1
        assert not result["changes_made"]

        assert f.read_text(encoding="utf-8") == original

    def test_no_mermaid_blocks(self, tmp_path):
        f = tmp_path / "plain.md"
        f.write_text("# No diagrams here\n")
        result = fix_mermaid.fix_mermaid_in_file(f)
        assert result["total_fixes"] == 0

    def test_multiple_blocks(self, tmp_path):
        f = tmp_path / "multi.md"
        f.write_text(
            '# Title\n\n'
            '```mermaid\nflowchart LR\nA[数据] --> B\n```\n\n'
            '```mermaid\nsequenceDiagram\nX->>Y:send msg\n```\n',
            encoding="utf-8",
        )
        result = fix_mermaid.fix_mermaid_in_file(f)
        assert result["total_fixes"] >= 2
        assert result["blocks_fixed"] == 2


class TestFixAllMermaid:
    """Tests for fix_all_mermaid()."""

    def test_scans_wiki_subdirectory(self, tmp_path):
        wiki = tmp_path / "wiki"
        wiki.mkdir()
        modules = wiki / "modules"
        modules.mkdir()

        (wiki / "index.md").write_text(
            '```mermaid\nflowchart LR\nA[数据] --> B\n```\n',
            encoding="utf-8",
        )
        (modules / "core.md").write_text(
            '```mermaid\nflowchart LR\nX[处理] --> Y\n```\n',
            encoding="utf-8",
        )

        results = fix_mermaid.fix_all_mermaid(str(tmp_path))
        affected = [r for r in results if r.get("total_fixes", 0) > 0]
        assert len(affected) == 2

    def test_nonexistent_directory(self, tmp_path):
        results = fix_mermaid.fix_all_mermaid(str(tmp_path / "nonexistent"))
        assert len(results) == 1
        assert "error" in results[0]
