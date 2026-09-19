"""Constants for the Phrase Router integration."""
from __future__ import annotations

DOMAIN = "phrase_router"
MANUFACTURER = "Phrase Router"

# v1 only builds rules for the light domain - kept as a constant (not
# exposed anywhere in the wizard yet) so adding another domain later is
# a schema addition, not a rename.
TARGET_DOMAIN = "light"

CONF_LABEL_ID = "label_id"
CONF_AREA_SCOPE = "area_scope"
CONF_FIXED_AREA = "fixed_area"
CONF_WORDINGS = "wordings"

AREA_SCOPE_DEVICE = "device"
AREA_SCOPE_FIXED = "fixed"
AREA_SCOPE_ALL = "all"
AREA_SCOPES = (AREA_SCOPE_DEVICE, AREA_SCOPE_FIXED, AREA_SCOPE_ALL)

WORDING_TOGGLE = "toggle"
WORDING_TURN_ON = "turn_on"
WORDING_TURN_OFF = "turn_off"
WORDING_KEYS = (WORDING_TOGGLE, WORDING_TURN_ON, WORDING_TURN_OFF)

# Which light.* service each wording bucket calls.
SERVICE_BY_WORDING = {
    WORDING_TOGGLE: "toggle",
    WORDING_TURN_ON: "turn_on",
    WORDING_TURN_OFF: "turn_off",
}

# No entity platforms in v1 - a rule is a device with no entities, just
# a registered sentence trigger. See triggers.py.
PLATFORMS: list[str] = []
