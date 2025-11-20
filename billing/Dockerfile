FROM python:3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /billing
#בהמשך כשנעבוד עם אקסל נצורך להשתשמש עם openpyxl שרק הוא עובד עם  alpine
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./run.py .
COPY ./app ./app
RUN mkdir -p /in
EXPOSE 5000
ENV DEBUG=true
CMD ["python3", "run.py"]
