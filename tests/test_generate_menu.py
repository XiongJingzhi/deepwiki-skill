import json

from scripts.wiki.generate_menu import generate_menu


def test_generate_menu_uses_menu_seed(tmp_path):
    cache = tmp_path / ".deepwiki" / "cache"
    wiki = tmp_path / ".deepwiki" / "wiki"
    cache.mkdir(parents=True)
    wiki.mkdir(parents=True)
    (wiki / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (wiki / "deep-dive").mkdir()
    (wiki / "deep-dive" / "runtime.md").write_text("# Runtime\n", encoding="utf-8")
    plan = {
        "pages": [
            {"page_id": "overview", "title": "Overview", "output_path": "overview.md", "page_type": "overview"},
            {"page_id": "runtime", "title": "Runtime", "output_path": "deep-dive/runtime.md", "page_type": "deep-dive"},
        ],
        "menu_seed": [
            {"title": "Start", "page_ids": ["overview"]},
            {"title": "Details", "page_ids": ["runtime"]},
        ],
    }
    (cache / "page-plan.json").write_text(json.dumps(plan), encoding="utf-8")

    menu = generate_menu(tmp_path, "Sample")

    assert menu["title"] == "Sample"
    assert menu["items"][0]["title"] == "Start"
    assert menu["items"][0]["items"][0] == {"title": "Overview", "path": "overview.md"}
    assert (wiki / "menu.json").exists()
    assert (wiki / "doc-map.md").exists()


def test_generate_menu_groups_by_page_type_without_seed(tmp_path):
    cache = tmp_path / ".deepwiki" / "cache"
    wiki = tmp_path / ".deepwiki" / "wiki"
    cache.mkdir(parents=True)
    wiki.mkdir(parents=True)
    plan = {
        "pages": [
            {"page_id": "runtime", "title": "Runtime", "output_path": "deep-dive/runtime.md", "page_type": "deep-dive"}
        ],
        "menu_seed": [],
    }
    (cache / "page-plan.json").write_text(json.dumps(plan), encoding="utf-8")

    menu = generate_menu(tmp_path)

    assert menu["items"] == [{"title": "Deep Dive", "items": [{"title": "Runtime", "path": "deep-dive/runtime.md"}]}]
