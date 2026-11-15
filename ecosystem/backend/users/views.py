from django.contrib.auth import authenticate, password_validation
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from audit.log import record
from common.permissions import IsInternalStaff, IsLeadership

from .models import User
from .serializers import UserSerializer


class LoginThrottle(ScopedRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        return f"throttle_login_{self.get_ident(request)}"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    user = authenticate(username=request.data.get("username", "").strip(), password=request.data.get("password", ""))
    if user is None:
        return Response({"detail": "That username and password do not match."}, status=400)
    if user.is_suspended:
        return Response({"detail": "This account is suspended. Ask the owner."}, status=403)
    app = request.data.get("app")
    allowed = {"staff": user.is_internal_staff, "teacher": user.is_teacher, "parent": user.is_parent}
    if app in allowed and not allowed[app]:
        return Response({"detail": "This login is not for this app."}, status=403)
    token, _ = Token.objects.get_or_create(user=user)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    record(user, "login", user, f"Signed in to the {app or 'API'}")
    return Response({"token": token.key, "user": UserSerializer(user).data})


@api_view(["POST"])
def logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=204)


@api_view(["GET"])
def me(request):
    return Response(UserSerializer(request.user).data)


@api_view(["POST"])
def change_password(request):
    if not request.user.check_password(request.data.get("current_password", "")):
        return Response({"current_password": ["Your current password is not right."]}, status=400)
    new = request.data.get("new_password", "")
    try:
        password_validation.validate_password(new, request.user)
    except Exception as e:  # noqa: BLE001 - shown to the user as plain messages
        return Response({"new_password": list(getattr(e, "messages", [str(e)]))}, status=400)
    request.user.set_password(new)
    request.user.save()
    Token.objects.filter(user=request.user).delete()
    token = Token.objects.create(user=request.user)
    record(request.user, "password", request.user, "Changed their password")
    return Response({"token": token.key})


class UserViewSet(viewsets.ModelViewSet):
    """Team and logins. Staff can read the list; only the owner changes roles or suspends."""
    serializer_class = UserSerializer
    search_fields = ["username", "first_name", "last_name", "email", "phone"]
    filterset_fields = ["role", "is_suspended"]
    ordering_fields = ["first_name", "role", "last_login"]

    def get_queryset(self):
        return User.objects.select_related("teacher_profile").order_by("role", "first_name")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsInternalStaff()]
        return [IsLeadership()]

    def perform_create(self, serializer):
        u = serializer.save()
        record(self.request.user, "create", u, f"Created login {u.username} ({u.get_role_display()})")

    def perform_update(self, serializer):
        before = serializer.instance.role
        u = serializer.save()
        if before != u.role:
            record(self.request.user, "role", u, f"Changed role from {before} to {u.role}")

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Logins are suspended, not deleted, so their history stays."}, status=400)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        u = self.get_object()
        if u == request.user:
            return Response({"detail": "You cannot suspend your own login."}, status=400)
        u.is_suspended = not u.is_suspended
        u.save(update_fields=["is_suspended"])
        Token.objects.filter(user=u).delete()
        record(request.user, "suspend", u, ("Suspended " if u.is_suspended else "Restored ") + u.username)
        return Response(UserSerializer(u).data)

    @action(detail=True, methods=["post"])
    def set_password(self, request, pk=None):
        u = self.get_object()
        new = request.data.get("password", "")
        try:
            password_validation.validate_password(new, u)
        except Exception as e:  # noqa: BLE001
            return Response({"password": list(getattr(e, "messages", [str(e)]))}, status=400)
        u.set_password(new)
        u.save()
        Token.objects.filter(user=u).delete()
        record(request.user, "password", u, f"Reset the password for {u.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)
