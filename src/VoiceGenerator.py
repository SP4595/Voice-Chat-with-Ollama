import wave
import torch
from typing import Any
import pyaudio
import numpy as np
import requests
from io import BytesIO
from pydub import AudioSegment
import simpleaudio as sa

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")



class VoiceGenerator:
    '''
    使用 GPT-sovits 的API服务（本地）
    api地址与端口 : http://127.0.0.1:9880
    '''
    def __init__(
        self,
        url : str = "http://127.0.0.1:9880",
        promt_text_path : str = "./data/voice_text_pear/text.txt",
        promt_wav_path : str = "C:\\Users\\Administrator\\Desktop\\Voice-Chat-with-Ollama\\data\\voice_text_pear\\voice.wav",
        prompt_language : str = "all_ja"
    ) -> None:
        self.url = url # 记录
        self.promt_text_path = promt_text_path
        self.promt_wav_path = promt_wav_path
        with open(promt_text_path, "r", encoding='utf-8') as f:
            prompt = f.read()

        self.prompt_text = prompt
        
        self.prompt_language = prompt_language
        
    def text2audio(
        self,
        text : str,
        text_language : str = 'auto',
        play_audio : bool = True
    ) -> requests.Response:
        '''
        Generate audio
        '''
        data = {
            "refer_wav_path": self.promt_wav_path,
            "prompt_text": self.prompt_text,
            "prompt_language": self.prompt_language,
            "text": text,
            "text_language": text_language
        }
        response = requests.post(
            url=self.url,
            json=data
        )
        
        # 确保请求成功
        if response.status_code == 200:
            if play_audio:
                self.audioplay(response)
            
            return response 
        
        
        
    def audioplay(
        self,
        response : requests.Response
    ) -> None:
    
        # 从响应中加载音频数据到 BytesIO 缓冲区
        audio_data = BytesIO(response.content)

        # 使用 pydub 从 BytesIO 对象加载音频
        audio = AudioSegment.from_file(audio_data, format="wav")

        # 导出到一个临时wav文件，或者直接从内存播放
        # audio.export("temp_audio.wav", format="wav")
        # wave_obj = sa.WaveObject.from_wave_file("temp_audio.wav")

        # 或者直接从内存播放
        wave_obj = sa.WaveObject(audio.raw_data, num_channels=audio.channels, bytes_per_sample=audio.sample_width, sample_rate=audio.frame_rate)

        # 播放音频
        play_obj = wave_obj.play()
        play_obj.wait_done()  # 等待音频播放完成



        
        
if __name__ == "__main__":
    generator = VoiceGenerator()
    text = ""
    while text != "end":
        text = input("请输入测试文本:\n")
        print("start")
        generator.text2audio(text, "zh")