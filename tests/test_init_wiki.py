from scripts.wiki.init_wiki import init_wiki


def test_init_wiki_creates_clean_layout(tmp_path):
    result = init_wiki(tmp_path)

    assert result["success"] is True
    assert (tmp_path / ".deepwiki" / "cache" / "page-context").is_dir()
    assert (tmp_path / ".deepwiki" / "state").is_dir()
    assert (tmp_path / ".deepwiki" / "wiki").is_dir()
    assert (tmp_path / ".deepwiki" / "config.yaml").exists()
