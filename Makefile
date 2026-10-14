PY ?= python

.PHONY: test run check clean

test:
	$(PY) -m pytest -q

run:
	$(PY) scripts/run_bridge.py --out build/sample-report.md

check:
	$(PY) scripts/run_bridge.py --out build/sample-report.md

clean:
	rm -rf build .pytest_cache
