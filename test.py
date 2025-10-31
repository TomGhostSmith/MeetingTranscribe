from faster_whisper import WhisperModel

# create a m3u8 file
# ffmpeg -i sample.mp4 -i sample.vtt -map 0:v -map 0:a -map 1:s -c:v copy -c:a copy -c:s webvtt -muxdelay 0 -f hls -hls_time 10 -hls_list_size 0 -hls_segment_filename "segment_%03d.ts" sample.m3u8

def formatTime(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    time_formatted = f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    return time_formatted

# Load model (large-v2 or large-v3 for best accuracy)
model = WhisperModel("model/faster-whisper-large-v3", device="cuda", compute_type="float16")

prompt = (
    "This is a group meeting with 诗涛 "
    "They are discussing a paper in metagenomic fields."
)

# Transcribe audio file
segments, info = model.transcribe("/Data/Video/test/sample.mp3", beam_size=5, vad_filter=True, initial_prompt=prompt)

results = []
print("WEBVTT")
for segment in segments:
    print(f"\n{formatTime(segment.start)} --> {formatTime(segment.end)}")
    print(segment.text.strip())
    # print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}")


    # results.append({
    #     "start": segment.start,
    #     "end": segment.end,
    #     "text": segment.text.strip()
    # })

# Print or save results
# for r in results: