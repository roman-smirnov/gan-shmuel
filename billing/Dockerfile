FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /billingdb

# TODO: Later, when we work with Excel, we will need to use openpyxl because it is the only one that works with Alpine.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./run.py .
COPY ./app ./app
COPY ./tests ./tests

RUN mkdir -p /in
EXPOSE 5000
ENV DEBUG=true

CMD ["python3", "run.py"]
