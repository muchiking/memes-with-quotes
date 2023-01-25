import pandas as pd
import os
from dotenv import load_dotenv
import shutil
load_dotenv()

def delete(path):
    for name in os.listdir(path):
        file_path = os.path.join(path, name)
        os.remove(file_path)
        # try:
        #     shutil.rmtree(file_path)
        # except IsADirectoryError:
        #     # Ignore directories, they will be deleted separately
        #     pass
        # except Exception as e:
        #     print(f"Failed to delete {file_path}: {e}")

def delete_file():
    delete("assets/output/")
    delete("assets/output_quotes/")


# Read the CSV file into a DataFrame
def readcsv(csv_path,rows):
    # csv_path=os.getenv("csv")
    csv_path=os.getenv("csv")
    df = pd.read_csv(csv_path)
    
    # new_df = df
    new_df = pd.read_csv("csv/output2.csv")
    new_df1 = df.loc[:(rows-1)]
    new_df= new_df.append(new_df1, ignore_index=True)
    new_df.to_csv("csv/output2.csv", index=False)
    # Drop the first three rows
    df = df.drop(df.index[:rows], axis=0)

    df.to_csv(csv_path, index=False)
    


def master(num):
    path=os.getenv("csv")
    print(path)
    readcsv(path,num)
    delete_file()


if __name__ == '__main__':
    # path=os.getenv("csv")
    # print(path)
    # readcsv(path,3)
    delete_file()

# df = pd.read_csv("data.csv")

# Save the DataFrame to a CSV file
# df.to_csv("output.csv", index=False)