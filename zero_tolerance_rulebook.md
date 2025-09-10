# zero-tolerance manim rulebook (coder→video)

This is the authoritative rulebook loaded into the model context. It should be treated as hard constraints and self-repair heuristics. (Original user-supplied content retained.)

## 0) environment invariants (must hold before any code runs)

* **Target**: Manim Community Edition **≥0.19.x**; Python **3.10–3.12** only. If version unknown, the AI must assume **0.19** APIs. ([Manim Community | Documentation][1])
* **FFmpeg** present on PATH. **Never** shell out; rely on Manim’s renderer which uses ffmpeg internally. ([Manim Community | Documentation][1])
* **LaTeX** is **optional**. If *any* `Tex/MathTex` appears, enforce “LaTeX present” precheck; otherwise **fall back to `Text`** with unicode math. On Windows, prefer TeX Live over MiKTeX when reliability matters (MiKTeX often needs updates mid-render). ([Manim Community | Documentation][2], [Reddit][3])
* **Fonts**: `Text` uses Pango/Harfbuzz; no LaTeX required. If a font name is used, require local availability or replace with default. ([Manim Community | Documentation][2])

## 1) scene boilerplate constraints (CE 0.19 semantics)

* Export **one** top-level `Scene` subclass named `MainScene` unless user asks otherwise. No `__main__` CLI shims; Manim handles that. ([Manim Community | Documentation][1])
* **No** direct mutation of `.points` arrays on `VMobject`s. All curve updates must use **`become(...)`** or re-create via `axes.plot(...)` inside an updater/`always_redraw`. ([Manim Community | Documentation][4])
* Updater signatures = `def f(mobject, dt): ...` or lambdas that ignore `dt`. Remove updaters with `clear_updaters()` before final fadeout if they cause flicker. ([Manim Community | Documentation][4])
* Prefer **`always_redraw(lambda: ... )`** to build live-recomputed mobjects from source of truth (`ValueTracker`s). ([Manim Community | Documentation][4])
* Use **`ValueTracker`**/`BooleanVar` style trackers for all time-varying scalars. **Never** read raw time; animate tracker values. ([Manim Community | Documentation][5])

## 2) graphing & coordinates (Axes/NumberPlane/NumberLine)

* Build plots with **`Axes(...).plot(func, x_range=None, use_smoothing=False)`**. Do **not** use deprecated `get_graph`/`FunctionGraph`. ([Manim Documentation][6])
* Axis labels & ticks: for numbers, call **`add_numbers(...)`** on number lines/axes; **do not** send unknown kwargs like `numbers_to_show` to `Axes` (this caused your errors). ([Manim Community | Documentation][7])
* Convert data→scene coordinates with `axes.c2p(x, y)` and back with `axes.p2c(point)`. Never assume pixel positions. ([Manim Documentation][6])
* For moving dots along curves, bind a `ValueTracker t` and compute `Dot(axes.c2p(x, f(x)))` inside **`always_redraw`**; drive `t` with `self.play(t.animate.set_value(...))`. ([Manim Community | Documentation][4])

## 3) text/math correctness

* **Prefer `Text`** for robustness; only use `MathTex/Tex` when you truly need TeX layout. If tex is used, **escape** backslashes and ensure packages are in the template; otherwise fallback to `Text`. ([Manim Community | Documentation][2])
* If a LaTeX error occurs (common on Windows), **auto-downgrade**: replace `MathTex(...)` with `Text(sympy.latex_expr or plain string)` and continue. ([Manim Community | Documentation][2])

## 4) animation semantics (safe patterns)

* Animate attributes via **`.animate`** or helper animations: `Create/FadeIn/Transform/Write/MoveAlongPath/Rotate/ScaleInPlace`. Avoid custom tweens unless necessary. ([Manim Community | Documentation][1])
* Rate functions: default `smooth`. For constant speed use **`linear`**, for ease-in/out use documented functions only (no custom callables unless deterministic). ([Manim Community | Documentation][8])
* `Transform` should preserve object type; transforming two graphs into the same third graph is legal but keep references distinct to avoid early garbage collection.

## 5) updaters & `always_redraw` (hard rules)

* **Never** add an updater that calls `self.play` (reentrancy).
* Updaters must be **idempotent** and cheap: compute from trackers, not from `time.time()`.
* Before scene end or transitions, call `clear_updaters()` on animated graphs to avoid *post-animation jerks*. ([Manim Community | Documentation][4])

