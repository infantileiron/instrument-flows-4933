from fastapi import FastAPI

from src.config.settings import CACHE
from src.middlewares import errors, headers
from src.models.db import transaction
from src.routes.api import router

app = FastAPI(title='吹桐民乐 · 跨馆器材调借透视')
headers.install(app)
errors.install(app)
app.include_router(router)


@app.get('/health', include_in_schema=False)
def health():
    with transaction() as cursor:
        cursor.execute('SELECT 1 FROM runs LIMIT 1')
    CACHE.ping()
    return {'status': 'ok'}
