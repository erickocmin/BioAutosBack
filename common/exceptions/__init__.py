from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException


class Conflict(APIException):
    status_code = 409
    default_detail = "La operación entra en conflicto con el estado actual del recurso."
    default_code = "conflict"


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    details = response.data
    if isinstance(details, dict) and "detail" in details:
        message = str(details["detail"])
        errors = None
    else:
        message = "Existen campos inválidos."
        errors = details
    codes = exc.get_codes() if hasattr(exc, "get_codes") else None
    code = codes if isinstance(codes, str) else getattr(exc, "default_code", "api_error")
    if code == "no_active_account":
        code = "authentication_failed"
        message = "Credenciales inválidas."
    response.data = {
        "code": code,
        "message": message,
        "errors": errors,
    }
    return response
