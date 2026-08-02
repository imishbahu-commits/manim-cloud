"""
AI Video Studio demo — "How Does GPS Know Where You Are?"
Three scenes, each with one narration line (see narration.txt).
Classic 3B1B palette, monospace fonts, no LaTeX needed.
"""

import numpy as np
from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"    # blue
SECONDARY = "#83C167"  # green
ACCENT = "#FFFF00"     # yellow
MONO = "monospace"


class Scene1_Intro(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text(
            "How Does GPS Know\nWhere You Are?",
            font_size=44, color=PRIMARY, weight=BOLD, font=MONO, line_spacing=1.15,
        )
        self.add_subcaption("How does GPS know where you are?", duration=3)
        self.play(Write(title), run_time=1.5)
        self.wait(0.8)

        sub = Text("Three satellites. One answer.", font_size=28, color=SECONDARY, font=MONO)
        sub.next_to(title, DOWN, buff=0.8)
        self.play(FadeIn(sub), run_time=1.0)
        self.wait(1.2)

        # phone + satellite with signal rings
        phone = RoundedRectangle(corner_radius=0.15, width=1.1, height=1.9,
                                 color=PRIMARY, stroke_width=4)
        phone.next_to(sub, DOWN, buff=1.0)
        sat = Dot(np.array([2.3, 1.6, 0]), color=ACCENT, radius=0.13)
        self.play(FadeIn(phone), FadeIn(sat), run_time=0.8)
        self.wait(0.3)
        for _ in range(2):
            ring = Circle(color=ACCENT, stroke_width=2, radius=0.3).move_to(sat)
            self.play(ring.animate.scale(3.0).set_opacity(0.05), run_time=1.1)
            self.wait(0.2)
        self.wait(1.0)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.3)


class Scene2_Trilateration(Scene):
    def construct(self):
        self.camera.background_color = BG

        label = Text("Trilateration: distance from 3 satellites",
                     font_size=28, color=PRIMARY, font=MONO)
        label.to_edge(UP, buff=0.6)
        self.add_subcaption("Trilateration: distance from three satellites", duration=3)
        self.play(Write(label), run_time=1.2)
        self.wait(0.4)

        sat_positions = [(-2.2, 1.8, 0), (2.3, 1.7, 0), (0.1, -2.1, 0)]
        colors = [PRIMARY, SECONDARY, ACCENT]
        dots, circles = VGroup(), VGroup()
        for pos, col in zip(sat_positions, colors):
            dots.add(Dot(pos, color=col, radius=0.12))
            c = Circle(color=col, stroke_width=3, radius=2.6).move_to(pos)
            circles.add(c)
        for dot, c in zip(dots, circles):
            self.play(FadeIn(dot), Create(c), run_time=1.1)
            self.wait(0.4)
        self.wait(1.6)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.3)


class Scene3_Answer(Scene):
    def construct(self):
        self.camera.background_color = BG

        sat_positions = [(-2.4, 1.8, 0), (2.4, 1.6, 0), (0.0, -2.2, 0)]
        colors = [PRIMARY, SECONDARY, ACCENT]
        dots, circles = VGroup(), VGroup()
        for pos, col in zip(sat_positions, colors):
            dots.add(Dot(pos, color=col, radius=0.12))
            circles.add(Circle(color=col, stroke_width=3, radius=2.8).move_to(pos))
        self.add_subcaption("Where all three circles meet, that is you", duration=3)
        self.play(*[FadeIn(d) for d in dots], *[Create(c) for c in circles], run_time=1.5)
        self.wait(0.8)

        you = Dot(ORIGIN, color=WHITE, radius=0.14)
        self.play(FadeIn(you), run_time=0.6)
        pulse = Circle(color=WHITE, stroke_width=3, radius=0.25).move_to(ORIGIN)
        self.play(Create(pulse), run_time=0.4)
        self.play(pulse.animate.scale(4.0).set_opacity(0.0), run_time=1.2)

        arrow = Arrow(ORIGIN + DOWN * 1.4, ORIGIN + DOWN * 0.3, color=WHITE, stroke_width=5)
        lbl = Text("That's you!", font_size=30, color=WHITE, weight=BOLD, font=MONO)
        lbl.next_to(arrow, DOWN, buff=0.3)
        self.play(GrowArrow(arrow), FadeIn(lbl), run_time=0.8)
        self.wait(2.0)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.3)
