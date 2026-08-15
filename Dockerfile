FROM python:3.11.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
RUN pip install --no-cache-dir .
COPY . .
ENTRYPOINT ["hizmet-nabiz"]
CMD ["--help"]
