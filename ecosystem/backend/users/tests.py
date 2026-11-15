from django.test import TestCase

from common.testing import client_for, make_user


class AuthTests(TestCase):
    def test_login_by_app_and_suspension(self):
        make_user("t", "teacher")
        c = client_for(None)
        self.assertEqual(c.post("/api/auth/login/", {"username": "t", "password": "test-password-123", "app": "staff"}).status_code, 403)
        r = c.post("/api/auth/login/", {"username": "t", "password": "test-password-123", "app": "teacher"})
        self.assertEqual(r.status_code, 200)
        owner = make_user("o", "owner")
        oc = client_for(owner)
        from users.models import User
        oc.post(f"/api/users/{User.objects.get(username='t').pk}/suspend/")
        tc = client_for(None)
        tc.credentials(HTTP_AUTHORIZATION="Token " + r.data["token"])
        self.assertEqual(tc.get("/api/auth/me/").status_code, 401)

    def test_only_owner_manages_users_and_audit(self):
        co = client_for(make_user("co", "coordinator"))
        self.assertEqual(co.get("/api/users/").status_code, 200)
        self.assertEqual(co.post("/api/users/", {"username": "x", "role": "owner"}).status_code, 403)
        self.assertEqual(co.get("/api/audit/").status_code, 403)
        self.assertEqual(client_for(make_user("o", "owner")).get("/api/audit/").status_code, 200)

    def test_every_private_endpoint_needs_login(self):
        c = client_for(None)
        for url in ["/api/families/", "/api/documents/", "/api/payments/", "/api/home/", "/api/teacher/lessons/",
                    "/api/parent/overview/", "/api/finance/overview/", "/api/teacher-pay/", "/api/settings/"]:
            self.assertEqual(c.get(url).status_code, 401, url)
