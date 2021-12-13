import time
from selenium.common.exceptions import NoSuchElementException
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
import algorithm_checker_utils
import sys

# from webdriver_manager.chrome import ChromeDriverManager

# driver = webdriver.Chrome(ChromeDriverManager().install())
# options = webdriver.FirefoxOptions()
# options.add_argument(
#     '--user-agent= Mozilla/5.0 (Linux; U; Android 2.3.5; ja-jp; T-01D Build/F0001) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1')
# .find_element(by=By.XPATH, value="//input[@type='text']")

BASE_PATH = algorithm_checker_utils.BASE_PATH

class ffChecker():
    def __init__(self):
        # self.driver = webdriver.Firefox(executable_path=os.path.abspath('')+'/chromedriver')
        self.driver = webdriver.Chrome(executable_path=BASE_PATH +'/chromedriver')
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
        login_pw = username
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
        if self.driver.current_url == 'http://localhost:8000/profile':
            login_success = True
        else:
            login_success = False
        return login_success
        


    def create_users(self,username,phnenumber):
        
        # ユーザー追加ページ
        self.driver.get('http://localhost:8000/admin/users/customuser/add/')

        # ユーザー情報の入力
        self.write_with_xpath('//*[@id="id_email"]',username+'@django.com') # email
        self.write_with_xpath('//*[@id="id_username"]',username) # username
        self.write_with_xpath('//*[@id="id_phone_number"]',phnenumber) # phnenumber
        self.write_with_xpath('//*[@id="id_password1"]',username) # pass
        self.write_with_xpath('//*[@id="id_password2"]',username) # pass confirmation
        self.click_with_xpath('//*[@id="customuser_form"]/div/div/input[1]')
        if self.driver.current_url == 'http://localhost:8000/admin/users/customuser/add/':
            is_success = False
        else:
            is_success = True
        return is_success
        # time.sleep(1)
    
    def create_userinfo(self, username):
            
        # userInfo作成ページ
        self.driver.get('http://localhost:8000/admin/users/userinfo/add/')
        
        dropdown = self.driver.find_element_by_id('id_user')
        select = Select(dropdown)
        select.select_by_visible_text(username)
        
        dropdown = self.driver.find_element_by_id('id_nationality')
        select = Select(dropdown)
        select.select_by_visible_text('Japan')
        
        self.click_with_xpath('//*[@id="userinfo_form"]/div/div/input[1]')
        if self.driver.current_url == 'http://localhost:8000/admin/users/userinfo/':
            is_success = True
        else:
            is_success = False
        return is_success
        
    

