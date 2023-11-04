import pandas as pd
from pamo.constants import COLUMNS_SHOPI

class CoreDf():

    df = pd.DataFrame()

    def __init__(self) -> None:
        pass

    def set_df(self, file):
        self.df = pd.read_excel(file)

    def get_df(self):
        return self.df
    
    def get_df_columns(self):
        return self.df.columns.values

    def rename_columns(self, dic_columns):
        del(dic_columns['csrfmiddlewaretoken'])
        Change_colums={}
        for key, value in dic_columns.items():
            if value != 'N/A':
                key = key.replace('~',' ')
                Change_colums[key] = value
        self.df.rename(columns=Change_colums, inplace=True)
        return self.df[[i for i in self.df.columns if i in COLUMNS_SHOPI]]

        