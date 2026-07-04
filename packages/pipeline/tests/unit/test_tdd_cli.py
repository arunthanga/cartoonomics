import pytest

from cartoonomics import config, tdd


@pytest.fixture(autouse=True)
def _isolate_state(monkeypatch, tmp_path):
    monkeypatch.delenv(config.TDD_ENV_VAR, raising=False)
    monkeypatch.setattr(config, "repo_root", lambda: tmp_path)


@pytest.mark.unit
def test_cli_on_off_status(capsys):
    assert tdd.main(["on"]) == 0
    assert config.tdd_mode_enabled() is True
    assert "ON" in capsys.readouterr().out

    assert tdd.main(["off"]) == 0
    assert config.tdd_mode_enabled() is False
    assert "OFF" in capsys.readouterr().out

    assert tdd.main(["status"]) == 0
    assert "OFF" in capsys.readouterr().out


@pytest.mark.unit
def test_cli_defaults_to_status(capsys):
    assert tdd.main([]) == 0
    assert "TDD mode" in capsys.readouterr().out


@pytest.mark.unit
def test_cli_unknown_command_errors(capsys):
    assert tdd.main(["frobnicate"]) == 2
    assert "unknown command" in capsys.readouterr().err
