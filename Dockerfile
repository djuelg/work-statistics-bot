# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install Poetry
RUN pip install poetry

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the pyproject.toml and optionally poetry.lock file
COPY pyproject.toml poetry.lock* ./

# Disable virtualenv creation by Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of your application's code
COPY . .

# Make port 80 available to the world outside this container
# EXPOSE 80

# Run bot.py when the container launches
CMD ["python3", "./bot.py"]