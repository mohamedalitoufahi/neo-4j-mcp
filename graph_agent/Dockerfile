# Dockerfile for Neo4j Graph Agent
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent code
COPY graph_agent.py ./

# Set environment variables (if needed)
# ENV GOOGLE_APPLICATION_CREDENTIALS=/app/formulai-dc0eba0c6712.json

CMD ["python", "graph_agent.py"]
