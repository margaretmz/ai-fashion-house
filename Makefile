.PHONY: start publish
publish:
	@echo "Building and publishing package..."
	@export $(shell grep -v '^#' .env | xargs) && \
	uv build && \
	uv publish --token $$PYPI_TOKEN
start:
	@echo "Starting the application..."
	@export $(shell grep -v '^#' .env | xargs) && \
	sh run.sh
