'''
import
'''
import sys
sys.path.append(r'D:\brady\python\package')

import time
import os
import wget
import re
import json

# 計時裝飾器
from display_time import benchmark_with_logger
# logger
from logging_helper import logger
# log 裝飾器工廠
from logging_decorator import log_factory

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as Soup


# 登入
@benchmark_with_logger(logger)
@log_factory(logger)
def login(driver, account_username: 'str', account_password: 'str'):
    try:
        # 等待直到互動元素出現
        # WebDriverWait: 等10秒
        # until: 直到什麼事情發生
        # EC: 期待的條件
        # presence_of_element_located: 有元素出現
        driver_username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                # 用CSS選擇器的方式
                (By.CSS_SELECTOR, 'input[name="username"]')
                )
            )
        # 因為帳號元素出現的話, 密碼元素也會出現, 就不再做等待直到互動元素出現, 而是直接找到元素
        driver_password = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
        
        
        # 清空帳號密碼
        driver_username.clear()
        driver_password.clear()
        
        # 輸入帳號密碼
        driver_username.send_keys(account_username)
        driver_password.send_keys(account_password)
        
        # 登入鍵
        driver_login = driver.find_element(By.XPATH, '//*[@id="loginForm"]/div/div[3]/button')

        # 點擊登入鍵
        driver_login.click()
        
        # 強制等待
        time.sleep(10)
        print('Login - Finish')
        
    # 逾時的例外處理
    except:
        print('等待逾時')
        time.sleep(3)
        # 關閉
        driver.quit()


# 關閉跳出視窗
@benchmark_with_logger(logger)
@log_factory(logger)
def notice(driver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'button._a9--._a9_1'))
        ).click()


# 搜尋關鍵字並點擊
@benchmark_with_logger(logger)
@log_factory(logger)
def search(driver, keyword: 'str'):
    # 搜尋按鈕元素, 等待直到互動元素出現
    driver_search_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[2]/span/div'))
        )
    # 點擊搜尋按鈕
    driver_search_button.click()
    
    # 搜尋關鍵字元素
    driver_search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div[1]/div/input'))
        )
    # 輸入搜尋關鍵字
    driver_search_input.send_keys(keyword)
    time.sleep(1)
    # 送出搜尋關鍵字, IG 這邊要送出2次且不能間隔太短
    driver_search_input.send_keys(Keys.RETURN)
    time.sleep(1)
    driver_search_input.send_keys(Keys.RETURN)
    
    # 強制等待
    time.sleep(10)
    print('Search - Finish')


# 取得頁面中所有貼文的網址
@benchmark_with_logger(logger)
@log_factory(logger)
def get_links(driver, set_link):
    # 取得元素(a 超連結)的集合
    element_a = driver.find_elements(
        By.CSS_SELECTOR,
        'div._ac7v._al3n > div._aabd._aa8k._al3l > a'
        )
    
    # 以迴圈逐一檢視元素
    for index, a in enumerate(element_a):
        # print(index)
        # 取得元素的連結
        link_a = a.get_attribute('href')
        # print(link_a)
        # 將連結放到 list 當中
        set_link.add(link_a)
        
    # 強制等待
    time.sleep(3)
    print('Get Links - Finish')


# 將頁面往下滾動指定次數
@benchmark_with_logger(logger)
@log_factory(logger)
def scroll_link(driver, set_link, limit: int=3):
    '''
    total_height: 瀏覽器內部的高度
    offset: 當前捲動的量(高度)
    count: 累計無效滾動次數
    limit: 最大無效滾動次數
    wait_second: 每次滾動後的強制等待時間
    '''
    total_height = 0
    offset = 0
    count = 0
    count_no_work = 0
    limit_no_work = 3
    wait_second = 3
    
    # 在捲動到沒有元素動態產生前, 持續捲動
    while (count < limit and count_no_work < limit_no_work):

        # 每次移動一定高度
        offset = driver.execute_script(
            'return window.document.documentElement.scrollHeight;'
            )
        
        # 捲動的 js code
        # 雙重大括號為跳脫
        js_code = f'''
        window.scrollTo({{
            top: {offset},
            behavior: 'smooth'
            }});
        '''
        
        # 執行 js code
        driver.execute_script(js_code)
        
        # 強制等待
        time.sleep(wait_second)
        
        # 透過 js 來取得捲動後的當前總高度
        total_height = driver.execute_script(
            'return window.document.documentElement.scrollHeight;'
            )

        if limit > 0:
            count += 1

        # 經過計算, 如果滾動距離(offset)大於等於視窗內部總高度(total_height), 代表已經到底了
        if offset >= total_height:
            count_no_work += 1
        
        # 取得頁面中所有貼文的網址
        get_links(driver, set_link)

    # 強制等待
    time.sleep(3)
    print('Scroll - Finish')
    return list(set_link)


