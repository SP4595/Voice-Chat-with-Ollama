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
        task_queue : Queue[requests.Response],
        process_done_event : threading.Event
    ) -> None:
        super().__init__()
        self.task_queue = task_queue
        self.process_done_event = process_done_event

    def audioplay(self, response: requests.Response) -> None:
        # 从响应中加载音频数据到 BytesIO 缓冲区
        audio_data = BytesIO(response.content)
        # 使用 pydub 从 BytesIO 对象加载音频
        audio : AudioSegment = AudioSegment.from_file(audio_data, format="wav")
        
        #  获取音频的原始数据
        raw_data = audio.raw_data

        # 获取音频的采样率和样本宽度
        sample_rate = audio.frame_rate
        sample_width = audio.sample_width
        num_channels = audio.channels

        # 使用 simpleaudio 播放音频
        play_obj = sa.play_buffer(raw_data, num_channels, sample_width, sample_rate) # 如果不wait的话这个默认开启新线程播放，本线程就继续执行了！

        # 等待音频播放完毕
        play_obj.wait_done()

    def run(self) -> None:
        while True:
            try:
                # 从队列中获取响应，如果队列为空则阻塞（这样比检查 empty 更安全！）
                response = self.task_queue.get(timeout=3)  # 设置超时以允许检查运行标志
                if response == None: # 空了(最后一个 None 标记结尾)
                    print("# End Response #\n# Please Speak #:") # 解除阻塞，开始下一个循环
                    self.process_done_event.set() # 只在完成任务时设置一次event，闲置的时候不会设置event！
                    continue # empty了
                    
                self.audioplay(response)
                self.task_queue.task_done()  # 标记任务完成
            except Empty:
                # 队列为空
                # 切记不要在这里设置event，因为这样每次 queue 中没有东西都会出问题！
                continue  # 队列为空时继续循环