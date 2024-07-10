from IPython.display import Audio
import ChatTTS
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class VoiceGenerator:
    def __init__(self) -> None:
        self.chat = ChatTTS.Chat()
        self.chat.load(
            source="custom",
            custom_path="./models/ChatTTS"
        )
        
    def text2voice(
        self,
        texts : str
    ) -> None:
        wavs = self.chat.infer(texts)
        Audio(wavs, rate=24_000, autoplay=True)