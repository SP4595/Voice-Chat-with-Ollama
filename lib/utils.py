import threading # python3 中用 threading 创建线程类
import time
import pyaudio
import wave

class isFinish:
    def __init__(
            self,
            lock : threading.Lock,
            isfinish : bool = False,
        ) -> None:
        '''
        线程锁 
        **锁的是代码块，而不是常数，我们保证同一个线程锁保护的代码块（可以是不同代码块），只要线程锁是同一个，那么就只能有一个线程执行这些代码块！**
        '''
        self.lock = lock # 线程锁
        self.isfinish : bool = isfinish

    def finish(
            self
        )->None:
        self.isfinish = True

    def need_wait(
            self
        )->None:
        self.isfinish = False


class WaitingThread(threading.Thread):
    def __init__(
            self,
            finish : isFinish,
            name :str= "wait thread"
        ) -> None:
        super().__init__(name = name)
        '''
        finish
        '''
        self.finish = finish
        self.element1 = ["|", "/","-","\\"] # 线程1使用
        self.count = 0 # 线程2使用

    def run(
            self
        ) -> None:
        '''
        打印转圈圈
        '''
        count : int = 0
        while not self.finish.isfinish:
            print(self.element1[count%len(self.element1)], end="\r")
            time.sleep(0.2)
            count += 1
            
