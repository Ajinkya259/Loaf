# Loaf — Idea Notes

_Status: pure brainstorm. Not built. Come back later._

## The core idea
A pixel-art (old-school **Minecraft-style — blocky, low-res, NOT 3D, NOT photoreal**) cat who lives on the desktop as an always-visible companion. She's a living status indicator for "how much is going on," reacting visually to your workload and your machine instead of you having to check a dashboard.

## How she reacts (the core mechanic)
Two mostly-independent signals drive her body/mood:
- **Task load → body size.** More tasks queued, or more detailed/heavy tasks → she gets fatter. Nothing pending → she's lean and chill.
- **System load → posture/mood.** High CPU usage → she gets scared/tense, hunches up, sits small and "congested" in a corner. System idle/free → she relaxes, could dance, or just chill.
- **Idle/chill styling**: sunglasses/goggles, wearing headphones, dancing, lounging — the "nothing to do" state should feel good to look at, not just blank.
- **Morning greeting**: opening the desktop (tied to system clock/wake) triggers something like "Good morning, here's what's up today" — pulled from schedule + memory.

## The bigger vision (explicitly "thinking wide," not all required)
Two layers to this:
1. **The pet layer** — pixel cat overlay + task/schedule awareness + CPU awareness + idle/chill/busy states + morning greeting. The tangible, buildable core.
2. **The brain layer** — an LLM (OpenAI) she's connected to, with memory (mem0 or cloud memory) so she remembers you across sessions, reachable through **channels**: Telegram, a web interface, or a Twilio phone number (call or text her from anywhere, whatever the location). Through the brain she can take actions — e.g. "hey cat, play Spotify" → she controls Spotify. More tool integrations as they come to mind.

## Naming
_Original entry:_ going with **Deskitty** (desk + kitty) as the working name — cute, and says exactly what she is. Other options if it doesn't stick: Purrsistant, Taskat, Meowbit.

**Settled 2026-07-30: the name is Loaf.** Deskitty named the product rather than the pet, and it doesn't survive being said out loud (*desk-itty* or *des-kitty*?). "Cat loaf" is the internet term for a cat sitting with its paws tucked — which is exactly the `sit` sprite — *loafing* is the idle state, and a loaf is a shape that gets bigger, which is the task-load mechanic. One word for the silhouette, the personality and the core mechanic. It also stands out against a field where every shipping competitor is named descriptively (Mac Pet, Desktop Pet, ScreenPets, PetBar, Running Cat).

## Relation to FlyThrough
[[project-flythrough]] is already a macOS menu-bar app with a cat character — photoreal, walks across screen before meetings, built on SwiftPM + an AppKit overlay. Loaf is conceptually different (a persistent pixel-art pet, not a one-off walk-through), but same domain — desktop cat companion on macOS — and could plausibly reuse overlay/animation plumbing when it's time to build. Worth a look at that code before starting from scratch.

## Open questions (decide when we start building, not now)
- Platform: native macOS (reuse FlyThrough's SwiftPM/AppKit overlay approach) vs cross-platform (Electron/Tauri) — matters more once channels/Twilio need a backend anyway.
- Where do "tasks" come from: a task list she owns natively, or ingesting from something that already exists (calendar, Linear, etc.)?
- Art: hand-drawn pixel sprite sheet vs AI-generated pixel sprites (states × frames).
- Smallest first buildable slice — likely just the pet + local task/CPU awareness, no brain/channels yet — but that's a call for whenever we actually start.

## Status
Nothing built yet. This file is the full brain-dump as given, for reference. Next step whenever picked up: scope the smallest buildable slice, one phase at a time.
