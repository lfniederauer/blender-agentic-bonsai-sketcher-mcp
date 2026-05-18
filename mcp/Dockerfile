# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

FROM python:3.12-slim

ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR ${APP_HOME}

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

COPY . ${APP_HOME}
RUN pip install --no-cache-dir .

EXPOSE 8050

CMD ["blender-mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8050"]
