from VoiceGenerator import VoiceGenerator
import os
import sys
from threading import Thread
from collections import deque
import threading
from queue import Queue, Empty
from requests import Response


class AudioGenerateThread(Thread):
    def __init__(
        self,
        generate_shared_queue : Queue[str],
        audio_play_queue : Queue[Response] # Audio player 生成任务队列
    ) -> None:
        '''
        用deque + split 模拟流式输出
        '''
        super().__init__()
        self.generater = VoiceGenerator()
        self.process_deque : deque[str] = deque() # deque 支持 iterable 直接插入 deque 故比 for 循环快很多
        self.task_queue = generate_shared_queue
        self.audio_play_queue = audio_play_queue
        
    def run(self) -> None:
        '''
        线程开始
        '''   
                
        while True:
            try:
                # 从队列中获取string，如果队列为空则阻塞（这样比检查 empty 更安全！）
                content = self.task_queue.get(timeout=3)  # 设置超时以允许检查运行标志
                response = self.generater.text2audio(
                    text = content,
                    play_audio = False
                )
                self.audio_play_queue.put(response)
                 
            except Empty:
                continue  # 队列为空时继续循环
        