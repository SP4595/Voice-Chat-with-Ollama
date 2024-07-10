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
            
def voice_intput() -> None:
    # 音频录制参数
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "./data/voice/output.wav"

    # 初始化PyAudio
    p = pyaudio.PyAudio()

    # 打开音频流
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("开始录音")
    frames = []

    # 录制音频数据
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("录音结束")

    # 停止和关闭流
    stream.stop_stream()
    stream.close()
    p.terminate()

    # 将录制的音频数据保存到文件
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()