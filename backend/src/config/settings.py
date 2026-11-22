import os

import redis

JWT_SECRET = os.environ['JWT_SECRET']
LEDGER_SECRET = os.environ['LEDGER_SECRET'].encode()
CACHE = redis.Redis(host='redis', socket_timeout=2, socket_connect_timeout=2)
