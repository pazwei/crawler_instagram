
import numpy as np
import pandas as pd
import sqlite3
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import community
import community as cl
from crawler_helper import path_folder_make

# 參數, 在 IG 上搜尋的關鍵字
from main import keyword
node_num = 40

path_folder = f'{keyword}\\network'
path_folder_make(path_folder)


# 取得庫中貼文跟留言的數據
def get_post_comment(keyword: str) -> pd.DataFrame:
    '''
    Parameters
    ----------
    keyword : str
        庫的名字, 等同於要做的主題, 等同於在 IG 上搜尋的關鍵字

    Returns
    -------
    get_post : pd.DataFrame
        貼文的數據
    get_comment : pd.DataFrame
        留言的數據
    '''
    # 從庫中取得 post 跟 comment 的數據
    with sqlite3.connect(f'database\{keyword}.db') as con:
        get_post = pd.read_sql_query('SELECT * FROM post', con)
        get_comment = pd.read_sql_query('SELECT * FROM comment', con)
    # 輸出為 xlsx
    get_post.to_excel(f'{keyword}\post.xlsx', sheet_name='post', index=False)
    get_comment.to_excel(f'{keyword}\comment.xlsx', sheet_name='comment', index=False)
    return get_post, get_comment


# 對於留言數據, 對有在同一篇貼文底下留言的 username 兩兩匹配為無向的連線
def df_to_relationship(get_comment: pd.DataFrame) -> pd.DataFrame:
    '''
    對於留言數據, 對有在同一篇貼文底下留言的 username 兩兩匹配為無向的連線
    Parameters
    ----------
    get_comment : pd.DataFrame
        來自庫的留言數據

    Returns
    -------
    df_relationship : pd.DataFrame
        每一筆是在同一篇貼文底下留言的兩兩匹配的 username
    '''
    # 保留 id 跟 username 欄位
    df_comment_id_username = get_comment.loc[:, ['id', 'comment_username']]
    # 以 id 來自己對自己做 merge, 使得同一篇 id (相同貼文)底下的留言, 所有 username 會彼此搓合
    df_relationship = df_comment_id_username.merge(df_comment_id_username, how='inner', on=['id'], suffixes=['_source', '_target'])
    # 排除 username 是自己跟自己搓合的, 並重置 index
    df_relationship = df_relationship.loc[df_relationship['comment_username_source'] != df_relationship['comment_username_target']].reset_index(drop=True)
    # 對每一筆 row 進行: 欄位 id 不變, 欄位 source 跟 target 會做 array 的排序, 
    # 排序較小的會被擺在 source 欄位, 排序較大的會被擺在 target 欄位, 確保關聯的兩者被放置成同樣的結果, 後面要去重
    sort_source_target = np.sort(df_relationship.loc[:, ['comment_username_source', 'comment_username_target']].values, axis=1)
    df_relationship = pd.DataFrame(
        np.concatenate((df_relationship.loc[:, ['id']].values, sort_source_target), axis=1), 
        columns=df_relationship.columns
        )
    # 去重 相同的貼文 且 相同的(已排序過的 username_source, username_target)
    df_relationship = df_relationship.drop_duplicates(subset=['id', 'comment_username_source', 'comment_username_target'])
    # 新增欄位 count, 後面以 sum() 加總使用
    df_relationship = df_relationship.assign(count=1)
    # 同一組的 username 搓合的次數加總 (username_x 跟 username_y 是相同的)
    # 代表兩個 username 在同一篇貼文留言的總次數
    df_relationship = df_relationship.groupby(['comment_username_source', 'comment_username_target'], as_index=False).sum()
    # 以欄位 count 做反序
    df_relationship = df_relationship.sort_values(['count'], ascending=False).reset_index(drop=True)
    return df_relationship


# 縮放映射為 1 到 10 的函式, 後面為了讓網路圖的節點大小比較好看而做的 normalize
# 因為 edge 的寬度想要根據 username 兩兩在同一篇貼文底下都有留言的總次數, 但原始值的話有一些 edge 會非常寬, 不好看
def scale_1_to_10(x, old_min, old_max, new_min=1, new_max=10):
    return (x - old_min) * (new_max - new_min) / (old_max - old_min) + new_min


