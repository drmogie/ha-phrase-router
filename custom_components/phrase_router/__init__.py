"""The Phrase Router integration.

Each config entry is one voice-phrase rule you build through the wizard
in config_flow.py (a domain, an optional label, an area scope, and
toggle/on/off wordings) - there is no auto-discovery. Setting up an
entry registers its sentence(s) directly with Home Assistant's own
conversation agent via the same mechanism the built-in Automation
"Sentence" trigger uses (see triggers.py) - nothing is written to
config/custom_sentences and no automation is created, so a rule never
shows up in the Automations list, only as its own device under this
integration.
"""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_DOMAIN, DEFAULT_TARGET_DOMAIN, DOMAIN, MANUFACTURER, PLATFORMS
from .triggers import async_register_rule


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Register one phrase rule's sentence trigger(s)."""
    unsubs = async_register_rule(hass, entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"unsubs": unsubs}

    data = entry.options if entry.options else entry.data
    rule_domain = data.get(CONF_DOMAIN, DEFAULT_TARGET_DOMAIN)

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        model=f"{rule_domain.capitalize()} phrase rule",
    )

    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    if PLATFORMS:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unregister this rule's sentence trigger(s)."""
    unload_ok = True
    if PLATFORMS:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if data:
            for unsub in data["unsubs"]:
                unsub()
    return unload_ok


async def _async_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload so an edited domain/label/area/wordings set takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)
