# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install FFMPEG
RUN apt-get update && apt-get install -y ffmpeg

RUN apt-get update && apt-get install -y gcc libpq-dev

# Copy the cloud_run app directory
COPY ./cloudrun /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./shared /usr/src/app/shared

# Expose the port the app runs on
EXPOSE 8080

# Run app.py when the container launches
CMD ["python", "./main.py"]