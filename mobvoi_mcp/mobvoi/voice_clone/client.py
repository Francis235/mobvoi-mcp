import os, sys
import typing
import httpx
import json
import time
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceCloneError(Exception):
    """Custom voice clone exception, containing error code and error message"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"Voice clone failed with code={code}, message={message}")

class VoiceCloneClient:
    def __init__(self, *, app_key: str, app_secret: str, voice_clone_client: typing.Union[httpx.Client, httpx.AsyncClient]):
        self._client = voice_clone_client
        self._app_key = app_key
        self._app_secret = app_secret
        
    def voice_clone_impl(self, *, is_url: bool, audio_file: str):
        logger.debug(f"is_url: {is_url}, audio_file: {audio_file}")
        
        timestamp = str(int(time.time()))
        message = '+'.join([self._app_key, self._app_secret, timestamp])
        m = hashlib.md5()
        m.update(message.encode("utf8"))
        signature = m.hexdigest()
        
        request_data = {
            'appKey': self._app_key,
            'signature': signature,
            'timestamp': timestamp,
            'wavUri': audio_file if is_url else None,
        }
        files = {
            'file': open(audio_file, 'rb')
        } if not is_url else None
        
        try:
            _response = self._client.request(
                method="POST",
                url="https://open.mobvoi.com/clone",
                data=request_data,
                files=files if not is_url else None
            )
            
            if _response.json()['code'] == 0:
                logger.info("voice clone success!")
                return _response.json()['speaker']
            else:
                code = _response.json()['code']
                error_msg = _response.json()['error']
                logger.error(f"Voice clone failed with code={code}, message={error_msg}")
                raise VoiceCloneError(code, error_msg)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise
    
    async def async_voice_clone_impl(self, *, is_url: bool, audio_file: str):
        logger.info(f"is_url: {is_url}, audio_file: {audio_file}")
        
        timestamp = str(int(time.time()))
        message = '+'.join([self._app_key, self._app_secret, timestamp])
        m = hashlib.md5()
        m.update(message.encode("utf8"))
        signature = m.hexdigest()
        
        request_data = {
            'appKey': self._app_key,
            'signature': signature,
            'timestamp': timestamp,
            'wavUri': audio_file if is_url else None,
        }
        files = {
            'file': open(audio_file, 'rb')
        } if not is_url else None
        
        try:
            _response = await self._client.request(
                method="POST",
                url="https://open.mobvoi.com/clone",
                data=request_data,
                files=files if not is_url else None
            )
            if _response.json()['code'] == 0:
                logger.info("voice clone success!")
                return _response.json()['speaker']
            else:
                code = _response.json()['code']
                error_msg = _response.json()['error']
                logger.error(f"Voice clone failed with code={code}, message={error_msg}")
                raise VoiceCloneError(code, error_msg)
        except Exception as e:
            logger.exception(f"Error: {e}")
            raise