"""Config flow for Phrase Router.

Building a brand-new rule still walks through separate screens - there's
nothing to review yet, so a guided step-by-step wizard makes more sense
than dropping someone into a page full of blank fields:
  1. async_step_user - pick the domain this rule controls (light, fan,
     or switch - all three share the same toggle/on/off services), and
     optionally one or more labels (an entity must carry all of them to
     match). Leave the label field blank to match every entity of that
     domain in the resolved area, no label filter at all.
  2. async_step_area_scope - which room a phrase said under this rule
     applies to: whichever room the satellite that heard it belongs to,
     one fixed room always, or the whole house.
  3. async_step_fixed_area - only shown when area_scope is "fixed".
  4. async_step_wordings - the phrases themselves: a required "toggle"
     wording, optional explicit "on"/"off" wordings, and four
     independent optional custom responses - success and error shown
     directly (fail sits right under success, since those are the two
     outcomes people actually customize), with the less-common
     not-found/unknown-room pair tucked into a collapsed "More
     responses" section.
  5. async_step_name - name the rule.

Its "Configure" option (async_step_init) is different on purpose: since
you're looking at a rule that already exists, seeing everything on one
page - grouped into the same four topics as above, as expandable
sections instead of screens - beats clicking back through steps you
don't need to touch just to get to the one field you came to change.
Every optional field there is pre-filled with description={"suggested_
value": ...} rather than a schema default, because a default doubles as
the fallback whenever the submitted value looks empty, not just when
the field was never touched - which would otherwise make emptying a
field and saving silently bring the old value right back.

An entry built before the domain field existed has nothing stored under
CONF_DOMAIN and falls back to "light" (see const.DEFAULT_TARGET_DOMAIN)
- the domain it always meant, back when light was the only option.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult, section
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
    CONF_AREA_SECTION,
    CONF_DOMAIN,
    CONF_FIXED_AREA,
    CONF_LABEL_ID,
    CONF_PHRASES_SECTION,
    CONF_RESPONSE,
    CONF_RESPONSE_ERROR,
    CONF_RESPONSE_NOT_FOUND,
    CONF_RESPONSE_UNKNOWN_ROOM,
    CONF_RESPONSES_SECTION,
    CONF_TARGETING_SECTION,
    CONF_WORDINGS,
    DEFAULT_TARGET_DOMAIN,
    DOMAIN,
    TARGET_DOMAIN_NAMES,
    WORDING_TOGGLE,
    WORDING_TURN_OFF,
    WORDING_TURN_ON,
)

_AREA_SCOPE_OPTIONS = [
    {"value": AREA_SCOPE_DEVICE, "label": "Whichever room heard it"},
    {"value": AREA_SCOPE_FIXED, "label": "Always one specific room"},
    {"value": AREA_SCOPE_ALL, "label": "Whole house"},
]

_DOMAIN_OPTIONS = [
    {"value": domain, "label": name} for domain, name in TARGET_DOMAIN_NAMES.items()
]


def _area_scope_selector(default: str) -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_AREA_SCOPE_OPTIONS, mode=SelectSelectorMode.DROPDOWN)
    )


def _domain_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(options=_DOMAIN_OPTIONS, mode=SelectSelectorMode.DROPDOWN)
    )


def _split_phrases(raw: str | None) -> list[str]:
    """Turn a comma-separated text field into a clean list of phrases."""
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def _join_phrases(phrases: list[str] | None) -> str:
    return ", ".join(phrases or [])


def _suggested_name(
    hass,
    domain: str,
    label_ids: list[str] | None,
    area_scope: str,
    fixed_area: str | None,
) -> str:
    bits = [TARGET_DOMAIN_NAMES.get(domain, TARGET_DOMAIN_NAMES[DEFAULT_TARGET_DOMAIN])]
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


# --------------------------------------------------------------------
# New-rule wizard (PhraseRouterConfigFlow) - one topic per screen.
# --------------------------------------------------------------------


def _wordings_schema(
    current: dict[str, list[str]],
    current_responses: dict[str, str | None] | None = None,
) -> vol.Schema:
    # Every field below except the required toggle uses
    # description={"suggested_value": ...} rather than default=... on
    # purpose - see the module docstring for why that distinction
    # matters (it's what lets a previously-set value be cleared back to
    # blank on the Configure side; harmless here where everything
    # starts blank anyway).
    current_responses = current_responses or {}
    return vol.Schema(
        {
            vol.Required(
                WORDING_TOGGLE, default=_join_phrases(current.get(WORDING_TOGGLE))
            ): str,
            vol.Optional(
                WORDING_TURN_ON,
                description={
                    "suggested_value": _join_phrases(current.get(WORDING_TURN_ON))
                },
            ): str,
            vol.Optional(
                WORDING_TURN_OFF,
                description={
                    "suggested_value": _join_phrases(current.get(WORDING_TURN_OFF))
                },
            ): str,
            vol.Optional(
                CONF_RESPONSE,
                description={
                    "suggested_value": current_responses.get(CONF_RESPONSE) or ""
                },
            ): str,
            vol.Optional(
                CONF_RESPONSE_ERROR,
                description={
                    "suggested_value": current_responses.get(CONF_RESPONSE_ERROR)
                    or ""
                },
            ): str,
            vol.Optional(CONF_RESPONSES_SECTION): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_RESPONSE_NOT_FOUND,
                            description={
                                "suggested_value": current_responses.get(
                                    CONF_RESPONSE_NOT_FOUND
                                )
                                or ""
                            },
                        ): str,
                        vol.Optional(
                            CONF_RESPONSE_UNKNOWN_ROOM,
                            description={
                                "suggested_value": current_responses.get(
                                    CONF_RESPONSE_UNKNOWN_ROOM
                                )
                                or ""
                            },
                        ): str,
                    }
                ),
                {"collapsed": True},
            ),
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


def _store_responses(data: dict[str, Any], user_input: dict[str, Any]) -> None:
    """Pull all four response fields out of user_input and into data.

    Success and error come straight off the top level; not-found and
    unknown-room arrive nested under CONF_RESPONSES_SECTION (that's how
    HA's collapsible "section" schema submits its fields) and get
    flattened back onto the same flat keys triggers.py already reads -
    it never needs to know the section exists.
    """
    data[CONF_RESPONSE] = user_input.get(CONF_RESPONSE) or None
    data[CONF_RESPONSE_ERROR] = user_input.get(CONF_RESPONSE_ERROR) or None
    advanced = user_input.get(CONF_RESPONSES_SECTION) or {}
    data[CONF_RESPONSE_NOT_FOUND] = advanced.get(CONF_RESPONSE_NOT_FOUND) or None
    data[CONF_RESPONSE_UNKNOWN_ROOM] = (
        advanced.get(CONF_RESPONSE_UNKNOWN_ROOM) or None
    )


class PhraseRouterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Build one voice-phrase rule: domain, label, area scope, wordings, name."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Pick the domain this rule controls, and optionally a label to filter targets by."""
        if user_input is not None:
            self._data[CONF_DOMAIN] = user_input[CONF_DOMAIN]
            self._data[CONF_LABEL_ID] = user_input.get(CONF_LABEL_ID)
            return await self.async_step_area_scope()

        schema = vol.Schema(
            {
                vol.Required(CONF_DOMAIN, default=DEFAULT_TARGET_DOMAIN): _domain_selector(),
                vol.Optional(CONF_LABEL_ID): LabelSelector(LabelSelectorConfig(multiple=True)),
            }
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
        """The phrases: required toggle, optional explicit on/off, optional responses."""
        if user_input is not None:
            wordings, errors = _parse_wordings(user_input)
            if not errors:
                self._data[CONF_WORDINGS] = wordings
                _store_responses(self._data, user_input)
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
            self._data.get(CONF_DOMAIN, DEFAULT_TARGET_DOMAIN),
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


# --------------------------------------------------------------------
# Configure / options flow (PhraseRouterOptionsFlow) - one page of
# expandable sections, pre-filled from the existing rule.
# --------------------------------------------------------------------


def _settings_schema(current: dict[str, Any]) -> vol.Schema:
    """The whole Configure page, pre-filled from `current` (the rule's
    existing flat data dict).

    Every optional field is pre-filled with description={"suggested_value":
    ...} rather than default=... - see the module docstring for why that
    distinction matters here. The two Required selects (domain, area
    scope) and the Required toggle wording keep default=..., since those
    can never be legitimately blank anyway.
    """
    current_labels = current.get(CONF_LABEL_ID)
    if isinstance(current_labels, str):
        # A pre-multi-label entry stored one label as a bare string; the
        # LabelSelector always wants a list.
        current_labels = [current_labels]
    current_domain = current.get(CONF_DOMAIN, DEFAULT_TARGET_DOMAIN)
    current_scope = current.get(CONF_AREA_SCOPE, AREA_SCOPE_DEVICE)
    current_fixed_area = current.get(CONF_FIXED_AREA)
    wordings = current.get(CONF_WORDINGS, {})

    return vol.Schema(
        {
            vol.Required(CONF_TARGETING_SECTION): section(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_DOMAIN, default=current_domain
                        ): _domain_selector(),
                        vol.Optional(
                            CONF_LABEL_ID,
                            description={"suggested_value": current_labels},
                        ): LabelSelector(LabelSelectorConfig(multiple=True)),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(CONF_AREA_SECTION): section(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_AREA_SCOPE, default=current_scope
                        ): _area_scope_selector(current_scope),
                        vol.Optional(
                            CONF_FIXED_AREA,
                            description={"suggested_value": current_fixed_area},
                        ): AreaSelector(),
                    }
                ),
                {"collapsed": False},
            ),
            vol.Required(CONF_PHRASES_SECTION): section(
                vol.Schema(
                    {
                        vol.Required(
                            WORDING_TOGGLE,
                            default=_join_phrases(wordings.get(WORDING_TOGGLE)),
                        ): str,
                        vol.Optional(
                            WORDING_TURN_ON,
                            description={
                                "suggested_value": _join_phrases(
                                    wordings.get(WORDING_TURN_ON)
                                )
                            },
                        ): str,
                        vol.Optional(
                            WORDING_TURN_OFF,
                            description={
                                "suggested_value": _join_phrases(
                                    wordings.get(WORDING_TURN_OFF)
                                )
                            },
                        ): str,
                        vol.Optional(
                            CONF_RESPONSE,
                            description={
                                "suggested_value": current.get(CONF_RESPONSE) or ""
                            },
                        ): str,
                        vol.Optional(
                            CONF_RESPONSE_ERROR,
                            description={
                                "suggested_value": current.get(CONF_RESPONSE_ERROR)
                                or ""
                            },
                        ): str,
                    }
                ),
                {"collapsed": False},
            ),
            vol.Optional(CONF_RESPONSES_SECTION): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_RESPONSE_NOT_FOUND,
                            description={
                                "suggested_value": current.get(
                                    CONF_RESPONSE_NOT_FOUND
                                )
                                or ""
                            },
                        ): str,
                        vol.Optional(
                            CONF_RESPONSE_UNKNOWN_ROOM,
                            description={
                                "suggested_value": current.get(
                                    CONF_RESPONSE_UNKNOWN_ROOM
                                )
                                or ""
                            },
                        ): str,
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def _parse_settings(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Pull every field back out of its section and flatten it onto one
    flat dict, using the same CONF_* keys triggers.py already reads -
    nothing outside this file ever needs to know sections exist.

    Always returns a best-effort `data` dict even when `errors` is
    non-empty, so the caller can redisplay the form pre-filled with
    exactly what the user just typed instead of resetting everything -
    only commit `data` once `errors` comes back empty.
    """
    errors: dict[str, str] = {}
    targeting = user_input.get(CONF_TARGETING_SECTION) or {}
    area = user_input.get(CONF_AREA_SECTION) or {}
    phrases = user_input.get(CONF_PHRASES_SECTION) or {}
    more_responses = user_input.get(CONF_RESPONSES_SECTION) or {}

    area_scope = area.get(CONF_AREA_SCOPE) or AREA_SCOPE_DEVICE
    fixed_area = area.get(CONF_FIXED_AREA)
    if area_scope == AREA_SCOPE_FIXED and not fixed_area:
        errors[f"{CONF_AREA_SECTION}.{CONF_FIXED_AREA}"] = "fixed_area_required"

    toggle = _split_phrases(phrases.get(WORDING_TOGGLE))
    if not toggle:
        errors[f"{CONF_PHRASES_SECTION}.{WORDING_TOGGLE}"] = "toggle_required"

    data: dict[str, Any] = {
        CONF_DOMAIN: targeting.get(CONF_DOMAIN, DEFAULT_TARGET_DOMAIN),
        CONF_LABEL_ID: targeting.get(CONF_LABEL_ID),
        CONF_AREA_SCOPE: area_scope,
        # Only kept when it's actually meaningful, same as the wizard's
        # separate fixed_area step guarantees.
        CONF_FIXED_AREA: fixed_area if area_scope == AREA_SCOPE_FIXED else None,
        CONF_WORDINGS: {
            WORDING_TOGGLE: toggle,
            WORDING_TURN_ON: _split_phrases(phrases.get(WORDING_TURN_ON)),
            WORDING_TURN_OFF: _split_phrases(phrases.get(WORDING_TURN_OFF)),
        },
        CONF_RESPONSE: phrases.get(CONF_RESPONSE) or None,
        CONF_RESPONSE_ERROR: phrases.get(CONF_RESPONSE_ERROR) or None,
        CONF_RESPONSE_NOT_FOUND: more_responses.get(CONF_RESPONSE_NOT_FOUND) or None,
        CONF_RESPONSE_UNKNOWN_ROOM: more_responses.get(CONF_RESPONSE_UNKNOWN_ROOM)
        or None,
    }
    return data, errors


class PhraseRouterOptionsFlow(config_entries.OptionsFlow):
    """Replay the one-page settings form so an existing rule can change."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if not self._data:
            entry = self.config_entry
            self._data = dict(entry.options) if entry.options else dict(entry.data)

        errors: dict[str, str] = {}
        current = self._data
        if user_input is not None:
            data, errors = _parse_settings(user_input)
            if not errors:
                self._data = data
                return self.async_create_entry(title="", data=self._data)
            current = data

        return self.async_show_form(
            step_id="init", data_schema=_settings_schema(current), errors=errors
        )
