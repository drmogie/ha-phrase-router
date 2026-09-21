# Phrase Router

A Home Assistant integration for short voice/text phrases that control lights, fans, switches, covers, and locks by **room + label**, instead of by naming a specific entity.

Say "lights" in your Bonus Bedroom and it toggles that room's lights - no need to say "bonus bedroom" out loud, because Phrase Router already knows which room a phrase came from based on which voice satellite/device heard it. Add an explicit "lights off" wording too, and that one always turns off instead of toggling. Build another rule against the fan, switch, cover, or lock domain the same way - each rule targets exactly one domain.

## Why

Home Assistant's built-in voice intents already handle "turn on the lights in the kitchen." Phrase Router is for the shorter, room-implicit version of that: walk into a room, say one or two words, done. It also lets you scope by **label** (e.g. only the lights labeled `default`) rather than controlling every entity in a room indiscriminately.

Each rule you build is its own device under this integration - nothing is written to `config/custom_sentences`, and no automation is created, so your Automations list stays clean. Under the hood, a rule registers its phrase(s) with Home Assistant's conversation agent the exact same way the built-in Automation "Sentence" trigger does, so it's picked up by Speech-to-Phrase's own training scan (if you use it) just like a Sentence-trigger automation would be.

## What a rule is

**Building** a new rule walks through separate screens, one topic at a time. **Editing** an existing rule (its **Configure** option) is different on purpose: one page with the same topics as expandable sections, so you're not clicking back through steps you don't need to touch just to change the one thing you came for. Either way, a rule has:

- **What to control.** **Domain** - lights, fans, switches, covers, or locks; a rule only ever targets one domain. Light/fan/switch share the same toggle/on/off behavior. **Cover** uses "on" = open, "off" = close, and does have its own toggle service. **Lock** has no native toggle service at all, so its toggle is handled per-door instead: it unlocks whichever targets are currently locked and locks the rest; "on" = unlock, "off" = lock. Because of that, toggle is the only *optional* phrase for locks - a lock rule just needs at least one of toggle/on/off filled in, not toggle specifically. **Label(s) (optional)** - every entity of that domain carrying *all* of the labels you pick becomes a target; leave it blank to target every entity of that domain in the resolved room instead.
- **Where.** **Area scope** - *whichever room heard it* (the room of the satellite/device that heard the phrase - the "walk in and say it" behavior), *always one specific room*, or *whole house*. **Room** only matters for "always one specific room", so on the Configure page it's tucked into its own collapsed "Fixed room" section - collapsed by default, already open if the rule already uses a fixed room. (Home Assistant can't yet hide a field live based on a sibling field's value in the same form - this is the closest available approximation.) On the new-rule wizard, the room screen is skipped outright unless you pick "always one specific room".
- **Phrases.** A **toggle** phrase (or several, comma-separated) that flips the matched entities' state - required for every domain except **lock**, where it's optional (see above); optional explicit **on** and **off** phrases that always do that instead of toggling; and two of the four custom responses: **response on success** (blank keeps Assist's own default reply) and **response when the action fails** (blank lets the error propagate normally) - these are the two most people actually customize.
- **More responses** - **response when nothing matched** (used when the domain/label filter found no entities to act on; blank stays silent) and **response when the room can't be resolved** (used for a "whichever room heard it" rule when the calling device has no area; blank falls back to the built-in "I'm not sure which room that was."). On the Configure page these two are collapsed by default, in their own section right after Phrases (Home Assistant only allows one level of sections, so it can't nest inside Phrases itself); when building a new rule, they're inside the same collapsed section on the Phrases screen.

None of the four responses change what actually happens - they only override what's said back. Every optional field, including the label filter, can be cleared back to blank later through **Configure** - emptying it and saving actually removes it rather than silently keeping the old value.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=drmogie&repository=ha-phrase-router&category=integration)

### Manual

Copy `custom_components/phrase_router` into your Home Assistant `config/custom_components/` folder, then restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → **Phrase Router**. Each time you add it, you're building one rule through a short wizard (see "What a rule is" above), then naming it. To add another rule, add the integration again. To change an existing rule, use its **Configure** option - the same topics, but as one page of expandable sections instead of separate screens.

## Current limitations

- **Light, fan, switch, cover, and lock only.** Other domains (climate, media players, etc.) use different service-verb shapes than any of these five, so they'd need their own mapping rather than fitting this same schema - planned as later additions rather than day one.
- **A rule targets exactly one domain.** There's no single rule that hits both a light and a fan, say - build a separate rule per domain if you want one phrase to feel like it's doing both (two rules can share the same wording).
- **"Whichever room heard it" only works from a real voice satellite device**, not a phone or browser-based Assist - that's a Home Assistant limitation (only a satellite carries a fixed device/area), not something this integration can work around.
- No query/status-style phrases yet ("what's the temperature in here?") - only actions (toggle/on/off).

## Versioning

Releases are tagged `YYYY.MM.DD.##`.
