"""Brightness / warmth / color sentence-trigger registration for a
light-domain rule's optional "Light Controls" wordings.

Deliberately its own module, imported lazily and wrapped in its own
try/except at the call site in __init__.py: unlike the fixed toggle/
on/off wordings triggers.py has always used, brightness/warmth/color
rely on wildcard sentence matching (a `{value}` placeholder that
swallows whatever number or color word was said) - new ground for this
integration, so a mistake here must not be able to prevent this rule's
own toggle/on/off from registering, or touch any other rule at all.
(This is the direct lesson from 2026.09.21.01/.02: a module-level
import that only broke at runtime took down every rule of every
domain, not just the one that needed it - see CHANGELOG.)

A `{value}` wildcard's own recognized-slot API isn't something this
integration has exercised before, so rather than depend on it, every
bucket here regexes/searches the plain heard text (`user_input.text`)
directly for the number or color word it needs - the wildcard's only
job is letting the sentence grammar match a phrase that contains one.

Targets are resolved exactly the same way as triggers.py's own rules -
same domain/label/area-scope reasoning, reusing its helpers directly -
and this reuses the SAME four response fields (CONF_RESPONSE and
friends) already stored on the rule, rather than a second set just for
Light Controls: it's the same device, so it should sound like the same
rule whether it succeeds, fails, or can't find a target.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.models import ConversationInput
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    AREA_SCOPE_ALL,
    AREA_SCOPE_FIXED,
    BRIGHTNESS_NUMBER_RANGE,
    BRIGHTNESS_PRESET_PCT,
    COLOR_WORD_HS,
    CONF_AREA_SCOPE,
    CONF_FIXED_AREA,
    CONF_LABEL_ID,
    CONF_LC_BRIGHTNESS_FULL,
    CONF_LC_BRIGHTNESS_HIGH,
    CONF_LC_BRIGHTNESS_LOW,
    CONF_LC_BRIGHTNESS_MEDIUM,
    CONF_LC_BRIGHTNESS_NUMBER,
    CONF_LC_COLOR_WORDS,
    CONF_LC_WARMTH_COOL,
    CONF_LC_WARMTH_NEUTRAL,
    CONF_LC_WARMTH_NUMBER,
    CONF_LC_WARMTH_WARM,
    CONF_LIGHT_CONTROLS_SECTION,
    CONF_RESPONSE,
    CONF_RESPONSE_ERROR,
    CONF_RESPONSE_NOT_FOUND,
    CONF_RESPONSE_UNKNOWN_ROOM,
    DEFAULT_UNKNOWN_ROOM_RESPONSE,
    TARGET_DOMAIN_LIGHT,
    WARMTH_NUMBER_RANGE,
    WARMTH_PRESET_KELVIN,
)
from .responses import pick_response
from .triggers import _normalize_label_ids, _resolve_device_area, _resolve_targets

_LOGGER = logging.getLogger(__name__)

_NUMBER_RE = re.compile(r"\d+")

# (kind, storage key) for every Light Controls wording bucket, in the
# order their sentence triggers get registered.
_BUCKETS = (
    ("brightness_preset", CONF_LC_BRIGHTNESS_LOW),
    ("brightness_preset", CONF_LC_BRIGHTNESS_MEDIUM),
    ("brightness_preset", CONF_LC_BRIGHTNESS_HIGH),
    ("brightness_preset", CONF_LC_BRIGHTNESS_FULL),
    ("brightness_number", CONF_LC_BRIGHTNESS_NUMBER),
    ("warmth_preset", CONF_LC_WARMTH_WARM),
    ("warmth_preset", CONF_LC_WARMTH_NEUTRAL),
    ("warmth_preset", CONF_LC_WARMTH_COOL),
    ("warmth_number", CONF_LC_WARMTH_NUMBER),
    ("color", CONF_LC_COLOR_WORDS),
)


def _extract_number(text: str | None, low: int, high: int) -> int | None:
    """First integer found anywhere in the heard phrase, clamped to
    [low, high] - not read off the wildcard's own recognized slot (see
    module docstring), just regexed straight out of the transcript."""
    match = _NUMBER_RE.search(text or "")
    if not match:
        return None
    return max(low, min(high, int(match.group())))


def _extract_color(text: str | None) -> tuple[int, int] | None:
    """First known color name found anywhere in the heard phrase."""
    lowered = (text or "").lower()
    for name, hs in COLOR_WORD_HS.items():
        if name in lowered:
            return hs
    return None


def async_register_light_controls(hass: HomeAssistant, entry) -> list[CALLBACK_TYPE]:
    """Register one sentence trigger per non-empty Light Controls wording
    bucket on this light-domain rule."""
    data: dict[str, Any] = entry.options if entry.options else entry.data
    label_ids = _normalize_label_ids(data.get(CONF_LABEL_ID))
    area_scope = data[CONF_AREA_SCOPE]
    fixed_area = data.get(CONF_FIXED_AREA)
    response_raw = data.get(CONF_RESPONSE)
    not_found_raw = data.get(CONF_RESPONSE_NOT_FOUND)
    unknown_room_raw = data.get(CONF_RESPONSE_UNKNOWN_ROOM)
    error_raw = data.get(CONF_RESPONSE_ERROR)
    light_controls = data.get(CONF_LIGHT_CONTROLS_SECTION) or {}

    agent_manager = get_agent_manager(hass)
    ent_reg = er.async_get(hass)

    def _make_action(kind: str, key: str):
        async def action(
            user_input: ConversationInput,
            result: Any,
            _kind: str = kind,
            _key: str = key,
        ) -> str | None:
            device_id = user_input.device_id
            satellite_id = user_input.satellite_id
            if satellite_id:
                satellite_entry = ent_reg.async_get(satellite_id)
                if satellite_entry:
                    device_id = satellite_entry.device_id

            if area_scope == AREA_SCOPE_ALL:
                area_id = None
            elif area_scope == AREA_SCOPE_FIXED:
                area_id = fixed_area
            else:
                area_id = _resolve_device_area(hass, device_id)
                if area_id is None:
                    _LOGGER.debug(
                        "Phrase Router: '%s' (Light Controls) heard '%s' but "
                        "couldn't tell which room it came from - ignoring",
                        entry.title,
                        user_input.text,
                    )
                    return (
                        pick_response(unknown_room_raw)
                        or DEFAULT_UNKNOWN_ROOM_RESPONSE
                    )

            targets = _resolve_targets(
                hass, area_id, label_ids, TARGET_DOMAIN_LIGHT
            )
            if not targets:
                _LOGGER.debug(
                    "Phrase Router: '%s' (Light Controls) matched '%s' but "
                    "found no light entities to act on",
                    entry.title,
                    user_input.text,
                )
                return pick_response(not_found_raw)

            service_data: dict[str, Any] = {"entity_id": targets}
            if _kind == "brightness_preset":
                service_data["brightness_pct"] = BRIGHTNESS_PRESET_PCT[_key]
            elif _kind == "brightness_number":
                value = _extract_number(user_input.text, *BRIGHTNESS_NUMBER_RANGE)
                if value is None:
                    return pick_response(error_raw)
                service_data["brightness_pct"] = value
            elif _kind == "warmth_preset":
                service_data["color_temp_kelvin"] = WARMTH_PRESET_KELVIN[_key]
            elif _kind == "warmth_number":
                value = _extract_number(user_input.text, *WARMTH_NUMBER_RANGE)
                if value is None:
                    return pick_response(error_raw)
                service_data["color_temp_kelvin"] = value
            elif _kind == "color":
                hs = _extract_color(user_input.text)
                if hs is None:
                    return pick_response(error_raw)
                service_data["hs_color"] = list(hs)

            try:
                await hass.services.async_call(
                    "light", "turn_on", service_data, blocking=True
                )
            except Exception:
                _LOGGER.exception(
                    "Phrase Router: '%s' (Light Controls) failed to act on %s",
                    entry.title,
                    targets,
                )
                return pick_response(error_raw)
            return pick_response(response_raw)

        return action

    unsubs: list[CALLBACK_TYPE] = []
    for kind, key in _BUCKETS:
        sentences = light_controls.get(key) or []
        if not sentences:
            continue
        unsubs.append(
            agent_manager.register_trigger(
                sentences=sentences, trigger_callback=_make_action(kind, key)
            )
        )
    return unsubs
