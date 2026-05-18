# Optional local overrides (silently skipped when absent).
# Exported so child processes inherit them as environment variables.
-include .env
export

PYTHON ?= python
PYTHON_SOURCE_DIRS_TO_CHECK = mcp/blmcp/ mcp/blender_mcp_addon/ chat_client/ _misc/

define HELP_TEXT

Targets
   * test:              Run unit tests in Docker (HTTP MCP + test container).
   * test_up:           Start blender-mcp test stack (HTTP on BLENDER_MCP_HTTP_PORT).
   * test_down:         Stop blender-mcp test stack.
   * test_blender:      Blender integration tests (host Blender + Docker MCP HTTP).
   * test_local:        Run unit tests on the host (stdio MCP, no Docker).
   * test_rst_parse:    Run unit tests for RST manual/API doc parsing.
   * test_rst_search:   Run unit tests for the RST text-search layer.
   * test_integration:  Run integration tests (requires BLENDER_BIN).
                        Loads .env if present (e.g. ANTHROPIC_API_KEY).
                        Uses .test_venv (delete to force a rebuild).
   * build:             Build MCP/agent Docker images (mcp/docker-compose.yml).
   * run:               Start MCP stack in the background (no rebuild).
   * run-build:         Build and start MCP stack in the background.
   * install_agents:    Install Google ADK agent dependencies from agents/requirements.txt.
   * run_agent:         Run BIM ADK coordinator once via Docker Compose (QUERY='...').
                        Starts blender-mcp if needed; uses mcp/.env (GEMINI_API_KEY).
   * run_agent_web:     Run ADK web UI with agents/main.py entrypoint.
   * agents_up:         Alias for run-build (MCP HTTP + optional BIM agent).
   * agents_down:       Stop MCP stack (alias: make down).

     List all tests:    make test_integration TESTS_LIST=1
     Run tests:         make test_integration TESTS=TestChatClient.test_name
     Multiple tests:    make test_integration TESTS="test_one test_two"
   * format:            Auto-format Python sources with autopep8.
   * readme_update:     Regenerate the tools listing in readme.rst.

Static Source Code Checking
   * check_license:   Verify SPDX headers in all Python files.
   * check_ascii:     Reject non-ASCII characters in sources.
   * check_mypy:      Run mypy type checking.
   * check_pylint:    Run pylint linting.
   * check_ruff:      Run ruff linting.
   * check_vulture:   Run vulture dead-code detection.
   * check_namespace: Verify __all__ is defined in all Python modules.
   * check_all:       Run all checks (ruff, mypy, vulture, license, ascii, namespace).

Reference Data
   * update_reference_manual:
     Copy RST and Python files from a Blender manual checkout.

     Usage: make update_reference_manual MANUAL_DIR=/path/to/manual

   * update_reference_api:
     Copy RST files from a Blender API reference build.

     Usage: make update_reference_api API_DIR=/path/to/api