# 使 df 只保留指定數量的 node, 由 df 的排序來取最前面所指定數量的 node 的數據, 並新增欄位為 edge 的寬度
def df_relationship_to_limit(df_relationship: pd.DataFrame, node_num: int) -> pd.DataFrame:
    '''
    使 df 只保留指定數量的 node, 由 df 的排序來取最前面所指定數量的 node 的數據, 並新增欄位為 edge 的寬度
    Parameters
    ----------
    df_relationship : pd.DataFrame
        要製成網路圖的 df, 須是排好序的 df, 取數量會由 df 的第一筆往下取
    node_num : int
        指定 node 的數量

    Returns
    -------
    df_relationship_limit : pd.DataFrame
        指定數量後的 df

    '''
    # 只保留指定數量的 node 的 df
    index_ = 0
    set_ = set()
    # 當 (set_ 的長度小於指定的 node 數量) 且 (index_ 小於等於數據的 row 數) 時
    # 因為 index_ 起始是從 0 開始, 所以判斷是看小於數據的 row 數
    # 因為數據的 index 從 0 開始, 所以 index_ 設計是從 0 開始
    # 也就是說, 數據的 index 到了盡頭時會跟總 row 數相差了 1
    while len(set_) < node_num and index_ < df_relationship.shape[0]:
        set_.add(df_relationship.loc[index_, 'comment_username_source'])
        set_.add(df_relationship.loc[index_, 'comment_username_target'])
        index_ += 1
    df_relationship_limit = df_relationship.loc[:index_, :]
    # 新增欄位 width 為將 count 縮放為 1 到 10, 畫圖出來的線會比較好看
    df_relationship_limit = df_relationship_limit.assign(
        width = lambda x: x['count'].apply(scale_1_to_10, args=(min(x['count']), max(x['count'])))
        )
    return df_relationship_limit


# 取得網路圖 G 的 degree_centrality, 並畫長方圖後保存在指定路徑
def dict_df_plot_degree(G, path_folder: str) -> dict:
    # degree_centrality
    dict_degree = nx.degree_centrality(G)
    df_degree = pd.DataFrame.from_dict(dict_degree, orient='index', columns=['centrality'])
    df_degree = df_degree.sort_values(['centrality'], ascending=(False))
    # 畫長方圖
    plot_degree = df_degree.plot(kind='bar')
    # 將長方圖保存在指定路徑
    plot_degree.get_figure().savefig(f'{path_folder}\\bar_degree_centrality.png', dpi=199, bbox_inches='tight')
    return dict_degree, df_degree


# 取得網路圖 G 的 betweenness_centrality, 並畫長方圖後保存在指定路徑
def dict_df_plot_betweenness(G, path_folder: str) -> dict:
    # betweenness_centrality
    dict_betweenness = nx.betweenness_centrality(G)
    df_betweenness = pd.DataFrame.from_dict(dict_betweenness, orient='index', columns=['centrality'])
    df_betweenness = df_betweenness.sort_values(['centrality'], ascending=(False))
    # 畫長方圖
    plot_betweenness = df_betweenness.plot(kind='bar')
    # 將長方圖保存在指定路徑
    plot_betweenness.get_figure().savefig(f'{path_folder}\\bar_betweenness_centrality.png', dpi=199, bbox_inches='tight')
    return dict_betweenness, df_betweenness


