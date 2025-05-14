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
        for line in support_language.split("\n"):
            if line.strip() == "":
                continue
            name, code, is_src, is_target = line.split(",")
            la = Language(code.lower().strip(), name.lower().strip(), is_src.lower().strip() == "true", is_target.lower().strip() == "true")

            self.language_list[name.lower().strip()] = la
            self.language_code_list[code.lower().strip()] = la

    def get_language_list(self):
        return list(self.language_list.values())

    def get_language_by_name(self, name: str):
        return self.language_list.get(name, None)

    def get_language_by_code(self, code: str):
        return self.language_code_list.get(code, None)
