FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_APP term_sim.py
ENV PORT 5000

EXPOSE 5000

# Define environment variable


CMD gunicorn --bind 0.0.0.0:$PORT term_sim:app
