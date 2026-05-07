from scripts.serve.server import find_available_port, wiki_dir_for_project


def test_wiki_dir_for_project_requires_wiki_dir(tmp_path):
    wiki = tmp_path / ".deepwiki" / "wiki"
    wiki.mkdir(parents=True)

    assert wiki_dir_for_project(tmp_path) == wiki


def test_find_available_port_returns_usable_port():
    port = find_available_port("127.0.0.1", 8742)

    assert isinstance(port, int)
    assert port >= 8742
