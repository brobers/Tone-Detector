import json, numpy as np, pyaudio, wave, RPi.GPIO as GPIO, time, os, datetime

# === Load configuration ===
CONFIG_FILE = "config.json"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"Missing {CONFIG_FILE}")
with open(CONFIG_FILE) as f:
    cfg = json.load(f)

PIN_OUT = cfg["gpio_output_pin"]
RATE = cfg["sample_rate"]
CHUNK = cfg["chunk_size"]
TONE1 = cfg["tones"]["tone1"]
TONE2 = cfg["tones"]["tone2"]
TOL = cfg["tone_tolerance"]
REQUIRED_TIME = cfg["tone_required_time"]
TIMEOUT_BETWEEN = cfg["timeout_between_tones"]
AUDIO_DEVICE_INDEX = cfg.get("audio_device_index")
RECORD_SECONDS = cfg.get("record_seconds", 40)
RECORD_DELAY = cfg.get("record_delay", 6)
PLAYBACK_TONES = cfg.get("playback_tones", [])

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_OUT, GPIO.OUT)
GPIO.output(PIN_OUT, 0)

p = pyaudio.PyAudio()

# --- Helpers ---
def generate_tone(freq, duration, rate=RATE):
    t = np.linspace(0, duration, int(rate * duration), endpoint=False)
    tone = 0.3 * np.sin(2 * np.pi * freq * t)
    return (tone * 32767).astype(np.int16)

def detect_tone(data, target_freq, tol, rate=RATE):
    fft = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(fft), 1.0 / rate)
    mag = np.abs(fft)
    idx = np.where((freqs >= target_freq - tol) & (freqs <= target_freq + tol))[0]
    return np.max(mag[idx]) if len(idx) else 0

# --- Playback ---
def play_tones(stream_out):
    print("Playing tones...")
    try:
        for tone_cfg in PLAYBACK_TONES:
            freq = tone_cfg["freq"]
            dur  = tone_cfg["duration"]
            tone = generate_tone(freq, dur)
            # Send in manageable chunks
            for i in range(0, len(tone), CHUNK):
                chunk = tone[i:i+CHUNK]
                stream_out.write(chunk.tobytes())
            time.sleep(0.05)
        print("Finished playing tones.")
    except Exception as e:
        print(f"Tone playback error: {e}")

def play_audio_file(stream_out, filename):
    print(f"Playing recorded file: {filename}")
    try:
        wf = wave.open(filename, 'rb')
        data = wf.readframes(CHUNK)
        while data:
            stream_out.write(data)
            data = wf.readframes(CHUNK)
        wf.close()
        print("Finished recorded playback.")
    except Exception as e:
        print(f"Audio playback error: {e}")

# --- Record ---
def record_audio(filename):
    print(f"Recording {RECORD_SECONDS}s...")
    p_in = pyaudio.PyAudio()
    stream_in = p_in.open(format=pyaudio.paInt16,
                          channels=1, rate=RATE,
                          input=True,
                          input_device_index=AUDIO_DEVICE_INDEX,
                          frames_per_buffer=CHUNK)
    frames=[]
    start=time.time()
    while time.time()-start<RECORD_SECONDS:
        frames.append(stream_in.read(CHUNK, exception_on_overflow=False))
    stream_in.stop_stream(); stream_in.close(); p_in.terminate()
    with wave.open(filename,'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))
    print(f"Saved recording {filename}")

# --- Listen ---
def listen_for_tones():
    print(f"Listening for {TONE1} Hz then {TONE2} Hz...")
    p_in = pyaudio.PyAudio()
    stream = p_in.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                       input=True, input_device_index=AUDIO_DEVICE_INDEX,
                       frames_per_buffer=CHUNK)
    state=0; tone1_time=None; threshold=1e6
    try:
        while True:
            samples=np.frombuffer(stream.read(CHUNK,exception_on_overflow=False),dtype=np.int16)
            samples=samples*np.hanning(len(samples))
            if state==0:
                if detect_tone(samples,TONE1,TOL)>threshold:
                    tone1_time=tone1_time or time.time()
                    if time.time()-tone1_time>=REQUIRED_TIME:
                        print(f"{TONE1}Hz detected"); state=1; tone1_time=time.time()
                else: tone1_time=None
            elif state==1:
                if detect_tone(samples,TONE2,TOL)>threshold:
                    print(f"{TONE2}Hz detected")
                    stream.stop_stream(); stream.close(); p_in.terminate(); return True
                elif time.time()-tone1_time>TIMEOUT_BETWEEN:
                    print("Timeout, restart"); state=0; tone1_time=None
    except KeyboardInterrupt:
        stream.stop_stream(); stream.close(); p_in.terminate(); GPIO.cleanup(); exit(0)

# --- Main loop ---
try:
    while True:
        if not listen_for_tones(): continue
        GPIO.output(PIN_OUT,1)
        print("Output triggered!")
        print(f"Waiting {RECORD_DELAY}s before recording...")
        time.sleep(RECORD_DELAY)

        timestamp=datetime.datetime.now().strftime("%y%m%d%H%M")
        filename=f"FD_disp_{timestamp}.wav"
        record_audio(filename)

        # open output stream as 16-bit PCM
        stream_out=p.open(format=pyaudio.paInt16, channels=1, rate=RATE,
                          output=True, output_device_index=AUDIO_DEVICE_INDEX,
                          frames_per_buffer=CHUNK)

        for i in range(2):
            print(f"Playback iteration {i+1}")
            play_tones(stream_out)
            play_audio_file(stream_out, filename)

        stream_out.stop_stream(); stream_out.close()
        GPIO.output(PIN_OUT,0)
        print("Cycle complete; listening again.\n")

except KeyboardInterrupt:
    GPIO.output(PIN_OUT,0)
    GPIO.cleanup()
    p.terminate()
    print("Exited cleanly.")

