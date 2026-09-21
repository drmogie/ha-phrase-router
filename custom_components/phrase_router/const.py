"""Constants for the Phrase Router integration."""
from __future__ import annotations

DOMAIN = "phrase_router"
MANUFACTURER = "Phrase Router"

CONF_DOMAIN = "domain"
CONF_LABEL_ID = "label_id"
CONF_AREA_SCOPE = "area_scope"
CONF_FIXED_AREA = "fixed_area"
CONF_WORDINGS = "wordings"
CONF_RESPONSE = "response"
CONF_RESPONSE_NOT_FOUND = "response_not_found"
CONF_RESPONSE_UNKNOWN_ROOM = "response_unknown_room"
CONF_RESPONSE_ERROR = "response_error"

# Form-only section keys for the single-page settings form (used by both
# the initial wizard and the Configure options - see config_flow.py).
# None of these are ever stored themselves: each section's fields get
# read out of user_input (nested under the section key, same as Home
# Assistant submits any "section" schema) and flattened back onto the
# same flat CONF_* keys this file already defines, so nothing outside
# config_flow.py needs to know sections exist at all.
#
# "More responses" reads, visually, as a continuation of "Phrases"
# right above it, but it's its own top-level section rather than nested
# inside Phrases - Home Assistant only allows one level of sections, so
# a section can't contain another one.
CONF_TARGETING_SECTION = "targeting"
CONF_AREA_SECTION = "area"
CONF_FIXED_AREA_SECTION = "fixed_area_section"
CONF_PHRASES_SECTION = "phrases"
CONF_RESPONSES_SECTION = "more_responses"

# The "couldn't tell which room" reply when a rule leaves
# CONF_RESPONSE_UNKNOWN_ROOM blank - the same wording this integration
# has always used.
DEFAULT_UNKNOWN_ROOM_RESPONSE = "I'm not sure which room that was."

# Domains a rule can target.
TARGET_DOMAIN_LIGHT = "light"
TARGET_DOMAIN_FAN = "fan"
TARGET_DOMAIN_SWITCH = "switch"
TARGET_DOMAIN_COVER = "cover"
TARGET_DOMAIN_LOCK = "lock"
TARGET_DOMAINS = (
    TARGET_DOMAIN_LIGHT,
    TARGET_DOMAIN_FAN,
    TARGET_DOMAIN_SWITCH,
    TARGET_DOMAIN_COVER,
    TARGET_DOMAIN_LOCK,
)

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
    TARGET_DOMAIN_COVER: "Covers",
    TARGET_DOMAIN_LOCK: "Locks",
}

AREA_SCOPE_DEVICE = "device"
AREA_SCOPE_FIXED = "fixed"
AREA_SCOPE_ALL = "all"
AREA_SCOPES = (AREA_SCOPE_DEVICE, AREA_SCOPE_FIXED, AREA_SCOPE_ALL)

WORDING_TOGGLE = "toggle"
WORDING_TURN_ON = "turn_on"
WORDING_TURN_OFF = "turn_off"
WORDING_KEYS = (WORDING_TOGGLE, WORDING_TURN_ON, WORDING_TURN_OFF)

# Which <domain>.* service each wording bucket calls.
#
# Light/fan/switch expose identical turn_on/turn_off/toggle services, so
# one shared table (_ON_OFF_TOGGLE) covers all three.
#
# Cover doesn't use turn_on/turn_off at all (it's open_cover/close_cover)
# but does have a native toggle service, so "on" is treated as open and
# "off" as closed.
#
# Lock has no turn_on/turn_off/toggle services whatsoever - only
# lock.lock, lock.unlock and lock.open. "On" is treated as the unlocked
# (more permissive/active) state and "off" as locked, same reasoning as
# cover's open/closed. There's deliberately no WORDING_TOGGLE entry for
# lock: a missing key here is triggers.py's signal to fall back to its
# own per-entity, state-based lock/unlock handling (see
# _toggle_locks in triggers.py) instead of calling one service for every
# target at once - unlike a light or switch, there's no single
# "lock.toggle" service that could receive a mixed-state target list.
_ON_OFF_TOGGLE = {
    WORDING_TOGGLE: "toggle",
    WORDING_TURN_ON: "turn_on",
    WORDING_TURN_OFF: "turn_off",
}

SERVICE_BY_WORDING = {
    TARGET_DOMAIN_LIGHT: _ON_OFF_TOGGLE,
    TARGET_DOMAIN_FAN: _ON_OFF_TOGGLE,
    TARGET_DOMAIN_SWITCH: _ON_OFF_TOGGLE,
    TARGET_DOMAIN_COVER: {
        WORDING_TOGGLE: "toggle",
        WORDING_TURN_ON: "open_cover",
        WORDING_TURN_OFF: "close_cover",
    },
    TARGET_DOMAIN_LOCK: {
        WORDING_TURN_ON: "unlock",
        WORDING_TURN_OFF: "lock",
    },
}

