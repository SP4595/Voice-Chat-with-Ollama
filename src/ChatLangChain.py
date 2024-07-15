from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings.ollama import OllamaEmbeddings
from typing import Literal # Listeral 是给 IDLE (VSCODE) 的 hint， 告诉他我的输入一定要在Literal里面
from typing import Union # Union 是给 IDLE 的 hint, 标定输出的可能性
import sys
import os
from queue import Queue
from VoiceGenerator import VoiceGenerator
from VoiceRecognizer import VoiceRecognizer
from AudioGenerateThread import AudioGenerateThread

# 获取当前脚本所在目录的父目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 将父目录添加到系统路径
lib_dir = os.path.join(parent_dir)
sys.path.append(lib_dir)

from lib.utils import WaitingThread, isFinish, check_characters

import json
import threading # python3 中用 threading 创建线程类
import time
import asyncio
import numpy as np
from lib.utils import custom_sentence_splitter, filter_characters, is_allowed_language

class OllamaThread(threading.Thread):
    def __init__(
            self, 
            run_mod : Literal["text", "audio"],      
            input_recongnize_shared_queue : Queue[str],
            output_generate_shared_queue : Queue[str],
            process_done_event : threading.Event,
            key : str = "",
            base_url : str = "http://localhost:11434",
            model : str = "phi3:3.8b",
            temperature : float = 0.2,
            top_p : int = 0.9,
            max_try_times :int = 3,
            max_tokens : int = 4*1024,
            stream : bool = True,
            seed : int = 4595,
            prompt_path : str = "./data/prompts/chatbot.prompt",
            force_intialize_client = False
        ) -> None:
        '''
        ## Usage:
        create a chatbot and voice recognize
        ## paras:
        force_initialize_client: 这个变量是为了强制初始化
        '''
        super().__init__() # 继承 treading.Tread 对象来实现多线程
        self.run_mod : Literal["text", "audio"] = run_mod
        self.key = key
        self.base_url = base_url
        
        self.client = ChatOllama(
            base_url = base_url,
            model = model,
            temperature = temperature,
            top_p = top_p,
            num_ctx = max_tokens, # 最大窗口长度设为1m
        )
        
        self.temperatrue = temperature
        self.model = model
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stream =stream
        self.max_try_times = max_try_times
        self.seed = seed
        
        self.message = []
        
        with open(prompt_path, "r") as f:
            self.system_prompt = f.read()
        if self.system_prompt != "": # if we got system_prompt
            self.message.append({"role" : "system", "content" : self.system_prompt})
            
        
        self.finish_flag_lock = threading.Lock() # 当这个线程作为主线程时使用
        self.finish_flag = isFinish(self.finish_flag_lock, False) # 是否完成 flag
        self.wait = WaitingThread(self.finish_flag) # 转圈圈进程
        
        self

        self.input_recongnize_queue = input_recongnize_shared_queue
        self.output_generate_queue = output_generate_shared_queue
        self.process_done_event = process_done_event # 停止 event
        
        

    def define_roles(
            self,
            system_prompt : str
        ) -> None:
        '''
        This method is used to define the role of GPT (i.e. prompt), This method will define the system message
        '''
        self.message.append({"role" : "system", "content" : system_prompt}) # save to memory
    
        
    def deal_with_queue(self) -> None:
        '''
        这个方法调用queue中的元素然后concate到一起识别，让llm生成，最后把llm生成的结果split成简单句交给语音生成线程
        '''
        if not self.input_recongnize_queue.empty():
            content = ""
            
            while not self.input_recongnize_queue.empty():
                content += self.input_recongnize_queue.get() + "。"
            
            print(f"input:\n{content}")

            chat_response =  self.send_message_sync(content=content)
            chat_response = filter_characters(
                input_string = chat_response
            )
            chat_response_splited = custom_sentence_splitter(chat_response) # 进行简单的split
            
            print(f"output:\n{chat_response_splited}")
             
            for sentence in chat_response_splited:
                self.output_generate_queue.put(sentence) # 入队
            self.output_generate_queue.put(None) # None 标记结束 (这个 None 是为了让 语音播放知道这段话已经停止了，可以放开语音接受线程了！)
    
    def send_message_sync(
            self,
            content : str = " ",
            self_print : bool = False
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
    
        for chunk in self.client.stream(input=self.message): # 使用异步函数实现流式输出
            if chunk is not None:
                if self_print:
                    self.finish_flag.finish() # 开始输出前停止转圈
                    self.wait.join()
                    print(chunk.content, end="")
                response += chunk.content

        if self_print:
            print() # 最后结尾的换行符
        
        if not self_print:
            self.finish_flag.finish() # flag设为False, 停止转圈圈等待
            self.wait.join() # 保证停止

        return response
            

    async def send_message_async(
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
        self.message.append({"role" : "user","content" : content})

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
        
    def text_run(
        self
    ) -> None:
        '''
        Run the chatbot in text mod
        '''
        print("Type \"quit\" or \"q\" to quit")
        print()
        message = input("#** user **#:\n\n")
        print()
        while message != "quit" and message != "q" :
            print("#** bot **#: \n") 
            asyncio.run(self.send_message_async(message, self_print = True)) # 允许在输出的时候把控制权交到别人手上
            print()
            message = input("#**user**#:\n")
            print()
        
    def run(self) -> None:
        '''
        Run the model in text or audio mode
        '''
    
        while True:
            if self.run_mod == "text":
                self.text_run()
            else:
                self.deal_with_queue()

if __name__ == '__main__':

    lock = threading.Lock()
    event = threading.Event()

    bot_thread = OllamaThread(
            shared_queue=None,
            run_mod="text",
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