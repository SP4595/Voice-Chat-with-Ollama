# Voice-Chat-with-Ollama
 
## 1. Introduction

&emsp; This Project is let your LLM speak. We use Ollama + Langchain + fast-whisper + GPT-so-vits (API version) to generate a four stage pipeline.

## 2. How to Use

&emsp; 0. Please make sure that the default python interpreter is above `python 3.10`. And your GPU memory should be larger than `8GB`.

&emsp; 1. please download every required package. You may try to run:

```bash
pip install requirements.txt
```

&emsp; 2. You have to download `Ollama` and `GPT-so-vits` and start server to use this projects.

&emsp; 3. Please change configeration of Ollama in config.json. And start `Ollama & GPT-so-vits` server.

&emsp; 4. just simply clip `run.bat` for Windows user or `run.sh` for Linux user to start chat.

## 3. Change Voice

&emsp; Please change voice in `./data/voice_text_pear` into your voice (`.wav format, 3-10 seconds`).

## 4. Future work

&emsp; 1. Add virtual Charactor for this LLM.

&emsp; 2. Make this project better to use.

&emsp; 3. Add GUI to it.