import threading
import pyaudio
import webrtcvad
import collections
import numpy as np
from queue import Queue
from VoiceRecognizer import VoiceRecognizer
import speechbrain as sb

class AudioStreamThread(threading.Thread):
    """
    用于音频流处理和语音活动检测的线程。
    注意，该线程不负责进行语音识别！
    """
    def __init__(
        self, 
        recongnize_shared_queue : Queue, 
        process_done_event : threading.Event,
        start_recognize_duration_bar_ms : int = 60,
        end_recognize_duration_bar_ms : int = 1000,
        max_speaking_duration_ms : int = 20000, 
        auto_stop : bool = True
    ) -> None:
        super().__init__()
        self.recongnize_shared_queue = recongnize_shared_queue
        self.start_recognize_duration_bar_ms = start_recognize_duration_bar_ms
        self.end_recognize_duration_bar_ms = end_recognize_duration_bar_ms
        self.max_speaking_duration_ms = max_speaking_duration_ms
        self.auto_stop = auto_stop
        self.vad = webrtcvad.Vad()
        
        self.process_done_event = process_done_event # event 开始
        self.vad.set_mode(3) # 0， 1， 2， 3 三个敏感模式， 3 最不敏感
        self.finish = False # 结束识别了吗？
        
    def save_and_reset(
        self, 
        total_frames : list
    ) -> None:
        """将记录的音频帧转换为numpy数组，存入队列，并重置帧列表。"""
        if total_frames:
            audio_data = b''.join(total_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            self.recongnize_shared_queue.put(audio_array)
            total_frames.clear() # 更新 total_frames

    def run(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK_DURATION_MS = 30
        CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
        MAX_RECORD_CHUNKS = int(self.max_speaking_duration_ms / CHUNK_DURATION_MS) # 最大CHUNK记录长度
        START_MAX_DURATION_CHUNKS = int(self.start_recognize_duration_bar_ms / CHUNK_DURATION_MS) # 判断如果3秒内不说话就是停止录音
        END_MAX_DURATION_CHUNKS = int(self.end_recognize_duration_bar_ms / CHUNK_DURATION_MS) # 判断如果3秒内不说话就是停止录音
        
        audio_interface = pyaudio.PyAudio()
        
        stream = audio_interface.open(
            format = FORMAT, 
            channels = CHANNELS, 
            rate = RATE,
            input = True,
            frames_per_buffer = CHUNK_SIZE
        )

        print("## Start Recording ##")
        is_speaking = False
        start_frame_buffer = collections.deque(maxlen=START_MAX_DURATION_CHUNKS)
        end_frame_buffer = collections.deque(maxlen=END_MAX_DURATION_CHUNKS)
        total_frames = []

        while True:
            
            frame = stream.read(CHUNK_SIZE)
            
            is_speech = self.vad.is_speech(frame, RATE)
            
            start_frame_buffer.append(is_speech)
            end_frame_buffer.append(is_speech)
            
            if len(start_frame_buffer) == start_frame_buffer.maxlen and all(speech for speech in start_frame_buffer): # 至少说 10 ms 才会被识别！(且必须等 buffer 已满)
                if not is_speaking:
                    print("# Speech start detect #")
                    is_speaking = True # 标记开始
                    start_frame_buffer.clear()
            
            if is_speaking and is_speech: # 必须要开始识别才能开始记录
                total_frames.append(frame)

            if len(total_frames) >= MAX_RECORD_CHUNKS:
                print("# Record Time Limit Reached, Start Saving ... #")
                self.save_and_reset(total_frames)
                start_frame_buffer.clear()
                end_frame_buffer.clear()
                self.finish = True
        
            else:
                if is_speaking and self.auto_stop:
                    if len(end_frame_buffer) == end_frame_buffer.maxlen and all(not speech for speech in end_frame_buffer):
                        print("# Speech end detect #")
                        is_speaking = False
                        self.save_and_reset(total_frames)
                        end_frame_buffer.clear()
                        self.finish = True # 标记结束
                        
            if self.finish:
                # 一旦录音结束，立刻阻塞线程！
                print("# Record stop, Start processing #") # 阻塞线程
                self.process_done_event.wait() # 如果 process event 是 未设置 （没有调用  .set()） 就开始阻塞线程
                self.process_done_event.clear() # 停止阻塞线程（恢复为未设置，直到调用 .set()）
                self.finish = False # 归位


if __name__ == "__main__":
    # 初始化共享队列
    shared_queue = Queue(maxsize=4)
    recongnizer = VoiceRecognizer()
    # 启动音频处理线程
    audio_thread = AudioStreamThread(shared_queue)
    audio_thread.start()
    while True:
        if not shared_queue.empty():
            print("start read")
            get = shared_queue.get(timeout=1)
            print(f"[Queue length: {shared_queue.qsize()}]{recongnizer.recognize(get)}")