# Domains whose toggle wording is optional rather than required. Lock is
# the only one so far - it has no native toggle service (see above), and
# a per-entity lock/unlock-by-state toggle isn't always a phrase worth
# wiring up, so a lock rule can rely on the explicit unlock/lock
# wordings alone. At least one of toggle/on/off is still required so a
# rule can't be saved with no phrases at all - see _parse_wordings /
# _parse_settings in config_flow.py.
TOGGLE_OPTIONAL_DOMAINS = frozenset({TARGET_DOMAIN_LOCK})

# --------------------------------------------------------------------
# Light Controls - a light-domain rule's optional fifth capability
# (brightness / warmth / color), alongside toggle/on/off. See
# light_controls.py for the sentence-trigger registration itself; the
# constants below are just the storage keys and the fixed value tables
# each wording bucket maps to.
#
# Every bucket is a user-editable wording (comma-separated phrase
# alternatives, same convention as toggle/turn_on/turn_off) except
# color, which is a single wording whose {value} wildcard is matched at
# runtime against a small fixed color-name vocabulary (COLOR_WORD_HS)
# rather than exposing one wording field per color - eight-plus nearly
# identical free-text fields would make the page unwieldy for what's a
# nice-to-have, not the main ask.
#
# The brightness/warmth *values* a preset maps to are NOT user-editable
# in v1 (only the wording that triggers them is) - keeps the config
# surface to "what do I say" rather than also "what does it set", which
# can always be added later if it turns out to matter.
CONF_LIGHT_CONTROLS_SECTION = "light_controls"

CONF_LC_BRIGHTNESS_LOW = "brightness_low"
CONF_LC_BRIGHTNESS_MEDIUM = "brightness_medium"
CONF_LC_BRIGHTNESS_HIGH = "brightness_high"
CONF_LC_BRIGHTNESS_FULL = "brightness_full"
CONF_LC_BRIGHTNESS_NUMBER = "brightness_number"
CONF_LC_WARMTH_WARM = "warmth_warm"
CONF_LC_WARMTH_NEUTRAL = "warmth_neutral"
CONF_LC_WARMTH_COOL = "warmth_cool"
CONF_LC_WARMTH_NUMBER = "warmth_number"
CONF_LC_COLOR_WORDS = "color_words"

LIGHT_CONTROL_WORDING_KEYS = (
    CONF_LC_BRIGHTNESS_LOW,
    CONF_LC_BRIGHTNESS_MEDIUM,
    CONF_LC_BRIGHTNESS_HIGH,
    CONF_LC_BRIGHTNESS_FULL,
    CONF_LC_BRIGHTNESS_NUMBER,
    CONF_LC_WARMTH_WARM,
    CONF_LC_WARMTH_NEUTRAL,
    CONF_LC_WARMTH_COOL,
    CONF_LC_WARMTH_NUMBER,
    CONF_LC_COLOR_WORDS,
)

# Fixed brightness percentages (light.turn_on's brightness_pct) for the
# three named presets.
BRIGHTNESS_PRESET_PCT = {
    CONF_LC_BRIGHTNESS_LOW: 25,
    CONF_LC_BRIGHTNESS_MEDIUM: 50,
    CONF_LC_BRIGHTNESS_HIGH: 75,
    CONF_LC_BRIGHTNESS_FULL: 100,
}

# Fixed color-temperature Kelvin values (light.turn_on's
# color_temp_kelvin) for the three named warmth presets - matches the
# "warm/neutral/cool white" vocabulary most smart bulbs already use on
# their own boxes/apps.
WARMTH_PRESET_KELVIN = {
    CONF_LC_WARMTH_WARM: 2700,
    CONF_LC_WARMTH_NEUTRAL: 4000,
    CONF_LC_WARMTH_COOL: 6500,
}

# Sane clamp range for the free-number brightness/warmth wordings, so a
# mis-heard or extreme number doesn't get sent to a light as-is. (low, high)
BRIGHTNESS_NUMBER_RANGE = (1, 100)
WARMTH_NUMBER_RANGE = (2000, 6500)

# Built-in color vocabulary for CONF_LC_COLOR_WORDS - fixed hue/
# saturation (light.turn_on's hs_color) per name.
COLOR_WORD_HS = {
    "red": (0, 100),
    "orange": (30, 100),
    "yellow": (55, 90),
    "green": (120, 100),
    "blue": (240, 100),
    "purple": (280, 90),
    "pink": (330, 80),
}

# No entity platforms - a rule is a device with no entities, just a
# registered sentence trigger. See triggers.py.
PLATFORMS: list[str] = []