# 對逐個網頁的連結內容進行解析
@benchmark_with_logger(logger)
@log_factory(logger)
def parse(driver, set_temp, link, list_data):
    # 清空暫存的圖片
    set_temp.clear()
    
    # 走訪迴圈當圈的頁面
    driver.get(link)
    
    # 取得 ig 連結的 id
    regex_ = r'\/p\/([a-zA-Z0-9-_]+)\/'
    page_id = re.search(regex_, link).group(1)
    
    # 強制等待
    time.sleep(2)
    
    # 點擊更多留言
    is_comment_more = True
    # 一直點, 直到不能點了為止
    while is_comment_more:
        try:
            # 登入鍵
            button_comment_more = driver.find_element(By.XPATH, '//div/ul/li/div/button')
            button_comment_more.click()
            time.sleep(2)
        except:
            is_comment_more = False
            print('Button Comment More - Finish')


    # 點開所有留言的回覆
    bottons = driver.find_elements(By.XPATH, '//ul/li/div/button')
    for b in bottons:
        # 如果顯示為 "查看回覆", 則點擊
        while bool(re.search('查看', b.text)):
            b.click()
            time.sleep(1)
    print('Button Comment reply - Finish')

    # html 原始碼
    html = driver.page_source
    # 引數 "lxml" 要放的參數是解析器
    soup = Soup(html, 'lxml')


    # 留言內容
    # 用標籤
    tag_comment_content = soup.find_all('span', {'class': re.compile(r'^_aacl')})
    # 用CSS編輯器
    # (擁有子級 div._a9zs 的父級 div._a9zr) > div._a9zs > span
    # (擁有子級 div._a9zs 的父級 div._a9zr): 擁有文字留言的整個該則留言區塊, 如果不這麼做會涵蓋到只有圖片的留言, 
    # 這時留言內容會抓不到, 但留言時間跟留言的讚數還是會抓到, list的長度將會對不上
    tag_comment_content = soup.select('div._a9zr:has(> div._a9zs) > div._a9zs > span')
    list_comment_content = [cc.text for cc in tag_comment_content]


    # 留言時間
    # 用標籤
    tag_comment_time = soup.find_all('time', {'class': '_a9ze _a9zf'})
    # 用CSS編輯器
    # (擁有子級 div._a9zs 的父級 div._a9zr) > div > span > a > time
    tag_comment_time = soup.select('div._a9zr:has(> div._a9zs) > div > span > a > time')
    list_comment_time = [ct['datetime'] for ct in tag_comment_time]


    # 各留言的讚, 如果是回覆就代表該留言沒有取得任何的讚
    # (擁有子級 div._a9zs 的父級 div._a9zr) > div > span > (第2個 button) > span
    tag_comment_like = soup.select('div._a9zr:has(> div._a9zs) > div > span > button:nth-child(2) > span')
    list_comment_like = [cl.text for cl in tag_comment_like]
    # 將非數字去除, 留下數值(讚的個數), 如果沒有讚的話變成0
    list_comment_like = [int(re.sub('\D', '', cl) or 0) for cl in list_comment_like]


    # 各留言的用戶名稱
    tag_comment_username = soup.select('div._a9zr:has(> div._a9zs) > h3 > div > div > div > a')
    list_comment_username = [ca.text for ca in tag_comment_username]
    
    
    # 貼文內容
    tag_post_content = soup.select('div._a9zs > h1')
    if len(tag_post_content) > 0:
        post_content = tag_post_content[0].get_text()
    # 有一些貼文完全沒有文字內容, 賦值以空字串
    else:
        post_content = ''
    
    
    # 貼文時間
    # 用標籤
    tag_post_time = soup.find_all('time', {'class': '_aaqe'})
    # 用CSS編輯器
    tag_post_time = soup.select('a > span > time')
    post_time = tag_post_time[0]['datetime']
    
    # 貼文讚數
    # 影片觀看數, 有些貼文會只有影片觀看數, 沒有直接顯示出讚數, 要點擊影片觀看數後會跳出顯示讚數的框框
    element_video_views = driver.find_elements(By.CSS_SELECTOR, 'section > div > span > span > span')
    if len(element_video_views) > 0:
            # 點擊觀看數的位置, 會跳出顯示讚數的框框
            element_video_views[0].click()
            # 取得貼文讚數
            element_post_like = driver.find_elements(By.CSS_SELECTOR, 'section > div > div > div._aauu > span')
            post_like = element_post_like[0].text
    # 有直接顯示出讚數的貼文, 直接取得貼文讚數
    else:
        tag_post_like = soup.select('section > div > div > span > a > span > span')
        post_like = tag_post_like[0].text

        
    '''
    判斷是否有向右的按鈕
    - 若有, 則代表會有多個 li
    - 若無, 則代表只有一個 li
    
    由於 find_elements 會回傳 list 格式,
    - 所以可以用 len() 來取得元素的長度, 藉此判斷元素使否存在
    '''
    
    # 當有右箭頭可以按的時候, 代表頁面中同時有多張圖片(也有可能有影片)
    if len(driver.find_elements(By.CSS_SELECTOR, 'button._afxw._al46._al47')) > 0:
        # 取得多元素的資訊(圖片)
        while len(driver.find_elements(By.CSS_SELECTOR, 'button._afxw._al46._al47')) > 0:
            # 按下向右的按鈕
            driver.find_element(By.CSS_SELECTOR, 'button._afxw._al46._al47').click()
            
            # 取得當前所有 li
            element_li = driver.find_elements(By.CSS_SELECTOR, 'li._acaz')
            # 各別取得 li 底下的圖片
            for li in element_li:
                # if len(li.find_elements(By.CSS_SELECTOR, 'li > div > div > div > div > div > img')) > 0:
                if len(li.find_elements(By.CSS_SELECTOR, 'li > div > div > div > div > div > img')) > 0:
                    # 取得 img 的 src
                    src_img = li.find_element(By.CSS_SELECTOR, 'li > div > div > div > div > div > img').get_attribute('src')
                    
                    # 加入圖片到 set 中
                    set_temp.add(src_img)
                # # 沒有圖片 或是 影片
                # else:
                    # pass
            
            # 強制等待, 每睡1秒, 就按一次向右的按鈕
            time.sleep(1)
    # 如果沒有右箭頭, 代表是單張的照片或是影片
    else:
        if len(driver.find_elements(By.CSS_SELECTOR, 'div > div > div._aagv > img')) > 0:
            # 取得 img 的 src
            src_img = driver.find_element(By.CSS_SELECTOR, 'div > div > div._aagv > img').get_attribute('src')
            # 加入圖片到 set 中
            set_temp.add(src_img)
        # 沒有圖片 或是 影片
        else:
            pass

    # 整合資料
    list_data.append({
        'id': page_id,
        'url': link,
        'post_content': post_content,
        'post_time': post_time,
        'post_like': post_like,
        'list_comment_username': list_comment_username,
        'list_comment_content': list_comment_content,
        'list_comment_time': list_comment_time,
        'list_comment_like': list_comment_like,
        'list_download': list(set_temp)
        })
    
    # 強制等待
    time.sleep(3)
    print('Parse - ' + page_id + ' - Finish')


