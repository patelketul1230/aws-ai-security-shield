.PHONY: help install test deploy destroy ui clean

VENV = .venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest

help:
	@echo "AWS AI Security & OWASP LLM Top 10 Shield Commands:"
	@echo "  make install   - Create virtualenv and install dependencies"
	@echo "  make test      - Run automated pytest test suite"
	@echo "  make deploy    - Deploy AWS infrastructure via Terraform & update UI config"
	@echo "  make destroy   - Teardown AWS infrastructure via Terraform"
	@echo "  make ui        - Launch Web UI Playground (http://localhost:8080)"
	@echo "  make clean     - Clean temporary build artifacts"

install:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	PYTHONPATH=. $(PYTEST) tests/ -v

deploy:
	@echo "Deploying AWS infrastructure via Terraform..."
	cd terraform && terraform init && terraform apply -auto-approve
	@echo "Updating Web UI configuration with dynamic Terraform endpoint..."
	@ENDPOINT=$$(cd terraform && terraform output -raw api_endpoint 2>/dev/null); \
	if [ -n "$$ENDPOINT" ]; then \
		echo "{\"api_endpoint\": \"$$ENDPOINT\"}" > src/ui/config.json; \
		echo "Successfully updated src/ui/config.json with: $$ENDPOINT"; \
	fi

destroy:
	cd terraform && terraform destroy -auto-approve

ui:
	@echo "Syncing Web UI configuration with Terraform state..."
	@ENDPOINT=$$(cd terraform && terraform output -raw api_endpoint 2>/dev/null); \
	if [ -n "$$ENDPOINT" ]; then \
		echo "{\"api_endpoint\": \"$$ENDPOINT\"}" > src/ui/config.json; \
		echo "Synced src/ui/config.json with live AWS API Gateway: $$ENDPOINT"; \
	elif [ ! -f src/ui/config.json ]; then \
		echo "{\"api_endpoint\": \"http://localhost:8080\"}" > src/ui/config.json; \
	fi
	@fuser -k 8080/tcp 2>/dev/null || true
	PYTHONPATH=. $(PYTHON) src/ui/server.py

clean:
	rm -rf __pycache__ .pytest_cache .venv terraform/.terraform terraform/*.tfstate* lambda_function.zip src/ui/config.json
