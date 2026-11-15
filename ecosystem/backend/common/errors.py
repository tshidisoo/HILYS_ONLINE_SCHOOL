"""Errors in plain words. Staff are not technical."""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


class RuleBroken(Exception):
    """A business rule said no. The message is shown to the person as written."""

    def __init__(self, message, field=None, code="rule"):
        super().__init__(message)
        self.message, self.field, self.code = message, field, code


PLAIN = {
    "not_authenticated": "Please sign in again.",
    "authentication_failed": "Please sign in again.",
    "permission_denied": "Your role cannot do this. Ask the owner if you need it.",
    "not_found": "We could not find that record. It may have been deleted.",
    "throttled": "Too many tries. Please wait a little and try again.",
}


def plain_exception_handler(exc, context):
    if isinstance(exc, RuleBroken):
        exc = ValidationError({exc.field or "detail": [exc.message]})
    elif isinstance(exc, DjangoValidationError):
        exc = ValidationError(exc.message_dict if hasattr(exc, "message_dict") else {"detail": exc.messages})
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and "detail" in response.data:
        code = getattr(response.data["detail"], "code", None)
        if code in PLAIN:
            response.data["detail"] = PLAIN[code]
    return response
