# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.11-bookworm-run

# Set environment variables
ENV TZ=Australia/Brisbane \
    PYTHONUNBUFFERED=1

WORKDIR /coopi

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tzdata \
    curl && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    pip install --no-cache-dir --extra-index-url https://www.piwheels.org/simple -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create data directory with appropriate permissions
RUN mkdir -p /data && \
    chmod 777 /data

# Copy application code
COPY coopi coopi/

# Make port 80 available
EXPOSE 80

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "120", "coopi.coopi:app"]