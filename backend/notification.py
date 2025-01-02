# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

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
