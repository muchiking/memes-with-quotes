from dotenv import load_dotenv
import os
import random
from pydub import AudioSegment

load_dotenv()
def process_sound(time):
    path=os.getenv("sound_dir")
    # print(path)
    music=os.listdir(path)
    print(random.choice(music))
    chosen_music=(random.choice(music))
    # print(path+chosen_music)
    chosen_music=(path+"/"+chosen_music)
    sound = AudioSegment.from_mp3(chosen_music)
    startmin=0
    endtime=(1000*int(time))
    extract=sound[startmin:endtime]
    extract.export(os.getenv("sound_fin"),format="mp3")