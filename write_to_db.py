
import pandas as pd
import sqlite3

# 參數, 在 IG 上搜尋的關鍵字
from main import keyword


# 數據存庫前整理

# 讀入 json 檔, 是先前爬蟲下來的數據
df = pd.read_json(f'{keyword}\\post_{keyword}.json')
# 將部分為 list 的欄位擴展為 row, 同一個貼文會擴展為多筆留言的 row, 並重置 index, 否則同一個貼文的擴展會是同一個 index
df_explode = df.explode(['list_comment_username', 'list_comment_content', 'list_comment_time', 'list_comment_like']).reset_index(drop=True)
# 將擴展的欄位重新命名欄位名稱
df_explode = df_explode.rename(columns={
    'list_comment_username': 'comment_username',
    'list_comment_content': 'comment_content',
    'list_comment_time': 'comment_time',
    'list_comment_like': 'comment_like'
    })

# 先指定好貼文 post 數據所需要的欄位
col_post = ['id', 'url', 'post_content', 'post_time', 'post_like']
# 先指定好留言 comment 數據所需要的欄位
col_comment = ['id', 'comment_username', 'comment_content', 'comment_time', 'comment_like']

# 貼文 post 數據的 dataframe
df_post = df.loc[:, col_post]
# 將 like 的中文單位(萬, 億)轉換為阿拉伯數字, 先定義一個針對 str 的函式, 後面放入欄位的 map 裡進行迭代
def like_num(x):
    if '萬' in x:
        return float(x.replace('萬', '')) * 10000
    elif '億' in x:
        return float(x.replace('億', '')) * 100000000
    else:
        return float(x)
# 將 like 轉為阿拉伯數字
df_post.post_like = df_post.post_like.astype(str).map(like_num)
# 將 time 轉為 datetime 類型, 格式為 YYYY-MM-DD hh:mm:ss
df_post.post_time = pd.to_datetime(df_post.post_time, utc=False).dt.tz_localize(None)

# 留言 comment 數據的 dataframe, 然後去重
df_comment = df_explode.loc[:, col_comment].drop_duplicates()
# 將 like 轉為阿拉伯數字
df_comment.comment_like = df_comment.comment_like.astype(str).map(like_num)
# 將 time 轉為 datetime 類型, 格式為 YYYY-MM-DD hh:mm:ss
df_comment.comment_time = pd.to_datetime(df_comment.comment_time, format='%Y-%m-%dT%H:%M:%S.000Z')
# 排除是 NA 的 row, 可能是留言只有圖片而沒有文字
df_comment = df_comment.loc[~(df_comment['comment_username'].isna()), :]


# 存庫

# 這次爬蟲下來的數據的 id, 將在後面刪除庫裡的這些 id, 再將這次爬蟲下來的存入庫裡, 避免重複存庫
dup_id = ','.join("'" + df_post['id'] + "'")

# 建立與庫的連接, 使用 with 語句就可以在執行完成後會自動關閉連接, 就不需要 con.close()
with sqlite3.connect(f'database\{keyword}.db') as con:
    # 建立游標, 使用 with 語句就可以在執行完成後會自動關閉游標, 就不需要 cursor.close()
    cursor = con.cursor()
    
    ### 建立游標後, 可以開始執行事務, 對數據庫做操作 ###
    try:
        # 建立貼文 post 表, 如果不存在則建立
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS post(
            id VARCHAR(100),
            url VARCHAR,
            post_content VARCHAR,
            post_time DATETIME,
            post_like INT,
            PRIMARY KEY (id)
            )
        ''')
        
        # 建立留言 comment 表, 如果不存在則建立
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment(
            id VARCHAR(100),
            comment_username VARCHAR,
            comment_content VARCHAR,
            comment_time DATETIME,
            comment_like INT,
            CONSTRAINT id_comment_username_time PRIMARY KEY (id, comment_username, comment_time)
            )
        ''')

        # 對 post 表刪除這次爬蟲下來的數據的 id, 避免重複存庫
        cursor.execute(f'DELETE FROM post WHERE `id` in ({dup_id})')
        # 將 post 表寫入庫中
        df_post.to_sql('post', con, if_exists='append', index=False)
        
        # 對 comment 表刪除這次爬蟲下來的數據的 id, 避免重複存庫
        cursor.execute(f'DELETE FROM comment WHERE `id` in ({dup_id})')
        # 將 comment 表寫入庫中
        df_comment.to_sql('comment', con, if_exists='append', index=False)
    
    # 不管上面執行事務有沒有出錯, 都關閉游標
    finally:
        cursor.close()

    # 提交操作, 將事務中的修改可以永久的保存到數據庫中
    con.commit()
    
    ### 自動關閉與庫的連接 ###



# =============================================================================
# 讀入存完後的數據
# =============================================================================
# # 建立與庫的連接, 並讀入存完後的數據
# with sqlite3.connect(f'database\{keyword}.db') as con:
#     df_post_read = pd.read_sql_query('SELECT * FROM post', con)
#     df_comment_read = pd.read_sql_query('SELECT * FROM comment', con)
# # 拿來存的數據 跟 存完後讀入的數據 的資訊, 可以比對一下
# df_post.info()
# df_post_read.info()
# df_comment.info()
# df_comment_read.info()
# =============================================================================




# =============================================================================
# 手動刪除庫中指定條件的紀錄
# =============================================================================
# 建立連接, 建立游標
# con = sqlite3.connect(f'database\{keyword}.db')
# cursor = con.cursor()
# # 刪除 comment 表中指定條件的紀錄
# cursor.execute('''
# DELETE
# FROM comment
# WHERE `id` in (
# 	SELECT `id`
# 	FROM post
# 	WHERE post_time <= '2022-09-30 23:59:59'
# )
#                ''')
# # 刪除 post 表中指定條件的紀錄
# cursor.execute('''
# DELETE
# FROM post
# WHERE post_time <= '2022-09-30 23:59:59'
#                ''')
# # 關閉游標, 提交操作, 關閉連接
# cursor.close()
# con.commit()
# con.close()
# =============================================================================







# =============================================================================
# import networkx as nx
# import matplotlib.pyplot as plt
# 
# dd = df_comment_read.dropna().loc[0:100, ['id', 'comment_username']]
# dd = df_comment_read.dropna().loc[:, ['id', 'comment_username']]
# 
# out = dd.merge(dd, on=['id'])
# func_xy = lambda n: '-'.join(sorted(n))
# out['xy'] = out[['comment_username_x', 'comment_username_y']].apply(func_xy, axis=1)
# out['hash'] = (out.id + '-' + out.xy).apply(hash)
# 
# out2 = out.drop_duplicates(subset=['hash'])
# out2['count'] = 1
# out2 = out2.loc[out2.comment_username_x != out2.comment_username_y, :]
# out2['sum'] = out2.groupby('xy')['count'].transform('sum')
# 
# 
# hash('-'.join(sorted(out[['comment_username_x', 'comment_username_y']].loc[5, :])))
# 
# 
# out['col_unique'] = out.comment_username_x + out.comment_username_y
# out.sort_values(['hash'])
# out2 = out.drop_duplicates()
# 
# out3 = out2.loc[out2['sum'] >= 12, :]
# 
# G = nx.Graph()
# G = nx.from_pandas_edgelist(out3, 'comment_username_x', 'comment_username_y')
# 
# # Plot it
# nx.draw(G, with_labels=True)
# plt.show()
# 
# =============================================================================

