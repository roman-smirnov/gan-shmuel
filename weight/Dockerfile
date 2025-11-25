FROM python:3.12-slim

# Create non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy requirements and install as root
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api/app.py src/app.py
COPY api/utils.py src/utils.py
COPY api/__init__.py src/__init__.py


#Copy UI files
COPY api/templates/ src/templates/
COPY api/static/ src/static/

#copy test files
COPY tests/ /app/tests
COPY __init__.py . 

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Run the application
ENTRYPOINT ["python", "-m", "src.app"]