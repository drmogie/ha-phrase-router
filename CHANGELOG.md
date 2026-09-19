# Changelog

## 2026.09.19.01 - Initial release

First version, built in-chat from a design conversation (schema and architecture worked out step by step - see the project's own notes for the full reasoning trail). Light domain only.

- Wizard-built rules (Settings → Devices & services → Add integration → Phrase Router): optional label filter, area scope (whichever room heard it / always one fixed room / whole house), and toggle/on/off wordings (toggle required, on/off optional).
- Each rule is its own device with no entities - it registers its phrase(s) directly with Home Assistant's conversation agent via the same internal mechanism (`conversation.agent_manager.get_agent_manager(...).register_trigger`) the built-in Automation "Sentence" trigger uses. Nothing is written to `config/custom_sentences`, and no automation entity is created - a rule only shows up as its own device under this integration.
- Target resolution: every `light.*` entity carrying the rule's label (if any) whose effective area (its own area override, else its device's area) matches the resolved room - "whichever room heard it" resolves that room from the calling device's own area via the standard `device_id`/`satellite_id` → device → area lookup, the same one a Sentence-trigger automation's `trigger.device_id` gives you.
- Options flow lets you edit an existing rule's label/area-scope/wordings without rebuilding it.
- Considered and deliberately deferred for a later release: other domains (switch/fan/cover/etc. - each has different on/off/toggle service verbs, so this needs its own per-domain mapping rather than assuming `turn_on`/`turn_off` everywhere), multi-domain rules (e.g. one phrase hitting both lights and a fan), and query/status-style phrases (asking a state rather than controlling something) - all discussed and intentionally scoped out of v1 rather than overlooked.