## 6) performance & stability

* Dense plots: pass `x_range=[xmin,xmax, step]` to `axes.plot` instead of massive default sampling if perf drops. For many samples prefer `ParametricFunction` or `VMobject.set_points_smoothly`. ([Manim Documentation][6])
* Avoid per-frame creation of **thousands** of small `Dot`s; use heatmap‐like textures only if necessary (Manim is vector-first). For interference “screens,” approximate with 1D scanlines or plot envelopes instead of pixel grids.

## 7) CLI & rendering

* Use Manim’s CLI (`manim -pqh file.py MainScene`) to render; do **not** invoke ffmpeg directly. Quality presets: `-ql/-qm/-qh/-pqh`. ([Manim Community | Documentation][1])
* If your pipeline needs a guaranteed mp4 path, compute from Manim’s media dir (or set `--media_dir`). ([Manim Community | Documentation][1])

## 8) Windows/LaTeX pitfalls (what to auto-fix)

* “latex: major issue: you have not checked MiKTeX updates” → either trigger MiKTeX update, or **replace** all `MathTex/Tex` with `Text` for this render. ([Reddit][3])
* `TypeError: Mobject.__init__ got unexpected kwarg 'numbers_to_show'` → **remove** that kwarg; add numbers via `add_numbers`. ([Manim Community | Documentation][7])
* `NameError` for trackers inside `always_redraw` blocks → declare trackers **before** the lambda and capture only `.get_value()`. ([Manim Community | Documentation][4])

## 9) graphing basics the model must “know by heart”

* **Axes**: construction, `plot`, `plot_parametric_curve`, `get_axis_labels`, `add_coordinates` (or `add_numbers` on lines). ([Manim Documentation][6], [Manim Community | Documentation][7])
* **NumberLine/NumberPlane**: don’t pass unknown kwargs; use documented helpers. ([Manim Community | Documentation][7])
* **Rate functions** dictionary: linear, smooth, ease\_in\_out, etc. (reference list). ([Manim Community | Documentation][8])
* **ValueTracker** usage: create tracker, bind to updater/`always_redraw`, animate via `.animate`. ([Manim Community | Documentation][5])
* **Examples gallery** is reference for canonical idioms (not to copy, but to constrain style/approach). ([Manim Community | Documentation][8])

## 10) “topic→plan→scene” contract (for the AI)

When given any topic, the coder must:

1. **Outline beats** (2–6 short bullets).
2. Map beats to **scene primitives** (graphs, shapes, text) using only allowed APIs.
3. Emit code that passes a **static rule scan**:

   * No `.points`/low-level mutation
   * No deprecated graphing calls (`get_graph`/`FunctionGraph`)
   * No Axis kwargs not in docs (e.g., `numbers_to_show`, `x_axis_label` on `Axes`)
   * All text via `Text` unless LaTeX confirmed
   * All motion via `ValueTracker` + `always_redraw` or `.animate`
   * Updaters have `(mobject, dt)` signature and are removable
4. If the scene needs math labels and LaTeX unavailable, **auto-replace** with `Text` and Unicode symbols.

## 11) auto-repair heuristics (self-debug)

* **Bad kwarg** on axis/number line → remove & re-create with supported params; then call `add_numbers()`/`add_labels()` as per docs. ([Manim Community | Documentation][7])
* **Graph not updating** → ensure the graph object is created via `always_redraw(lambda: axes.plot(...))` where lambda reads **trackers** only. ([Manim Community | Documentation][4])
* **Janky transforms** → swap to `ReplacementTransform` or animate target `.become(...)` within an updater.
* **LaTeX error** → replace `MathTex` with `Text`, keep going. ([Manim Community | Documentation][2])
* **Slow frame** → reduce sampling or shorten ranges on `plot`; avoid nested Python loops building thousands of submobjects.

## 12) no-samples / dynamic generation policy

The model MUST NOT copy or emit canned sample scenes, template classes (e.g., `SampleScene`, `PresetScene`, `TemplateScene`), or verbatim tutorial code. All output must be freshly synthesized using the rule constraints and topic semantics. Any illustrative idioms previously listed have been removed to avoid leakage—concepts are retained, literal code is forbidden. Dynamic construction is mandatory: derive axes ranges, tracker usage, and grouping from the provided topic, not from fixed presets.

