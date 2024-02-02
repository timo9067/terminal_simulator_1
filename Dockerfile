FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Define environment variable
ENV FLASK_APP term_sim.py


CMD ["gunicorn", "--bind", "0.0.0.0:5000", "term_sim:app"]
