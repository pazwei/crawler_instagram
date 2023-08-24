
'''
import
'''
import sys
sys.path.append(r'D:\brady\python\package')

import json
import crawler_helper as ch
from selenium import webdriver


'''
參數
'''
# 要搜尋的關鍵字
keyword = 'marrymydeadbody'


'''
config
'''
# 先建立 dict 格式的 account.json 檔, 並取得其中的帳號密碼
with open('config.json', 'r', encoding='utf-8') as file_config:
    # 會是 str 類型, 長得就是讀入檔案的模樣(json樣)
    str_config = file_config.read()
# 變成 disc 格式
dict_config = json.loads(str_config)

# chromedriver 的路徑, 不是瀏覽器
PATH_CHROMEDRIVER = dict_config['path']['chromedriver']
# instagram 的首頁
URL_INSTAGRAM = dict_config['url']['instagram']
# 登入帳號
ACCOUNT_USERNAME = dict_config['account']['username']
# 登入密碼
ACCOUNT_PASSWORD = dict_config['account']['password']





if __name__ == '__main__':
    
    '''
    瀏覽器工具的設置
    '''
    # 啟動瀏覽器工具的選項
    options = webdriver.ChromeOptions()
    # # 不開啟實體瀏覽器背景執行
    # options.add_argument('--headless')
    # 最大化視窗
    options.add_argument('--start-maximized')
    # 開啟無痕模式
    options.add_argument('--incognito')
    # 禁用彈出攔截
    options.add_argument('--disable-popup-blocking')
    
    
    
    '''
    數據放置
    '''
    # 放置爬取的資料
    list_data = []
    
    # 放置圖片的超連結 
    set_link = set()
    
    # 設定 set 物件, 放置圖片連結, 協助過濾重複的元素
    # - 因為 IG 會把只留當前圖片與前一張與後一張, 總共3張, 其他不會留
    set_temp = set()
    
    
    
    '''
    selenium
    '''
    # 啟用
    service = webdriver.chrome.service.Service(executable_path=PATH_CHROMEDRIVER)
    driver = webdriver.Chrome(service=service, options=options)
    # 前往首頁
    driver.get(URL_INSTAGRAM)
    
    ch.login(driver, account_username=ACCOUNT_USERNAME, account_password=ACCOUNT_PASSWORD)
    # 再次前往首頁
    driver.get(URL_INSTAGRAM)
    ch.notice(driver)
    ch.search(driver, keyword)
    list_link = ch.scroll_link(driver, set_link, limit=20)
    
    # for link in list_link[0:5]:
    for link in list_link:
    # for link in list_link_continue_1:
        ch.parse(driver, set_temp, link, list_data)
    
    ch.path_folder(keyword)
    ch.save_json(keyword, list_data)
    str_json = ch.open_json(keyword)
    ch.download_img(keyword, str_json)


# ['CkAO15UPV61' in x for x in list_link].index(True)

# list_link_continue_1 = list_link[223:]
# ['p/CnJftzbvl7Y' in x for x in list_link_continue_1]

# list_link_finish_1 = list_link[:152]
# ','.join(['"' + i.replace('https://www.instagram.com/p/', '').replace('/', '') + '"' for i in list_link_finish_1])
# ','.join(['"' + i.replace('https://www.instagram.com/p/', '').replace('/', '') + '"' for i in list_link_continue_1])


# # 輸出JSON檔案
# json_str = json.dumps(list_link)
# with open('list.json', 'w') as file:
#     file.write(json_str)
# 讀取JSON檔案
# with open('list.json', 'r') as file:
#     json_str = file.read()

# # 將JSON轉換回list
# list_link = json.loads(json_str)
# print(list_link)




