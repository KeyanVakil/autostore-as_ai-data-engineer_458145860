FROM python:3.11-slim

# Install Java for PySpark
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PYSPARK_PYTHON=python3

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY src/ src/
COPY data/ data/

RUN mkdir -p /data/delta /data/uploads

EXPOSE 8000

CMD ["uvicorn", "warehouse_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
