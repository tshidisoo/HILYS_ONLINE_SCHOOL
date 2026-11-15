from rest_framework import serializers

from .models import Family, Message, Student


class StudentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    level_label = serializers.CharField(source="get_level_display", read_only=True)
    has_support_notes = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ["id", "family", "first_name", "last_name", "name", "birth_year", "level", "level_label", "notes",
                  "support_notes", "has_support_notes", "is_demo"]
        extra_kwargs = {"support_notes": {"write_only": True}}

    def get_has_support_notes(self, s):
        return bool(s.support_notes)


class FamilySerializer(serializers.ModelSerializer):
    students = StudentSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.display_name", default="", read_only=True)
    balance = serializers.SerializerMethodField()
    has_login = serializers.SerializerMethodField()
    override_reason = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Family
        fields = ["id", "parent_name", "email", "phone", "whatsapp", "country", "city", "time_zone", "payer_name",
                  "owner", "owner_name", "tags", "notes", "founding_family", "needs_cleanup", "cleanup_reasons",
                  "source", "students", "balance", "has_login", "is_demo", "created_at", "override_reason"]
        read_only_fields = ["needs_cleanup", "cleanup_reasons", "is_demo"]

    def get_balance(self, f):
        from billing.rules import balances
        b = balances(f)
        return {k: {c: str(v) for c, v in d.items()} for k, d in b.items()}

    def get_has_login(self, f):
        return bool(f.login_id)


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.display_name", default="HILYS", read_only=True)
    from_family = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "family", "sender", "sender_name", "from_family", "body", "created_at", "read_by_family", "read_by_staff"]
        read_only_fields = ["sender", "read_by_family", "read_by_staff", "family"]

    def get_from_family(self, m):
        return bool(m.sender and m.sender.role == "parent")