Environment Variables
   Variables may be set in a .env file (loaded automatically).

   PYTHON              Python interpreter (default: python).
   BLENDER_BIN         Path to the Blender binary (default: blender).
   BLENDER_MCP         Path to the blender-mcp command (default: blender-mcp).
   BLENDER_PATH        Path to the Blender binary used by the MCP server
                       (default: blender).
   BLENDER_MCP_HOST    Host the MCP addon listens on (default: localhost).
   BLENDER_MCP_PORT    Port the MCP addon listens on (default: 9876).
   BLENDER_MCP_TIMEOUT Startup timeout in seconds for tests (default: 10).
   GLOBAL_TIMEOUT_SCALE
                       Multiply all test timeouts by this factor
                       (default: 1). Useful on slower systems or
                       with slower models.
   BLENDER_MCP_FOREGROUND
                       When set, run Blender in the foreground during tests.
   ANTHROPIC_API_KEY   API key for Claude integration tests.
   ANTHROPIC_MODEL     Model name for Claude tests
                       (default: claude-sonnet-4-20250514).
   USE_LLAMA_CXX       When set, run LLM tests using llama-server.
                       Cannot be combined with USE_ANTHROPIC.
                       Requires LLAMA_SERVER_BIN and
                       LLAMA_SERVER_ARGS.
                       Note: many tests may fail depending on the
                       capability of the model.
   LLAMA_SERVER_BIN    Path to the llama-server binary.
   LLAMA_SERVER_ARGS   Extra arguments for llama-server
                       (e.g. --jinja -m model.gguf).
                       The port is provided by the test harness;
                       do not include --port.
   LLAMA_SERVER_VERBOSE
                       When set, forward llama-server output to
                       the terminal.
   GEMINI_API_KEY      API key used by Google ADK model calls.
   BLENDER_MCP_HTTP_URL
                       HTTP MCP endpoint used by agents and Docker tests
                       (default: http://127.0.0.1:8050/).
   BLENDER_MCP_TEST_HTTP_PORT
                       Port for blender-mcp HTTP in the Docker *test* stack
                       (default: 18050; avoids clashing with production 8050).
   BLENDER_MCP_HTTP_PORT
                       Port for blender-mcp HTTP in mcp/docker-compose.yml
                       (default: 8050).
   BIM_AGENT_HTTP_PORT
                       Port for the Docker BIM agent HTTP API (default: 8060).

endef

TEST_COMPOSE = docker compose -f tests/docker-compose.test.yml
MCP_COMPOSE = docker compose -f mcp/docker-compose.yml
# Dedicated port for the test stack (avoids clashing with mcp/docker-compose on 8050).
BLENDER_MCP_TEST_HTTP_PORT ?= 18050
BLENDER_MCP_HTTP_PORT ?= 8050
BLENDER_MCP_HTTP_URL ?= http://127.0.0.1:$(BLENDER_MCP_TEST_HTTP_PORT)/
export BLENDER_MCP_TEST_HTTP_PORT
export BLENDER_MCP_HTTP_URL
export HELP_TEXT

help:
	@echo "$$HELP_TEXT"

test: test_up
	$(TEST_COMPOSE) --profile test run --rm --build test
	$(MAKE) test_down

test_up:
	$(TEST_COMPOSE) up -d --build blender-mcp

test_down:
	$(TEST_COMPOSE) down --remove-orphans

test_local:
	$(PYTHON) tests/test_rst_parse.py
	$(PYTHON) tests/test_rst_search.py
	$(PYTHON) tests/test_mcp_server.py
	$(PYTHON) tests/test_tool_listing.py
	$(PYTHON) -m pytest tests/test_knowledge_loader.py -q

test_blender: test_up
	@command -v "$(BLENDER_BIN)" >/dev/null 2>&1 || command -v blender >/dev/null 2>&1 || { \
		echo "ERROR: set BLENDER_BIN or install blender for test_blender"; exit 1; }
	BLENDER_MCP_HTTP_URL="$(BLENDER_MCP_HTTP_URL)" BLENDER_MCP_PORT="$(BLENDER_MCP_PORT)" \
		$(PYTHON) tests/test_blender_mcp_with_blender.py
	$(MAKE) test_down

test_rst_parse:
	$(PYTHON) tests/test_rst_parse.py

test_rst_search:
	$(PYTHON) tests/test_rst_search.py

test_integration:
ifdef TESTS_LIST
	@$(PYTHON) _misc/test_integration_tests_list.py
else
	$(PYTHON) tests/integration/test_blender_mcp_with_llm.py $(TESTS)
endif

install_agents:
	$(PYTHON) -m pip install -r agents/requirements.txt

run_agent:
	$(MCP_COMPOSE) up -d --build blender-mcp
	$(MCP_COMPOSE) run --rm --build --no-deps bim-agent \
		python -m agents.main \
		$$(if [ "$$ADK_TRACE" = "1" ]; then echo --trace; fi) \
		"$${QUERY:-bim_status and summarize the scene}"

run_agent_web:
	@if [ -z "$$GEMINI_API_KEY" ]; then \
		export GEMINI_API_KEY=$$(grep '^GEMINI_API_KEY=' .env 2>/dev/null | sed 's/^GEMINI_API_KEY=//'); \
	fi; \
	if [ -z "$$BLENDER_MCP_HTTP_URL" ]; then \
		export BLENDER_MCP_HTTP_URL=$$(grep '^BLENDER_MCP_HTTP_URL=' .env 2>/dev/null | sed 's/^BLENDER_MCP_HTTP_URL=//'); \
	fi; \
	PYTHONPATH=. adk web agents/main.py

build:
	$(MCP_COMPOSE) build

run:
	$(MCP_COMPOSE) up -d

run-build:
	$(MCP_COMPOSE) up -d --build

agents_up: run-build

agents_down down:
	$(MCP_COMPOSE) down

format:
	@for d in mcp addon _misc tests chat_client; do \
		autopep8 --in-place --recursive $$d || exit 1; \
	done

check_license:
	@$(PYTHON) _misc/check_license.py

check_ascii:
	@$(PYTHON) _misc/check_ascii.py

check_mypy:
	@! $(PYTHON) -m mypy --exclude 'data/api/examples/' $(PYTHON_SOURCE_DIRS_TO_CHECK) 2>&1 | grep -v '^stubs/' | grep ': error:' || \
		{ echo "mypy: found errors"; exit 1; }

check_pylint:
	pylint $(PYTHON_SOURCE_DIRS_TO_CHECK) \
		--disable=C0103,C0115,C0116,C0209,C0413,C0415,R0801,R0903,R0912,R0914,R0915,W0122

check_ruff:
	ruff check $(PYTHON_SOURCE_DIRS_TO_CHECK)

check_vulture:
	vulture $(PYTHON_SOURCE_DIRS_TO_CHECK) \
		--exclude mcp/blmcp/data/api/examples \
		--ignore-decorators '@mcp.tool,@mcp.prompt' \
		--ignore-names 'bl_*,draw,execute,exclude' \
		--min-confidence 61

check_namespace:
	@$(PYTHON) _misc/check_namespace.py --skip mcp/blmcp/data/api/examples $(PYTHON_SOURCE_DIRS_TO_CHECK)

check_all: check_ruff check_mypy check_vulture check_license check_ascii check_namespace

readme_update:
	$(PYTHON) _misc/readme_update_from_tools.py

update_reference_manual:
	@test -n "$(MANUAL_DIR)" || { echo "Usage: make update_reference_manual MANUAL_DIR=/path/to/blender/manual"; exit 1; }
	$(PYTHON) _misc/update_reference_manual.py "$(MANUAL_DIR)"

update_reference_api:
	@test -n "$(API_DIR)" || { echo "Usage: make update_reference_api API_DIR=/path/to/api"; exit 1; }
	$(PYTHON) _misc/update_reference_api.py "$(API_DIR)"

.PHONY: test test_up test_down test_local test_blender build run run-build install_agents run_agent run_agent_web agents_up agents_down down
