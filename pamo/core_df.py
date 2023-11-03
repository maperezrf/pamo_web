import pandas as pd

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