Key enforcement points:
* No placeholder text like "Your Title Here" or generic "Sample" labels.
* No unexplained static sine/cosine graphs unless inherently tied to topic narrative (e.g., EM wave depiction for Maxwell).
* All mathematical visuals must tie to declared beat structure (plan→beats→animations mapping internal to generation process).
* VectorField / StreamLines usage must be minimal and performance-conscious (small grid, or short-lived visualization) and only if conceptually relevant.

Violation of this section triggers regeneration with an explicit "remove preset/sample code" instruction.

## 13) integrated user augmentation (hard-lock environment & guardrails)

Incorporated directives (summarized from user augmentation):
1. Preflight toolchain check (`manim checkhealth`) gates LaTeX usage; fallback to Unicode `Text` instantly if unhealthy.
2. Guardrail enforcement eliminates invalid kwargs (`x_axis_label`, `y_axis_label`, `numbers_to_show`, `unit_size`) before render.
3. Banned structural mutations: direct `.points` edits, method `.wiggle()` calls on groups, deprecated `get_graph`/`FunctionGraph` usage.
4. Auto-patcher semantics (mirrored in generation logic): rewrite invalid graphing / axis patterns, substitute MathTex→Text on LaTeX failure, eradicate banned tokens.
5. Error mapping table (conceptual) embedded in prompts to prevent recurrence rather than reactive patching.
6. Scene richness threshold (≥6 distinct animations) enforced; additional animations must be meaningful (transformative, pedagogical) not filler.
7. Resolution/FPS default (1080p60) assumed; code should not hardcode config unless essential.

## 14) prohibition of literal code idioms

All previously embedded concrete code examples have been excised. The model holds conceptual patterns only:
* Use trackers + always_redraw for dynamic curves.
* Use add_numbers()/get_axis_labels after axis creation.
* Use Wiggle/Indicate/AnimationGroup (animation classes) instead of method calls.

If literal snippet emission is detected that matches known documentation or removed examples, treat as violation and regenerate.

## why these rules (and where they come from)

* **Updaters / always\_redraw / trackers** are the canonical way to create dynamic scenes; they’re stable across CE releases and documented clearly. ([Manim Community | Documentation][4])
* **Graphing** via `Axes.plot` is the supported path in CE 0.19; old helpers like `get_graph`/`FunctionGraph` are not the baseline anymore. ([Manim Documentation][6])
* **Axis ticks/labels** are added with methods like `add_numbers()`; passing random kwargs (e.g., `numbers_to_show`) into `Axes` triggers exactly the errors you hit. ([Manim Community | Documentation][7])
* **LaTeX** is optional; `Text` avoids toolchain failures. When LaTeX *is* needed, follow the Tex/MathTex guidelines. ([Manim Community | Documentation][2])
* **Render** through Manim’s CLI; it orchestrates ffmpeg, config, and cache. ([Manim Community | Documentation][1])
* **Rate functions**: only use the official set for consistent timing. ([Manim Community | Documentation][8])
* **Graphing tutorial** (official) models the style the generator should emulate (trackers, plots, transforms). ([Manim Documentation][6])

---

## if you want this to be “fail-closed” in your pipeline

Wire these checks into your coder before rendering:

1. **Rule scan** (static):

   * Reject code containing: `.points`, `get_graph`, `FunctionGraph`, unknown `Axes` kwargs (`numbers_to_show`, `x_axis_label`, `y_axis_label`, `unit_size` on `Axes`, etc.).
   * If `MathTex`/`Tex` detected and LaTeX not verified → auto-replace with `Text`.

2. **Runtime guard**:

   * Wrap `Scene.construct()` in try/except; on LaTeX error, regenerate with “no-LaTeX” mode.
   * On `TypeError unexpected kwarg` → regenerate axes with a minimal set, then append numbers via `add_numbers()`.

3. **Refiner prompts**:

   * “Remove deprecated/unknown kwargs to `Axes`.”
   * “Rebuild dynamic curves using `always_redraw` + trackers; no direct mobject point edits.”
   * “Use `Text` instead of `MathTex` unless LaTeX is verified.”

---

### high-value references (bookmark these)

