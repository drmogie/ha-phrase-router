## 2026.09.19.05 - Reorder and collapse the response fields

- In the wordings step, the **response when the action fails** field now sits directly below **response on success** - the two responses most people actually set.
- **Response when nothing matched** and **response when the room can't be resolved** now live inside a collapsed "More responses" section instead of always being shown - expand it if you need those two. Nothing about how they behave changed, only where they show up in the form.
- Existing rules are unaffected either way - this only reshapes the wizard, not what's stored.

## 2026.09.19.04 - Custom responses

- Rules can now set their own reply for each of four independent outcomes: a **success** response (after a successful toggle/on/off), a **not-found** response (the domain/label filter matched nothing), an **unknown-room** response (a "whichever room heard it" rule couldn't tell which room), and an **error** response (the underlying service call itself raised an error).
- Every field is independent and optional. Leaving one blank keeps exactly the old behavior for that outcome: Assist's own default reply on success, silence on no match, the built-in "I'm not sure which room that was." for unknown-room, and letting the error propagate for a failed service call.
- None of the four change what actually happens - they only override what's spoken/typed back.

## 2026.09.19.03 - Fan and switch domains

- Rules can now target **fan** or **switch** entities, not just lights - pick the domain on the first wizard screen (and in an existing rule's Configure options). Light, fan, and switch all share the same toggle/turn_on/turn_off services, so wordings and area scope work exactly the same regardless of which one you pick.
- Existing rules keep working unchanged - a rule built before this update has nothing stored for its domain, so it's treated as a light rule, same as it always was.
- A rule still targets exactly one domain - there's no single rule that controls both a light and a fan.

# Changelog

## 2026.09.19.02 - Multiple labels per rule

- The label picker now accepts more than one label. A light must carry **all** of the labels you pick to match (same subset/AND rule Label Master Control uses for its own multi-label devices) - not just any one of them.
- Existing rules with a single label keep working unchanged; nothing needs to be redone.

## 2026.09.19.01 - Initial release

First version, built in-chat from a design conversation (schema and architecture worked out step by step - see the project's own notes for the full reasoning trail). Light domain only.

- Wizard-built rules (Settings → Devices & services → Add integration → Phrase Router): optional label filter, area scope (whichever room heard it / always one fixed room / whole house), and toggle/on/off wordings (toggle required, on/off optional).
- Each rule is its own device with no entities - it registers its phrase(s) directly with Home Assistant's conversation agent via the same internal mechanism (`conversation.agent_manager.get_agent_manager(...).register_trigger`) the built-in Automation "Sentence" trigger uses. Nothing is written to `config/custom_sentences`, and no automation entity is created - a rule only shows up as its own device under this integration.
- Target resolution: every `light.*` entity carrying the rule's label (if any) whose effective area (its own area override, else its device's area) matches the resolved room - "whichever room heard it" resolves that room from the calling device's own area via the standard `device_id`/`satellite_id` → device → area lookup, the same one a Sentence-trigger automation's `trigger.device_id` gives you.
- Options flow lets you edit an existing rule's label/area-scope/wordings without rebuilding it.
- Considered and deliberately deferred for a later release: other domains (switch/fan/cover/etc. - each has different on/off/toggle service verbs, so this needs its own per-domain mapping rather than assuming `turn_on`/`turn_off` everywhere), multi-domain rules (e.g. one phrase hitting both lights and a fan), and query/status-style phrases (asking a state rather than controlling something) - all discussed and intentionally scoped out of v1 rather than overlooked.
