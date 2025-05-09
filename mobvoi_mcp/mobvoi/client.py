import typing
import json
import re
import os
import httpx

from typing import Optional
from .text_to_speech import TextToSpeechClient
from .voice_clone import VoiceCloneClient

DEFAULT_SPAEKER = "xiaoyi_meet"

class Mobvoi:
    def __init__(
        self,
        *,
        app_key: typing.Optional[str] = None,
        app_secret: typing.Optional[str] = None,
        httpx_client: typing.Optional[httpx.Client] = None
    ):
        self.text_to_speech_client = TextToSpeechClient(app_key=app_key, app_secret=app_secret, text2speech_client=httpx_client)
        self.voice_clone_client = VoiceCloneClient(app_key=app_key, app_secret=app_secret, voice_clone_client=httpx_client)
    
    def speech_generate(
        self,
        *,
        text: str,
        speaker: typing.Optional[str] = DEFAULT_SPAEKER,
        audio_type: Optional[str] = "mp3",
        speed: Optional[float] = 1.0,
        rate: Optional[int] = 24000,
        volume: Optional[float] = 1.0,
        pitch: Optional[float] = 0,
        streaming: Optional[bool] = False,
    ):
        return self.text_to_speech_client.text2speech_with_timestamps(
            text=text,
            speaker=speaker,
            audio_type=audio_type,
            speed=speed,
            rate=rate,
            volume=volume,
            pitch=pitch,
            streaming=streaming
        )
        
    async def async_speech_generate(
        self,
        *,
        text: str,
        speaker: typing.Optional[str] = DEFAULT_SPAEKER,
        audio_type: Optional[str] = "mp3",
        speed: Optional[float] = 1.0,
        rate: Optional[int] = 24000,
        volume: Optional[float] = 1.0,
        pitch: Optional[float] = 0,
        streaming: Optional[bool] = False,
    ):
        return await self.text_to_speech_client.async_text2speech_with_timestamps(
            text=text,
            speaker=speaker,
            audio_type=audio_type,
            speed=speed,
            rate=rate,
            volume=volume,
            pitch=pitch,
            streaming=streaming
        )
    
    def voice_clone(self, *, is_url: bool, audio_file: str):
        return self.voice_clone_client.voice_clone_impl(is_url=is_url, audio_file=audio_file)
    
    async def async_voice_clone(self, *, is_url: bool, audio_file: str):
        return await self.voice_clone_client.async_voice_clone_impl(is_url=is_url, audio_file=audio_file)
