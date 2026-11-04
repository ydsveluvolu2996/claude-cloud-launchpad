#!/usr/bin/env python3
"""Render the share card and an animation of recorded doctor output.

Optional maintainer tool: uv run --with Pillow==12.0.0 python scripts/render_visuals.py
The demo text must come from a real `bash doctor.sh --profile full` run.
"""
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/images"
OUT.mkdir(parents=True, exist_ok=True)


def face(size, bold=False, mono=False):
    choices = (
        ["/System/Library/Fonts/Menlo.ttc", "DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf"]
        if mono else
        [f"/System/Library/Fonts/Supplemental/Arial{' Bold' if bold else ''}.ttf",
         f"DejaVuSans{'-Bold' if bold else ''}.ttf",
         f"C:/Windows/Fonts/arial{'bd' if bold else ''}.ttf"]
    )
    for choice in choices:
        try:
            return ImageFont.truetype(choice, size)
        except OSError:
            pass
    raise RuntimeError("Install Arial or DejaVu Sans to render these optional graphics")


def share_card():
    canvas = Image.new("RGB", (1280, 640), "#101E35")
    d = ImageDraw.Draw(canvas)
    for y in range(640):
        t = y / 640
        d.line((0, y, 1280, y), fill=(int(16 + 8*t), int(30 + 9*t), int(53 + 16*t)))
    d.ellipse((975, -180, 1535, 380), outline="#2A4464", width=2)
    d.ellipse((1005, -150, 1505, 350), outline="#2A4464", width=2)
    d.rounded_rectangle((68, 60, 327, 99), radius=18, fill="#243D56")
    d.text((87, 67), "YOUR CLOUD TOOLKIT", font=face(18, True), fill="#9EE9DF")
    d.text((65, 140), "Claude Cloud", font=face(78, True), fill="#FFFFFF")
    d.text((65, 226), "Launchpad", font=face(78, True), fill="#9EE9DF")
    d.text((69, 337), "A clear start with Claude Code.", font=face(32), fill="#E4ECF7")
    d.text((69, 385), "Choose your tools. Check your setup. Start building.", font=face(25), fill="#B5C7DB")
    x = 69
    for label in ["macOS + Windows", "AWS", "Collaboration", "Design"]:
        w = int(d.textlength(label, font=face(19, True))) + 32
        d.rounded_rectangle((x, 465, x+w, 506), radius=9, fill="#243D56")
        d.text((x+16, 475), label, font=face(19, True), fill="#E4ECF7")
        x += w + 14
    d.line((69, 551, 1211, 551), fill="#38506A", width=1)
    d.text((69, 575), "OPEN SOURCE  /  BEGINNER FRIENDLY", font=face(18, True), fill="#90A9C3")
    d.text((1094, 571), "v1.0.0", font=face(26, True), fill="#9EE9DF")
    # Original terminal icon; no vendor logos or endorsement implied.
    d.rounded_rectangle((985, 157, 1198, 320), radius=20, fill="#243D56", outline="#4A6B87", width=2)
    d.line((1016, 207, 1043, 235, 1016, 263), fill="#9EE9DF", width=7, joint="curve")
    d.line((1064, 263, 1133, 263), fill="#FFFFFF", width=7)
    canvas.save(OUT / "social-preview.png", optimize=True)


def demo():
    transcript = ROOT / "docs/demo-output.txt"
    if not transcript.is_file():
        return
    lines = transcript.read_text(encoding="utf-8").splitlines()
    # Only the recorded command/output are animated; provenance stays in the text file.
    start = next(i for i, line in enumerate(lines) if line.startswith("$ bash doctor.sh"))
    lines = lines[start:]
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=96, subsequent_indent="  ") or [""])
    width, height = 1280, 760
    frames = []
    # Group line arrivals for readable playback; this is a transcript replay, not a video.
    checkpoints = sorted(set([1] + list(range(4, len(wrapped)+1, 4)) + [len(wrapped)]))
    for count in checkpoints:
        canvas = Image.new("RGB", (width, height), "#F2F5F9")
        d = ImageDraw.Draw(canvas)
        d.text((42, 27), "CHECK YOUR SETUP", font=face(18, True), fill="#146B65")
        d.text((42, 60), "Real output. Clear next steps.", font=face(35, True), fill="#13283E")
        d.rounded_rectangle((37, 124, 1243, 693), radius=17, fill="#101E35")
        for i, color in enumerate(["#E67C76", "#F1C96D", "#86C99E"]):
            d.ellipse((58+i*24, 144, 70+i*24, 156), fill=color)
        d.text((474, 138), "Claude Cloud Launchpad", font=face(18), fill="#AFC1D6")
        visible = wrapped[max(0, count-19):count]
        for i, line in enumerate(visible):
            color = "#A5E7D2" if line.startswith("PASS") else "#E5EDF8"
            if line.startswith("$"):
                color = "#A8D4FF"
            if line.startswith(("NOTE", "NEXT", "Optional")):
                color = "#F1D69A"
            d.text((58, 180+i*25), line, font=face(20, mono=True), fill=color)
        d.text((42, 718), "Recorded macOS diagnostic output · replay paced for readability · text transcript linked below", font=face(19), fill="#4B6077")
        frames.append(canvas)
    durations = [1600] + [1500] * max(0, len(frames)-2) + [6000]
    if len(frames) == 1:
        durations = [6000]
    frames[0].save(OUT / "demo.gif", save_all=True, append_images=frames[1:], duration=durations, loop=0, optimize=True)
    frames[-1].save(OUT / "demo-still.png", optimize=True)


if __name__ == "__main__":
    share_card()
    demo()
    print("Rendered share card and available recorded demo.")
