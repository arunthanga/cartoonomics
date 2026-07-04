import json

import pytest

from cartoonomics.format import CartoonSpec
from cartoonomics.pipeline import main, run_demo


@pytest.mark.unit
def test_run_demo_produces_valid_spec():
    spec = run_demo()
    assert isinstance(spec, CartoonSpec)
    assert spec.entity_name == "Acme Industries Ltd"
    assert spec.provenance.source == "BSE"
    assert spec.provenance.source_hash  # provenance captured


@pytest.mark.unit
def test_main_writes_json_file(tmp_path, capsys):
    out = tmp_path / "spec.json"
    rc = main(["--out", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text())
    assert payload["cartoon_type"] == "cashflow"
    assert "Wrote CartoonSpec" in capsys.readouterr().out


@pytest.mark.unit
def test_main_prints_json_when_no_out(capsys):
    rc = main([])
    assert rc == 0
    printed = capsys.readouterr().out
    assert json.loads(printed)["entity_name"] == "Acme Industries Ltd"
