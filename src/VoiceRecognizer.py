from faster_whisper import WhisperModel
import os
import numpy as np
import librosa

# 设置环境变量以允许多个库同时加载
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"

# 初始化模型并配置运行设备

class VoiceRecognizer():
    def __init__(
        self,
        model_size : str = "large-v3"
    ) -> None:
        self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
    
    def preprocess_audio(
        self,
        audio : np.ndarray, 
        original_rate : int
    ) -> np.ndarray:
        # 重新采样为 16000 Hz
        if original_rate != 16000:
            audio = librosa.resample(audio, orig_sr=original_rate, target_sr=16000)
        return audio

    def recognize(
        self,
        audio : np.ndarray,
        original_rate : int = 16000, 
    ) -> str:
        '''
        ### Usage:
        Convert voice to string
        '''
        

        # 将录音数据转换为适合Whisper模型的格式（如果需要）
        # 例如，使用ffmpeg将音频重采样到16000 Hz单声道
        # 这部分代码未展示，假设输出文件为processed_output.wav

        # 读取处理后的音频文件，使用Whisper模型进行语音识别
        # with open(voice_file_path, "rb") as audio_file:
        print("start recongnize")
        audio = self.preprocess_audio(audio, original_rate)
        segments, info = self.model.transcribe(audio, beam_size=5)

        # print("Detected language: '%s' with probability %f" % (info.language, info.language_probability))

        return_str = ""

        for segment in segments:
            # print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            return_str += segment.text + " "
        print("end recongnize")
        return return_str
    
    def recognize_wav(
        self,
        voice_file_path : str,
        original_rate : int = 16000, 
    ) -> str:
        '''
        ### Usage:
        Convert voice to string
        '''
        

        # 将录音数据转换为适合Whisper模型的格式（如果需要）
        # 例如，使用ffmpeg将音频重采样到16000 Hz单声道
        # 这部分代码未展示，假设输出文件为processed_output.wav

        # 读取处理后的音频文件，使用Whisper模型进行语音识别
        # with open(voice_file_path, "rb") as audio_file:
        audio, sr = librosa.load(voice_file_path, sr=None)
        segments, info = self.model.transcribe(audio, beam_size=5)

        # print("Detected language: '%s' with probability %f" % (info.language, info.language_probability))

        return_str = ""

        for segment in segments:
            print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            return_str += segment.text + " "
            
        return return_str
    
if __name__ == "__main__":
    a = VoiceRecognizer()
    print(a.recognize_wav("./data/voice/test.wav"))
        
