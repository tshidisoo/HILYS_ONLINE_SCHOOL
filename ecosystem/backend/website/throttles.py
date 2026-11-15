from rest_framework.throttling import AnonRateThrottle


class PublicThrottle(AnonRateThrottle):
    scope = "public"
