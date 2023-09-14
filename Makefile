PATH := ./venv/bin:${PATH}
sources = garminconnect tests setup.py

.PHONY: .venv  ## Install virtual environment
.venv:
	python3 -m venv .venv
	python3 -m pip install -qU pip

.PHONY: install  ## Install package
install: .venv
	pip3 install -qUe .

.PHONY: install-test  ## Install package in development mode
install-test: .venv install
	pip3 install -qU -r requirements-test.txt

.PHONY: test  ## Run tests
test:
	pytest --cov=garminconnect --cov-report=term-missing