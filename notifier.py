import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def send_email(config, subject, body_html):
    """
    Sends an HTML email using the configuration.
    """
    sender_email = config['email']['sender']
    app_password = config['email']['password']
    recipient = config['email']['recipient']
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body_html, 'html'))
    
    try:
        logging.info(f"Sending email to {recipient}...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient, msg.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
