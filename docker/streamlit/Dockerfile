FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
# We only need a subset of requirements for streamlit, but installing all is easier for now
# or we can manually install specific ones to keep image small
RUN pip install streamlit requests pandas plotly graphviz

COPY src/ /app/src/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "src/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