* **Updaters** (concept + `always_redraw`) — Manim CE docs. ([Manim Community | Documentation][4])
* **ValueTracker & updaters** — reference manual. ([Manim Community | Documentation][5])
* **Graphing basics & `Axes.plot`** — official tutorial. ([Manim Documentation][6])
* **NumberLine / ticks / `add_numbers`** — reference manual. ([Manim Community | Documentation][7])
* **Tex/MathTex (LaTeX requirements & pitfalls)** — docs. ([Manim Community | Documentation][2])
* **Rate functions** — list and meanings. ([Manim Community | Documentation][8])
* **Getting started / CLI / rendering** — docs home. ([Manim Community | Documentation][1])

[1]: https://docs.manim.community/en/stable/reference/manim.mobject.graphing.coordinate_systems.CoordinateSystem.html?utm_source=chatgpt.com "CoordinateSystem - Manim Community v0.19.0"
[2]: https://docs.manim.community/en/stable/reference/manim.animation.updaters.mobject_update_utils.html?utm_source=chatgpt.com "mobject_update_utils - Manim Community v0.19.0"
[3]: https://www.reddit.com/r/manim/comments/nrli6h/how_to_config_axis_labels_with_axes/?utm_source=chatgpt.com "How to config axis labels with Axes() ? : r/manim"
[4]: https://docs.manim.community/en/stable/installation/macos.html?utm_source=chatgpt.com "Installing Manim locally"
[5]: https://docs.manim.community/en/stable/reference/manim.mobject.value_tracker.html?utm_source=chatgpt.com "value_tracker - Manim Community v0.19.0"
[6]: https://manim.readthedocs.io/en/latest/installation/windows.html?utm_source=chatgpt.com "Windows - Manim documentation - Read the Docs"
[7]: https://docs.manim.community/en/stable/_modules/manim/mobject/graphing/coordinate_systems.html?utm_source=chatgpt.com "manim.mobject.graphing.coordinate_systems"
[8]: https://docs.manim.community/en/stable/examples.html?utm_source=chatgpt.com "Example Gallery - Manim Community v0.19.0"

---

## 15) dynamic policy extensions (sections A–M)

The following sections (A–M) are additive, mandatory, and verbatim policy (no samples). They refine determinism, layout safety, accessibility, performance, and repair logic.

## A) Deterministic, reproducible renders (no “works on my machine”)

* **Seed control**: require a single random seed for any stochastic layout or sampling so two identical prompts produce the same frames unless the topic changes.
* **Cache discipline**: allow Manim’s cache; forbid custom temp writing. Require a clean re-render path (delete partials only when necessary).
* **Config invariants**: mandate *only* documented config keys (renderer, pixel size, frame rate, media_dir). Disallow hidden/undocumented flags.

## B) Layout that never overlaps (auto-layout contract)

* **Atomic placement**: all static arrangements must use `next_to`, `align_to`, and **`VGroup.arrange`/`arrange_in_grid`** with explicit `buff`; never hand-tuned coordinates.
* **Collision pass**: when adding dynamic labels, run a bbox overlap check and push conflicting items via another `arrange` with increased `buff`.
* **Z-order rules**: use **`set_z_index()`** for layering (e.g., text above graphs), or `bring_to_front`/`send_to_back`; forbid ad-hoc re-adds to change order.

## C) Legible text without LaTeX (and safe LaTeX when healthy)

* **Default to `Text`** (Pango) for titles/labels; switch to `MathTex` only when LaTeX passes preflight. If LaTeX fails at any time, *auto-downgrade* those elements to `Text` with Unicode math—no retry loops.
* **Font safety**: if a requested font isn’t present, silently fall back to the default.
* **Contrast rule**: all foreground text must meet **WCAG 2.1 1.4.3** (≥4.5:1), with ≥3:1 allowed for very large titles. ([W3C][WCAG])

## D) Graphing API whitelist (and hard bans)

* **Only** `Axes.plot`, `plot_parametric_curve`, `add_coordinates`/`get_axis_labels`.
* **Banned**: `get_graph`, `FunctionGraph`, unknown kwargs on `Axes`/NumberLine (e.g., `numbers_to_show`, `x_axis_label`, `y_axis_label`).
* **Numbers/ticks**: add ticks/numbers *after* creation via documented helpers (e.g., `add_coordinates` on `Axes`, `add_numbers` on `NumberLine`).

## E) Dynamic motion: trackers + always_redraw (no low-level edits)

* All continuous changes are driven by **`ValueTracker`** objects and **`always_redraw`**; *never* mutate `.points` or read wall clock time.
* Updaters must be pure functions of tracker values and remove themselves (or `clear_updaters`) before end to avoid drift/flicker.

