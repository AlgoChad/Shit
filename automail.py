import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.mime.image import MIMEImage
import ssl
import smtplib

#mailing constants
EMAIL_SENDER = 'intranetawit123'
EMAIL_PASSWORD = 'dqpbgowrtyzbaeon'

class automail(MIMEMultipart, MIMEText):
    def __init__(self):
        self.subject = "Eye See Cataract Analysis"
        self.image_dir = "temp_image_dir"
        self.image_name = "tempfile.png"
        
    def send_mail(self, body, reciever):
        Message = MIMEMultipart()
        Message['from'] = EMAIL_SENDER
        Message['to'] = reciever
        Message['subject'] = self.subject
        Message.attach(MIMEText(body))
        Message.attach(MIMEImage(Path(os.path.join(self.image_dir, self.image_name)).read_bytes()))
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as sm:
            sm.ehlo()
            sm.login(EMAIL_SENDER, EMAIL_PASSWORD)
            sm.send_message(Message)
            print('Sent...')
            
            
