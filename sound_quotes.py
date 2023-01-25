from gtts import gTTS
from mutagen.mp3 import MP3
from dotenv import load_dotenv
# from mutagen.wave import WAVE
import audioread
import re
import os

load_dotenv()

def audio(path):
    with audioread.audio_open(path) as f:
        seconds = f.duration
        return seconds
        # audio = WAVE(path)
    # audio_info = audio.info
    # length = int(audio_info.length)
    # print(length)


def create_mp3(text,num):
    text=sanitize_text(text)
    tts = gTTS(text, lang="en", slow=False, tld="com.au")
    path=os.getenv("sound")+str(num)+".mp3"
    tts.save(path)
    print(path)
    seconds=audio(path)
    # print(seconds)
    return seconds,path

    
def sanitize_text(text: str) -> str:
    r"""Sanitizes the text for tts.
        What gets removed:
     - following characters`^_~@!&;#:-%“”‘"%*/{}[]()\|<>?=+`
     - any http or https links

    Args:
        text (str): Text to be sanitized

    Returns:
        str: Sanitized text
    """

    # remove any urls from the text
    regex_urls = r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*"

    result = re.sub(regex_urls, " ", text)

    # note: not removing apostrophes
    regex_expr = r"\s['|’]|['|’]\s|[\^_~@!&;#:\-–—%“”‘\"%\*/{}\[\]\(\)\\|<>=+]"
    result = re.sub(regex_expr, " ", result)
    result = result.replace("+", "plus").replace("&", "and")
    # remove extra whitespace
    return result

if __name__ == "__main__":
    create_mp3("The height and width of an image can be set using height and width attribute",1)



# create_mp3("""Stop creating mp3 files if the length is greater than 50 seconds. This can be longer, but this is just a good starting point
#         if length > 50:""")