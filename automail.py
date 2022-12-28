import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.mime.image import MIMEImage
import ssl
import smtplib

message = MIMEMultipart()

email_sender = 'intranetawit123'
email_password = 'dqpbgowrtyzbaeon'
email_reciever = 'givillamor01@gmail.com'


subject = "test"
body = """
    tang ina mo jb bobo HAHAHAH
"""

image_dir = "temp_image_dir"
image_name = "tempfile.png"

message['from'] = email_sender
message['to'] = email_reciever
message['subject'] = subject
message.attach(MIMEText(body))
message.attach(MIMEImage(Path(os.path.join(image_dir, image_name)).read_bytes()))

context = ssl.create_default_context()

with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as sm:
    sm.ehlo()
    sm.login(email_sender, email_password)
    sm.send_message(message)
    print('Sent...')