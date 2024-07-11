from ChatLangChain import OllamaThread
from AudioRecognizeThread import AudioStreamThread
from AudioGenerateThread import AudioGenerateThread
from queue import Queue
import numpy as np
import threading
from AudioPlayerThread import AudioPlayerThread
from requests import Response
import os
import sys

# 获取当前脚本所在目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 将父目录添加到系统路径
lib_dir = os.path.join(parent_dir)
sys.path.append(lib_dir)

from lib.utils import isFinish

class Main(threading.Thread):
    def __init__(self) -> None:
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
            silence_duration_ms = 3000,
            process_done_event = self.process_done_event
        )
        
        self.chat_thread = OllamaThread(
            run_mod = "audio",
            input_recongnize_shared_queue = self.recongnize_shared_queue,
            output_generate_shared_queue = self.generate_shared_queue,
            process_done_event = self.process_done_event,
            base_url= "http://192.168.3.101:11434", # 服务器
            model= "qwen2:72b",
            force_intialize_client = True
        )
        self.chat_thread.client.invoke([{"role" : "user", "content" : " "}]) # 强制初始化线程内部模型
        self.voice_generator_thread = AudioGenerateThread(
            generate_shared_queue = self.generate_shared_queue, 
            audio_play_queue=self.audio_play_queue,
            process_done_event = self.process_done_event  
        )
        
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
    main_thread = Main()
    main_thread.start()
    main_thread.join()