if __name__ == '__main__':
    args = sys.argv
    checker = ffChecker()
    csv_controller = algorithm_checker_utils.csv_controller4user()
    user_num = algorithm_checker_utils.USER_NUM
    sim_days =algorithm_checker_utils.SIM_DAYS
    
    if args[1] is not None and args[1]=='init':
        
        checker.driver.get('http://localhost:8000/admin/')
        # admin ログイン
        checker.write_with_xpath('//*[@id="id_username"]',"admin@django.com")
        checker.write_with_xpath('//*[@id="id_password"]',"admin")
        checker.click_with_xpath('//*[@id="login-form"]/div[3]/input')
        
        # 既存userの削除
        checker.driver.get('http://localhost:8000/admin/users/customuser/')
        count = 1
        while True:
            try:
                if count == 1:
                    count += 1
                    continue # adminは削除しない
                check_box = checker.driver.find_element_by_xpath('//*[@id="result_list"]/tbody/tr['+str(count)+']/td[1]/input')
                print(count)
                check_box.click()
                count += 1
            except NoSuchElementException:
                if count==2:
                    print('削除するユーザーはいません')
                    break
                else:
                    delete_user_num = count-2
                    print(f'{delete_user_num}人のユーザーを削除します')
                    # print(asdf)
                    # 削除を選択
                    dropdown = checker.driver.find_element_by_xpath('//*[@id="changelist-form"]/div[1]/label/select')
                    select = Select(dropdown)
                    select.select_by_visible_text('Delete selected custom users')
                    # goボタンを押す
                    checker.click_with_xpath('//*[@id="changelist-form"]/div[1]/button')
                    time.sleep((0.2))
                    # 確認ボタンを押す
                    checker.click_with_xpath('//*[@id="content"]/form/div/input['+str(delete_user_num+3)+']')
                    time.sleep(1)
                    break
            except:
                import traceback
                traceback.print_exc()
                sys.exit()

        # adminのuser_info作成
        _ = checker.create_userinfo(username='admin')
        
        # Executedfunctionの登録
        # update_seiding_priority_rankを追加
        checker.driver.get('http://localhost:8000/admin/postapp/executedfunction/add/')
        checker.write_with_xpath('//*[@id="id_name"]', 'update_sending_priority_rank')
        checker.click_with_xpath('//*[@id="executedfunction_form"]/div/div/input[1]') # save
        # reset_count_for_priority_rankを追加
        checker.driver.get('http://localhost:8000/admin/postapp/executedfunction/add/')
        checker.write_with_xpath('//*[@id="id_name"]', 'reset_count_for_priority_rank')
        checker.click_with_xpath('//*[@id="executedfunction_form"]/div/div/input[1]') # save
        
        
        
        # userとuserInfoの作成
        user_count  = 0
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

        
        
    if args[1] is not None and args[1]=='sim':
        # userの選択
        user_login_rate = np.random.normal(
                                loc   = 0,      # 平均
                                scale = 1,      # 標準偏差
                                size  = user_num# 出力配列のサイズ(タプルも可)
                                )
        # ログイン率（0~1で正規化）
        _min = user_login_rate.min()
        _max = user_login_rate.max()
        user_login_rate = (user_login_rate - _min).astype(float) / (_max - _min).astype(float)
        user_login_rate.sort()
        with open(BASE_PATH+'/user_login_rate.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(user_login_rate)
            
        
        # 返信率
        user_reply_rate = np.random.rand(user_num)
        with open(BASE_PATH+'/user_reply_rate.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(user_reply_rate)
        
        # 投稿率
        user_newpost_rate = np.random.rand(user_num)
        with open(BASE_PATH+'/user_newpost_rate.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(user_newpost_rate)
        
        # userの名前リストの作成
        users_name = []
        for i in range(user_num):
            users_name.append('user_'+str(i))

        # user dataを保存するcsvファイルの作成
        for name in users_name:
            csv_controller.init_csv(file_name=name)
        
        df = pd.DataFrame(columns=['day']+users_name)
        df.to_csv(BASE_PATH + "/rank.csv", index=False, header=True)

        days = list(range(1, sim_days+1))
        for day in days:
            print(f' ======================== day : {day} ======================== ')
            print()

            # 日付の更新
            with open(BASE_PATH + '/day.txt', mode='w') as f:
                f.write(str(day))
                
            for name in users_name:
                csv_controller.add_one_line(file_name=name, idx_name='day'+str(day), receive_num=0, is_logedin=False)

            
            # 1日分のシミュレーション
            for user_idx, login_rate in enumerate(user_login_rate):
                username = users_name[user_idx]
                
                if login_rate <= random.random():# ログインするかどうか
                    print(f'{username} --> skip login')
                    continue
                print(f' --------- {username}  login --------- ')
                
                # ログイン画面へ
                checker.driver.get('http://localhost:8000/login')
                login_success = checker.login(username)
                if login_success:
                    print(f'ログイン成功')
                else:
                    print(f'ログイン失敗：終了')
                    sys.exit()
                time.sleep(1)
                
                # 新規投稿
                max_post_num = 3
                post_num = int((max_post_num+1) * user_newpost_rate[user_idx])
                print(f'{post_num}件投稿します')
                for i in range(post_num):
                        # 投稿ページへ
                        checker.driver.get('http://localhost:8000/post/talk_create/')
                        # 投稿
                        content = f'やあ、僕は{username}だよ！！！'*random.randint(1, 20)
                        checker.write_with_xpath('//*[@id="id_content"]',send_word=content)
                        checker.click_with_xpath('//html/body/div/div/input')
                        #プロフィールへ
                        checker.driver.get('http://127.0.0.1:8000/profile')
                

                # トーク一覧へ http://localhost:8000/post/talk_all/
                checker.driver.get('http://localhost:8000/post/talk_all/')
                talk_detail_urls = []
                for i in range(20):
                    #未読の時にトーク詳細へのリンクを取得する
                    try:
                        status = checker.driver.find_element(by=By.XPATH, value='//*[@id="talks"]/table/tbody/tr['+str(i+2)+']/td[1]').text
                        if status=='Unread':
                            talk_detail_urls.append(checker.driver.find_element(by=By.XPATH, value='//*[@id="talks"]/table/tbody/tr['+str(i+2)+']/td[2]/a').get_attribute("href"))
                    except:
                        pass
                print(f'{len(talk_detail_urls)}件の未読')
                # 一定の割合で返信
                if len(talk_detail_urls)!=0:
                    reply_rate = user_reply_rate[user_idx]# 返信するかどうか
                    random.shuffle(talk_detail_urls)
                    for talk_detail_url in talk_detail_urls[0:int(len(talk_detail_urls)*reply_rate)]:
                        is_reply = reply_rate >= random.random()
                        checker.driver.get(talk_detail_url)
                        # 返信
                        content = '返信だYO！！！'*random.randint(1, 20)
                        checker.write_with_xpath('//*[@id="id_content"]',send_word=content)
                        checker.click_with_xpath('/html/body/div/form/button')
                        break
                # logout
                checker.click_with_xpath('//*[@id="navbarNavAltMarkup"]/div/a[2]')



            # 1日分のシミュレーションが終わったかどうかを記録
            with open(BASE_PATH + '/day_end.txt', mode='w') as f:
                f.write(str(True))




        checker.driver.close()