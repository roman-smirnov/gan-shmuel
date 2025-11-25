FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /billingdb

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./run.py .
COPY ./app ./app
COPY ./tests ./tests

RUN mkdir -p /in
EXPOSE 5000
ENV DEBUG=true

CMD ["python3", "run.py"]