# 畫出網路圖, 並保存在指定路徑
def plot_network(G, path_folder: str, node_size_by):
    # 網路圖中 node 放置位置的演算法
    pos = nx.kamada_kawai_layout(G)
    
    fig, ax = plt.subplots(figsize=(12, 12))
    # Visualize graph components
    nx.draw_networkx_edges(
        G, pos, 
        alpha=0.3, 
        # edge 的寬度, 根據網路圖 G 的屬性 width 數據, 
        # 也就是經過 normalize 為 1 到 10 的兩兩 username 在同一篇貼文下留言的匹配次數
        width=list(nx.get_edge_attributes(G, 'width').values()),
        # edge 的顏色, 'k'為黑色
        edge_color='k'
        )
    nx.draw_networkx_nodes(
        G, pos, 
        alpha=0.9,
        # node 的大小, 依據網路圖 G 的屬性 comment_like 數據, 也就是 username 所有留言的總 like 數
        node_size=list(nx.get_node_attributes(G, node_size_by).values()),
        # node 的顏色, 依據網路圖 G 的屬性 group 數據, 也就是根據社區發現 Louvain
        node_color=list(nx.get_node_attributes(G, 'group').values())
        )
    label_options = {
        "ec": "k", 
        "fc": "white", 
        "alpha": 0.5
        }
    nx.draw_networkx_labels(G, pos, font_size=14, bbox=label_options)
    
    # Title/legend
    font = {
        "color": "k", 
        "fontweight": "bold", 
        "fontsize": 14
        }
    ax.set_title(f"Instgram Comment - {keyword}", font)
    # Change font color for legend
    font["color"] = "r"
    # text of legend
    ax.text(
        0.80,
        0.10,
        "edge width = # comment in same post",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontdict=font,
    )
    ax.text(
        0.80,
        0.06,
        "node size = # like of comment",
        horizontalalignment="center",
        transform=ax.transAxes,
        fontdict=font,
    )
    # Resize figure for label readability
    ax.margins(0.1, 0.05)
    fig.tight_layout()
    plt.axis("off")
    # plt.show()
    # 將網路圖保存在指定路徑
    plt.savefig(f'{path_folder}\\network_{keyword}_{node_num}_nodes.png')


# df 在指定 row 為第幾筆到第幾筆的 index 的 list
def index_list_by_row_num(df: pd.DataFrame, num_st: int, num_ed: int) -> list:
    '''
    df 在指定 row 為第幾筆到第幾筆的 index 的 list
    Parameters
    ----------
    df : pd.DataFrame
    num_st : int
        要抓取的 df 的起始 row 為第幾筆
    num_ed : int
        要抓取的 df 的結尾 row 為第幾筆

    Returns
    -------
    list
        df 在指定 row 為第幾筆到第幾筆的 index 的 list

    '''
    return list(df[(num_st-1):num_ed].index)


# 各個 username 在各個年月份的 degree centrality 折線圖
def plot_evol_degree(get_comment, list_username, path_folder):
    # 新增欄位為留言的年月份
    get_comment['comment_month'] = get_comment['comment_time'].apply(lambda x: x[:7])
    # list 為留言的年月份做去重後的排序
    list_month_sort = sorted(get_comment['comment_month'].unique())
    
    # 網路圖的放置
    list_graph = []
    
    # 對排序過後的年月份做迴圈, 每一圈會對當年月份的數據做網路圖物件, 並新增放置到 list 中
    for month in list_month_sort:
        print(month)
        # 只保留當一迴圈的年月份的留言數據
        get_comment_ = get_comment.loc[get_comment['comment_month'] == month, :]
        # 將留言數據變為可以製成網路圖 G_ 的 df, 也就是兩兩 username 在同一篇貼文底下留言的紀錄
        df_relationship_ = df_to_relationship(get_comment_)
        G_ = nx.from_pandas_edgelist(
            df=df_relationship_, 
            source='comment_username_source', 
            target='comment_username_target', 
            create_using=nx.Graph()
            )
        # 將網路圖 G_ 放置到 list 中
        list_graph.append(G_)
    
    # 對每個網路圖物件取得各自的 degree centrality
    list_evol = [nx.degree_centrality(g) for g in list_graph]
    # 轉換為 df, 欄位名稱為各個帳號, 各欄位的數據為各個帳號在不同年月份的 degree centrality
    df_evol = pd.DataFrame.from_records(list_evol)
    # 將 index 改為排序過後的年月份, 畫圖的時候會變成 x 軸
    df_evol.index = list_month_sort
    
    # 畫圖: 各個帳號在不同年月份下的 degree centrality
    str_username = '_'.join(list_username)
    plot_evol = df_evol[list_username].plot().legend(bbox_to_anchor=(1.0, 1.0))
    plot_evol.get_figure().savefig(f'{path_folder}\\evol_degree_username_{str_username}.png', dpi=199, bbox_inches='tight')


