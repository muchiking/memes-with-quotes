import pandas as pd

# pd.options.display.max_rows = 9999

def readcsv(csv_path):
    # csv_path=os.getenv("csv")
    df = pd.read_csv(csv_path)

    # print(df.index[1])
    # print(df.loc[5])
    # print(df.columns)
    # print(df.index.size)
    df=df.fillna("nan")
    quotes=df['Quote']
    author=df['author']
    number_of_rows=len(df.index)

    # print(quotes,author,number_of_rows)
    return quotes,author,df.index.size
# print(df['author'])
# for num in quotes:
#     print(num)\
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    readcsv(os.getenv("csv"))