## F) Camera, pacing, and rhythm

* **Pacing budget**: each scene has ≥6 meaningful animations; cap single-action beats at ~1.5–3.0s; use `LaggedStart`/`AnimationGroup` for choreographed entrances.
* **Framing**: use the camera frame for pans/zooms; keep text inside safe margins; forbid abrupt teleports unless the beat calls for a “cut”.

## G) Color & style system (consistent, accessible, non-clashing)

* **Palette contract**: one categorical palette + one sequential palette per render; forbid mixing many unrelated hues.
* **Contrast check**: enforce the WCAG rule (above) for any text/line on its background; adjust colors or stroke width to pass. ([W3C][WCAG])

## H) Audio & muxing policy (optional but supported)

* If audio is present, attach with **`Scene.add_sound`** at explicit offsets; never call ffmpeg directly—let Manim mux. **Fail closed** if sound file missing.

## I) Performance ceilings (so “dynamic” stays smooth)

* **Sampling control**: when plotting, set an `x_range` to bound samples; prefer fewer, denser curves over thousands of tiny objects.
* **Vector fields/streamlines**: restrict grid density and lifetime; show a small, pedagogical subset only (brief on screen).
* **No per-frame mass object creation** inside updaters; rebuild via `always_redraw` that returns a *single* mobject each frame.

## J) Error taxonomy → auto-repair (no human in the loop)

* **Unexpected kwarg** to `Axes`/NumberLine → recreate the axis with documented kwargs, then apply numbers/labels via helpers.
* **LaTeX error** → rewrite *just* the failed `MathTex` nodes to `Text` and rerender.
* **Deprecated/banned calls** (`get_graph`, `.points`) → regenerate with the whitelisted API and `always_redraw`.
* **AttributeError on “wiggle”** (method on animation class, not groups) → replace with `Wiggle(...)` animation or `Indicate`.
   (References for allowed updater primitives and animation types: **updaters & updater-based utilities**.)

## K) Topic→beats→scene contract (strict, but sample-free)

* **Beats**: 2–6 atomic beats per topic (outline only).
* **Mapping**: for each beat, choose primitives from the whitelist; for math labels, decide **Text vs MathTex** *after* LaTeX preflight.
* **Emit-only-code mode**: when invoked for production, reply with *code only* to the token limit; all narration lives inside comments or `Text` mobjects (LaTeX permitting).
* **Self-check**: before emitting code, run static scan against the whitelist (sections D–E) and reject any violations.

## L) Windows specifics (your environment)

* **LaTeX**: Manim docs confirm Pango (`Text`) doesn’t need LaTeX; only use MathTex when toolchain is healthy. If using MiKTeX, expect “update required”; your default path is brittle—prefer TeX Live if reliability matters. See **Rendering Text and Formulas** and the object reference pages for `Text`/`MathTex`.

## M) Configuration invariants (so the CLI never surprises you)

* **Renderer/quality/fps/output dirs** must be set using documented config/CLI options only. Publish a single source of truth (e.g., `config.media_dir`, `frame_rate`, `pixel_width/height`).

---

## Drop-in checklists you can paste into your framework

**Preflight**

* Validate Manim version ≥0.19; set renderer/quality/output via documented config.
* LaTeX precheck: if unhealthy → enforce `Text` only.
* Seed set; media_dir set; clean cache policy declared.

**Static scan (reject-on-fail)**

* No banned APIs/kwargs (see D).
* All dynamics use trackers + `always_redraw`; no `.points`.

**Runtime guard**

* Catch LaTeX errors → auto-downgrade to `Text`.
* Catch kwargs/attr errors → rebuild axis/layout via documented methods.

**Visual QA**

* At least six meaningful animations; no dead time.
* Text contrast ≥4.5:1 (≥3:1 for large titles).
* No overlaps after collision pass; consistent z-order.

---

### Rationale for additions

* Determinism simplifies diff-based QC and regression reproduction.
* Auto-layout + collision pass eliminates overlapping text/equations at generation time.
* Accessibility (contrast) ensures legibility across varied backgrounds.
* Performance ceilings prevent frame drops from unbounded sampling or object proliferation.
* Error taxonomy codifies automatic repair pathways; no manual intervention required.

---

[WCAG]: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html "Understanding Success Criterion 1.4.3: Contrast (Minimum) | WAI | W3C"