@benchmark_with_logger(logger)
@log_factory(logger)
def path_folder_make(keyword):
    # 如果資料夾路徑不存在, 則以作業系統建立資料夾
    if not os.path.isdir(keyword):
        os.mkdir(keyword)

# 存成 json
@benchmark_with_logger(logger)
@log_factory(logger)
def save_json(keyword, list_data):
    path_file = keyword + '\\post_' + keyword + '.json'
    fp = open(path_file, 'w', encoding='utf-8')
    # ensure_ascii: 避免亂碼
    fp.write(json.dumps(list_data, ensure_ascii=False))
    fp.close()
    
    # 強制等待
    time.sleep(3)
    print('Save json - Finish')


@benchmark_with_logger(logger)
@log_factory(logger)
def open_json(keyword):
    # 開啟 json 檔案
    path_file = keyword + '\\post_' + keyword + '.json'
    fp = open(path_file, 'r', encoding = 'utf-8')
    # 取得 json 字串
    str_json = fp.read()
    # 關閉檔案
    fp.close()
    
    # 強制等待
    print('Open json - Finish')
    return str_json


@benchmark_with_logger(logger)
@log_factory(logger)
def download_img(keyword, str_json):
    # 如果資料夾路徑不存在, 則以作業系統建立資料夾
    path_folder = os.path.join(keyword + '\\img')
    path_folder_make(path_folder)
    
    # 將 json 轉成 list (裡面是 dict 集合)
    list_result = json.loads(str_json)
    # 把 list_result 底下的 dict 找出來
    for dict_obj in list_result:
        # dict_obj 底下有個 list_download 屬性, 它對應的是個 list, 將 list 裡面所有的 url 找出來
        for index, download_url in enumerate(dict_obj['list_download']):
            str_file_name = dict_obj['id'] + '_' + str(index) + '.jpg'
            # os.system(f'curl "{download_url}" -o ./{path_folder}/{str_file_name}')
            save_as = os.path.join(path_folder, str_file_name)
            wget.download(download_url, save_as)
        print(f'Download img: {dict_obj["id"]}')
    print('Download img - Finish')
    
    
    
    
    
    