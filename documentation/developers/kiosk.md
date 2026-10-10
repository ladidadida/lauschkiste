# Kiosk app (reduced view on the box's screen)

Status: plan, nothing implemented yet.

A box with a screen should show something a child can use without changing settings. Today `lauschctl setup kiosk`
starts Chromium full screen on the normal web app, which offers everything. The plan: a **separate, small web app
for the screen**, delivered by a plugin, and the normal web app stays as it is: the administration and the fallback,
without themes or elaborate looks, it only has to work.

## Decisions so far

- **Two web apps.** The normal web app is unchanged. The kiosk app is its own frontend with its own build, in the
  plugin package `lauschkiste-plugin-kiosk`, served by the core under `/kiosk` while the plugin is enabled.
- **Same technology (React, MUI) and shared components.** Components that both need (player display, cover, library
  lists) move to a shared place in `packages/webapp` or a package of its own, so nothing is written twice. The kiosk
  bundle contains only what it needs.
- **Touch only** to begin with.
- **What a child sees:** the player (cover, title, controls, volume), the library to tap through (music, audiobooks,
  radio, podcasts) and "Continue". No settings, no card management. Which parts are shown becomes configurable.
- **Settings and themes belong to the plugin.** The plugin has a settings model, so the normal web app shows a form
  for it like for any plugin; the kiosk app reads the values through the API.
- **No new rights.** The kiosk app uses the same API and event stream as the normal one. It is a simplification, not
  a lock: anyone who can open the normal web app in a browser can still change everything. A real lock (a PIN for the
  normal web app, or reachable from the box only) is a separate decision.

## Parts

| Part | Content |
| --- | --- |
| Plugin `kiosk` | settings (theme, visible parts, text size, idle behaviour), serves the built kiosk app at `/kiosk`, a query that returns the settings |
| Core | an extension point or helper to serve the static files of a plugin (today only the normal web app and the logs are served) |
| Kiosk app | React app: player page, library page, "Continue"; reads the settings; German and English like the normal web app |
| Themes | a theme is a set of CSS variables (colours, radii, font, spacing) in a file; the plugin ships a few, the settings pick one |
| `lauschctl setup kiosk` | opens `/kiosk` when the plugin is enabled, otherwise the normal web app |

## Settings of the plugin (first idea)

`theme`, `sections` (which of player, music, audiobooks, radio, podcasts are offered), `text_size`, `show_volume`,
`screen_off_after_minutes` (dark screen when nothing plays), `start_page`.

## Phases and estimate

Rough working days of focused work; the first look on a real screen decides the details.

| Phase | Content | Days |
| --- | --- | --- |
| 0 | Look at the normal web app on the target screen with Chromium in kiosk mode: speed, memory, touch sizes; decide what the kiosk app needs | 0.5 |
| 1 | Core: serve the static files of a plugin; plugin skeleton with settings; `/kiosk` shows a page | 1 |
| 2 | Shared components out of the normal web app; kiosk app with player and library | 3 to 4 |
| 3 | Themes (variables, 2 or 3 themes, picker in the settings), configurable sections, screen-off | 1 to 2 |
| 4 | `lauschctl setup kiosk` points at `/kiosk`; documentation, help pages, translations; tests (unit and Playwright) | 1 |

About 6 to 9 days.

## Risks and open points

- **The device.** Chromium in kiosk mode is the heavy part, not the bundle: the normal web app is 1.2 MB of
  JavaScript (not compressed). A Pi Zero W with 427 MB RAM is probably too small for a Chromium kiosk; a Pi 3 or Zero 2
  and better should be fine. The first test device is a Pi 3B (1 GB RAM) with a HiFiBerry amplifier and a
  third-party touch display; phase 0 measures on it. It currently runs another audio software, which the
  installation of Lauschkiste would replace (a fresh Raspberry Pi OS Lite image).
- **Shared components** need a clean split (no code in the normal web app that only works with its router or settings
  context); this is most of phase 2.
- **Lightweight alternative.** A kiosk app without React (plain JavaScript or Preact) would load faster, but cannot
  reuse the components. Only worth it if phase 0 shows the React version is too slow on the target device.
- **Idle behaviour:** what the screen shows when nothing plays (a clock, the last cover, dark)?
- **Looks of the normal web app** stay plain on purpose; themes are only for the kiosk app.

## Questions

1. Display model, size and resolution of the test device (how the display is connected and how touch is wired).
2. Should a child be able to see the queue, or only the current title?
3. Should the kiosk be locked to the app (no way out to the normal web app)? Chromium's `--kiosk` already prevents
   it from the screen.
