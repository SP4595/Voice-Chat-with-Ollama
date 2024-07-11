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
    注意，该线程不负责进行语音识别活动！
    """
    def __init__(
        self, 
        shared_queue : Queue, 
        silence_duration_ms : int = 1000,
        max_speaking_duration_ms : int = 15000, 
        auto_stop : bool = True
    ) -> None:
        super().__init__()
        self.shared_queue = shared_queue
        self.silence_duration_ms = silence_duration_ms
        self.max_speaking_duration_ms = max_speaking_duration_ms
        self.auto_stop = auto_stop
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(3) # 0， 1， 2， 3 三个敏感模式， 3 最不敏感
        
    def save_and_reset(
        self, 
        total_frames : list
    ) -> None:
        """将记录的音频帧转换为numpy数组，存入队列，并重置帧列表。"""
        if total_frames:
            audio_data = b''.join(total_frames)
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            self.shared_queue.put(audio_array)
            total_frames.clear() # 更新 total_frames

    def run(self):
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK_DURATION_MS = 30
        CHUNK_SIZE = int(RATE * CHUNK_DURATION_MS / 1000)
        MAX_RECORD_CHUNKS = int(self.max_speaking_duration_ms / CHUNK_DURATION_MS) # 最大CHUNK记录长度
        MAX_SILENCE_CHUNKS = int(self.silence_duration_ms / CHUNK_DURATION_MS) # 判断如果3秒内不说话就是停止录音
        
        audio_interface = pyaudio.PyAudio()
        
        stream = audio_interface.open(
            format = FORMAT, 
            channels = CHANNELS, 
            rate = RATE,
            input = True,
            frames_per_buffer = CHUNK_SIZE
        )

        print("开始录音，请说话")
        is_speaking = False
        frame_buffer = collections.deque(maxlen=MAX_SILENCE_CHUNKS)
        total_frames = []

        while True:
            frame = stream.read(CHUNK_SIZE)
            is_speech = self.vad.is_speech(frame, RATE)
            frame_buffer.append(is_speech)
            total_frames.append(frame)

            if len(total_frames) >= MAX_RECORD_CHUNKS:
                print("录音时间达到最大限制，正在保存数据")
                self.save_and_reset(total_frames)
                frame_buffer.clear()

            if is_speech:
                if not is_speaking:
                    print("检测到说话")
                    is_speaking = True
            else:
                if is_speaking and self.auto_stop:
                    if all(not speech for speech in frame_buffer):
                        print("检测到停止说话")
                        is_speaking = False
                        self.save_and_reset(total_frames)
                        frame_buffer.clear()

        stream.stop_stream()
        stream.close()
        audio_interface.terminate()


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

