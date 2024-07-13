import threading # python3 中用 threading 创建线程类
import time
import re
import regex

def check_characters(text):
    # 正则表达式匹配中文、日文、英文以及所有ASCII字符，包括中日标点
    pattern = regex.compile(r'^[\u0000-\u007F\u4E00-\u9FFF\u3040-\u30FF\u31F0-\u31FF\u3000-\u303F]+$')
    return pattern.match(text) # 要求输入必须只包含以上字符！

def custom_sentence_splitter(text : str) -> str:
    '''
    ### Usage:
    简单的语义分割方法
    '''
    # 定义中英文常见的分割符号，现在包括引号、括号等
    separators = r'[；;。.\!\？\?：:]'
    # 使用正则表达式分割文本
    parts = re.split(separators, text)
    # 去除空白，并过滤空字符串
    parts = [part.strip() for part in parts if part.strip() != '']
    return parts

def filter_characters(
    input_string : str, 
    chars_to_remove : str = '-\"\\/[]\{\}【】()（）“”’——`·',
    change_to : str = " "
) -> str:
    '''
    删除指定字符
    :param input_string: 输入的字符串
    :param chars_to_remove: 要删除的字符
    :param change_to: 要替换成的字符
    :return: 处理后的字符串
    '''
    # 创建一个正则表达式模式，将所有需要删除的字符组合成一个字符类
    pattern = f"[{re.escape(chars_to_remove)}]"
    # 使用sub方法将这些字符替换为空字符串
    filtered_str = re.sub(pattern, change_to, input_string)
    return filtered_str

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
            
