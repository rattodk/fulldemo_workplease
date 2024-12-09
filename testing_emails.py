from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import uuid
from config import EMAIL_CONFIG

def send_verify_email():
    try:
        # Generate a test verification key
        verification_key = str(uuid.uuid4())
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message["To"] = "elmstrommen@gmail.com"  # Hardcoded recipient email
        message["Subject"] = "Test Verify Email - Wolt Web Dev Exam"

        # Email body
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #0066cc;">Verify Your Email</h2>
                    <p>This is a test email to verify the email system is working correctly.</p>
                    <p>Sample verification link:</p>
                    <div style="margin: 20px 0; text-align: center;">
                        <a href="{EMAIL_CONFIG['BASE_URL']}/verify/{verification_key}"
                           style="background-color: #0066cc; color: white; padding: 12px 25px; 
                                  text-decoration: none; border-radius: 4px; display: inline-block;">
                            Verify Account
                        </a>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        Verification Key: {verification_key}
                    </p>
                    <hr style="border: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        This is a test email sent from the Wolt Web Dev Exam project.
                    </p>
                </div>
            </body>
        </html>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to the SMTP server
        print("Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            print("Starting TLS...")
            server.starttls()
            print("Logging in...")
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['APP_PASSWORD'])
            print("Sending email...")
            server.send_message(message)

        print("Email sent successfully!")
        return True

    except Exception as ex:
        print(f"Error sending email: {str(ex)}")
        return False


if __name__ == "__main__":
    print("Starting verify email test...")
    send_verify_email()
