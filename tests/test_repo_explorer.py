from codex_contributor.repo_explorer import map_repository


def test_maps_python_symbols_and_test_runner(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    package = tmp_path / "src"
    package.mkdir()
    (package / "app.py").write_text("class Service:\n    def run(self):\n        pass\n", encoding="utf-8")
    result = map_repository(tmp_path)
    assert result.languages == {"Python": 1}
    assert result.test_command == ["python", "-m", "pytest"]
    assert result.symbols["src/app.py"] == ["Service", "run"]

