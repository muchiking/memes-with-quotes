from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.editor import *
import os

def compile_both_files():
    vid_quotes=os.listdir("assets/output_quotes/")
    videos=os.listdir("assets/output/")
    print(vid_quotes)
    print(videos)
    number_of_vids= len(videos)
    clip3 = VideoFileClip("assets/drop/test.mp4")
    # mid_clip=ImageClip("assets/test.png", duration=4)
    # clip3=concatenate_videoclips([clip3,mid_clip])
    # clip3.write_videofile("assets/final/output34.mp4")

    # clip3 = CompositeVideoClip([clip3,mid_clip])
    #.set_pos(("center","center"))
    # mid_clip=mid_clip.resize((1080, 1920)) #1920,1080
    for num in range(number_of_vids):
        clip1_path ="assets/output/"+str(videos[num])
        clip1_path2 ="assets/output_quotes/"+str(vid_quotes[num])
        clip1 = VideoFileClip(clip1_path)
        clip2 = VideoFileClip(clip1_path2)
        final_clip = concatenate_videoclips([clip1,clip3,clip2])
        final_clip.write_videofile("assets/final/B.Have a Great Day"+str(num)+".mp4")
        print("completed")
        print(videos[num])

    # return number_of_vids

# clip1 = VideoFileClip("script1.mp4")
# clip2 = VideoFileClip("script2.mp4")

# final_clip = concatenate_videoclips([clip1, clip2])
# final_clip.write_videofile("output.mp4")
if __name__ == "__main__":
    compile_both_files()


