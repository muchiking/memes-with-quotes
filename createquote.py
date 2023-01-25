import pdcsv
from dotenv import load_dotenv
import os
import compile_quotes as compile
import sound_quotes as sound

load_dotenv()


def run(num):
    quotes, authors, size = pdcsv.readcsv(os.getenv("csv"))
    # size = 2
    for index in range(int(num)):
        write_text = quotes[index]
        if authors[index] == "nan" or authors[index] == "NaN":
            compile.compile(str(quotes[index]),str(write_text), index)
            # sound.create_mp3(str(quotes[index]), index)
        else:

            write_text += " \n - " + authors[index]
        # sec,path=sound.create_mp3(quotes[index], index)
            compile.compile(str(quotes[index]),str(write_text), index)


if __name__ == "__main__":
    run(1)
