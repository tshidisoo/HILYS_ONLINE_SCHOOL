"""Small builders for tests."""
from datetime import date
from decimal import Decimal

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from catalogue.models import CatalogueItem
from families.models import Family, Student
from users.models import TeacherProfile, User


def make_user(username, role, **kw):
    u = User.objects.create_user(username=username, password="test-password-123", role=role, first_name=username.title(), **kw)
    if role == "teacher":
        TeacherProfile.objects.create(user=u)
    return u


def client_for(user):
    c = APIClient()
    if user:
        c.credentials(HTTP_AUTHORIZATION="Token " + Token.objects.get_or_create(user=user)[0].key)
    return c


def make_family(name="Test Parent", email="", phone="", **kw):
    return Family.objects.create(parent_name=name, email=email, phone=phone, **kw)


def make_student(family, first="Child", level="beginner"):
    return Student.objects.create(family=family, first_name=first, level=level)


def make_package(price="48", lesson_type="one_to_one", per_week=1):
    return CatalogueItem.objects.create(name=f"{per_week} a week {lesson_type}", kind="package", lesson_type=lesson_type,
                                        lessons_per_week=per_week, price=Decimal(price))
