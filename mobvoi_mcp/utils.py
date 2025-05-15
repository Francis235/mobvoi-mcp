import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fuzzywuzzy import fuzz


class MobvoiMcpError(Exception):
    pass

def make_error(error_text: str):
    raise MobvoiMcpError(error_text)

def is_file_writeable(path: Path) -> bool:
    if path.exists():
        return os.access(path, os.W_OK)
    parent_dir = path.parent
    return os.access(parent_dir, os.W_OK)

def make_output_file(
    tool: str, text: str, output_path: Path, extension: str, full_id: bool = False
) -> Path:
    id = text if full_id else text[:8]

    output_file_name = f"{tool}_{id.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return output_path / output_file_name

def make_output_path(
    output_directory: Optional[str], base_path: Optional[str] = None
) -> Path:
    output_path = None
    if output_directory is None:
        output_path = Path.home() / "Desktop"
    elif not os.path.isabs(output_directory) and base_path:
        output_path = Path(os.path.expanduser(base_path)) / Path(output_directory)
    else:
        output_path = Path(os.path.expanduser(output_directory))
    if not is_file_writeable(output_path):
        make_error(f"Directory ({output_path}) is not writeable")
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        make_error(f"Permission denied creating directory ({output_path})")
    return output_path

def find_similar_filenames(
    target_file: str, directory: Path, threshold: int = 70
) -> list[tuple[str, int]]:
    """
    Find files with names similar to the target file using fuzzy matching.

    Args:
        target_file (str): The reference filename to compare against
        directory (str): Directory to search in (defaults to current directory)
        threshold (int): Similarity threshold (0 to 100, where 100 is identical)

    Returns:
        list: List of similar filenames with their similarity scores
    """
    target_filename = os.path.basename(target_file)
    similar_files = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if (
                filename == target_filename
                and os.path.join(root, filename) == target_file
            ):
                continue
            similarity = fuzz.token_sort_ratio(target_filename, filename)

            if similarity >= threshold:
                file_path = Path(root) / filename
                similar_files.append((file_path, similarity))

    similar_files.sort(key=lambda x: x[1], reverse=True)

    return similar_files

def check_audio_file(path: Path) -> bool:
    audio_extensions = {
        ".wav",
        ".mp3",
        ".m4a",
        ".aac",
        ".ogg",
        ".flac",
        ".mp4",
        ".avi",
        ".mov",
        ".wmv",
    }
    return path.suffix.lower() in audio_extensions

def try_find_similar_files(
    filename: str, directory: Path, take_n: int = 5
) -> list[Path]:
    similar_files = find_similar_filenames(filename, directory)
    if not similar_files:
        return []

    filtered_files = []

    for path, _ in similar_files[:take_n]:
        if check_audio_file(path):
            filtered_files.append(path)

    return filtered_files

def handle_input_file(file_path: str, audio_content_check: bool = True) -> Path:
    if not os.path.isabs(file_path) and not os.environ.get("ELEVENLABS_MCP_BASE_PATH"):
        make_error(
            "File path must be an absolute path if ELEVENLABS_MCP_BASE_PATH is not set"
        )
    path = Path(file_path)
    if not path.exists() and path.parent.exists():
        parent_directory = path.parent
        similar_files = try_find_similar_files(path.name, parent_directory)
        similar_files_formatted = ",".join([str(file) for file in similar_files])
        if similar_files:
            make_error(
                f"File ({path}) does not exist. Did you mean any of these files: {similar_files_formatted}?"
            )
        make_error(f"File ({path}) does not exist")
    elif not path.exists():
        make_error(f"File ({path}) does not exist")
    elif not path.is_file():
        make_error(f"File ({path}) is not a file")

    if audio_content_check and not check_audio_file(path):
        make_error(f"File ({path}) is not an audio or video file")
    return path

class Language:
    def __init__(self, code: str, name: str, is_src: bool, is_target: bool):
        self.code = code
        self.name = name
        self.is_src = is_src
        self.is_target = is_target

class LanguageTable:
    def __init__(self):
        self.language_list = {}
        self.language_code_list = {}
        support_language="""Afrikaans,af,TRUE,FALSE
Arabic,ar,TRUE,TRUE
Azerbaijani,az,TRUE,FALSE
Belarusian,be,TRUE,FALSE
Bulgarian,bg,TRUE,TRUE
Bosnian,bs,TRUE,FALSE
Catalan,ca,TRUE,FALSE
Czech,cs,TRUE,TRUE
Welsh,cy,TRUE,FALSE
Danish,da,TRUE,TRUE
German,de,TRUE,TRUE
Greek,el,TRUE,TRUE
English,en,TRUE,TRUE
Spanish,es,TRUE,TRUE
Estonian,et,TRUE,FALSE
Persian,fa,TRUE,FALSE
Finnish,fi,TRUE,TRUE
French,fr,TRUE,TRUE
Galician,gl,TRUE,FALSE
Hebrew,he,TRUE,FALSE
Hindi,hi,TRUE,TRUE
Croatian,hr,TRUE,TRUE
Hungarian,hu,TRUE,TRUE
Armenian,hy,TRUE,FALSE
Indonesian,id,TRUE,TRUE
Icelandic,is,TRUE,FALSE
Italian,it,TRUE,TRUE
Japanese,ja,TRUE,TRUE
Kazakh,kk,TRUE,FALSE
Kannada,kn,TRUE,FALSE
Korean,ko,TRUE,TRUE
Lithuanian,lt,TRUE,FALSE
Latvian,lv,TRUE,FALSE
Maori,mi,TRUE,FALSE
Macedonian,mk,TRUE,FALSE
Marathi,mr,TRUE,FALSE
Malay,ms,TRUE,TRUE
Nepali,ne,TRUE,FALSE
Dutch,nl,TRUE,TRUE
Norwegian,no,TRUE,TRUE
Polish,pl,TRUE,TRUE
Portuguese,pt,TRUE,TRUE
Romanian,ro,TRUE,TRUE
Russian,ru,TRUE,TRUE
Slovak,sk,TRUE,TRUE
Slovenian,sl,TRUE,FALSE
Serbian,sr,TRUE,FALSE
Swedish,sv,TRUE,TRUE
Swahili,sw,TRUE,FALSE
Tamil,ta,TRUE,TRUE
Thai,th,TRUE,TRUE
Filipino,tl,TRUE,TRUE
Turkish,tr,TRUE,TRUE
Ukrainian,uk,TRUE,TRUE
Urdu,ur,TRUE,FALSE
Vietnamese,vi,TRUE,TRUE
Chinese,zh,TRUE,TRUE
"""

        for line in support_language.split("\n"):
            if line.strip() == "":
                continue
            name, code, is_src, is_target = line.split(",")
            la = Language(code.lower().strip(), name.strip(), is_src.lower().strip() == "true", is_target.lower().strip() == "true")

            self.language_list[name.lower().strip()] = la
            self.language_code_list[code.lower().strip()] = la

    def get_language_list(self):
        return list(self.language_list.values())

    def get_language_by_name(self, name: str):
        return self.language_list.get(name, None)

    def get_language_by_code(self, code: str):
        return self.language_code_list.get(code, None)
