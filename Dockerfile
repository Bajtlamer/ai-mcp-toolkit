FROM python:3.13.7-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for UI
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy Python requirements
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy UI source
COPY ui/ ./ui/

# Build UI
WORKDIR /app/ui
RUN npm install && npm run build

# Back to main directory
WORKDIR /app

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8000 5173

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting AI MCP Toolkit..."\n\
echo "Starting MCP Server on port 8000..."\n\
ai-mcp-toolkit serve --host 0.0.0.0 --port 8000 &\n\
echo "Starting UI on port 5173..."\n\
cd /app/ui && npm run preview -- --host 0.0.0.0 --port 5173\n\
' > start.sh && chmod +x start.sh

CMD ["./start.sh"]
