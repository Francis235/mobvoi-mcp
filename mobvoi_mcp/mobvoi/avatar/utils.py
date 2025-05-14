import time
import hashlib
from pydantic import BaseModel
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_signature(app_key: str, app_secret: str):
    timestamp = int(time.time())
    signature = hashlib.md5(f"{app_key}+{app_secret}+{timestamp}".encode()).hexdigest()
    signature_info = {
        "appKey": app_key,
        "signature": signature,
        "timestamp": str(timestamp),
    }
    return signature_info

class ImageToVideoRequest(BaseModel):
    # in this case, only use this two factor, will support more in the future
    imageUrl: str
    audioUrl: str

class VoiceOverRequest(BaseModel):
    videoUrl: str
    wavUrl: str

class VideoTranslateRequest(BaseModel):
    videoUrl: str
    speakerNum: int = 1
    originalLanguage: str
    targetLanguage: str

class BaseService:
    def __init__(self, use_async: bool) -> None:
        self.__use_async = use_async
        self.__client = httpx.Client(timeout=20)
    
    def call_service_kernel(self, url: str, header: dict = None, request: dict = None, method: str = "POST"):
        if method == "POST":
            return self.__client.post(url, headers=header, json=request)
        elif method == "GET":
            return self.__client.get(url, headers=header, params=request)

    def call_service(self, request: dict):
        raise NotImplementedError

# common post service
class PostService(BaseService):
    def __init__(self, app_key: str, app_secret: str, url: str, use_async: bool = False):
        super().__init__(use_async)
        self.__app_key = app_key
        self.__app_secret = app_secret
        self.__url = url

    def call_service(self, request: dict):
        headers = parse_signature(self.__app_key, self.__app_secret)
        response = self.call_service_kernel(self.__url, headers, request)
        code = response.json().get("code", 0)
        if code != 200:
            logger.error(f"Failed to call service, code: {code}, response: {response.json()}")
            return None
        else:
            print(response.json())
        return response.json().get("data", None)

class GetService(BaseService):
    def __init__(self, app_key: str, app_secret: str, url: str, use_async: bool = False):
        super().__init__(use_async)
        self.__app_key = app_key
        self.__app_secret = app_secret
        self.__url = url

    def call_service(self, request: dict):
        headers = parse_signature(self.__app_key, self.__app_secret)
        response = self.call_service_kernel(self.__url, headers, request, "GET")
        code = response.json().get("code", 0)
        if code != 200:
            logger.error(f"Failed to call service, code: {code}, response: {response.json()}")
            return None
        return response.json().get("data", None)

# for the case which url will concat with task id
class GetResultService(BaseService):
    def __init__(self, app_key: str, app_secret: str, url: str, use_async: bool = False):
        super().__init__(use_async)
        self.__app_key = app_key
        self.__app_secret = app_secret
        self.__url = url

    def call_service(self, request: dict):
        task_id = request.get("task_id", None)
        if not task_id:
            logger.error("task_id is required")
            return None

        url = self.__url + task_id

        headers = parse_signature(self.__app_key, self.__app_secret)
        response = self.call_service_kernel(url, headers, None, "GET")
        code = response.json().get("code", 0)
        if code != 200:
            logger.error(f"Failed to call service, code: {code}, response: {response.json()}")
            return None
        return response.json().get("data", None)


class ServiceFactory:
    def create_service(service_type: str, app_key: str, app_secret: str) -> BaseService:
        if service_type == "image_to_video":
            return PostService(app_key, app_secret, "https://openman.weta365.com/metaman/open/image/toman/cmp")
        elif service_type == "image_to_video_result":
            return GetResultService(app_key, app_secret, "https://openman.weta365.com/metaman/open/image/toman/cmp/result/")
        elif service_type == "voice_over":
            return PostService(app_key, app_secret, "https://openman.weta365.com/metaman/open/video/voiceover/createTask")
        elif service_type == "voice_over_result":
            return GetService(app_key, app_secret, "https://openman.weta365.com/metaman/open/video/voiceover/detail")
        elif service_type == "video_translate":
            return PostService(app_key, app_secret, "https://openman.weta365.com/metaman/open/video/translate/start")
        elif service_type == "video_translate_result":
            return GetResultService(app_key, app_secret, "https://openman.weta365.com/metaman/open/video/translate/result/")
        else:
            raise ValueError(f"Invalid service type: {service_type}")
