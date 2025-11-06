import os
import json
import subprocess
from tqdm import tqdm
from faster_whisper import WhisperModel

import torch
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook

# import whisperx
# from whisperx.diarize import DiarizationPipeline

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

def getHFToken():
    with open("working/HF_TOKEN") as fp:
        token = fp.readline().strip()
    return token

def extractAudio(videoFile, audioFile):
    cmd = f'ffmpeg -i {videoFile} -vn -acodec libmp3lame -ar 16000 -ac 1 {audioFile}'
    # cmd = f'ffmpeg -i {videoFile} -vn -acodec libmp3lame -ar 16000 -ss 00:00:00 -to 00:05:00 -ac 1 {audioFile}'
    subprocess.run(cmd, shell=True)

def transcribe(audioFile, vttFile, scriptFile):
    device = "cuda"
    prompt = (
        "This is a group meeting with 诗涛 "
        "They are discussing a paper in metagenomic fields."
    )
    model = WhisperModel("model/faster-whisper-large-v3", device="cuda", compute_type="float16")

    segments, info = model.transcribe(audioFile, beam_size=5, vad_filter=True, initial_prompt=prompt)

    videoLength = getVideoLength(audioFile)

    scriptFP = open(scriptFile, 'wt')
    vttFP = open(vttFile, 'wt')
    vttFP.write("WEBVTT\n")
    speakerFP = open("working/speaker.txt", 'wt')

    # recognize speaker
    pipeline = Pipeline.from_pretrained("model/speaker-diarization-community-1")

    # send pipeline to GPU (when available)
    pipeline.to(torch.device("cuda"))

    # apply pretrained pipeline (with optional progress hook)
    with ProgressHook() as hook:
        # output = pipeline(audioFile, hook=hook)  # runs locally
        output = pipeline(audioFile, hook=hook, num_speakers=4)  # runs locally

    # print the result
    allSpeaker = set()
    speakerList = []
    for turn, speaker in output.speaker_diarization:
        speakerFP.write(f"{turn.start:.2f}\t{turn.end:.2f}\t{speaker}\n")
        speakerList.append([turn.start, turn.end, speaker])
        # print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        allSpeaker.add(speaker)

    speakerFP.close()


    pbar = tqdm(total=videoLength, unit="sec", desc="transcribe")
    lastEnd = 0
    lastSpeaker = None
    lastSpeakerSegIdx = 0
    for segment in segments:
        # print(segment.text.strip() + ", " + str(segment.start) + ", " + str(segment.end))
        vttFP.write(f"\n{formatTime(segment.start)} --> {formatTime(segment.end)}\n")
        vttFP.write(segment.text.strip() + "\n")


        # calculate speaker
        durations = {s: 0 for s in allSpeaker}

        # add the final segment
        # start, end, speaker = speakerList[lastSpeakerSegIdx]
        coveredEnd = segment.start
        # if (end > segment.end):
        #     thisSpeaker = speaker
        # else:
        #     if (end > segment.start):
        #         realDuration = end - max(start, segment.start)
        #         durations[speaker] += realDuration
        #         coveredEnd = end
        #     lastSpeakerSegIdx += 1
        while coveredEnd < segment.end:
            start, end, speaker = speakerList[lastSpeakerSegIdx]
            if (start > segment.end):
                break
            realDuration = min(end, segment.end) - max(start, coveredEnd)
            durations[speaker] += realDuration
            coveredEnd = end
            if (end <= segment.end):
                lastSpeakerSegIdx += 1

        thisSpeaker = max(durations, key=durations.get)
        if thisSpeaker != lastSpeaker or segment.start - lastEnd > 5:
            scriptFP.write(f"{thisSpeaker}\n")
            lastSpeaker = thisSpeaker

        scriptFP.write(f"{segment.text.strip()}\t{segment.start}\t{segment.end}\n")

        pbar.update(segment.end - lastEnd)
        lastEnd = segment.end

    pbar.close()
    scriptFP.close()




    
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
    audioFile = f"{baseName}.wav"
    vttFile = f"{baseName}.vtt"
    scriptFile = f"{baseName}.script"

    # transcribe:
    # extractAudio(videoFile, f"{cwd}/{audioFile}")
    transcribe(f"{cwd}/{audioFile}", f"{cwd}/{vttFile}", f"{cwd}/{scriptFile}")
    # extractAudio(videoFile, f"working/test.wav")
    # transcribe(f"working/test.wav", f"working/test.vtt", f"working/test.script")
    # m3u8File = generateM3U8(videoFile, vttFile, baseName, cwd)
    # print(m3u8File)

if (__name__ == "__main__"):
    main()