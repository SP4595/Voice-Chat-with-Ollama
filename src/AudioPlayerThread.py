from io import BytesIO
import requests
from pydub import AudioSegment
import simpleaudio as sa
import threading
from queue import Queue, Empty # Empty 是一个 queue 专属异常
from pydub.playback import play

class AudioPlayerThread(threading.Thread):
    def __init__(
        self,
        task_queue : Queue[requests.Response]
    ) -> None:
        super().__init__()
        self.task_queue = task_queue

    def audioplay(self, response: requests.Response) -> None:
        # 从响应中加载音频数据到 BytesIO 缓冲区
        audio_data = BytesIO(response.content)
        # 使用 pydub 从 BytesIO 对象加载音频
        audio : AudioSegment = AudioSegment.from_file(audio_data, format="wav")
        play(audio)

    def run(self) -> None:
        while True:
            try:
                # 从队列中获取响应，如果队列为空则阻塞（这样比检查 empty 更安全！）
                response = self.task_queue.get(timeout=3)  # 设置超时以允许检查运行标志
                self.audioplay(response)
                self.task_queue.task_done()  # 标记任务完成
            except Empty:
                continue  # 队列为空时继续循环