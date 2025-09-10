<!-- Zero-Tolerance rulebook loaded from knowledge/zero_tolerance_rulebook.md -->
Manim Coder Knowledge Base (CE 0.19+)

A. Golden Invariants

1) Imports & Base
- Use exactly:
	from manim import *
	import numpy as np
- Provide one class MainScene(Scene) with construct(self).

2) Axes & Plotting (modern API)
- Use Axes(...) or NumberPlane(...). Use Axes.plot for functions (not get_graph / FunctionGraph).
- Valid keys: x_range=[xmin,xmax,step], y_range=[ymin,ymax,step], tips: bool, axis_config={"include_numbers": True}.
- For specific numbers, use axes.x_axis.add_numbers(...) / axes.y_axis.add_numbers(...) or numbers_to_include on axes; never numbers_to_show.
- Never pass x_axis_label / y_axis_label / unit_size to Axes/NumberLine.

3) Axis Labels (correct pattern)
- labels = axes.get_axis_labels(MathTex("x"), MathTex("y")) or Text fallback; then self.play(FadeIn(labels)).

4) LaTeX vs. Text (Windows)
- Use MathTex/Tex only if LaTeX is healthy; otherwise fallback to Text. Proceed even if LaTeX fails.

5) Dynamics = ValueTracker + always_redraw
- Use ValueTracker and always_redraw(lambda: ... returns NEW mobject). Do not mutate .points. Use become() if needed.

6) Animation Budget
- Target >= 6 distinct animations per scene (Create/FadeIn/Write/Transform/Animate/UpdateFromAlphaFunc/Rotate/MoveToTarget/Indicate/FocusOn/Unwrite).

7) No direct .points edits
- Don’t assign to .points; prefer always_redraw or become().

8) Rendering
- Follow manim CLI; ensure ffmpeg available.

B. Canonical Patterns

B1) Axes + Live Plot + Marker
axes = Axes(x_range=[-6,6,1], y_range=[-3,3,1], tips=False, axis_config={"include_numbers": True})
t = ValueTracker(0)
curve = always_redraw(lambda: axes.plot(lambda x: np.sin(x + t.get_value())))
dot = always_redraw(lambda: Dot(axes.c2p(t.get_value(), np.sin(t.get_value())), radius=0.06, color=YELLOW))
self.play(Create(axes), Create(curve), FadeIn(dot))
self.play(t.animate.set_value(2*np.pi), run_time=3, rate_func=linear)

B2) Axis Labels with Text fallback
labels = axes.get_axis_labels(MathTex("x"), MathTex("y"))  # or Text("x"), Text("y")
self.play(FadeIn(labels))

B3) Updating Numeric Readouts
val = ValueTracker(0.0)
readout = DecimalNumber(0, num_decimal_places=2).to_corner(UR).scale(0.8)
readout.add_updater(lambda m: m.set_value(val.get_value()))
self.add(readout)
self.play(val.animate.set_value(6.28), run_time=2)

B4) Structured Beats
title = Text("<Title>").to_edge(UP)
self.play(Write(title))
# ...
self.play(FadeOut(title))

C. Guardrails (bans & auto-fixes)
- Ban: x_axis_label=, y_axis_label=, unit_size=, numbers_to_show=, get_graph(, FunctionGraph(, direct .points mutation.
- LaTeX fails => replace MathTex/Tex with Text and continue.
- Missing imports => add from typing import Sequence if Sequence is referenced.
- Updaters: the lambda passed to always_redraw must return a Mobject (avoid m.update()).

D. Planning Grammar (internal JSON)
- topic, beats array, visuals list, parameters (ValueTracker), animations with targets, text, latex_ok flag.

E. Robustness Playbook
- Unexpected kwarg => remove and rebuild Axes with allowed keys.
- numbers_to_show => use include_numbers and add_numbers / numbers_to_include.
- LaTeX compile fail => switch to Text.
- Updater returns None => return a new Mobject or use become().
- Deprecated API => Axes.plot only.
- NameError on Sequence => import from typing.
- Too few animations => add more beats/animations.

F. Scene Skeleton (emit this shape)
from manim import *
import numpy as np

class MainScene(Scene):
		def construct(self):
				title = Text("{{TITLE}}").to_edge(UP)
				self.play(Write(title))
				axes = Axes(x_range=[{{x0}},{{x1}},{{dx}}], y_range=[{{y0}},{{y1}},{{dy}}], tips=False, axis_config={"include_numbers": True})
				self.play(Create(axes))
				t = ValueTracker({{t0}})
				curve = always_redraw(lambda: axes.plot(lambda x: {{CURVE_EXPR}}))
				marker = always_redraw(lambda: Dot(axes.c2p({{MARKER_X}}, {{MARKER_Y}}), color=YELLOW, radius=0.06))
				self.play(Create(curve), FadeIn(marker))
				xlab = MathTex("x") if {{latex_ok}} else Text("x")
				ylab = MathTex("y") if {{latex_ok}} else Text("y")
				labels = axes.get_axis_labels(xlab, ylab)
				self.play(FadeIn(labels))
				readout = DecimalNumber(0, num_decimal_places=2).to_corner(UR).scale(0.8)
				readout.add_updater(lambda m: m.set_value(t.get_value()))
				self.add(readout)
				self.play(t.animate.set_value({{t1}}), run_time={{rt}}, rate_func=linear)
				self.play(FadeOut(marker), FadeOut(curve), FadeOut(labels), FadeOut(axes), FadeOut(title))
				self.wait(0.2)

G. Render & Video
- Use manim CLI. If needed, post-process with ffmpeg keeping yuv420p.

H. Self-Tests (pre-render)
- Import manim >= 0.19; probe MathTex("x") offscreen; if fail => latex_ok=False.
- Build Axes with allowed keys; strip unknown kwargs and retry.
- Ensure each always_redraw lambda returns a Mobject; deny .points mutation.
