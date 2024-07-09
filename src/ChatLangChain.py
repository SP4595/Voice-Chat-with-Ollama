from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from typing import Literal # Listeral 是给 IDLE (VSCODE) 的 hint， 告诉他我的输入一定要在Literal里面
from typing import Union # Union 是给 IDLE 的 hint, 标定输出的可能性
import sys
import os

# 获取当前脚本所在目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 将父目录添加到系统路径
lib_dir = os.path.join(parent_dir)
sys.path.append(lib_dir)

from lib.utils import WaitingThread, isFinish

import json
import threading # python3 中用 threading 创建线程类
import time
import asyncio


class OllamaThread(threading.Thread):
    def __init__(
            self, 
            key : str,      
            lock = None,
            event = None,
            base_url : str = "http://localhost:11434",
            model : str = "qwen2:7b",
            temperature : float = 0.8,
            top_p : int = 1,
            max_try_times :int = 3,
            max_tokens : int = 4*1024,
            stream : bool = True,
            seed : int = 4595,
            prompt_path : str = "./data/prompts/chatbot.prompt"
        ) -> None:
        '''
        create a chatbot
        '''
        super().__init__() # 继承 treading.Tread 对象来实现多线程
        self.key = key
        self.base_url = base_url
        self.client = ChatOllama(
            base_url = base_url,
            model = model,
            temperature = temperature,
            top_p = top_p,
            num_ctx = max_tokens, # 最大窗口长度设为1m
        )
        self.max_try_times = max_try_times
        self.message = []
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()
        self.temperatrue = temperature
        self.model = model
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stream =stream
        self.finish_flag_lock = threading.Lock() # 当这个线程作为主线程时使用
        self.finish_flag = isFinish(self.finish_flag_lock, False) # 是否完成 flag
        self.wait = WaitingThread(self.finish_flag) # 转圈圈进程
        self.seed = seed

        if self.system_prompt != "": # if we got system_prompt
            self.message.append({"role" : "system", "content" : self.system_prompt})

    def define_roles(
            self,
            system_prompt : str
        ) -> None:
        '''
        This method is used to define the role of GPT (i.e. prompt), This method will define the system message
        '''
        self.message.append({"role" : "system", "content" : system_prompt})

    async def send_message(
            self,
            content : str = " ",
            self_print :bool = False
        ) -> str:
        '''
        (使用异步函数)
        send_message to server
        这里用到了.join(), 其实 .join() 在只有主线程调用单个子线程的时候没有意义，但是如果一个主线程要调用多个子线程就非常有意义了
        .join() 必须要等到对应子线程结束之后才能继续主线程的任务, 这样我们可以通过一个for循环来确保所有子线程结束了才能再继续
        '''
 
        response : str = ""
        self.message.append({"role" : "user","content":content})

        self.finish_flag.need_wait() # flag设为True, 需要转圈圈等待
        self.wait = WaitingThread(self.finish_flag) # 重新赋值转圈圈进程（每个进程只能start一次,）
        self.wait.start() # 开始转圈圈

        # completion = self.client.invoke( // invoke : 非流式输出
        #    input=self.message
        #)
    
        async for chunk in self.client.astream(input=self.message): # 使用异步函数实现流式输出
            if chunk is not None:
                if self_print:
                    self.finish_flag.finish() # 开始输出前停止转圈
                    self.wait.join()
                    print(chunk.content, end="")
                response += chunk.content

        if self_print:
            print() # 最后结尾的换行符

        self.message.append({"role" : "assistant","content":response})
        
        if not self_print:
            self.finish_flag.finish() # flag设为False, 停止转圈圈等待
            self.wait.join() # 保证停止

        return response
        
    def run (
            self
        ) -> None:
        '''
        Run the chatbot
        '''
        print("Type \"quit\" or \"q\" to quit")
        print()
        message = input("#** user **#:\n\n")
        print()
        while message != "quit" and message != "q" :
            print("#** bot **#: \n") 
            asyncio.run(self.send_message(message, self_print = True)) # 允许在输出的时候把控制权交到别人手上
            print()
            message = input("#**user**#:\n")
            print()

if __name__ == '__main__':

    lock = threading.Lock()
    event = threading.Event()

    bot_thread = OllamaThread(
            key = "",
            model = "qwen2:7b",
            lock = lock,
            event = event,
            temperature = 0.9,
            top_p = 1,
            prompt_path="./data/prompts/chatbot.prompt"
        )
    
    bot_thread.start()
    bot_thread.join()