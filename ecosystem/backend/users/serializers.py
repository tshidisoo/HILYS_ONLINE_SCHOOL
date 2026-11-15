from rest_framework import serializers

from .models import TeacherProfile, User


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ["bio", "pay_one_to_one", "pay_group", "pay_currency", "zoom_link", "takes_new_students"]


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    teacher_profile = TeacherProfileSerializer(required=False, allow_null=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "display_name", "email", "phone", "role", "role_label",
                  "time_zone", "is_suspended", "teacher_profile", "permissions", "last_login"]
        read_only_fields = ["last_login"]

    def get_permissions(self, u):
        return {k: getattr(u, k) for k in ["is_internal_staff", "is_leadership", "can_record_payments",
                                            "can_issue_documents", "can_override_rules", "is_teacher", "is_parent"]}

    def _save_profile(self, user, profile):
        if user.role == User.Role.TEACHER:
            p, _ = TeacherProfile.objects.get_or_create(user=user)
            for k, v in (profile or {}).items():
                setattr(p, k, v)
            p.save()

    def create(self, data):
        profile = data.pop("teacher_profile", None)
        user = User.objects.create(**data)
        user.set_unusable_password()
        user.save()
        self._save_profile(user, profile)
        return user

    def update(self, user, data):
        profile = data.pop("teacher_profile", None)
        user = super().update(user, data)
        self._save_profile(user, profile)
        return user
