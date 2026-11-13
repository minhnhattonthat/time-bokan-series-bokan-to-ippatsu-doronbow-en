"""Second Whisper pass on a clip of a movie wav (from fmv_transcribe.py), times printed movie-relative.

usage: fmv_clip.py work/fmv/MOVE04.wav START END   (prints start, end, avg_logprob, text)"""
import os
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

wav, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
with wave.open(wav) as w:
    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
pcm = pcm[int(a * 16000):int(b * 16000)]
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
segs, _ = m.transcribe(pcm, language="ja", vad_filter=False, beam_size=5, condition_on_previous_text=False,
                       no_speech_threshold=None)
for s in segs:
    print(f"{s.start + a:.2f}\t{s.end + a:.2f}\t{s.avg_logprob:.2f}\t{s.text.strip()}")
