import warnings
warnings.filterwarnings('ignore')
from ChatLangChain import OllamaThread
from AudioRecordThread import AudioStreamThread
from AudioGenerateThread import AudioGenerateThread
from queue import Queue
import numpy as np
import threading
from AudioPlayerThread import AudioPlayerThread
from requests import Response
import os
import sys
import json

# 获取当前脚本所在目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 将父目录添加到系统路径
lib_dir = os.path.join(parent_dir)
sys.path.append(lib_dir)

VOICE_PATH = "./data/voice_text_pear/"
ABS_VOICE_PATH = os.path.abspath(VOICE_PATH) # Get absolute path

class Main(threading.Thread):
    def __init__(
        self,
        model_name : str = "phi3:3.8b",
        base_url : str = "https://127.0.0.1:11434",
    ) -> None:
        '''
        由四级 thread 流水线和三个 queue 组成的主类
        '''
        super().__init__()
        self.recongnize_shared_queue : Queue[np.ndarray] = Queue() # Audio 识别任务队列
        self.generate_shared_queue : Queue[str] = Queue() # Text 生成 Audio 任务队列
        self.audio_play_queue : Queue[Response] = Queue()# Audio 播放队列
        self.process_done_event = threading.Event() # 确保 process 完成了
       
        
        self.recongnizer_thread = AudioStreamThread(
            recongnize_shared_queue = self.recongnize_shared_queue,
            process_done_event = self.process_done_event
        )
        
        self.chat_thread = OllamaThread(
            run_mod = "audio",
            input_recongnize_shared_queue = self.recongnize_shared_queue,
            output_generate_shared_queue = self.generate_shared_queue,
            process_done_event = self.process_done_event,
            base_url= base_url, # 服务器
            model= model_name,
            force_intialize_client = True
        )
        
        print("# Initializing LLM Server ... #")
        
        self.chat_thread.client.invoke([{"role" : "user", "content" : " "}]) # 强制初始化线程内部模型
        
        print("# Initializing Voice Recognizer ... #")
        
        self.chat_thread.voice_recongnizer.recognize_wav(
            voice_file_path = "./data/voice_text_pear/voice.wav",
            print_outcome = False
        ) # 强制初始化 recognizer
        
        
        
        self.voice_generator_thread = AudioGenerateThread(
            generate_shared_queue = self.generate_shared_queue, 
            audio_play_queue=self.audio_play_queue,
            process_done_event = self.process_done_event,
            absolute_pair_path = ABS_VOICE_PATH  
        )
        
        print("# Initializing TTS Server ... #")
        
        self.voice_generator_thread.generater.text2audio(
            text = "a", 
            play_audio = False
        ) # 强制初始化 generator
        
        self.player_thread = AudioPlayerThread(
            self.audio_play_queue,
            process_done_event = self.process_done_event
        )
        
    def run(self) -> None:
        self.recongnizer_thread.start()
        self.chat_thread.start()
        self.voice_generator_thread.start()
        self.player_thread.start()
            
if __name__ == "__main__":
    print("''''\nInithialize server...\n''''")
    with open("config.json", "r") as f:
        config = json.load(f)
    main_thread = Main(
        model_name = config["OllamaModel"],
        base_url = config["base_url"]
    )
    main_thread.start()
    main_thread.join()