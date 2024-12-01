# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.10-bullseye-run

# Set environment variables
ENV TZ=Australia/Brisbane \
    VERSION=${VERSION:-v0.1.0} \
    PYTHONUNBUFFERED=1

WORKDIR /coopi

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p var

# Copy application code
COPY coopi coopi/

# Make port 80 available
EXPOSE 80

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "120", "coopi.coopi:app"]