import os, sys
import typing
import httpx
import time
import logging
import concurrent.futures

from .utils import ServiceFactory, ImageToVideoRequest, VoiceOverRequest, VideoTranslateRequest
from .language import LanguageTable


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
def download_file(url: str, output_path: str, num_threads: int = 4, chunk_size: int = 1024*1024):
    """Download a file from a URL using multiple threads.
    
    Args:
        url: The URL of the file to download
        output_path: The path where the file should be saved
        num_threads: Number of threads to use for downloading
        chunk_size: Size of each chunk in bytes
    """
    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Get file size
    with httpx.Client() as client:
        response = client.head(url, follow_redirects=True)
        response.raise_for_status()
        file_size = int(response.headers.get('Content-Length', 0))
    
    if file_size == 0:
        # Can't use multi-threading if we don't know the file size
        with httpx.Client() as client:
            with client.stream("GET", url, follow_redirects=True) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        return
    
    # Calculate chunk ranges
    ranges = []
    for i in range(num_threads):
        start = i * (file_size // num_threads)
        end = (i + 1) * (file_size // num_threads) - 1 if i < num_threads - 1 else file_size - 1
        ranges.append((start, end))
    
    # Create temporary directory for chunks
    temp_dir = os.path.join(os.path.dirname(output_path), f".download_temp_{int(time.time())}")
    os.makedirs(temp_dir, exist_ok=True)
    
    def download_chunk(range_index):
        start, end = ranges[range_index]
        range_header = {'Range': f'bytes={start}-{end}'}
        temp_file = os.path.join(temp_dir, f"chunk_{range_index}")
        
        with httpx.Client() as client:
            with client.stream("GET", url, headers=range_header, follow_redirects=True) as response:
                response.raise_for_status()
                with open(temp_file, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
        return temp_file
    
    # Download chunks in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_chunk, i) for i in range(len(ranges))]
        chunk_files = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Combine chunks
    with open(output_path, 'wb') as output_file:
        for i in range(len(ranges)):
            chunk_file = os.path.join(temp_dir, f"chunk_{i}")
            with open(chunk_file, 'rb') as chunk:
                output_file.write(chunk.read())
    
    # Clean up temp files
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

class ImageToVideoError(Exception):
    """Custom image to video exception, containing error code and error message"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"Image to video failed with code={code}, message={message}")

class VoiceOverError(Exception):
    """Custom voice over exception, containing error code and error message"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"Voice over failed with code={code}, message={message}")

class AvatarClient:
    def __init__(self, *, app_key: str, app_secret: str, http_client: typing.Union[httpx.Client, httpx.AsyncClient]):
        self._client = http_client
        self._app_key = app_key
        self._app_secret = app_secret

        self._language_table = LanguageTable()

    def image_to_video_impl(self, *, image_url: str, audio_url: str, output_dir: str = "./"):
        # parse and call image to video service
        i2v_serv = ServiceFactory.create_service("image_to_video", self._app_key, self._app_secret)

        i2v_req = ImageToVideoRequest(
            imageUrl=image_url,
            audioUrl=audio_url
        )
        # in this case the data of this request is a task_id
        i2v_result = i2v_serv.call_service(i2v_req.model_dump())
        if i2v_result is None:
            raise ImageToVideoError(10000, "Failed to call image to video service")

        logger.info(f"Image to video request send successfully, task_id: {i2v_result}")

        # get result from image to video service
        i2v_get_result_serv = ServiceFactory.create_service("image_to_video_result", self._app_key, self._app_secret)
        while True:
            res = i2v_get_result_serv.call_service({"task_id": i2v_result})
            if res is None:
                raise ImageToVideoError(10001, f"Failed to get i2v result, task_id: {i2v_result}")
            status = res.get("status")
            if status == "suc":
                result_url = res.get("resultUrl")
                break
            elif status == "ing":
                time.sleep(10)
                logger.info(f"task_id: {i2v_result}, status: {status}, still waiting for result...")
                continue
            else:
                raise ImageToVideoError(10002, f"Image to video failed with status={status}, message={res.get('msg', 'Unknown error')}")
        
        logger.info(f"task_id: {i2v_result}, result url: {result_url}")
        
        # Download the video
        result_root = os.path.join(output_dir)
        os.makedirs(result_root, exist_ok=True)
        output_video_path = os.path.join(result_root, f"{i2v_result}.mp4")

        # Use the multi-threaded download function
        download_file(result_url, output_video_path)
        return output_video_path, result_url
    

    def voice_over_impl(self, *, video_url: str, audio_url: str, output_dir: str = "./"):
        voice_over_serv = ServiceFactory.create_service("voice_over", self._app_key, self._app_secret)

        voice_over_req = VoiceOverRequest(
            videoUrl=video_url,
            audioUrl=audio_url
        )
        voice_over_result = voice_over_serv.call_service(voice_over_req.model_dump())
        if voice_over_result is None:
            raise VoiceOverError(10000, "Failed to call voice over service")

        logger.info(f"Voice over request send successfully, task_id: {voice_over_result}")

        voice_over_get_result_serv = ServiceFactory.create_service("voice_over_result", self._app_key, self._app_secret)
        task_id_req = {
            "taskId": voice_over_result,
            "taskUuid": voice_over_result
        }
        while True:
            res = voice_over_get_result_serv.call_service(task_id_req)
            if res is None:
                raise VoiceOverError(10001, f"Failed to get voice over result, task_id: {voice_over_result}")
            status = res.get("status")
            if status == "suc":
                result_url = res.get("resultUrl")
                cover_image_url = res.get("coverImg")
                break
            elif status == "ing":
                time.sleep(10)
                logger.info(f"task_id: {voice_over_result}, status: {status}, still waiting for result...")
                continue
            else:
                raise VoiceOverError(10002, f"Voice over failed with status={status}, message={res.get('msg', 'Unknown error')}")
        
        # download the video and cover image
        result_root = os.path.join(output_dir)
        os.makedirs(result_root, exist_ok=True)
        output_video_path = os.path.join(result_root, f"{voice_over_result}.mp4")
        output_cover_image_path = os.path.join(result_root, f"{voice_over_result}.jpg")

        download_file(result_url, output_video_path)
        download_file(cover_image_url, output_cover_image_path)
        return output_video_path, output_cover_image_path, result_url, cover_image_url

    def video_translate_get_language_list_impl(self):
        language_list = self._language_table.get_language_list()
        language_str = ""
        for language in language_list:
            language_str += f"{language.name}, {language.code}, {language.is_src}, {language.is_target}\n"
        return language_str
    
    def video_translate_impl(self, *, video_url: str, original_language: str, target_language: str, output_dir: str = "./"):
        video_translate_serv = ServiceFactory.create_service("video_translate", self._app_key, self._app_secret)

        # verify original language and target language
        original_language = original_language.lower()
        target_language = target_language.lower()

        # load by name or code
        ori_lang_obj = self._language_table.get_language_by_name(original_language)
        if ori_lang_obj is None:
            ori_lang_obj = self._language_table.get_language_by_code(original_language)
        if ori_lang_obj is None:
            raise ValueError(f"Original language {original_language} is not supported")
        
        if not ori_lang_obj.is_src:
            raise ValueError(f"Original language {original_language} is not supported")
        
        target_lang_obj = self._language_table.get_language_by_name(target_language)
        if target_lang_obj is None:
            target_lang_obj = self._language_table.get_language_by_code(target_language)
        if target_lang_obj is None:
            raise ValueError(f"Target language {target_language} is not supported")

        if not target_lang_obj.is_target:
            raise ValueError(f"Target language {target_language} is not supported")

        
        video_translate_req = VideoTranslateRequest(
            videoUrl=video_url,
            originalLanguage=original_language,
            targetLanguage=target_language
        )
        video_translate_result = video_translate_serv.call_service(video_translate_req.model_dump())

        print(video_translate_result)

        if video_translate_result is None:
            raise ValueError(f"Failed to call video translate service")
        
        logger.info(f"Video translate request send successfully, task_id: {video_translate_result}")

        video_translate_get_result_serv = ServiceFactory.create_service("video_translate_result", self._app_key, self._app_secret)
        while True:

            try:
                logger.info(f"Calling video translate result...")
                res = video_translate_get_result_serv.call_service({"task_id": video_translate_result})
                logger.info(f"video translate result: {res}")
                if res is None:
                    raise ValueError(f"Failed to get video translate result")
                status = res.get("status")
                if status == "success":
                    result_url = res.get("videoUrl")
                    break
                elif status == "ing":
                    logger.info(f"task_id: {video_translate_result}, status: {status}, still waiting for result...")
                    time.sleep(10)
                    continue
                else:
                    raise ValueError(f"Video translate failed with status={status}, message={res.get('msg', 'Unknown error')}")
            except Exception as e:
                logger.error(f"Error calling video translate result: {e}")
                time.sleep(10)
                continue
        
        # download the video
        result_root = os.path.join(output_dir)
        os.makedirs(result_root, exist_ok=True)
        output_video_path = os.path.join(result_root, f"{video_translate_result}.mp4")
        download_file(result_url, output_video_path)
        return output_video_path, result_url