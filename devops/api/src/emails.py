import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")


SENDER = os.getenv("EMAIL_SENDER")
PASSWORD = os.getenv("EMAIL_PASSWORD")
DEVELOPERS_RAW = os.getenv("EMAIL_DEVELOPERS", "")
DEVOPS_RAW = os.getenv("EMAIL_DEVOPS_DEVELOPERS", "")


DEVOPS_DEVELOPERS = [email.strip() for email in DEVOPS_RAW.split(",") if email.strip()]
DEVELOPERS = [email.strip() for email in DEVELOPERS_RAW.split(",") if email.strip()]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(subject, body, recipients):
    if not SENDER:
        print(" Missing EMAIL_SENDER in environment variables")
        return False

    if not PASSWORD:
        print(" Missing EMAIL_PASSWORD in environment variables")
        return False

    if not recipients:
        print(" No recipients provided")
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = ", ".join(recipients)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, recipients, msg.as_string())

        print(f"✔ Email sent: {subject}")
        return True

    except Exception as e:
        print(f" Email error: {e}")
        return False


def notify_service_down(service_name):
    body = (
        f"Service Down\n"
        f"Service: {service_name}\n"
        f"Status: Not Responding\n"
        f"Immediate attention required."
    )

    return send_email(
        subject=f"Service DOWN: {service_name}",
        body=body,
        recipients=DEVELOPERS
    )


def notify_service_recovered(service_name, downtime_minutes):
    body = (
        f"Service Recovered\n"
        f"Service: {service_name}\n"
        f"Downtime: {downtime_minutes} minutes\n"
        f"Status: Online"
    )

    return send_email(
        subject=f"Service UP: {service_name}",
        body=body,
        recipients=DEVELOPERS
    )

def notify_devops_deployment(status_msg):
    return send_email(
        subject="DEPLOYMENT STATUS",
        body=status_msg,
        recipients=DEVOPS_DEVELOPERS
    )

