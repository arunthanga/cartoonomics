import pytest

from cartoonomics import config


@pytest.mark.unit
def test_default_is_tdd_on(monkeypatch, tmp_path):
    monkeypatch.delenv(config.TDD_ENV_VAR, raising=False)
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)
    assert config.tdd_mode_enabled() is True


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [("on", True), ("1", True), ("true", True), ("off", False), ("0", False), ("no", False)],
)
def test_env_var_overrides(monkeypatch, tmp_path, value, expected):
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)
    monkeypatch.setenv(config.TDD_ENV_VAR, value)
    assert config.tdd_mode_enabled() is expected


@pytest.mark.unit
def test_state_file_used_when_env_absent(monkeypatch, tmp_path):
    monkeypatch.delenv(config.TDD_ENV_VAR, raising=False)
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)
    config.set_tdd_mode(False)
    assert config.tdd_mode_enabled() is False
    config.set_tdd_mode(True)
    assert config.tdd_mode_enabled() is True


@pytest.mark.unit
def test_env_var_beats_state_file(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)
    config.set_tdd_mode(False)
    monkeypatch.setenv(config.TDD_ENV_VAR, "on")
    assert config.tdd_mode_enabled() is True


@pytest.mark.unit
def test_unparseable_env_falls_through_to_default(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)
    monkeypatch.setenv(config.TDD_ENV_VAR, "maybe")
    assert config.tdd_mode_enabled() is True