if __name__ == '__main__':
    get_post, get_comment = get_post_comment(keyword)
    
    # get_post.info()
    # get_comment.info()
    
    df_relationship = df_to_relationship(get_comment)
    
    df_relationship_limit = df_relationship_to_limit(df_relationship, node_num)
    
    # 透過 df_relationship_limit 生成的網路圖物件
    G = nx.from_pandas_edgelist(
        df=df_relationship_limit, 
        source='comment_username_source', 
        target='comment_username_target', 
        edge_attr=['width'], 
        create_using=nx.Graph()
        )
    
    dict_degree, df_degree = dict_df_plot_degree(G, path_folder)
    
    dict_betweenness, df_betweenness = dict_df_plot_betweenness(G, path_folder)
    
    nx.set_node_attributes(G, dict_degree, 'degree_centrality')
    nx.set_node_attributes(G, dict_betweenness, 'betweenness_centrality')
    
    # 社區發現 Louvain
    # communities = cl.best_partition(G, weight='width')
    communities = cl.best_partition(G, random_state=1)
    nx.set_node_attributes(G, communities, 'group')
    
    # 每個帳號所有留言的總 like 數
    df_username_like = get_comment.groupby(['comment_username'])['comment_like'].agg(sum).reset_index()
    get_comment_with_post_like = get_comment.merge(get_post.loc[:, ['id', 'post_like']], how='left', on=['id'], validate='many_to_one')
    get_comment_with_post_like['ratio_like'] = get_comment_with_post_like.apply(lambda x: x['comment_like'] / x['post_like'], axis=1)
    
    series_username_like_ratio = get_comment_with_post_like.groupby(['comment_username']).apply(lambda x: x['ratio_like'].sum() / x['ratio_like'].count() * 1000000)
    series_username_like_ratio.name = 'username_like_ratio'
    df_username_like = df_username_like.merge(series_username_like_ratio, how='left', on=['comment_username'])
    
    df_comment_like_by_id_username = get_comment.groupby(['id', 'comment_username'])['comment_like'].agg(sum).reset_index()
    df_comment_like_by_id_username_with_post_like = df_comment_like_by_id_username.merge(get_post.loc[:, ['id', 'post_like']], how='left', on=['id'], validate='many_to_one')
    df_comment_like_by_id_username_with_post_like['ratio_like'] = df_comment_like_by_id_username_with_post_like.apply(lambda x: x['comment_like'] / x['post_like'], axis=1)

    series_username_like_ratio_by_id_username = df_comment_like_by_id_username_with_post_like.groupby(['comment_username']).apply(lambda x: x['ratio_like'].sum() / x['ratio_like'].count() * 1000000)
    series_username_like_ratio_by_id_username.name = 'username_like_ratio_by_id_username'
    df_username_like = df_username_like.merge(series_username_like_ratio_by_id_username, how='left', on=['comment_username'])
    
    dict_username_like = df_username_like.set_index('comment_username').to_dict('index')
    nx.set_node_attributes(G, dict_username_like)
    
    df_username_like['username_like_ratio'].describe()
    df_username_like['username_like_ratio_by_id_username'].describe()
    
    get_comment_with_post_like.loc[(get_comment_with_post_like['id'] == 'Coq6jaRMMk2') & (get_comment_with_post_like['comment_username'] == 'wakkk94'), :]
    df_comment_like_by_id_username_with_post_like.loc[(df_comment_like_by_id_username_with_post_like['id'] == 'Coq6jaRMMk2') & (df_comment_like_by_id_username_with_post_like['comment_username'] == 'wakkk94'), :]
        
    # quantile_ = df_username_like['username_like_ratio_by_id_username'].quantile(1 - 50/df_username_like['username_like_ratio_by_id_username'].count())
    # x = df_username_like.loc[df_username_like['username_like_ratio_by_id_username'] >= quantile_, :]['comment_username'].tolist()
    # get_comment_ = get_comment.loc[get_comment['comment_username'].isin(x), :]
    
    
    # x=get_comment_with_post_like.loc[get_comment_with_post_like['comment_username'] == 'y_1_daily', :]
    # x['ratio_like'].count()
    # x['ratio_like'].sum()
    # x['ratio_like'].sum() / x['ratio_like'].count()
    
    # G.nodes(data=True)
    # G.edges(data=True)
    
    # 畫出網路圖 G
    plot_network(G, path_folder, 'comment_like')
    plot_network(G, path_folder, 'username_like_ratio')
    plot_network(G, path_folder, 'username_like_ratio_by_id_username')
    
    G.nodes(data=True)['wakkk94']
    
    
    x = nx.community.louvain_communities(G)
    dict_ = {}
    for i, c in enumerate(x):
        for username in c:
            dict_[username] = i
    nx.set_node_attributes(G, dict_, 'group')
    
    
    
    # 指定要畫出 degree centrality 折線圖的 username 的 list, 
    # 依據已經對 degree centrality 做好反序的 df 去取得第 1 到第 5 的 username
    list_username = index_list_by_row_num(df_degree, 1, 5)
    # 畫出指定的各個 username 在各個年月份的 degree centrality 折線圖
    plot_evol_degree(get_comment, list_username, path_folder)
    
    # 直接套要指定 username 的 list 的函式, 指定 df 中第 6 到第 10 的 username, 畫出折線圖
    plot_evol_degree(get_comment, index_list_by_row_num(df_degree, 6, 10), path_folder)
    # 直接指定要畫出折線圖的 username
    plot_evol_degree(get_comment, ['a', 'b'], path_folder)








