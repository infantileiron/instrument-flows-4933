import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymysql.err import IntegrityError

logger = logging.getLogger(__name__)


def install(app):
    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, exc: RequestValidationError):
        fields = [{'field': '.'.join(map(str, item['loc'][1:])), 'message': item['msg']}
                  for item in exc.errors()]
        return JSONResponse(status_code=422, content={'detail': '请核对表单字段', 'fields': fields})

    @app.exception_handler(IntegrityError)
    async def database_conflict(request: Request, exc: IntegrityError):
        if exc.args[0] == 1062:
            return JSONResponse(status_code=409, content={'detail': '凭据编号或方案版本已存在'})
        logger.error('Database rejected %s with code %s', request.url.path, exc.args[0])
        return JSONResponse(status_code=422, content={'detail': '数据与台账约束不一致'})
