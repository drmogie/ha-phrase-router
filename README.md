# Phrase Router

A Home Assistant integration for short voice/text phrases that control lights by **room + label**, instead of by naming a specific entity.

Say "lights" in your Bonus Bedroom and it toggles that room's lights - no need to say "bonus bedroom" out loud, because Phrase Router already knows which room a phrase came from based on which voice satellite/device heard it. Add an explicit "lights off" wording too, and that one always turns off instead of toggling.

## Why

Home Assistant's built-in voice intents already handle "turn on the lights in the kitchen." Phrase Router is for the shorter, room-implicit version of that: walk into a room, say one or two words, done. It also lets you scope by **label** (e.g. only the lights labeled `default`) rather than controlling every light in a room indiscriminately.

Each rule you build is its own device under this integration - nothing is written to `config/custom_sentences`, and no automation is created, so your Automations list stays clean. Under the hood, a rule registers its phrase(s) with Home Assistant's conversation agent the exact same way the built-in Automation "Sentence" trigger does, so it's picked up by Speech-to-Phrase's own training scan (if you use it) just like a Sentence-trigger automation would be.

## What a rule is

Each rule has:

- **Label (optional).** Every light carrying this label becomes a target. Leave it blank to target every light in the resolved room instead.
- **Area scope.** *Whichever room heard it* (the room of the satellite/device that heard the phrase - this is the "walk in and say it" behavior), *always one specific room* (pick a fixed room regardless of where it's said), or *whole house* (no room filtering at all).
- **Wordings.** A required **toggle** phrase (or several, comma-separated) that flips the matched lights' state, plus optional explicit **on** and **off** phrases that always do that instead of toggling.

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=drmogie&repository=ha-phrase-router&category=integration)

### Manual

Copy `custom_components/phrase_router` into your Home Assistant `config/custom_components/` folder, then restart Home Assistant.

## Setup

Settings → Devices & services → Add integration → **Phrase Router**. Each time you add it, you're building one rule through a short wizard (label, area scope, wordings, name). To add another rule, add the integration again. To change an existing rule, use its **Configure** option.

## Current limitations (v1)

- **Light domain only.** Other domains (switch, fan, cover, etc.) aren't supported yet - they use different service-verb pairs (on/off isn't universal), so that's planned as a later addition rather than day one.
- **"Whichever room heard it" only works from a real voice satellite device**, not a phone or browser-based Assist - that's a Home Assistant limitation (only a satellite carries a fixed device/area), not something this integration can work around.
- No query/status-style phrases yet ("what's the temperature in here?") - only actions (toggle/on/off).

## Versioning

Releases are tagged `YYYY.MM.DD.##`.
