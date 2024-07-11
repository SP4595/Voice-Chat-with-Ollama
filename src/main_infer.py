from ChatLangChain import OllamaThread
from AudioRecognizeThread import AudioStreamThread
from AudioGenerateThread import AudioGenerateThread
from queue import Queue
import numpy as np
import threading
from AudioPlayerThread import AudioPlayerThread
from requests import Response


class Main(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.recongnize_shared_queue : Queue[np.ndarray] = Queue() # Audio 识别任务队列
        self.generate_shared_queue : Queue[str] = Queue() # Text 生成 Audio 任务队列
        self.audio_play_queue : Queue[Response] = Queue()# Audio 播放队列
        
        self.chat_thread = OllamaThread(
            run_mod = "audio",
            input_recongnize_shared_queue = self.recongnize_shared_queue,
            output_generate_shared_queue = self.generate_shared_queue,
            base_url= "http://192.168.3.101:11434", # 服务器
            model= "qwen2:7b-instruct-fp16"  
        )
        self.chat_thread.send_message_sync("please output `Hello world` (do not output anything else!)") # 强制初始化模型
        
        self.recongnizer_thread = AudioStreamThread(
            self.recongnize_shared_queue,
            silence_duration_ms=3000
        )
        
        self.voice_generator_thread = AudioGenerateThread(
            generate_shared_queue = self.generate_shared_queue, 
            audio_play_queue=self.audio_play_queue  
        )
        
        self.player_thread = AudioPlayerThread(self.audio_play_queue)
        
    def run(self) -> None:
        self.recongnizer_thread.start()
        self.chat_thread.start()
        self.voice_generator_thread.start()
        self.player_thread.start()
            
if __name__ == "__main__":
    main_thread = Main()
    main_thread.start()
    main_thread.join()