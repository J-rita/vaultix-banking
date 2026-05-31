import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import threading

def send_email_async(to_email, subject, body):
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not sender_email or not sender_password:
        print(f"[Email Service Mock] Sending email to {to_email}")
        print(f"[Email Service Mock] Subject: {subject}")
        print(f"[Email Service Mock] Note: Set SMTP_EMAIL and SMTP_PASSWORD environment variables to send real emails.")
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"[Email Service] Email sent successfully to {to_email}")
    except Exception as e:
        print(f"[Email Service] Failed to send email to {to_email}: {e}")

def send_transaction_email(to_email, amount, transaction_type, balance, account_number, description=""):
    subject = f"Vaultix Transaction Alert: {transaction_type}"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Vaultix Banking Alert</h2>
                <p>Dear Customer,</p>
                <p>A <strong>{transaction_type}</strong> transaction has occurred on your account.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Amount</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{amount:,.2f} NGN</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Account Number</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{account_number}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Description</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{description}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Current Balance</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #eee;">{balance:,.2f} NGN</td>
                    </tr>
                </table>
                <p>Thank you for banking with Vaultix!</p>
            </div>
        </body>
    </html>
    """
    thread = threading.Thread(target=send_email_async, args=(to_email, subject, body))
    thread.start()
