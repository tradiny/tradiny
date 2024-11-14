Web push notifications are the default method for delivering notifications.

To implement a new notification type, the `send_notification(subscription, message)` method in `notification.py` is triggered on these events:

1. Alert initialization
1. Successful alert evaluation condition
1. Alert expiration

Simply add a new method handler in `notifications/YOUR_NOTIFICATION_TYPE.py` and call it from `notification.py`. You can see an example in `notifications/web_push.py`.