# =============================================================================
# # 讀入 json 檔, 是先前爬蟲下來的數據
# df = pd.read_json(f'{keyword}\\post_{keyword}.json')
# # 將部分為 list 的欄位擴展為 row, 同一個貼文會擴展為多筆留言的 row, 並重置 index, 否則同一個貼文的擴展會是同一個 index
# df_explode = df.explode(['list_comment_username', 'list_comment_content', 'list_comment_time', 'list_comment_like']).reset_index(drop=True)
# # 將擴展的欄位重新命名欄位名稱
# df_explode = df_explode.rename(columns={
#     'list_comment_username': 'comment_username',
#     'list_comment_content': 'comment_content',
#     'list_comment_time': 'comment_time',
#     'list_comment_like': 'comment_like'
#     })
# 
# # 先指定好貼文 post 數據所需要的欄位
# col_post = ['id', 'url', 'post_content', 'post_time', 'post_like']
# # 先指定好留言 comment 數據所需要的欄位
# col_comment = ['id', 'comment_username', 'comment_content', 'comment_time', 'comment_like']
# 
# # 貼文 post 數據的 dataframe
# df_post = df.loc[:, col_post]
# # 將 like 的中文單位(萬, 億)轉換為阿拉伯數字, 先定義一個針對 str 的函式, 後面放入欄位的 map 裡進行迭代
# def like_num(x):
#     if '萬' in x:
#         return float(x.replace('萬', '')) * 10000
#     elif '億' in x:
#         return float(x.replace('億', '')) * 100000000
#     else:
#         return float(x)
# # 將 like 轉為阿拉伯數字
# df_post.post_like = df_post.post_like.astype(str).map(like_num)
# # 將 time 轉為 datetime 類型, 格式為 YYYY-MM-DD hh:mm:ss
# df_post.post_time = pd.to_datetime(df_post.post_time, utc=False).dt.tz_localize(None)
# 
# # 留言 comment 數據的 dataframe, 然後去重
# df_comment = df_explode.loc[:, col_comment].drop_duplicates()
# # 將 like 轉為阿拉伯數字
# df_comment.comment_like = df_comment.comment_like.astype(str).map(like_num)
# # 將 time 轉為 datetime 類型, 格式為 YYYY-MM-DD hh:mm:ss
# df_comment.comment_time = pd.to_datetime(df_comment.comment_time, format='%Y-%m-%dT%H:%M:%S.000Z')
# 
# 
# # 存庫
# import sqlite3
# 
# # 這次爬蟲下來的數據的 id, 將在後面刪除庫裡的這些 id, 再將這次爬蟲下來的存入庫裡, 避免重複存庫
# dup_id = ','.join("'" + df_post['id'] + "'")
# 
# # 建立與庫的連接, 使用 with 語句就可以在執行完成後會自動關閉連接, 就不需要 con.close()
# with sqlite3.connect(f'database\{keyword}.db') as con:
#     # 建立游標, 使用 with 語句就可以在執行完成後會自動關閉游標, 就不需要 cursor.close()
#     cursor = con.cursor()
#     
#     ### 建立游標後, 可以開始執行事務, 對數據庫做操作 ###
#     try:
#         # 建立貼文 post 表, 如果不存在則建立
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS post(
#             id VARCHAR(100),
#             url VARCHAR,
#             post_content VARCHAR,
#             post_time DATETIME,
#             post_like INT,
#             PRIMARY KEY (id)
#             )
#         ''')
#         
#         # 建立留言 comment 表, 如果不存在則建立
#         cursor.execute('''
#         CREATE TABLE IF NOT EXISTS comment(
#             id VARCHAR(100),
#             comment_username VARCHAR,
#             comment_content VARCHAR,
#             comment_time DATETIME,
#             comment_like INT,
#             CONSTRAINT id_comment_username_time PRIMARY KEY (id, comment_username, comment_time)
#             )
#         ''')
# 
#         # 對 post 表刪除這次爬蟲下來的數據的 id, 避免重複存庫
#         cursor.execute(f'DELETE FROM post WHERE `id` in ({dup_id})')
#         # 將 post 表寫入庫中
#         df_post.to_sql('post', con, if_exists='append', index=False)
#         
#         # 對 comment 表刪除這次爬蟲下來的數據的 id, 避免重複存庫
#         cursor.execute(f'DELETE FROM comment WHERE `id` in ({dup_id})')
#         # 將 comment 表寫入庫中
#         df_comment.to_sql('comment', con, if_exists='append', index=False)
#     
#     # 不管上面執行事務有沒有出錯, 都關閉游標
#     finally:
#         cursor.close()
# 
#     # 提交操作, 將事務中的修改可以永久的保存到數據庫中
#     con.commit()
#     
#     ### 自動關閉與庫的連接 ###
#     
# 
# df_post_read = pd.read_sql_query('SELECT * FROM post', con)
# df_comment_read = pd.read_sql_query('SELECT * FROM comment', con)
# 
# df_post.info()
# df_post_read.info()
# df_comment.info()
# df_comment_read.info()
# =============================================================================







# =============================================================================
# # 登入
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def login(account_username: 'str', account_password: 'str'):
#     try:
#         # 等待直到互動元素出現
#         # WebDriverWait: 等10秒
#         # until: 直到什麼事情發生
#         # EC: 期待的條件
#         # presence_of_element_located: 有元素出現
#         driver_username = WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located(
#                 # 用CSS選擇器的方式
#                 (By.CSS_SELECTOR, 'input[name="username"]')
#                 )
#             )
#         # 因為帳號元素出現的話, 密碼元素也會出現, 就不再做等待直到互動元素出現, 而是直接找到元素
#         driver_password = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
#         
#         
#         # 清空帳號密碼
#         driver_username.clear()
#         driver_password.clear()
#         
#         # 輸入帳號密碼
#         driver_username.send_keys(account_username)
#         driver_password.send_keys(account_password)
#         
#         # 登入鍵
#         driver_login = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')
# 
#         # 點擊登入鍵
#         driver_login.click()
#         
#         # 強制等待
#         time.sleep(3)
#         print('Login - Finish')
#         
#     # 逾時的例外處理
#     except:
#         print('等待逾時')
#         time.sleep(2)
#         # 關閉
#         driver.quit()
# 
# 
# # 關閉跳出視窗
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def notice():
#     WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.CSS_SELECTOR, 'button._a9--._a9_1'))
#         ).click()
# 
# 
# # 搜尋關鍵字並點擊
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def search(keyword: 'str'):
#     # 搜尋按鈕元素, 等待直到互動元素出現
#     driver_search_button = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, '//div[2]/span/div'))
#         )
#     # 點擊搜尋按鈕
#     driver_search_button.click()
#     
#     # 搜尋關鍵字元素
#     driver_search_input = WebDriverWait(driver, 10).until(
#         EC.presence_of_element_located((By.XPATH, '//body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div[1]/div/input'))
#         )
#     # 輸入搜尋關鍵字
#     driver_search_input.send_keys(keyword)
#     time.sleep(1)
#     # 送出搜尋關鍵字, IG 這邊要送出2次且不能間隔太短
#     driver_search_input.send_keys(Keys.RETURN)
#     time.sleep(1)
#     driver_search_input.send_keys(Keys.RETURN)
#     
#     # 強制等待
#     time.sleep(3)
#     print('Search - Finish')
# 
# 
# # 將頁面往下滾動指定次數
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def scroll(limit: int=3):
#     '''
#     total_height: 瀏覽器內部的高度
#     offset: 當前捲動的量(高度)
#     count: 累計無效滾動次數
#     limit: 最大無效滾動次數
#     wait_second: 每次滾動後的強制等待時間
#     '''
#     total_height = 0
#     offset = 0
#     count = 0
#     count_no_work = 0
#     limit_no_work = 3
#     wait_second = 3
#     
#     # 在捲動到沒有元素動態產生前, 持續捲動
#     while (count < limit and count_no_work < limit_no_work):
# 
#         # 每次移動一定高度
#         offset = driver.execute_script(
#             'return window.document.documentElement.scrollHeight;'
#             )
#         
#         # 捲動的 js code
#         # 雙重大括號為跳脫
#         js_code = f'''
#         window.scrollTo({{
#             top: {offset},
#             behavior: 'smooth'
#             }});
#         '''
#         
#         # 執行 js code
#         driver.execute_script(js_code)
#         
#         # 強制等待
#         time.sleep(wait_second)
#         
#         # 透過 js 來取得捲動後的當前總高度
#         total_height = driver.execute_script(
#             'return window.document.documentElement.scrollHeight;'
#             )
# 
#         if limit > 0:
#             count += 1
# 
#         # 經過計算, 如果滾動距離(offset)大於等於視窗內部總高度(total_height), 代表已經到底了
#         if offset >= total_height:
#             count_no_work += 1
# 
#     # 強制等待
#     time.sleep(3)
#     print('Scroll - Finish')
# 
# 
# # 取得頁面中所有貼文的網址
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def get_links():
#     # 取得元素(a 超連結)的集合
#     element_a = driver.find_elements(
#         By.CSS_SELECTOR,
#         'div._ac7v._al3n > div._aabd._aa8k._al3l > a'
#         )
#     # 以迴圈逐一檢視元素
#     for index, a in enumerate(element_a):
#         # print(index)
#         # 取得元素的連結
#         link_a = a.get_attribute('href')
#         # print(link_a)
#         # 將連結放到 list 當中
#         list_link.append(link_a)
#         
#     # 強制等待
#     time.sleep(3)
#     print('Get Links - Finish')
# 
# 
# # 對逐個網頁的連結內容進行解析
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def parse(link):
#     # 清空暫存的圖片
#     set_temp.clear()
#     
#     # 走訪迴圈當圈的頁面
#     driver.get(link)
#     
#     # 取得 ig 連結的 id
#     regex_ = r'\/p\/([a-zA-Z0-9-_]+)\/'
#     page_id = re.search(regex_, link).group(1)
#     
#     # 強制等待
#     time.sleep(2)
#     
#     # 點擊更多留言
#     is_comment_more = True
#     # 一直點, 直到不能點了為止
#     while is_comment_more:
#         try:
#             # 登入鍵
#             button_comment_more = driver.find_element(By.XPATH, '//div/ul/li/div/button')
#             button_comment_more.click()
#             time.sleep(2)
#         except:
#             is_comment_more = False
#             print('Button Comment More - Finish')
# 
# 
#     # 點開所有留言的回覆
#     bottons = driver.find_elements(By.XPATH, '//ul/li/div/button')
#     for b in bottons:
#         print(b.text)
#         # 如果顯示為 "查看回覆", 則點擊
#         while bool(re.search('查看', b.text)):
#             b.click()
#             time.sleep(1)
#     print('Button Comment reply - Finish')
# 
#     # html 原始碼
#     html = driver.page_source
#     # 引數 "lxml" 要放的參數是解析器
#     soup = Soup(html, 'lxml')
# 
# 
#     # 留言內容
#     # 用標籤
#     tag_comment_content = soup.find_all('span', {'class': re.compile(r'^_aacl')})
#     # 用CSS編輯器
#     tag_comment_content = soup.select('div._a9zs > span')
#     list_comment_content = [cc.text for cc in tag_comment_content]
# 
# 
# 
#     # 留言時間
#     # 用標籤
#     tag_comment_time = soup.find_all('time', {'class': '_a9ze _a9zf'})
#     # 用CSS編輯器
#     tag_comment_time = soup.select('span > a > time')
#     list_comment_time = [ct['datetime'] for ct in tag_comment_time]
# 
# 
#     # 各留言的讚, 如果是回覆就代表該留言沒有取得任何的讚
#     tag_comment_like = soup.select('span > button:nth-child(2) > span')
#     list_comment_like = [cl.text for cl in tag_comment_like]
#     # 將非數字去除, 留下數值(讚的個數), 如果沒有讚的話變成0
#     list_comment_like = [int(re.sub('\D', '', cl) or 0) for cl in list_comment_like]
#     
#     
#     
#     # 貼文內容
#     tag_post_content = soup.select('div._a9zs > h1')
#     post_content = tag_post_content[0].get_text()
#     
#     # 貼文時間
#     # 用標籤
#     tag_post_time = soup.find_all('time', {'class': '_aaqe'})
#     # 用CSS編輯器
#     tag_post_time = soup.select('a > span > time')
#     post_time = tag_post_time[0]['datetime']
#     
#     
#     # 貼文讚數
#     tag_post_like = soup.select('section > div > div > span > a > span > span')
#     post_like = tag_post_like[0].text
# 
#         
#     '''
#     判斷是否有向右的按鈕
#     - 若有, 則代表會有多個 li
#     - 若無, 則代表只有一個 li
#     
#     由於 find_elements 會回傳 list 格式,
#     - 所以可以用 len() 來取得元素的長度, 藉此判斷元素使否存在
#     '''
#     
#     # 當有右箭頭可以按的時候, 代表頁面中同時有多張圖片(也有可能有影片)
#     if len(driver.find_elements(By.CSS_SELECTOR, 'button._afxw._al46._al47')) > 0:
#         # 取得多元素的資訊(圖片)
#         while len(driver.find_elements(By.CSS_SELECTOR, 'button._afxw._al46._al47')) > 0:
#             # 按下向右的按鈕
#             driver.find_element(By.CSS_SELECTOR, 'button._afxw._al46._al47').click()
#             
#             # 取得當前所有 li
#             element_li = driver.find_elements(By.CSS_SELECTOR, 'li._acaz')
#             li = element_li[0]
#             # 各別取得 li 底下的圖片
#             for li in element_li:
#                 # if len(li.find_elements(By.CSS_SELECTOR, 'li > div > div > div > div > div > img')) > 0:
#                 if len(li.find_elements(By.CSS_SELECTOR, 'img')) > 0:
#                     # 取得 img 的 src
#                     src_img = li.find_element(By.CSS_SELECTOR, 'li > div > div > div > div > div > img').get_attribute('src')
#                     
#                     # 加入圖片到 set 中
#                     set_temp.add(src_img)
#                 # # 沒有圖片 或是 影片
#                 # else:
#                     # pass
#             
#             # 強制等待, 每睡1秒, 就按一次向右的按鈕
#             time.sleep(1)
#     # 如果沒有右箭頭, 代表是單張的照片或是影片
#     else:
#         if len(driver.find_elements(By.CSS_SELECTOR, 'div > div > div._aagv > img')) > 0:
#             # 取得 img 的 src
#             src_img = driver.find_element(By.CSS_SELECTOR, 'div > div > div._aagv > img').get_attribute('src')
#             # 加入圖片到 set 中
#             set_temp.add(src_img)
#         # 沒有圖片 或是 影片
#         else:
#             pass
# 
#     # 整合資料
#     list_data.append({
#         'id': page_id,
#         'url': link,
#         'post_content': post_content,
#         'post_time': post_time,
#         'post_like': post_like,
#         'list_comment_content': list_comment_content,
#         'list_comment_time': list_comment_time,
#         'list_comment_like': list_comment_like,
#         'list_download': list(set_temp)
#         })
#     
#     # 強制等待
#     time.sleep(3)
#     print('Parse - ' + page_id + ' - Finish')
# 
# 
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def path_folder(keyword):
#     # 如果資料夾路徑不存在, 則以作業系統建立資料夾
#     if not os.path.isdir(keyword):
#         os.mkdir(keyword)
# 
# # 存成 json
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def save_json(keyword):
#     path_file = keyword + '\\post_' + keyword + '.json'
#     fp = open(path_file, 'w', encoding='utf-8')
#     # ensure_ascii: 避免亂碼
#     fp.write(json.dumps(list_data, ensure_ascii=False))
#     fp.close()
#     
#     # 強制等待
#     time.sleep(3)
#     print('Save json - Finish')
# 
# 
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def open_json(keyword):
#     # 開啟 json 檔案
#     path_file = keyword + '\\post_' + keyword + '.json'
#     fp = open(path_file, 'r', encoding = 'utf-8')
#     # 取得 json 字串
#     str_json = fp.read()
#     # 關閉檔案
#     fp.close()
#     
#     # 強制等待
#     print('Open json - Finish')
#     return str_json
# 
# 
# @benchmark_with_logger(logger)
# @log_factory(logger)
# def download_img(keyword, str_json):
#     # 如果資料夾路徑不存在, 則以作業系統建立資料夾
#     path_folder = os.path.join(keyword + '\\img')
#     if not os.path.isdir(path_folder):
#         os.mkdir(path_folder)
#     
#     # 將 json 轉成 list (裡面是 dict 集合)
#     list_result = json.loads(str_json)
#     # 把 list_result 底下的 dict 找出來
#     for dict_obj in list_result:
#         # dict_obj 底下有個 list_download 屬性, 它對應的是個 list, 將 list 裡面所有的 url 找出來
#         for index, download_url in enumerate(dict_obj['list_download']):
#             str_file_name = dict_obj['id'] + '_' + str(index) + '.jpg'
#             # os.system(f'curl "{download_url}" -o ./{path_folder}/{str_file_name}')
#             save_as = os.path.join(path_folder, str_file_name)
#             wget.download(download_url, save_as)
#         print(f'Download img: {dict_obj["id"]}')
#     print('Download img - Finish')
# 
# =============================================================================





# try:
#     int(link)
# except Exception as error:
#     allLogger.error(f'failed', exc_info=True)
#     allLogger.exception(error)

# #1.setup log path and create log directory
# logName = 'MyProgram.log'
# logDir = 'log'
# logPath = logDir + '/' + logName

# #create log directory 
# os.makedirs(logDir,exist_ok=True)

# #2.create logger, then setLevel
# allLogger = logging.getLogger('allLogger')
# allLogger.setLevel(logging.DEBUG)

# #3.create file handler, then setLevel
# #create file handler
# fileHandler = logging.FileHandler(logPath,mode='a')
# fileHandler.setLevel(logging.INFO)

# #4.create stram handler, then setLevel
# #create stream handler
# streamHandler = logging.StreamHandler()
# streamHandler.setLevel(logging.WARNING)

# #5.create formatter, then handler setFormatter
# AllFormatter = logging.Formatter("%(asctime)s - [line:%(lineno)d] - %(levelname)s: %(message)s")
# fileHandler.setFormatter(AllFormatter)
# streamHandler.setFormatter(AllFormatter)

# #6.logger addHandler
# allLogger.addHandler(fileHandler)
# allLogger.addHandler(streamHandler)

# #7.start logging
# allLogger.debug('This is debug level log.')
# allLogger.info('This is info level log.')
# allLogger.warning('This is warning level log.')
# allLogger.error('This is error level log.')
# allLogger.critical('This is critical level log.')

# #8.logger remove handler
# allLogger.removeHandler(streamHandler)
# allLogger.removeHandler(fileHandler)



# @log_exception
# def xxx():
#     int(link)
# link='gg'
# xxx()
# xxx.__name__
# xxx.__module__
# xxx.__doc__
# xxx.__code__





