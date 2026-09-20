"""Sentence-trigger registration and target resolution for one rule.

Uses the same runtime mechanism Home Assistant's own Automation
"Sentence" trigger is built on
(homeassistant.components.conversation.agent_manager.get_agent_manager(...)
.register_trigger(...)) instead of writing anything to
config/custom_sentences or defining a custom Intent. That means a rule
built here behaves, to Speech-to-Phrase's own training scan and to
Assist generally, exactly like a Sentence-trigger automation would -
but it's registered directly by this integration's config entry, so it
never shows up in the Automations list and there's nothing on disk to
keep in sync.

Target resolution (which entities a rule actually controls) is a plain
entity_registry/device_registry/area_registry scan against the rule's
own domain (light/fan/switch, all three sharing the same turn_on/
turn_off/toggle services) - the domain check and label check
deliberately mirror Label Master Control's own aggregator.py (a
subset/AND check against entity_entry.labels - an entity must carry
every label the rule requires, no inheritance from a device's or
area's own labels), so both integrations agree on what "carries these
labels" means. A rule with no labels at all matches every entity of
its domain in the resolved area, same as before; more than one label
requires all of them together rather than any one of them.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.conversation.agent_manager import get_agent_manager
from homeassistant.components.conversation.models import ConversationInput
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    AREA_SCOPE_ALL,
    AREA_SCOPE_FIXED,
    CONF_AREA_SCOPE,
    CONF_DOMAIN,
    CONF_FIXED_AREA,
    CONF_LABEL_ID,
    CONF_WORDINGS,
    DEFAULT_TARGET_DOMAIN,
    SERVICE_BY_WORDING,
)

_LOGGER = logging.getLogger(__name__)


def _effective_area_id(hass: HomeAssistant, entity_entry) -> str | None:
    """An entity's own area override, else its device's area."""
    if entity_entry.area_id:
        return entity_entry.area_id
    if entity_entry.device_id:
        device_entry = dr.async_get(hass).async_get(entity_entry.device_id)
        if device_entry:
            return device_entry.area_id
    return None


def _resolve_device_area(hass: HomeAssistant, device_id: str | None) -> str | None:
    if not device_id:
        return None
    device_entry = dr.async_get(hass).async_get(device_id)
    return device_entry.area_id if device_entry else None


def _normalize_label_ids(raw: Any) -> frozenset[str]:
    """Accept a pre-multi-label entry's single string, a list, or nothing.

    Old entries stored one label as a bare string under CONF_LABEL_ID;
    the LabelSelector now returns a list. Both read the same way from
    here on, so no migration of stored entries is needed.
    """
    if not raw:
        return frozenset()
    if isinstance(raw, str):
        return frozenset({raw})
    return frozenset(raw)


def _resolve_targets(
    hass: HomeAssistant,
    area_id: str | None,
    label_ids: frozenset[str],
    domain: str,
) -> list[str]:
    """Every `domain` entity carrying all of label_ids (or all entities of
    that domain, if label_ids is empty) within area_id - or house-wide, if
    area_id is None."""
    registry = er.async_get(hass)
    targets = []
    for entity_entry in registry.entities.values():
        if entity_entry.entity_id.split(".", 1)[0] != domain:
            continue
        if label_ids and not label_ids.issubset(entity_entry.labels):
            continue
        if area_id is not None and _effective_area_id(hass, entity_entry) != area_id:
            continue
        targets.append(entity_entry.entity_id)
    return targets


def async_register_rule(hass: HomeAssistant, entry) -> list[CALLBACK_TYPE]:
    """Register one sentence trigger per non-empty wording bucket on this rule."""
    data: dict[str, Any] = entry.options if entry.options else entry.data
    domain = data.get(CONF_DOMAIN, DEFAULT_TARGET_DOMAIN)
    label_ids = _normalize_label_ids(data.get(CONF_LABEL_ID))
    area_scope = data[CONF_AREA_SCOPE]
    fixed_area = data.get(CONF_FIXED_AREA)
    wordings = data.get(CONF_WORDINGS, {})

    agent_manager = get_agent_manager(hass)
    ent_reg = er.async_get(hass)
    unsubs: list[CALLBACK_TYPE] = []

    for wording_key, service in SERVICE_BY_WORDING.items():
        sentences = wordings.get(wording_key) or []
        if not sentences:
            continue

        async def call_action(
            user_input: ConversationInput,
            result: Any,
            _service: str = service,
        ) -> str | None:
            """Resolve this rule's targets for whoever just said it, and act."""
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
                        "Phrase Router: '%s' heard '%s' but couldn't tell which "
                        "room it came from (no device area) - ignoring",
                        entry.title,
                        user_input.text,
                    )
                    return "I'm not sure which room that was."

            targets = _resolve_targets(hass, area_id, label_ids, domain)
            if not targets:
                _LOGGER.debug(
                    "Phrase Router: '%s' matched '%s' but found no %s entities to %s",
                    entry.title,
                    user_input.text,
                    domain,
                    _service,
                )
                return None

            await hass.services.async_call(
                domain, _service, {"entity_id": targets}, blocking=True
            )
            return None

        unsubs.append(
            agent_manager.register_trigger(
                sentences=sentences, trigger_callback=call_action
            )
        )

    return unsubs
