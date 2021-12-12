import pandas as pd
import csv
import numpy as np
import os
import time
BASE_PATH = os.path.dirname(__file__)
USER_DATA_DIR = BASE_PATH + '/user_data/'
USER_NUM = 100
SIM_DAYS = 50
TALK_LIMIT_DAYS = 7
FRERUENCY_UPDATE_PRIORITY = 7
TIMING_UPDATE_PRIORITY = np.arange(1,SIM_DAYS+1, step = FRERUENCY_UPDATE_PRIORITY).tolist()
TIMING_UPDATE_PRIORITY.pop(0)
TIMING_DELETE_TALK = np.arange(1,SIM_DAYS+1, step = TALK_LIMIT_DAYS).tolist()
TIMING_DELETE_TALK.pop(0)

class csv_controller4user():
    def __init__(self):
        if not os.path.exists(USER_DATA_DIR):
            os.mkdir(USER_DATA_DIR)
        else:
            import shutil
            shutil.rmtree(USER_DATA_DIR)
            os.mkdir(USER_DATA_DIR)
    def init_csv(self, file_name):
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

