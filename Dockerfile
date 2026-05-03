FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "kinagent @ git+https://github.com/kinvestor-platform/kinagent.git@develop"
COPY agent/ ./agent/
COPY agent.manifest.json .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "agent.main"]
