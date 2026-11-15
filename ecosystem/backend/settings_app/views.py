from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from audit.log import record
from common.permissions import IsInternalStaff

from .models import CompanySettings


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySettings
        exclude = ["id"]


@api_view(["GET", "PATCH"])
@permission_classes([IsInternalStaff])
def company_settings(request):
    obj = CompanySettings.get()
    if request.method == "PATCH":
        if not request.user.is_leadership:
            return Response({"detail": "Only the owner can change settings."}, status=403)
        s = SettingsSerializer(obj, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        record(request.user, "settings", obj, "Changed company settings: " + ", ".join(request.data.keys()))
    return Response(SettingsSerializer(obj).data)
