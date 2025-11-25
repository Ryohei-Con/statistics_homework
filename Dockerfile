FROM python:3.12 AS builder

ENV POETRY_HOME="opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true
RUN poetry install --no-root --only main


FROM python:3.12-slim AS final

COPY --from=builder /app/.venv /app/.venv
WORKDIR /app
COPY . .

ENV VENV_PATH="/app/.venv"
ENV PATH="$VENV_PATH/bin:$PATH"