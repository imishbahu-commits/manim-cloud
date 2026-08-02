"""
Example Manim scene for the free cloud render farm.
Drop your own scene files in the scenes/ folder and push —
GitHub Actions, Colab, and Kaggle will all render them.

To make your own: copy this file, rename the class, edit construct().
Save as scenes/my_animation.py and push.
"""

from manim import *

# Shared visual language (classic 3B1B palette)
BG = "#1C1C1C"
PRIMARY = "#58C4DD"   # blue
SECONDARY = "#83C167" # green
ACCENT = "#FFFF00"    # yellow
MONO = "monospace"    # monospace fonts render cleanly everywhere


class ExampleScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        # Title
        title = Text(
            "Your Cloud Animation",
            font_size=48,
            color=PRIMARY,
            weight=BOLD,
            font=MONO,
        )
        self.add_subcaption("Your cloud animation", duration=2)
        self.play(Write(title), run_time=1.5)
        self.wait(1.0)

        # Subtitle
        subtitle = Text(
            "Rendered on a FREE cloud server",
            font_size=30,
            color=SECONDARY,
            font=MONO,
        )
        subtitle.next_to(title, DOWN, buff=0.8)
        self.play(FadeIn(subtitle), run_time=1.0)
        self.wait(1.0)

        # Circle that grows
        circle = Circle(color=ACCENT, stroke_width=6)
        circle.next_to(subtitle, DOWN, buff=1.0)
        self.play(Create(circle), run_time=1.5)
        self.wait(0.5)
        self.play(circle.animate.scale(1.6).set_color(PRIMARY), run_time=1.5)
        self.wait(2.0)

        # Clean exit
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
        self.wait(0.3)
