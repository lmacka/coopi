# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.11.2-bullseye-run

# Set environment variable for timezone and working directory
ENV TZ=Australia/Brisbane
WORKDIR /coopi

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Combine all RUN commands and clean up in the same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache && \
    # Create var directory
    mkdir -p var

# Copy only the application code
COPY coopi coopi/

# Make port 8086 available
EXPOSE 8086

# Run the application
CMD ["python", "-m", "coopi.coopi"]