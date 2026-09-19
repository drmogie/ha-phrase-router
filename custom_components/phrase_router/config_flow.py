"""Config flow for Phrase Router.

A wizard, same shape as Label Master Control's own "pick label(s), then
name it" flow, adapted for one voice-phrase rule instead of one
aggregate control device:
  1. async_step_user - optionally pick one or more labels (a light must
     carry all of them to match). Leave it blank to match every light
     in the resolved area, no label filter at all.
  2. async_step_area_scope - which room a phrase said under this rule
     applies to: whichever room the satellite that heard it belongs to,
     one fixed room always, or the whole house.
  3. async_step_fixed_area - only shown when area_scope is "fixed".
  4. async_step_wordings - the phrases themselves: a required "toggle"
     wording, plus optional explicit "on"/"off" wordings.
  5. async_step_name - name the rule.

v1 only builds light-domain rules (see const.TARGET_DOMAIN) - the
domain isn't asked in the wizard at all yet.

Its "Configure" option replays the label/area/wordings steps so an
existing rule's phrases or targeting can change without rebuilding it.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.selector import (
    AreaSelector,
    LabelSelector,
    LabelSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    AREA_SCOPE_ALL,
    AREA_SCOPE_DEVICE,
    AREA_SCOPE_FIXED,
    CONF_AREA_SCOPE,
    CONF_FIXED_AREA,
    CONF_LABEL_ID,
    CONF_WORDINGS,
    DOMAIN,
    WORDING_TOGGLE,
    WORDING_TURN_OFF,
    WORDING_TURN_ON,
)

_AREA_SCOPE_OPTIONS = [
    {"value": AREA_SCOPE_DEVICE, "label": "Whichever room heard it"},
    {"value": AREA_SCOPE_FIXED, "label": "Always one specific room"},
    {"value": AREA_SCOPE_ALL, "label": "Whole house"},
]


def _area_scope_selector(default: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_AREA_SCOPE_OPTIONS, mode=SelectSelectorMode.DROPDOWN)
    )


def _split_phrases(raw: str | None) -> list[str]:
    """Turn a comma-separated text field into a clean list of phrases."""
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _join_phrases(phrases: list[str] | None) -> str:
    return ", ".join(phrases or [])


def _wordings_schema(current: dict[str, list[str]]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                WORDING_TOGGLE, default=_join_phrases(current.get(WORDING_TOGGLE))
            ): str,
            vol.Optional(
                WORDING_TURN_ON, default=_join_phrases(current.get(WORDING_TURN_ON))
            ): str,
            vol.Optional(
                WORDING_TURN_OFF, default=_join_phrases(current.get(WORDING_TURN_OFF))
            ): str,
        }
    )


def _parse_wordings(user_input: dict[str, Any]) -> tuple[dict[str, list[str]], dict[str, str]]:
    errors: dict[str, str] = {}
    toggle = _split_phrases(user_input.get(WORDING_TOGGLE))
    if not toggle:
        errors[WORDING_TOGGLE] = "toggle_required"
        return {}, errors
    return (
        {
            WORDING_TOGGLE: toggle,
            WORDING_TURN_ON: _split_phrases(user_input.get(WORDING_TURN_ON)),
            WORDING_TURN_OFF: _split_phrases(user_input.get(WORDING_TURN_OFF)),
        },
        errors,
    )


def _suggested_name(
    hass, label_ids: list[str] | None, area_scope: str, fixed_area: str | None
) -> str:
    bits = ["Lights"]
    if label_ids:
        registry = lr.async_get(hass)
        names = [
            (label.name if (label := registry.async_get_label(lid)) else lid)
            for lid in label_ids
        ]
        bits.append(f"({', '.join(names)})")
    if area_scope == AREA_SCOPE_FIXED and fixed_area:
        area = ar.async_get(hass).async_get_area(fixed_area)
        bits.append(f"— {area.name if area else fixed_area}")
    elif area_scope == AREA_SCOPE_ALL:
        bits.append("— whole house")
    return " ".join(bits)


class PhraseRouterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Build one voice-phrase rule: label, area scope, wordings, name."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Optionally pick a label to filter targets by."""
        if user_input is not None:
            self._data[CONF_LABEL_ID] = user_input.get(CONF_LABEL_ID)
            return await self.async_step_area_scope()

        schema = vol.Schema(
            {vol.Optional(CONF_LABEL_ID): LabelSelector(LabelSelectorConfig(multiple=True))}
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_area_scope(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick which room(s) this rule applies to."""
        if user_input is not None:
            self._data[CONF_AREA_SCOPE] = user_input[CONF_AREA_SCOPE]
            if user_input[CONF_AREA_SCOPE] == AREA_SCOPE_FIXED:
                return await self.async_step_fixed_area()
            self._data[CONF_FIXED_AREA] = None
            return await self.async_step_wordings()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_AREA_SCOPE, default=AREA_SCOPE_DEVICE
                ): _area_scope_selector(AREA_SCOPE_DEVICE)
            }
        )
        return self.async_show_form(step_id="area_scope", data_schema=schema)

    async def async_step_fixed_area(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Only shown when area_scope is 'fixed' - pick the one room."""
        if user_input is not None:
            self._data[CONF_FIXED_AREA] = user_input[CONF_FIXED_AREA]
            return await self.async_step_wordings()

        schema = vol.Schema({vol.Required(CONF_FIXED_AREA): AreaSelector()})
        return self.async_show_form(step_id="fixed_area", data_schema=schema)

    async def async_step_wordings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """The phrases: required toggle, optional explicit on/off."""
        if user_input is not None:
            wordings, errors = _parse_wordings(user_input)
            if not errors:
                self._data[CONF_WORDINGS] = wordings
                return await self.async_step_name()
        else:
            errors = {}

        return self.async_show_form(
            step_id="wordings", data_schema=_wordings_schema({}), errors=errors
        )

    async def async_step_name(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Name the rule."""
        if user_input is not None:
            return self.async_create_entry(title=user_input["name"], data=self._data)

        default = _suggested_name(
            self.hass,
            self._data.get(CONF_LABEL_ID),
            self._data[CONF_AREA_SCOPE],
            self._data.get(CONF_FIXED_AREA),
        )
        schema = vol.Schema({vol.Required("name", default=default): str})
        return self.async_show_form(step_id="name", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PhraseRouterOptionsFlow()


class PhraseRouterOptionsFlow(config_entries.OptionsFlow):
    """Replay label / area-scope / wordings so an existing rule can change."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self.config_entry
        self._data = dict(entry.options) if entry.options else dict(entry.data)
        return await self.async_step_label()

    async def async_step_label(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._data[CONF_LABEL_ID] = user_input.get(CONF_LABEL_ID)
            return await self.async_step_area_scope()

        # A pre-multi-label entry stored one label as a bare string; the
        # LabelSelector now needs a list default regardless of how it was
        # originally saved.
        current_labels = self._data.get(CONF_LABEL_ID)
        if isinstance(current_labels, str):
            current_labels = [current_labels]
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LABEL_ID, default=current_labels
                ): LabelSelector(LabelSelectorConfig(multiple=True))
            }
        )
        return self.async_show_form(step_id="label", data_schema=schema)

    async def async_step_area_scope(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._data[CONF_AREA_SCOPE] = user_input[CONF_AREA_SCOPE]
            if user_input[CONF_AREA_SCOPE] == AREA_SCOPE_FIXED:
                return await self.async_step_fixed_area()
            self._data[CONF_FIXED_AREA] = None
            return await self.async_step_wordings()

        current_scope = self._data.get(CONF_AREA_SCOPE, AREA_SCOPE_DEVICE)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_AREA_SCOPE, default=current_scope
                ): _area_scope_selector(current_scope)
            }
        )
        return self.async_show_form(step_id="area_scope", data_schema=schema)

    async def async_step_fixed_area(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._data[CONF_FIXED_AREA] = user_input[CONF_FIXED_AREA]
            return await self.async_step_wordings()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_FIXED_AREA, default=self._data.get(CONF_FIXED_AREA)
                ): AreaSelector()
            }
        )
        return self.async_show_form(step_id="fixed_area", data_schema=schema)

    async def async_step_wordings(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = self._data.get(CONF_WORDINGS, {})
        if user_input is not None:
            wordings, errors = _parse_wordings(user_input)
            if not errors:
                self._data[CONF_WORDINGS] = wordings
                return self.async_create_entry(title="", data=self._data)
        else:
            errors = {}

        return self.async_show_form(
            step_id="wordings", data_schema=_wordings_schema(current), errors=errors
        )
