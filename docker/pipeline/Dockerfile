FROM python:3.11-slim

# Installer dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget curl build-essential python3-dev gfortran libopenblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer uv (ultra rapide)
RUN pip install uv

WORKDIR /workspace

COPY requirements.txt /workspace/requirements.txt

# Installer les dépendances (avec cache Docker BuildKit si dispo)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache -r /workspace/requirements.txt

# Installer mc (MinIO client)
RUN wget -q https://dl.min.io/client/mc/release/linux-amd64/mc -O /usr/bin/mc \
    && chmod +x /usr/bin/mc

# Script init
COPY init_dvc.sh /workspace/init_dvc.sh
RUN chmod +x /workspace/init_dvc.sh

CMD ["/workspace/init_dvc.sh"]
