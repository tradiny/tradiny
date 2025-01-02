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

from pywebpush import webpush, WebPushException
from urllib.parse import urlparse
from vapid import get_vapid
import json
import logging


def send_notification(subscription, message):
    if not subscription:
        return

    subscription_url = subscription["endpoint"]
    parsed_url = urlparse(subscription_url)
    aud = parsed_url.scheme + "://" + parsed_url.netloc

    claims = {
        "sub": "mailto:michal@tradiny.com",
        "aud": aud,
    }

    vapid = get_vapid()

    data = {"notification": {"title": message}}

    message = json.dumps(data)

    try:
        logging.info(f"sending: {message}")
        webpush(subscription, message, vapid_private_key=vapid, vapid_claims=claims)
        logging.info("Push notification sent successfully.")
    except WebPushException as ex:
        logging.error(f"Unable to send the notification: {ex}")
        # Mozilla returns additional information in the body of the response.
        if ex.response and ex.response.json():
            extra = ex.response.json()
            logging.error(
                f"Remote service replied with a {extra.code}:{extra.errno}, {extra.message}, {extra.more_info}"
            )
    except Exception as ex:
        logging.error("An error occurred while sending push notification:", repr(ex))
