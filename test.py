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
    subprocess.run(cmd, shell=True)

def transcribeWithWhisperX(audioFile):  # problem: whisperX will change the text!!!
    device = "cuda"
    prompt = (
        "This is a group meeting with 诗涛 "
        "They are discussing a paper in metagenomic fields."
    )

    model = whisperx.load_model("model/faster-whisper-large-v3", device=device, compute_type="float16", asr_options={
        "beam_size": 5,
        "initial_prompt": prompt
    })
    audio = whisperx.load_audio(audioFile)

    result = model.transcribe(audio)

    # 3. Assign speaker labels
    diarize_model = DiarizationPipeline("model/speaker-diarization-3.1/config.yaml", use_auth_token=getHFToken(), device=device)

    # add min/max number of speakers if known
    diarize_segments = diarize_model(audio)
    diarize_model(audio, min_speakers=3, max_speakers=3)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    print(diarize_segments)
    print(result["segments"]) # segments are now assigned speaker IDs
    return

def transcribe(audioFile, vttFile, scriptFile):
    device = "cuda"
    prompt = (
        "This is a group meeting with 诗涛 "
        "They are discussing a paper in metagenomic fields."
    )
    # model = WhisperModel("model/faster-whisper-large-v3", device="cuda", compute_type="float16")

    # segments, info = model.transcribe(audioFile, beam_size=5, vad_filter=True, initial_prompt=prompt)

    # videoLength = getVideoLength(audioFile)

    # # vttFP = open(vttFile, 'wt')
    # # scriptFP = open(scriptFile, 'wt')
    # # vttFP.write("WEBVTT\n")
    speakerFP = open("working/speaker.txt", 'wt')
    # pbar = tqdm(total=videoLength, unit="sec", desc="transcribe")
    # lastEnd = 0
    # for segment in segments:
    #     print(segment.text.strip() + ", " + str(segment.start) + ", " + str(segment.end))
    #     # vttFP.write(f"\n{formatTime(segment.start)} --> {formatTime(segment.end)}\n")
    #     # vttFP.write(segment.text.strip() + "\n")

    #     # scriptFP.write(f"{segment.text.strip()}\t{segment.start}\n")

    #     pbar.update(segment.end - lastEnd)
    #     lastEnd = segment.end
    #     # print(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}")

    # pbar.close()

    pipeline = Pipeline.from_pretrained("model/speaker-diarization-community-1")

    # send pipeline to GPU (when available)
    pipeline.to(torch.device("cuda"))

    # pipeline._pipelines["segmentation"].min_duration_on = 5.0  # minimum speech segment duration (seconds)
    # pipeline._pipelines["segmentation"].min_duration_off = 0.3 # minimum silence between segments
    # pipeline._pipelines["segmentation"].step = 0.5            # step size between analysis frames
    # pipeline._pipelines.pop("resegmentation", None)

    # apply pretrained pipeline (with optional progress hook)
    with ProgressHook() as hook:
        # output = pipeline(audioFile, hook=hook)  # runs locally
        output = pipeline(audioFile, hook=hook, num_speakers=4)  # runs locally

    # print the result
    for turn, speaker in output.speaker_diarization:
        speakerFP.write(f"{turn.start:.2f}\t{turn.end:.2f}\t{speaker}\n")
        # print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")


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
    extractAudio(videoFile, f"{cwd}/{audioFile}")
    transcribe(f"{cwd}/{audioFile}", f"{cwd}/{vttFile}", f"{cwd}/{scriptFile}")
    # m3u8File = generateM3U8(videoFile, vttFile, baseName, cwd)
    # print(m3u8File)

if (__name__ == "__main__"):
    main()