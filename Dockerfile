FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server ./server
COPY upstream ./upstream
COPY openenv.yaml README.md ATTRIBUTION.md LICENSE ./
RUN cp server/runner.py /opt/reconcile-runner.py && chmod 700 /app && chmod 644 /opt/reconcile-runner.py && mkdir /workspaces && chmod 711 /workspaces
EXPOSE 8000
CMD ["uvicorn","server.app:app","--host","0.0.0.0","--port","8000"]
