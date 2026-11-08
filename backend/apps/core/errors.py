"""统一错误体 {code, message, details?}（ADR-021）。"""
from rest_framework import status
from rest_framework.exceptions import APIException


class ApiError(APIException):
    def __init__(self, code: str, message: str, http_status: int = 400, details: dict | None = None):
        self.status_code = http_status
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(detail=message)


class RateLimited(ApiError):
    def __init__(self, retry_after: int, message: str = "操作过于频繁，请稍后再试"):
        super().__init__("CODE_RATE_LIMITED", message, status.HTTP_429_TOO_MANY_REQUESTS, {"retry_after": retry_after})


class NotFound(ApiError):
    def __init__(self, message: str = "资源不存在"):
        super().__init__("NOT_FOUND", message, status.HTTP_404_NOT_FOUND)


def exception_handler(exc, context):
    from rest_framework.views import exception_handler as drf_exception_handler

    if isinstance(exc, ApiError):
        body = {"code": exc.code, "message": exc.message}
        if exc.details:
            body["details"] = exc.details
        from rest_framework.response import Response

        return Response(body, status=exc.status_code)
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        response.data = {"code": "BAD_REQUEST", "message": message}
    elif isinstance(detail, dict):
        response.data = {"code": "VALIDATION_ERROR", "message": "请求参数不合法", "details": detail}
    else:
        response.data = {"code": "BAD_REQUEST", "message": str(detail)}
    return response
