"""Draft FMV speech transcripts: XA audio from each raw STR dump through faster-whisper, plus frame sheets every 2 s.

usage: fmv_transcribe.py STR_DIR OUT_DIR [--movies MOVIE00 ...] [--no-whisper] [--no-sheets]
STR_DIR holds MOVIExx.raw from tools/str_frames.py. Writes OUT_DIR/MOVIExx.wav, MOVIExx.whisper.tsv
(start, end, avg_logprob, no_speech_prob, text) and OUT_DIR/MOVIExx/sheet_NN.png. Output is a draft for a human
or agent pass, never the script itself: Whisper mishears names and invents lines over music."""
import argparse
import os
import subprocess
import sys
import wave

import numpy as np


def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        sys.exit(f"{cmd[0]} failed: {r.stderr[-400:]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("strs")
    ap.add_argument("out")
    ap.add_argument("--movies", nargs="*")
    ap.add_argument("--no-whisper", action="store_true")
    ap.add_argument("--no-sheets", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = a.movies or sorted(f[:-4] for f in os.listdir(a.strs) if f.endswith(".raw"))
    model = None
    for name in names:
        raw = os.path.join(a.strs, name + ".raw")
        wav = os.path.join(a.out, name + ".wav")
        if not a.no_sheets:
            d = os.path.join(a.out, name)
            os.makedirs(d, exist_ok=True)
            # drawtext would need a font path on Windows; sheet order gives time: cell n of sheet k = 2*((k-1)*30+n) seconds
            run("ffmpeg", "-y", "-loglevel", "error", "-f", "psxstr", "-i", raw, "-an", "-vf",
                "fps=1/2,scale=200:-1,tile=6x5:padding=2", os.path.join(d, "sheet_%02d.png"))
        if a.no_whisper:
            continue
        run("ffmpeg", "-y", "-loglevel", "error", "-f", "psxstr", "-i", raw, "-vn", "-ac", "1", "-ar", "16000", wav)
        if model is None:
            from faster_whisper import WhisperModel
            # CPU: CTranslate2 finds the GPU here but cublas64_12.dll is missing
            model = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
        with wave.open(wav) as w:  # samples, not the path: this PyAV rejects faster-whisper's open() arguments
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        # VAD off: platform-ps1.md, lines went missing with it on. No previous-text conditioning: it loops over music.
        # No initial_prompt: over 8 movies' music-heavy first 30 s it came back verbatim in place of the speech.
        segs, _ = model.transcribe(pcm, language="ja", vad_filter=False, beam_size=5, word_timestamps=True,
                                   condition_on_previous_text=False, no_speech_threshold=None)
        with open(os.path.join(a.out, name + ".whisper.tsv"), "w", encoding="utf-8", newline="\n") as f:
            for s in segs:
                f.write(f"{s.start:.2f}\t{s.end:.2f}\t{s.avg_logprob:.2f}\t{s.no_speech_prob:.2f}\t{s.text.strip()}\n")
        print(name, "done", flush=True)


if __name__ == "__main__":
    main()
