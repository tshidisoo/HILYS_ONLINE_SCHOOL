"""Phone numbers are normalised on the way in, so local and international forms of one number match."""
import phonenumbers

# Families live abroad; an unprefixed number is read in this order.
DEFAULT_REGIONS = ["GB", "ZW", "ZA", "AU", "US"]


def normalise_phone(raw, country_hint=None):
    """Returns (e164 or "", ok). Never raises: a bad number is kept for cleanup, not rejected."""
    raw = (raw or "").strip()
    if not raw:
        return "", True
    regions = ([country_hint] if country_hint else []) + DEFAULT_REGIONS
    for region in regions:
        try:
            parsed = phonenumbers.parse(raw, region)
        except phonenumbers.NumberParseException:
            continue
        if phonenumbers.is_possible_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164), True
    return raw, False
