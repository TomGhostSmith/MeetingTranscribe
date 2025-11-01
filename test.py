import os
import json
import subprocess
from tqdm import tqdm
from faster_whisper import WhisperModel

# create a m3u8 file
# ffmpeg -i sample.mp4 -i sample.vtt -map 0:v -map 0:a -map 1:s -c:v copy -c:a copy -c:s webvtt -muxdelay 0 -f hls -hls_time 10 -hls_list_size 0 -hls_segment_filename "segment_%03d.ts" sample.m3u8

def getVideoLength(filePath):
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json', filePath
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(json.loads(result.stdout)['format']['duration'])
    return duration

def formatTime(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    time_formatted = f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    return time_formatted

def extractAudio(videoFile, audioFile):
    cmd = f'ffmpeg -i {videoFile} -vn -acodec libmp3lame -ac 1 {audioFile}'
    subprocess.run(cmd, shell=True)

def transcribe(videoFile, vttFile, scriptFile):
    # Load model (large-v2 or large-v3 for best accuracy)
    model = WhisperModel("model/faster-whisper-large-v3", device="cuda", compute_type="float16")

    prompt = (
        "This is a group meeting with 诗涛 "
        "They are discussing a paper in metagenomic fields."
    )


    # Transcribe audio file
    segments, info = model.transcribe(videoFile, beam_size=5, vad_filter=True, initial_prompt=prompt)
    videoLength = getVideoLength(videoFile)

    vttFP = open(vttFile, 'wt')
    scriptFP = open(scriptFile, 'wt')
    vttFP.write("WEBVTT\n")
    pbar = tqdm(total=videoLength, unit="sec", desc="transcribe")
    lastEnd = 0
    for segment in segments:
        vttFP.write(f"\n{formatTime(segment.start)} --> {formatTime(segment.end)}\n")
        vttFP.write(segment.text.strip() + "\n")

        scriptFP.write(f"{segment.text.strip()}\t{segment.start}\n")

        pbar.update(segment.end - lastEnd)
        lastEnd = segment.end
        # print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}")

    pbar.close()
    return 

def generateM3U8(videoFile, vttFile, basename, cwd):
    cmd = f'ffmpeg -i {videoFile} -i {vttFile} -map 0:v -map 0:a -map 1:s -c:v copy -c:a copy -c:s webvtt -muxdelay 0 -f hls -hls_time 10 -hls_list_size 0 -hls_segment_filename "{basename}_%03d.ts" {basename}_video.m3u8'
    m3u8File = f"{cwd}/{basename}.m3u8"
    subprocess.run(cmd, cwd=cwd, shell=True)
    with open(m3u8File, 'wt') as fp:
        fp.write("#EXTM3U\n")
        fp.write("#EXT-X-VERSION:3\n\n")
        fp.write(f'#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Chinese",DEFAULT=YES,AUTOSELECT=YES,LANGUAGE="cn",URI="{basename}_video_vtt.m3u8"\n\n')
        fp.write('#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION=1920x1080,SUBTITLES="subs"\n')
        fp.write(f"{basename}_video.m3u8")
    return m3u8File

def main():
    videoFile = "/Data/Video/test/sample.mp4"
    fileName = os.path.basename(videoFile)
    cwd = os.path.dirname(videoFile)
    baseName = fileName[:fileName.rfind(".")]
    audioFile = f"{baseName}.mp3"
    vttFile = f"{baseName}.vtt"
    scriptFile = f"{baseName}.script"

    # transcribe:
    # extractAudio(videoFile, f"{cwd}/{audioFile}")
    transcribe(f"{cwd}/{audioFile}", f"{cwd}/{vttFile}", f"{cwd}/{scriptFile}")
    # m3u8File = generateM3U8(videoFile, vttFile, baseName, cwd)
    # print(m3u8File)

if (__name__ == "__main__"):
    main()