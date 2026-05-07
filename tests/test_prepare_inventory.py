import json

from scripts.pipeline.prepare_inventory import prepare_inventory


def test_prepare_inventory_classifies_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "app.py").write_text("def main(): pass\n", encoding="utf-8")
    (tmp_path / "tests" / "test_app.py").write_text("def test_app(): pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Sample\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='sample'\n", encoding="utf-8")

    inventory = prepare_inventory(tmp_path)
    by_path = {item["path"]: item for item in inventory["files"]}

    assert by_path["src/app.py"]["category"] == "code"
    assert by_path["tests/test_app.py"]["is_test"] is True
    assert by_path["README.md"]["is_doc"] is True
    assert by_path["pyproject.toml"]["is_config"] is True
    assert "python" in inventory["languages"]
    assert "pip" in inventory["package_managers"]
    assert inventory["entry_candidates"]


def test_prepare_inventory_writes_cache_file(tmp_path):
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")

    inventory = prepare_inventory(tmp_path, save_to_cache=True)

    output = tmp_path / ".deepwiki" / "cache" / "project-inventory.json"
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["project_name"] == inventory["project_name"]
