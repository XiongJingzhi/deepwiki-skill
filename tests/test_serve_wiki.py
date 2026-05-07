from scripts.serve.server import create_server_with_port_fallback, resolve_wiki_dir


def test_resolve_wiki_dir(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)

    assert resolve_wiki_dir(tmp_path) == wiki


def test_create_server_with_port_fallback_finds_port():
    from scripts.serve.handler import WikiHandler

    server, port = create_server_with_port_fallback("127.0.0.1", 0, WikiHandler)
    server.server_close()

    assert isinstance(port, int)
    assert port > 0
