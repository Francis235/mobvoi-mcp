import time
import hashlib
import httpx

class ServiceNotFoundError(Exception):
    def __init__(self, service: str, region: str):
        super().__init__(f"Service '{service}' not found in region '{region}', check your region and service name")

class ApiClient:
    def __init__(self, app_key: str, app_secret: str, region: str = "mainland"):
        self.__app_key = app_key
        self.__app_secret = app_secret

        self.__region = region

        self.__client = httpx.Client(
            timeout=20
        )

        self.__service_dict = {
            "mainland": {
                # naming: {group_name}.{service_name}
                "avatar.image_to_video": "https://openman.weta365.com/metaman/open/image/toman/cmp",
                "avatar.image_to_video_result": "https://openman.weta365.com/metaman/open/image/toman/cmp/result/",
                "avatar.video_dubbing": "https://openman.weta365.com/metaman/open/video/voiceover/createTask",
                "avatar.video_dubbing_result": "https://openman.weta365.com/metaman/open/video/voiceover/detail",
            },
            "global": {

            }
        }

    def __get_url(self, service: str):
        regional_service_dict = self.__service_dict.get(self.__region, None)
        if regional_service_dict is None:
            raise ServiceNotFoundError(service, self.__region)
        service_url = regional_service_dict.get(service, None)
        if service_url is None:
            raise ServiceNotFoundError(service, self.__region)
        return service_url

    def __parse_signature(self):
        timestamp = int(time.time())
        signature = hashlib.md5(f"{self.__app_key}+{self.__app_secret}+{timestamp}".encode()).hexdigest()
        signature_info = {
            "appKey": self.__app_key,
            "signature": signature,
            "timestamp": str(timestamp),
        }
        return signature_info

    def post(self, service: str, request: dict = {}, headers: dict = {}, path: str = ""):
        post_header = self.__parse_signature()
        post_header.update(headers)

        url = self.__get_url(service)
        if path:
            url = f"{url}/{path}"

        response = self.__client.post(url, headers=post_header, json=request)
        return response.json()

    def get(self, service: str, request: dict = {}, headers: dict = {}, path: str = ""):
        get_header = self.__parse_signature()
        get_header.update(headers)

        url = self.__get_url(service)
        if path:
            url = f"{url}/{path}"

        response = self.__client.get(url, headers=get_header, params=request)
        return response.json()
