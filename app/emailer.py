# app/emailer.py
import os
import smtplib
from email.mime.text import MIMEText

def send_email(subject: str, body: str, recipients_csv: str):
    recipients = [e.strip() for e in recipients_csv.split(",") if e.strip()]
    if not recipients:
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = os.getenv("SMTP_FROM")
    msg["To"] = ", ".join(recipients)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(msg["From"], recipients, msg.as_string())
