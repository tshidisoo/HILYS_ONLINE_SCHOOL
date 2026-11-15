"""Encrypted text for sensitive personal data (children's support notes, dates of birth)."""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


def _fernet():
    return Fernet(settings.FIELD_ENCRYPTION_KEY.encode())


class EncryptedTextField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return _fernet().decrypt(value.encode()).decode()
        except InvalidToken:
            return ""

    def get_prep_value(self, value):
        if not value:
            return value
        return _fernet().encrypt(str(value).encode()).decode()