# network 圖的最長路徑, 用來衡量圖的 size
nx.diameter(G)

# network 的 density, 介於 0 到 1 之間
density = nx.density(G)
print(density)

# network 圖是否只有一個組成(component)
nx.is_connected(G)

# triadic closure, 有提到相關係數
triadic_closure = nx.transitivity(G)
print(triadic_closure)



get_post_label = pd.read_excel(f'{keyword}\post_label.xlsx', sheet_name='label')
get_post_label['labels'] = get_post_label[['label1', 'label2', 'label3', 'label4']].values.tolist()
get_post_label = get_post_label.loc[:, ['id', 'labels']]

get_comment_label = get_comment.loc[:, ['id', 'comment_username']].merge(get_post_label, on=['id']).groupby('comment_username').agg({'labels': 'sum'}).reset_index()
get_comment_label['labels'] = get_comment_label['labels'].apply(lambda labels: [label for label in labels if str(label) != 'nan'])

from collections import Counter
get_comment_label['labels_dict'] = get_comment_label['labels'].apply(lambda labels: Counter(labels))



'yin_yin_1027_' in G.nodes
get_comment_label['is_in_nodes'] = get_comment_label['comment_username'].apply(lambda username: username in G.nodes)

get_comment_label_in_nodes = get_comment_label.loc[get_comment_label['is_in_nodes'], :]

get_comment_label_in_nodes.to_excel(f'{keyword}\comment_label_in_nodes.xlsx', sheet_name='labels', index=False)








# mary11_25: 幕後工作夥伴
# yin_yin_1027_: 許光漢, 電影金句, 見面會, 幕後工作夥伴
# bess_chang: 電影金句
# greghanholic: 許光漢, 電影金句, 番外篇, 林柏宏, 再生父母, 紅包 (什麼都留)
# wakkk94: 兩人, 見面會, 幕後工作夥伴, 敲碗, 番外篇, 票房
# xiaoyuyang75: 許光漢, 紅包
# g.han_twfans: 許光漢, 番外篇
# __hhhhhhhhhhho: 許光漢, 番外篇, 警察
# ccynnk__: 電影金句, 許光漢
# flowerchen9286: 許光漢, 番外篇, 拜年, 角色介紹
# kkuma1123: 電影金句
# emmalee975622: 番外篇, 許光漢, 影評 (番外篇)
# liqingchen_: 許光漢, 番外篇, 林柏宏 (許光漢)





