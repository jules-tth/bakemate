.PHONY: run install test

VENV_DIR = .venv

# Install dependencies
install: activate
	$(VENV_DIR)/bin/pip install -r requirements.txt

# Run the application
run: activate
	#$(VENV_DIR)/bin/python main.py
	$(VENV_DIR)/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test: activate
	$(VENV_DIR)/bin/pytest -v tests/

activate:
	@echo "Activating virtual environment at $(VENV_DIR)"
