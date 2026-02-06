import datetime

class AnalyticsService:
    def __init__(self):
        self.events = []
        self.user_statistics = {}

    def track_conversion(self, user_id, conversion_data):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        event = {'event_type': 'conversion', 'user_id': user_id, 'data': conversion_data, 'timestamp': timestamp}
        self.events.append(event)
        self.update_user_statistics(user_id, event)

    def track_premium_purchase(self, user_id, purchase_data):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        event = {'event_type': 'premium_purchase', 'user_id': user_id, 'data': purchase_data, 'timestamp': timestamp}
        self.events.append(event)
        self.update_user_statistics(user_id, event)

    def track_error(self, user_id, error_message):
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        event = {'event_type': 'error', 'user_id': user_id, 'error': error_message, 'timestamp': timestamp}
        self.events.append(event)
        self.update_user_statistics(user_id, event)

    def update_user_statistics(self, user_id, event):
        if user_id not in self.user_statistics:
            self.user_statistics[user_id] = {'conversions': 0, 'premium_purchases': 0, 'errors': 0}

        if event['event_type'] == 'conversion':
            self.user_statistics[user_id]['conversions'] += 1
        elif event['event_type'] == 'premium_purchase':
            self.user_statistics[user_id]['premium_purchases'] += 1
        elif event['event_type'] == 'error':
            self.user_statistics[user_id]['errors'] += 1

    def get_events(self):
        return self.events

    def get_user_statistics(self, user_id):
        return self.user_statistics.get(user_id, {})
