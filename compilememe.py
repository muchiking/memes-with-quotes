import os
from moviepy.editor import *
import shutil
import sound
# import moviepy.video.fx.all.resize
from moviepy.video.fx.resize import resize


# w,h = 1080, 1920
def compile_clips():
    img_clips = []
    path_list = []
    arr = os.listdir("assets/images")
    for image in os.listdir("assets/images"):
        if image.endswith(".jpg" or ".png" or ".jpeg"):
            path_list.append(os.path.join("assets/images", image))

    # creating slide for each image
    for img_path in path_list:
        slide = ImageClip(img_path, duration=2.7)
        img_clips.append(slide)
    # concatenating slides
    video_slides = concatenate_videoclips(img_clips, method='compose')
    # exporting final video
    video_slides.write_videofile("assets/output/output_video.mp4", fps=24)


def listsize_f(x, y):
    if x % y == 0:
        return x - 1
    else:
        return x - y


def compile_clips1():
    # VideoFileClip.reW = lambda clip: clip.resize(width=W)
    # VideoFileClip.reH = lambda clip: clip.resize(width=H)
    img_clips = []
    path_list = []
    arr = os.listdir("assets/images")
    for image in os.listdir("assets/images"):
        if image.endswith(".jpg"):
            path_list.append(os.path.join("assets/images", image))
        if image.endswith(".png"):
            path_list.append(os.path.join("assets/images", image))
        if image.endswith(".jpeg"):
            path_list.append(os.path.join("assets/images", image))

    listsize = len(path_list)

    # print(listsize)

    # test/in/basic
    video_numbber = 0
    i = 1
    no_of_meems = 3
    time_duration = 5.0
    length = no_of_meems * time_duration
    lower_counter = 0
    no_printed = 1
    listsize = listsize_f(listsize, no_of_meems)
    while i <= (listsize):
        # print(i)
        for num in range(lower_counter, no_of_meems):
            try:
                print(path_list[num])
            except IndexError:
                return video_numbber
            slide = ImageClip(str(path_list[num]), duration=time_duration)
            img_clips.append(slide)
            i += 1
        # concatenating slides
        video_slides = concatenate_videoclips(img_clips, method='compose')
        # add audio to video
        sound = audio(length)
        video_slides.audio = sound
        video_slides = video_slides.resize((1080, 1920))
        # exporting final video
        video_slides.write_videofile("assets/output/output_video" + str(no_printed) + ".mp4", fps=24)
        no_printed += 1
        no_of_meems += 4
        lower_counter += 4
        img_clips = []
        video_numbber += 1
        print(video_numbber)
        # print(no_printed)

    return video_numbber
    # for li in path_list:
    #     print(li)


def movefiles():
    source_folder = "assets/images"
    destination_folder = "assets/tmp"
    # fetch all files
    for file_name in os.listdir(source_folder):
        # construct full file path
        source = source_folder + file_name
        destination = destination_folder + file_name
        # move only filesc
        if os.path.isfile(source):
            shutil.move(source, destination)
            print('Moved:', file_name)


def audio(length):
    sound.process_sound(length)
    audioclip = AudioFileClip(str(os.getenv("sound_fin")))
    # audio_concat = concatenate_audioclips[audioclip]
    audio_composite = CompositeAudioClip([audioclip])
    return audio_composite


if __name__ == "__main__":
    compile_clips1()
