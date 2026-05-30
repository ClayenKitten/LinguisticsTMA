FROM python:3.14-slim
WORKDIR /app
EXPOSE 8501

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock /app/
RUN uv sync --locked

COPY . /app/

CMD ["uv", "run", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
