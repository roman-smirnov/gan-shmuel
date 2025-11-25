FROM python:3.12-slim


WORKDIR /app

# Copy requirements and install
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and tests
COPY api /app/api
COPY tests /app/tests

ENV PYTHONPATH=/app


EXPOSE 5000

# Run app.py 
CMD ["python", "api/app.py"]
