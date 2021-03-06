import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
import random
import pandas as pd
import csv
import os
import bs4
import numpy as np


DAYS = 0
HOURS=9
MINUTES=2
SEND_NUM_LIMIT = 4
# from webdriver_manager.chrome import ChromeDriverManager

# driver = webdriver.Chrome(ChromeDriverManager().install())
# options = webdriver.FirefoxOptions()
# options.add_argument(
#     '--user-agent= Mozilla/5.0 (Linux; U; Android 2.3.5; ja-jp; T-01D Build/F0001) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1')
# .find_element(by=By.XPATH, value="//input[@type='text']")


class ffChecker():
    def __init__(self):
        # self.driver = webdriver.Firefox(executable_path=os.path.abspath('')+'/chromedriver')
        self.driver = webdriver.Chrome(executable_path=os.path.abspath('')+'/chromedriver')
        url = 'http://127.0.0.1:8000/'
        self.driver.get(url)

    def write_with_xpath(self, xpath, send_word, wait_time=20):
        WebDriverWait(self.driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        self.driver.find_element(by=By.XPATH, value=xpath).send_keys(send_word)

    def click_with_xpath(self, xpath, wait_time=10):
        # 最大待機時間（秒）wait_time = 10
        # xpathの要素が見つかるまで待機。
        WebDriverWait(self.driver, wait_time).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        # クリック
        self.driver.find_element(by=By.XPATH, value=xpath).click()

    def login(self,username):
        # ログイン情報
        email = username + '@django.com'
        login_pw = username + '1111'
        # 最大待機時間（秒）
        # wait_time = 30

        # IDを入力
        email_xpath = '//*[@id="id_username"]'
        self.write_with_xpath(xpath=email_xpath, send_word=email)
        # パスワードを入力
        login_pw_xpath = '//*[@id="id_password"]'
        self.write_with_xpath(xpath=login_pw_xpath, send_word=login_pw)
        time.sleep(1)  # クリックされずに処理が終わるのを防ぐために追加。

        # ログイン
        login_button_xpath = '/html/body/div/form/input[2]'
        self.click_with_xpath(login_button_xpath)


    def create_users(self,username,phnenumber):
        
        # ユーザー追加ページ
        self.driver.get('http://localhost:8000/admin/users/customuser/add/')

        # ユーザー情報の入力
        self.write_with_xpath('//*[@id="id_email"]',username+'@django.com') # email
        self.write_with_xpath('//*[@id="id_username"]',username) # username
        self.write_with_xpath('//*[@id="id_phone_number"]',phnenumber) # phnenumber
        self.write_with_xpath('//*[@id="id_password1"]',username+'1111') # pass
        self.write_with_xpath('//*[@id="id_password2"]',username+'1111') # pass confirmation
        self.click_with_xpath('//*[@id="customuser_form"]/div/div/input[1]')
        if self.driver.current_url == 'http://localhost:8000/admin/users/customuser/add/':
            is_success = False
        else:
            is_success = True
        return is_success
        time.sleep(1)
    
    def create_userinfo(self, username):
            
        # userInfo作成ページ
        self.driver.get('http://localhost:8000/admin/users/userinfo/add/')
        
        dropdown = self.driver.find_element_by_id('id_user')
        select = Select(dropdown)
        time.sleep(1)
        select.select_by_visible_text(username)
        time.sleep(1)

        dropdown = self.driver.find_element_by_id('id_nationality')
        select = Select(dropdown)
        time.sleep(1)
        select.select_by_visible_text('Japan')
        
        self.click_with_xpath('//*[@id="userinfo_form"]/div/div/input[1]')
        if self.driver.current_url == 'http://localhost:8000/admin/users/userinfo/':
            is_success = True
        else:
            is_success = False
        return is_success
        
    

if __name__ == '__main__':
    checker = ffChecker()
    user_num = 50

    checker.driver.get('http://localhost:8000/admin/')
    # admin ログイン
    checker.write_with_xpath('//*[@id="id_username"]',"admin@django.com")
    checker.write_with_xpath('//*[@id="id_password"]',"admin")
    checker.click_with_xpath('//*[@id="login-form"]/div[3]/input')
    
    # adminのuser_info作成
    # _ = checker.create_userinfo(username='admin')
    
    # Executedfunctionの登録
    checker.driver.get('http://localhost:8000/admin/postapp/executedfunction/add/')
    # update_seiding_priorityを追加
    checker.write_with_xpath('//*[@id="id_name"]', 'update_seiding_priority')
    checker.click_with_xpath('//*[@id="executedfunction_form"]/div/div/input[2]') # save and add another
    # update_count_for_priorityを追加
    checker.write_with_xpath('//*[@id="id_name"]', 'update_count_for_priority')
    checker.click_with_xpath('//*[@id="executedfunction_form"]/div/div/input[1]') # save
    
    
    
    # userとuserInfoの作成
    user_count  =0
    while user_count < user_num:
        
        username = 'user_'+str(user_count)
        phnenumber = '+81'
        for _ in range(9):
            phnenumber += str(random.randrange(1, 10))
        is_success = checker.create_users(username=username, phnenumber=phnenumber)
        if is_success:
            is_success_userinfo  = False
            while True:
                is_success_userinfo = checker.create_userinfo(username=username)
                if is_success_userinfo:
                    user_count += 1
                    print(user_count)
                    break
    
    # admin ログアウト
    checker.click_with_xpath('//*[@id="user-tools"]/a[3]')
"""
    

    
    # userの選択
    user_login_rate = np.random.normal(
                            loc   = 0,      # 平均
                            scale = 1,      # 標準偏差
                            size  = user_num# 出力配列のサイズ(タプルも可)
                            )
    # 0~1で正規化
    _min = user_login_rate.min()
    _max = user_login_rate.max()
    user_login_rate = (user_login_rate - _min).astype(float) / (_max - _min).astype(float)
    user_login_rate.sort()
    
    users_name = ["user_0","user_1","user_2","user_3","user_4","user_5","user_6","user_7","user_8","user_9",
                    "user_10","user_11","user_12","user_13","user_14","user_15","user_16","user_17","user_18",
                    "user_19","user_20","user_21","user_22","user_23","user_24","user_25","user_26","user_27",
                    "user_28","user_29","user_30","user_31","user_32","user_33","user_34","user_35","user_36",
                    "user_37","user_38","user_39","user_40","user_41","user_42","user_43","user_44","user_45",
                    "user_46","user_47","user_48","user_49","user_50","user_51","user_52","user_53","user_54",
                    "user_55","user_56","user_57","user_58","user_59","user_60","user_61","user_62","user_63",
                    "user_64","user_65","user_66","user_67","user_68","user_69","user_70","user_71","user_72",
                    "user_73","user_74","user_75","user_76","user_77","user_78","user_79","user_80","user_81",
                    "user_82","user_83","user_84","user_85","user_86","user_87","user_88","user_89","user_90",
                    "user_91","user_92","user_93","user_94","user_95","user_96","user_97","user_98","user_99"]


    for user_idx, login_rate in enumerate(user_login_rate):
        rand = random.random()
        if login_rate >= rand:
            continue

        username = users_name[user_idx]
        # ログイン画面へ
        checker.driver.get('http://localhost:8000/login')
        checker.login(username)

        # トーク一覧へ http://localhost:8000/post/talk_all/
        checker.driver.get('http://localhost:8000/post/talk_all/')
        print('=====================================================')
        talk_detail_urls = []
        for i in range(1000):
            #未読の時にトーク詳細へのリンクを取得する
            try:
                status = checker.driver.find_element(by=By.XPATH, value='//*[@id="talks"]/table/tbody/tr['+str(i+2)+']/td[1]').text
                if status=='Unread':
                    talk_detail_urls.append(checker.driver.find_element(by=By.XPATH, value='//*[@id="talks"]/table/tbody/tr['+str(i+2)+']/td[2]/a').get_attribute("href"))
            except:
                pass
        # 一定の割合で（7割）返信
        if len(talk_detail_urls)!=0:
            reply_rate = 0.7
            for talk_detail_url in random.shuffle(talk_detail_urls)[0:int(len(talk_detail_urls)*reply_rate)]:
                checker.driver.get(talk_detail_url)
                # 返信
                content = '返信だYO！！！'*random.randint(1, 20)
                checker.write_with_xpath('//*[@id="id_content"]',send_word=content)
                checker.click_with_xpath('/html/body/div/form/button')
                break

        # 新規投稿 ランダムな数postする
        max_post_num = 3
        post_num = random.randint(1, max_post_num)
        for i in range(post_num):
                # 投稿ページへ
                checker.driver.get('http://localhost:8000/post/talk_create/')
                # 投稿
                content = 'やあ、僕はショータだよ！！！'*random.randint(1, 20)
                checker.write_with_xpath('//*[@id="id_content"]',send_word=content)
                checker.click_with_xpath('//html/body/div/div/input')
                #プロフィールへ
                checker.driver.get('http://127.0.0.1:8000/profile')
         # logout
        checker.click_with_xpath('//*[@id="navbarNavAltMarkup"]/div/a[2]')



    time.sleep(5)
    checker.driver.close()

# //*[@id="talks"]/table/tbody/tr[2]/td[2]/a
# //*[@id="talks"]/table/tbody/tr[3]/td[2]/a

//*[@id="talks"]/table/tbody/tr[2]/td[1]
//*[@id="talks"]/table/tbody/tr[3]/td[1]

//*[@id="talks"]/table/tbody/tr[2]/td[2]/a
//*[@id="talks"]/table/tbody/tr[3]/td[2]/a
//*[@id="talks"]/table/tbody/tr[3]/td[2]/a

//*[@id="talks"]/table/tbody/tr[2]/td[1]

"""
