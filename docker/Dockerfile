FROM python:3.12-alpine AS builder

RUN apk add --virtual build-deps
RUN apk add gcc python3-dev musl-dev linux-headers postgresql-dev

RUN pip3 install --no-cache-dir poetry


COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

WORKDIR /app
RUN poetry config virtualenvs.create false && \
    poetry install --with dev --no-root


COPY ya_gpt_bot /app/ya_gpt_bot

RUN pip3 install .

ENTRYPOINT ["ya-gpt-bot"]
CMD ["run", "config.yaml"]
