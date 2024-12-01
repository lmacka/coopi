# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.10.10-bullseye-run

# Set environment variable for timezone
ENV TZ=Australia/Brisbane

# Set the working directory in the container
WORKDIR /coopi

# Copy the current directory contents into the container at /coopi
COPY . /coopi

# Install tzdata package and set up the timezone
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    # Install Python dependencies
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Make port 8086 available to the world outside this container
EXPOSE 8086

# Run coopi.py when the container launches
CMD ["python", "-m", "coopi.coopi"]