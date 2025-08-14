# Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY ollama_loki_agent.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 11435
CMD ["python", "ollama_loki_agent.py"]
