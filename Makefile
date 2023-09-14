PATH := ./venv/bin:${PATH}
sources = garminconnect tests setup.py

.PHONY: .venv  ## Install virtual environment
.venv:
	python -m venv .venv
	python -m pip install -qU pip

.PHONY: install  ## Install package
install: .venv
	pip install -qUe .

.PHONY: install-test  ## Install package in development mode
install-test: .venv install
	pip install -qU -r requirements-test.txt

.PHONY: test  ## Run tests
test:
	pytest --cov=garminconnect --cov-report=term-missing