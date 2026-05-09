# Westlake Singularity — Docker Image
# Developer: Jiaxiang Cong · Lingyuan Kong Lab · Westlake University

FROM python:3.11-slim

LABEL org.opencontainers.image.title="Westlake Singularity"
LABEL org.opencontainers.image.description="AI-Native Quantum Laboratory OS"
LABEL org.opencontainers.image.authors="Jiaxiang Cong <congjiaxiang@westlake.edu.cn>"
LABEL org.opencontainers.image.vendor="Lingyuan Kong Lab, Westlake University"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

EXPOSE 9876

ENV SINGULARITY_HOME=/app/data

CMD ["python", "-m", "core.main"]
