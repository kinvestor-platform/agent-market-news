FROM python:3.12-slim
WORKDIR /app
# Copy and install kinagent from local source (avoids git-over-HTTPS in cross-platform builds)
COPY kinagent/ ./kinagent/
RUN pip install --no-cache-dir ./kinagent
# Install agent
COPY agent/ ./agent/
COPY agent.manifest.json .
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "agent.main"]
