"""Tests for scripts/fix_mermaid.py"""

import json
import sys
import pytest
from scripts.wiki import fix_mermaid


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


    def test_nested_double_quotes_replaced_with_single(self):
        # A["Skill.run(\"message, context\")"] -> A["Skill.run('message, context')"]
        text = 'A["Skill.run("message, context")"] --> B["init"]\n'
        fixed, count = fix_mermaid.fix_flowchart(text)
        assert count == 1
        assert "Skill.run('message, context')" in fixed
        assert 'B["init"]' in fixed

    def test_multiple_nested_double_quotes_in_diagram(self):
        real_text = (
            'graph TD\n'
            '    A["fn("x", "y")"] --> B["plain"]\n'
            '    B --> C["other("z")"] --> D["no quotes"]\n'
        )
        fixed, count = fix_mermaid.fix_flowchart(real_text)
        assert count == 2
        assert "fn('x', 'y')" in fixed
        assert "other('z')" in fixed
        assert 'D["no quotes"]' in fixed

    def test_nested_quotes_in_full_diagram(self):
        diagram = (
            'graph TD\n'
            '    A["Skill.run("message, context")"] --> B["初始化 scratchpad"]\n'
            '    B --> C["Tool 1: extract_params("message, context, scratchpad")"]\n'
            '    C --> D["render_prompt("template, message, tool_results, variables")"]\n'
        )
        fixed, count = fix_mermaid.fix_flowchart(diagram)
        assert count == 3
        assert "Skill.run('message, context')" in fixed
        assert "extract_params('message, context, scratchpad')" in fixed
        assert "render_prompt('template, message, tool_results, variables')" in fixed

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

    def test_session_header_nested_quotes(self):
        """节点标签内嵌套双引号的 JSON 场景：内部双引号应替换为单引号。"""
        text = """flowchart TD
    HEADER["SessionHeader\\n{'type: session, id, timestamp, cwd'}"]
    HEADER --> E1["Entry A\\n{"type: message, id: a1, parentId: null"}"]
    E1 --> E2["Entry B\\n{"type: message, id: a2, parentId: a1"}"]
    E2 --> E3["Entry C\\n{"type: message, id: a3, parentId: a2"}"]
    E3 --> E4["Entry D (branch)\\n{"type: message, id: a4, parentId: a1"}"]
    E3 --> E5["Entry E\\n{"type: message, id: a5, parentId: a3"}"]

    style E4 fill:#f9f,stroke:#333
"""
        fixed, count = fix_mermaid.fix_mermaid_block(text)
        # HEADER 内部已是单引号，不需要修改
        assert '"SessionHeader' in fixed
        assert "'type: session" in fixed
        # E1-E5 内部双引号应被替换为单引号
        assert "'type: message, id: a1, parentId: null'" in fixed
        assert "'type: message, id: a2, parentId: a1'" in fixed
        assert "'type: message, id: a4, parentId: a1'" in fixed
        assert "'type: message, id: a5, parentId: a3'" in fixed
        # style 行不变
        assert 'style E4 fill:#f9f,stroke:#333' in fixed
        # 5 处修复 (E1-E5)
        assert count == 5


class TestFixClassDiagram:
    """Tests for fix_class_diagram()."""

    def test_generic_class_def_tilde(self):
        """class "Model~TApi~" → class "Model<TApi>" as Model"""
        text = 'class "Model~TApi~" {\n        +string id\n    }\n'
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count >= 1
        assert 'class "Model<TApi>" as Model' in fixed

    def test_generic_member_type_tilde(self):
        """Record~string,string~ → Record<string, string> in member type"""
        text = '    +Record~string,string~ headers\n'
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count >= 1
        assert 'Record<string, string>' in fixed

    def test_generic_relationship_ref(self):
        """关系行引用泛型 display name → 替换为 alias"""
        text = (
            'class "Model~TApi~" {\n'
            '        +string id\n'
            '    }\n'
            '    Model~TApi~ : "tagged with"\n'
        )
        fixed, count = fix_mermaid.fix_class_diagram(text)
        assert count >= 2  # class def + relationship ref
        assert 'Model : "tagged with"' in fixed
        assert 'class "Model<TApi>" as Model' in fixed

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

    def test_full_generic_class_diagram(self):
        """完整 classDiagram 测试：泛型类定义、成员类型含空格、方法返回值泛型、关系行。"""
        text = """classDiagram
    class "Model~TApi~"
        +string id
        +string name
        +TApi api
        +Provider provider
        +string baseUrl
        +boolean reasoning
        +Cost cost
        +number contextWindow
        +number maxTokens
        +Record~string,string~ headers
        +Compat compat
    }

    class "ApiProvider~TApi~"
        +TApi api
        +StreamFunction stream
        +StreamFunction streamSimple
    }

    class ApiRegistry {
        -Map~string, RegisteredApiProvider~ registry
        +registerApiProvider(provider, sourceId)
        +getApiProvider(api) ApiProviderInternal
        +getApiProviders() ApiProviderInternal[]
        +unregisterApiProviders(sourceId)
        +clearApiProviders()
    }

    class StreamFunction {
        <<type>>
        (model, context, options) → AssistantMessageEventStream
    }

    class AssistantMessageEventStream {
        +push(event)
        +end(result?)
        +result() Promise~AssistantMessage~
    }

    ApiRegistry --> ApiProvider : manages
    ApiProvider --> StreamFunction : exposes
    StreamFunction --> AssistantMessageEventStream : returns
    Model  : "tagged with"
    Model  : "served by"
"""
        fixed, count = fix_mermaid.fix_class_diagram(text)
        # 泛型类定义
        assert 'class "Model<TApi>" as Model' in fixed
        assert 'class "ApiProvider<TApi>" as ApiProvider' in fixed
        # 成员类型中的泛型
        assert 'Record<string, string>' in fixed
        # 泛型参数含空格
        assert 'Map<string, RegisteredApiProvider>' in fixed
        # 方法返回值中的泛型
        assert 'Promise<AssistantMessage>' in fixed
        # 关系行中的泛型引用应被解析为 alias
        assert 'ApiProvider : ' in fixed
        assert count >= 5


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
        assert len(results) == 0


def test_cli_returns_success_after_applying_regex_fixes(tmp_path, monkeypatch):
    """Applying deterministic Mermaid fixes is success, not an unresolved failure."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "index.md").write_text(
        "```mermaid\nflowchart LR\nA[数据处理] --> B\n```\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        ["fix_mermaid.py", str(tmp_path)],
    )

    assert fix_mermaid.main() == 0
