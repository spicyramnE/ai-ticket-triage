# Containerize the triage web app (demonstrates Docker / containerization).
FROM python:3.11-slim

WORKDIR /app
COPY . .

# Only Flask is needed to serve the app and the 3-stage demo (the queue, the
# rule-based triage, and the AI results, which are read from output_with_ai.csv).
RUN pip install --no-cache-dir flask

EXPOSE 5000
CMD ["python", "webapp.py"]
