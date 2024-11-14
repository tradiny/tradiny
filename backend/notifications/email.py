# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import smtplib
from email.mime.text import MIMEText
import re
import logging

from config import Config


def format_subject(message):
    # Replace line breaks with a space
    single_line_message = re.sub(r"[\r\n]+", " ", message)

    # Strip leading and trailing whitespace
    single_line_message = single_line_message.strip()

    # Optionally, you might choose to truncate the subject to a reasonable length
    # For example, limit to 78 characters which is a common convention for email subjects
    max_length = 78
    if len(single_line_message) > max_length:
        single_line_message = single_line_message[:max_length]

    return single_line_message


def send_notification(message):
    if not Config.SMTP_EMAIL_FROM:
        return

    msg = MIMEText(message)
    msg["Subject"] = format_subject(message)
    msg["From"] = Config.SMTP_EMAIL_FROM
    msg["To"] = Config.SMTP_EMAIL_TO
    with smtplib.SMTP_SSL(Config.SMTP_HOST, int(Config.SMTP_PORT)) as smtp_server:
        smtp_server.login(Config.SMTP_EMAIL_FROM, Config.SMTP_PASSWORD)
        smtp_server.sendmail(
            Config.SMTP_EMAIL_FROM, [Config.SMTP_EMAIL_TO], msg.as_string()
        )

    logging.info("Email sent successfully.")
