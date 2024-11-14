# This software is licensed under a dual license:
#
# 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
#    for individuals and open source projects.
# 2. Commercial License for business use.
#
# For commercial inquiries, contact: license@tradiny.com
#
# For more details, refer to the LICENSE.md file in the root directory of this project.

import logging
from notifications.web_push import send_notification as send_push_notification
from notifications.email import send_notification as send_email_notification


def send_notification(subscription, message):
    try:
        send_push_notification(subscription, message)
    except Exception as e:
        logging.error(f"Error while sending push notification: {e}")

    try:
        send_email_notification(message)
    except Exception as e:
        logging.error(f"Error while sending email notification: {e}")
