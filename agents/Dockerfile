# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY agents/requirements.txt /tmp/agents-requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/agents-requirements.txt

COPY agents /app/agents

EXPOSE 8060

CMD ["python", "-m", "uvicorn", "agents.http_app:app", "--host", "0.0.0.0", "--port", "8060"]
