# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.11-bookworm-run

ARG VERSION
ARG BUILD_DATE
ARG VCS_REF

LABEL org.label-schema.version=$VERSION \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.vcs-ref=$VCS_REF

# Set version as an environment variable during build
ENV APP_VERSION=$VERSION

# Set environment variables
ENV TZ=Australia/Brisbane \
    PYTHONUNBUFFERED=1

WORKDIR /coopi

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    pip install --no-cache-dir --extra-index-url https://www.piwheels.org/simple -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p var

# Copy application code
COPY coopi coopi/

# Make port 80 available
EXPOSE 80

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout", "120", "coopi.coopi:app"]