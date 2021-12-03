import pandas as pd
import csv
import numpy as np

BASE_PATH = "/Users/NaoYamada/Desktop/django/ff/algorithm_check/"
class csv_controller4user():
    def init_csv(self, file_name):
        # CSV ファイルの初期化
        df = pd.DataFrame(columns=['day', 'recieve_num', 'is_logedin'],)
        df.to_csv(BASE_PATH + file_name+".csv", index=False, header=True)

    def add_one_line(self, file_name, idx_name, receive_num, is_logedin):
        df = pd.read_csv(BASE_PATH + file_name+".csv", index_col=0)
        df.loc[idx_name] = [receive_num, is_logedin]
        df.to_csv(BASE_PATH + file_name+".csv", index=True, header=True)

    def incriment_receive_num(self, file_name, idx_name):
        df = pd.read_csv(BASE_PATH + file_name+".csv", index_col=0)
        recieve_num = df.loc[idx_name].recieve_num + 1
        is_logedin = df.loc[idx_name].is_logedin
        df.loc[idx_name] = [recieve_num, is_logedin]
        df.to_csv(BASE_PATH + file_name+".csv", index=True, header=True)
        
    def record_logedin(self, file_name, idx_name):
        df = pd.read_csv(BASE_PATH + file_name+".csv", index_col=0)
        recieve_num = df.loc[idx_name].recieve_num
        is_logedin = True
        df.loc[idx_name] = [recieve_num, is_logedin]
        df.to_csv(BASE_PATH + file_name+".csv", index=True, header=True)
        
    def get_day(self):
        with open('/Users/NaoYamada/Desktop/django/ff/day.txt') as f:
            l = f.readlines()
            day = l[0]
        return day

# class csv_controller4rank():
#     def init_csv(self, fale_name, columns):
#         # CSV ファイルの初期化
#         df = pd.DataFrame(columns=columns,)
#         df.to_csv(file_name+".csv", index=False, header=True)

#     def add_one_line(self, file_name, idx_name, receive_num, is_logedin):
#         df = pd.read_csv(file_name+".csv", index_col=0)
#         df.loc[idx_name] = [receive_num, is_logedin]
#         df.to_csv(file_name+".csv", index=True, header=True)

#     def incriment_receive_num(self, file_name, idx_name):
#         df = pd.read_csv(file_name+".csv", index_col=0)
#         recieve_num = df.loc[idx_name].recieve_num + 1
#         is_logedin = df.loc[idx_name].is_logedin
#         df.loc[idx_name] = [recieve_num, is_logedin]
#         df.to_csv(file_name+".csv", index=True, header=True)
        
#     def record_logedin(self, file_name, idx_name):
#         df = pd.read_csv(file_name+".csv", index_col=0)
#         recieve_num = df.loc[idx_name].recieve_num
#         is_logedin = True
#         df.loc[idx_name] = [recieve_num, is_logedin]
#         df.to_csv(file_name+".csv", index=True, header=True)
        
#     def get_day(self):
#         with open('day.txt') as f:
#             l = f.readlines()
#             day = l[0]
#         return day