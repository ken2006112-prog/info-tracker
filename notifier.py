import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import requests
import json

def send_discord_webhook(config, subject, body_html):
    """
    Sends a message to Discord via Webhook.
    Note: Discord webhooks don't render HTML. We need to convert to basic text or markdown.
    """
    webhook_url = config['discord']['webhook_url']
    if not webhook_url:
        logging.warning("Discord enabled but no webhook URL provided.")
        return

    # Simple HTML to Text conversion (strip tags)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body_html, 'html.parser')
    text_content = soup.get_text(separator='\n')
    
    # Format message
    message = {
        "content": f"**{subject}**\n\n{text_content[:1900]}" # Discord limit is 2000 chars
    }
    
    try:
        logging.info("Sending Discord webhook...")
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        logging.info("Discord message sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send Discord message: {e}")

def send_email(config, subject, body_html):
    """
    Sends an HTML email using the configuration.
    """
    if not config['email'].get('enabled', True):
        return

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
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient, msg.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
