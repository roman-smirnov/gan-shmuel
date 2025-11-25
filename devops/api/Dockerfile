FROM docker:27-cli

RUN apk add --no-cache python3 py3-pip git bash 


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY devops/api/requirements.txt /app/devops/api/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages \
    -r /app/devops/api/requirements.txt

COPY devops/api/src /app/devops/api/src

WORKDIR /app/devops/api/src

EXPOSE 5000

ENTRYPOINT ["python3", "app.py"]