# Phrase Router

A Home Assistant integration for short voice/text phrases that control lights, fans, and switches by **room + label**, instead of by naming a specific entity.

Say "lights" in your Bonus Bedroom and it toggles that room's lights - no need to say "bonus bedroom" out loud, because Phrase Router already knows which room a phrase came from based on which voice satellite/device heard it. Add an explicit "lights off" wording too, and that one always turns off instead of toggling. Build another rule against the fan or switch domain the same way - each rule targets exactly one domain.

## Why

Home Assistant's built-in voice intents already handle "turn on the lights in the kitchen." Phrase Router is for the shorter, room-implicit version of that: walk into a room, say one or two words, done. It also lets you scope by **label** (e.g. only the lights labeled `default`) rather than controlling every entity in a room indiscriminately.

Each rule you build is its own device under this integration - nothing is written to `config/custom_sentences`, and no automation is created, so your Automations list stays clean. Under the hood, a rule registers its phrase(s) with Home Assistant's conversation agent the exact same way the built-in Automation "Sentence" trigger does, so it's picked up by Speech-to-Phrase's own training scan (if you use it) just like a Sentence-trigger automation would be.

## What a rule is

Each rule has:

- **Domain.** What kind of entity this rule controls - lights, fans, or switches. All three share the same toggle/on/off behavior, so this is the only thing that changes what a rule can reach; a rule only ever targets one domain.
- **Label(s) (optional).** Every entity of that domain carrying *all* of the labels you pick becomes a target. Leave it blank to target every entity of that domain in the resolved room instead.
- **Area scope.** *Whichever room heard it* (the room of the satellite/device that heard the phrase - this is the "walk in and say it" behavior), *always one specific room* (pick a fixed room regardless of where it's said), or *whole house* (no room filtering at all).
- **Wordings.** A required **toggle** phrase (or several, comma-separated) that flips the matched entities' state, plus optional explicit **on** and **off** phrases that always do that instead of toggling.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=drmogie&repository=ha-phrase-router&category=integration)

### Manual

Copy `custom_components/phrase_router` into your Home Assistant `config/custom_components/` folder, then restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → **Phrase Router**. Each time you add it, you're building one rule through a short wizard (domain, label, area scope, wordings, name). To add another rule, add the integration again. To change an existing rule, use its **Configure** option.

## Current limitations

- **Light, fan, and switch only.** Other domains (cover, climate, media players, etc.) use different service-verb pairs than a plain toggle/turn_on/turn_off, so they'd need their own per-domain mapping rather than fitting this same schema - planned as a later addition rather than day one.
- **A rule targets exactly one domain.** There's no single rule that hits both a light and a fan, say - build a separate rule per domain if you want one phrase to feel like it's doing both (two rules can share the same wording).
- **"Whichever room heard it" only works from a real voice satellite device**, not a phone or browser-based Assist - that's a Home Assistant limitation (only a satellite carries a fixed device/area), not something this integration can work around.
- No query/status-style phrases yet ("what's the temperature in here?") - only actions (toggle/on/off).

## Versioning

Releases are tagged `YYYY.MM.DD.##`.
