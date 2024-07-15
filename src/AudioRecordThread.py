import threading
import pyaudio
import numpy as np
from queue import Queue
from vosk import Model, KaldiRecognizer
import torch
import os
import sys
import VoiceRecognizer
import json

# 获取当前脚本所在目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 将父目录添加到系统路径
sys.path.append(parent_dir)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class AudioStreamThread(threading.Thread):
    """
    用于音频流处理和语音活动检测的线程。
    注意，该线程将会负责进行语音识别！
    """
    def __init__(
        self, 
        recongnize_shared_queue : Queue[str], 
        process_done_event : threading.Event,
        auto_stop : bool = True,
    ) -> None:
        super().__init__()
        self.recongnize_shared_queue = recongnize_shared_queue
        self.process_done_event = process_done_event
        self.auto_stop = auto_stop
        
        # 设置音频参数
        self.RATE = 16000
        
        # 初始化 Vosk 语音识别模型
        self.model = Model("./model/vosk-model-small-cn-0.22")
        self.rec = KaldiRecognizer(self.model, self.RATE) 
        
    def run(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        audio_interface = pyaudio.PyAudio()

        # 打开音频流
        stream = audio_interface.open(
            format=FORMAT, 
            channels=CHANNELS, 
            rate=self.RATE,
            input=True,
            frames_per_buffer=8000
        )

        print("## Start Recording ##")

        while True:
            frame = stream.read(4000, exception_on_overflow=False)
            if self.rec.AcceptWaveform(frame):
                # 识别到完整的语句
                result : dict[str, str] = json.loads(self.rec.Result())
                if result.get('text', ''):
                    user_instruct = result['text'].replace(" ", "")
                    if len(user_instruct) > 1:
                        self.recongnize_shared_queue.put(user_instruct)
                        if self.auto_stop:
                            self.process_done_event.wait() # 如果 process event 是 未设置 （没有调用  .set()） 就开始阻塞线程
                            self.process_done_event.clear() # 停止阻塞线程（恢复为未设置，直到调用 .set()）

        # 后续有停止手段了再说 #
        # stream.stop_stream()
        #stream.close()
        # audio_interface.terminate()
        # print("## Recording Stopped ##")




if __name__ == "__main__":
    # 初始化共享队列
    shared_queue = Queue(maxsize=4)
    # 启动音频处理线程
    audio_thread = AudioStreamThread(shared_queue, threading.Event(), auto_stop=False)
    audio_thread.start()
    while True:
        if not shared_queue.empty():
            print("start read")
            print(f"[Queue length: {shared_queue.qsize()}]{shared_queue.get(timeout=1)}")

