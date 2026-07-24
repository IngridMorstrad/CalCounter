#!/usr/bin/env python3
"""Generate narration audio segments for the Kiro Tasks demo.

For each "beat" we synthesize speech with gTTS, measure its duration,
then build:
  - narration.wav : all segments concatenated with a fixed gap of silence
  - timings.json  : per-beat target duration (speech + gap) used by the
                    Playwright script to keep on-screen actions in sync.
"""
import json
import os
import subprocess
import imageio_ffmpeg
from gtts import gTTS
from mutagen.mp3 import MP3

HERE = os.path.dirname(os.path.abspath(__file__))
SEG_DIR = os.path.join(HERE, "audio")
os.makedirs(SEG_DIR, exist_ok=True)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

GAP = 0.75          # seconds of silence between beats
LEAD_IN = 0.6       # silence before the first word
SR = 44100          # audio sample rate

# Each beat: the narration line. Actions are attached in the Playwright script
# by index, so the order here defines the demo timeline.
BEATS = [
    "Welcome to Kiro Tasks, a clean, browser based to-do app with Kiro's signature look. Let's take a quick tour.",
    "Adding a task is simple. Just type what's on your mind, and press Add.",
    "You can queue up as many tasks as you need. Each new one drops neatly to the top of your list.",
    "Finished something? Click the checkbox to mark it done. It gets crossed off with a satisfying Kiro purple check.",
    "Use the filters to focus. Active hides what's done, while Completed shows only the tasks you've finished.",
    "The footer keeps a live count of what's left, and hovering over a task reveals a delete button to remove it entirely.",
    "Clear completed wipes out finished tasks in a single click. And because everything is saved to your browser, your list is still here when you come back.",
    "That's Kiro Tasks. Simple, fast, and ready to help you ship your day. Thanks for watching!",
]


def synth(text, path_mp3):
    gTTS(text=text, lang="en", tld="com", slow=False).save(path_mp3)


def to_wav(mp3, wav):
    subprocess.run(
        [FFMPEG, "-y", "-i", mp3, "-ar", str(SR), "-ac", "2", wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def silence_wav(seconds, wav):
    subprocess.run(
        [FFMPEG, "-y", "-f", "lavfi", "-i",
         f"anullsrc=r={SR}:cl=stereo", "-t", f"{seconds:.3f}", wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def main():
    timings = []
    concat_parts = []

    # lead-in silence
    lead = os.path.join(SEG_DIR, "lead.wav")
    silence_wav(LEAD_IN, lead)
    concat_parts.append(lead)

    gap_wav = os.path.join(SEG_DIR, "gap.wav")
    silence_wav(GAP, gap_wav)

    for i, text in enumerate(BEATS):
        mp3 = os.path.join(SEG_DIR, f"seg{i}.mp3")
        wav = os.path.join(SEG_DIR, f"seg{i}.wav")
        synth(text, mp3)
        dur = MP3(mp3).info.length
        to_wav(mp3, wav)
        concat_parts.append(wav)
        concat_parts.append(gap_wav)
        beat_total = dur + GAP
        timings.append({"index": i, "speech": round(dur, 3),
                         "duration": round(beat_total, 3), "text": text})
        print(f"beat {i}: speech={dur:.2f}s total={beat_total:.2f}s")

    # Build concat list file
    listfile = os.path.join(SEG_DIR, "concat.txt")
    with open(listfile, "w") as f:
        for p in concat_parts:
            f.write(f"file '{p}'\n")

    narration = os.path.join(HERE, "narration.wav")
    subprocess.run(
        [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c", "copy", narration],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    total = LEAD_IN + sum(t["duration"] for t in timings)
    manifest = {"lead_in": LEAD_IN, "gap": GAP, "total": round(total, 3),
                "beats": timings}
    with open(os.path.join(HERE, "timings.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nnarration.wav total ~= {total:.2f}s")
    print("wrote timings.json")


if __name__ == "__main__":
    main()
