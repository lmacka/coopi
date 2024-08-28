# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /coopi

# Copy the current directory contents into the container at /coopi
COPY . /coopi

# Install any needed packages specified in requirements.txt using prebuilt wheels from PiWheels
RUN pip install --no-cache-dir --only-binary=:all: --extra-index-url=https://www.piwheels.org/simple -r requirements.txt

# Make port 8086 available to the world outside this container
EXPOSE 8086

# Run coopi.py when the container launches
CMD ["python", "coopi.py"]