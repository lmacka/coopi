# Use a balena Python runtime as a parent image
FROM balenalib/raspberry-pi-python:3.10.10-bullseye-run

# Set the working directory in the container
WORKDIR /coopi

# Copy the current directory contents into the container at /coopi
COPY . /coopi

# # Install any needed packages specified in requirements.txt using prebuilt wheels from PiWheels and PyPI
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Make port 8086 available to the world outside this container
EXPOSE 8086

# # Run coopi.py when the container launches
CMD ["python", "-m", "coopi.coopi"]