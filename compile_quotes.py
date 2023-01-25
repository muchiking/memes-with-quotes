from ctypes import resize
from moviepy.editor import *
import textwrap
from dotenv import load_dotenv
import sound_quotes as sound
# from moviepy.config import change_settings
# change_settings({"IMAGEMAGICK_BINARY": r"/usr/bin/convert"})
load_dotenv()
import os

def compile(simple_quote,text,count):
    print("now running compile")
    num=10
    wait_time,mp3_path=sound.create_mp3(simple_quote,count)
    print(wait_time)
    wait_time=float(wait_time)
    wait_time+=0.5
    print(mp3_path)
    print(wait_time)
    video=VideoFileClip(os.getenv("back"),target_resolution=(1920,1080)).subclip(num,(num+wait_time)).without_audio()
    wrapper = textwrap.TextWrapper(width=12,break_long_words=False)
    text_w = wrapper.fill(text=text)
    # t=textwrap.TextWrapper(width=20)
    # text_w =t.TextWrapper.fill(text)
    
    # text=TextClip("How To",fontsize=40,colour="red").set_position(("left","top")).set_duration(10)
    # txt_clip = ( TextClip("《Netkiller Python ⼿札》",font="/System/Library/Fonts/PingFang.ttc",
    # fontsize=70,color='white')
    #  .set_position('center')
    #  .set_duration(10) )

    text = ( TextClip(text_w,fontsize=70,font=os.getenv("font"),color='white').set_position('center').set_duration(wait_time) )
    # text = ( TextClip(text,fontsize=50,color='white',font=os.getenv("font"), method='caption').set_position('center').set_duration(10) )
    final = CompositeVideoClip([video,text])
    audioclip = AudioFileClip(mp3_path)
    final = final.set_audio(audioclip)
    # final= final.resize((1080, 1920))
    final.write_videofile("assets/output_quotes/output"+str(count)+".mp4")
# final.ipython_display(width=200 )

## to display
## create function to delete some sheets