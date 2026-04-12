# Get the logger
import time
from datetime import datetime, timedelta
import logging
import requests

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(self, config, profile):
        self.profile = profile
        url = config['http'].get('url')
        self.server = f"{url}"
        self.container = config['DEFAULT'].get('container')
        self.clock = float(config['simulation'].get('clock-rate'))

    async def send(self, route, points):
        server_url = f'{self.server}/containers/{self.container}/routes/{route}'
        act_time = datetime.now()
        for i, point in enumerate(points):
            temp, hum = self.profile.simulate(i, len(points))
            act_time = act_time + timedelta(0, 5)  # simulate interval of 5sec
            entries = [
                f"{act_time},{point[0]},{point[1]},{temp},{hum}"
            ]
            msg = {
                "entries": entries
            }
            response = requests.put(url=server_url, json=msg, timeout=5)
            if response.ok:
                logging.debug('sent message {}'.format(msg))
            response.raise_for_status()
            # wait
            time.sleep(self.clock)
