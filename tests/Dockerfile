# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM python:3.12-slim

ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=${APP_HOME}:${APP_HOME}/mcp
ENV BLENDER_MCP_TEST_IN_DOCKER=1

WORKDIR ${APP_HOME}

COPY mcp/requirements.txt /tmp/mcp-requirements.txt
COPY tests/requirements.txt /tmp/test-requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/mcp-requirements.txt -r /tmp/test-requirements.txt

COPY mcp ${APP_HOME}/mcp
RUN pip install --no-cache-dir -e ${APP_HOME}/mcp

COPY agents ${APP_HOME}/agents
COPY tests ${APP_HOME}/tests
COPY _misc ${APP_HOME}/_misc
COPY chat_client ${APP_HOME}/chat_client

CMD ["python", "tests/run_unit_tests.py"]
