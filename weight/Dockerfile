FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements and install
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and tests
COPY api /app/api
COPY tests /app/tests

ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

EXPOSE 5000

# Run app.py 
CMD ["python", "api/app.py"]
