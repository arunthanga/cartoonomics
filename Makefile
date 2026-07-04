PYTHON ?= python3
export PYTHONPATH := src

.PHONY: help install tdd-on tdd-off tdd-status test test-unit test-regression demo clean

help:
	@echo "cartoonomics — make targets"
	@echo "  install          Install dev dependencies (pytest, hypothesis, pdfplumber, fpdf2)"
	@echo "  tdd-on           Switch TDD mode ON  (tests + coverage gate development)"
	@echo "  tdd-off          Switch TDD mode OFF (tests run but do not gate)"
	@echo "  tdd-status       Show current TDD mode"
	@echo "  test             Run unit + regression suites (honours TDD mode)"
	@echo "  test-unit        Run only the unit suite"
	@echo "  test-regression  Run only the regression suite"
	@echo "  demo             Regenerate web/cartoon_spec.json from the sample filing"

install:
	$(PYTHON) -m pip install --user -e ".[dev]"

tdd-on:
	$(PYTHON) -m cartoonomics.tdd on

tdd-off:
	$(PYTHON) -m cartoonomics.tdd off

tdd-status:
	$(PYTHON) -m cartoonomics.tdd status

test:
	bash scripts/run_tests.sh all

test-unit:
	bash scripts/run_tests.sh unit

test-regression:
	bash scripts/run_tests.sh regression

demo:
	$(PYTHON) -m cartoonomics.pipeline --out web/cartoon_spec.json

serve: demo
	@echo "Serving the cartoon at http://localhost:8000 (Ctrl-C to stop)"
	cd web && $(PYTHON) -m http.server 8000

clean:
	rm -rf .pytest_cache .coverage htmlcov **/__pycache__
