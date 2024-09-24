# Use the base image with Python 3.10
FROM python:3.10 as base

# Builder stage for installing dependencies
FROM base as builder

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container at /code/requirements.txt
COPY requirements.txt /code/requirements.txt

# Install the Python dependencies
RUN pip install --upgrade --no-cache-dir -r /code/requirements.txt

# Copy the application folder inside the container
COPY app /code/app

# Final stage: Set up the environment for running the application
FROM builder

# Set the working directory in the container
WORKDIR /code/app

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
