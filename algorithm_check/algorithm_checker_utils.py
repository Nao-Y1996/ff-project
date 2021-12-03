import pandas as pd
import csv
import numpy as np
import os

BASE_PATH = os.path.dirname(__file__)
USER_DATA_DIR = BASE_PATH + '/user_data/'
# print('='*20)
# print(BASE_PATH)
class csv_controller4user():
    def init_csv(self, file_name):
        if not os.path.exists(USER_DATA_DIR):
            os.mkdir(USER_DATA_DIR)
        else:
            import shutil
            shutil.rmtree(USER_DATA_DIR)
            # os.listdir(USER_DATA_DIR)
            os.mkdir(USER_DATA_DIR)
        # CSV ファイルの初期化
        df = pd.DataFrame(columns=['day', 'recieve_num', 'is_logedin'],)
        df.to_csv(USER_DATA_DIR+file_name+".csv", index=False, header=True)

    def add_one_line(self, file_name, idx_name, receive_num, is_logedin):
        df = pd.read_csv(USER_DATA_DIR+file_name+".csv", index_col=0)
        df.loc[idx_name] = [receive_num, is_logedin]
        df.to_csv(USER_DATA_DIR+file_name+".csv", index=True, header=True)

    def incriment_receive_num(self, file_name, idx_name):
        df = pd.read_csv(USER_DATA_DIR+file_name+".csv", index_col=0)
        recieve_num = df.loc[idx_name].recieve_num + 1
        is_logedin = df.loc[idx_name].is_logedin
        df.loc[idx_name] = [recieve_num, is_logedin]
        df.to_csv(USER_DATA_DIR+file_name+".csv", index=True, header=True)
        
    def record_logedin(self, file_name, idx_name):
        df = pd.read_csv(USER_DATA_DIR+file_name+".csv", index_col=0)
        recieve_num = df.loc[idx_name].recieve_num
        is_logedin = True
        df.loc[idx_name] = [recieve_num, is_logedin]
        df.to_csv(USER_DATA_DIR+file_name+".csv", index=True, header=True)
        
    def get_day(self):
        with open(BASE_PATH + '/day.txt') as f:
            l = f.readlines()
            day = l[0]
        return day

