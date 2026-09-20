"""Constants for the Phrase Router integration."""
from __future__ import annotations

DOMAIN = "phrase_router"
MANUFACTURER = "Phrase Router"

CONF_DOMAIN = "domain"
CONF_LABEL_ID = "label_id"
CONF_AREA_SCOPE = "area_scope"
CONF_FIXED_AREA = "fixed_area"
CONF_WORDINGS = "wordings"

# Domains a rule can target - all three expose the same turn_on/turn_off/
# toggle services, so SERVICE_BY_WORDING below needs no per-domain
# mapping. Only add a domain here once its services line up the same
# way, or SERVICE_BY_WORDING needs its own per-domain table too.
TARGET_DOMAIN_LIGHT = "light"
TARGET_DOMAIN_FAN = "fan"
TARGET_DOMAIN_SWITCH = "switch"
TARGET_DOMAINS = (TARGET_DOMAIN_LIGHT, TARGET_DOMAIN_FAN, TARGET_DOMAIN_SWITCH)

# Entries built before the domain field existed have nothing stored under
# CONF_DOMAIN - they were light-only rules, so this is what they fall
# back to.
DEFAULT_TARGET_DOMAIN = TARGET_DOMAIN_LIGHT

# Friendly plural per domain - used for the device/model name and the
# wizard's suggested rule name.
TARGET_DOMAIN_NAMES = {
    TARGET_DOMAIN_LIGHT: "Lights",
    TARGET_DOMAIN_FAN: "Fans",
    TARGET_DOMAIN_SWITCH: "Switches",
}

AREA_SCOPE_DEVICE = "device"
AREA_SCOPE_FIXED = "fixed"
AREA_SCOPE_ALL = "all"
AREA_SCOPES = (AREA_SCOPE_DEVICE, AREA_SCOPE_FIXED, AREA_SCOPE_ALL)

WORDING_TOGGLE = "toggle"
WORDING_TURN_ON = "turn_on"
WORDING_TURN_OFF = "turn_off"
WORDING_KEYS = (WORDING_TOGGLE, WORDING_TURN_ON, WORDING_TURN_OFF)

# Which <domain>.* service each wording bucket calls - the same three
# verbs on light, fan and switch, so this table is shared across all of
# them.
SERVICE_BY_WORDING = {
    WORDING_TOGGLE: "toggle",
    WORDING_TURN_ON: "turn_on",
    WORDING_TURN_OFF: "turn_off",
}

# No entity platforms - a rule is a device with no entities, just a
# registered sentence trigger. See triggers.py.
PLATFORMS: list[str] = []
