'''
    Qiita API v2 を利用したストック記事の取得
'''
import requests
import json
import os
import re
import time
from pprint import pprint

from multiprocessing import Pool
import multiprocessing as multi

user_id = "user_id"                                  # QiitaユーザーID
token = "******************************"             # Qiita個人用アクセストークン
path = "./md"                                        # アウトプット用ディレクトリパス
get_contents_result = True

def get_stocks(user_id,token,count):
    '''
        description : ユーザーのストック一覧を取得
    '''
    url = 'https://qiita.com/api/v2/users/{}/stocks?page={}&per_page=20'.format(user_id,count)
    headers = {'Authorization': 'Bearer {}'.format(token)}
    try:
        response = requests.get(url, headers=headers, timeout = 7.5)
    except:
        get_stocks(user_id,token,count)

    return response

def get_item_md(url):
    '''
        特定記事のMarkdownフォーマットを取得
    '''
    md_url = url +".md"
    try:
        response = requests.get(md_url, timeout = 7.5)
        #print(response.headers["Content-Type"])
    except:
        get_item_md(url)

    return response

def main(count):
    '''
        Main関数
    '''
    global get_contents_result
    get_contents_result = True
    
    # ストック一覧(json形式)の取得
    res_get_stocks = get_stocks(user_id,token,str(count))
    print(str(count) + ":" + res_get_stocks.headers["Content-Type"] )
    # text/html が response headerとなった場合 retry.
    if res_get_stocks.headers["Content-Type"] == "text/html":
        print("retry! " + str(count))
        main(count)
        get_contents_result = False
    # print(res_get_stocks.content.decode(res_get_stocks.encoding))

    # コンテンツを正常に取得できているかどうか
    if get_contents_result:
        ## JSON文字列読み込み
        json_data_get_stocks = json.loads(res_get_stocks.content.decode(res_get_stocks.encoding))

        # print(type(res_get_stocks.content.decode(res_get_stocks.encoding))) -> str
        # print(type(json_data_get_stocks)) -> list

        if len(json_data_get_stocks) > 0:

            for data in json_data_get_stocks:
                # pprint(data) -> デフォルトで20件表示
                title = data['title']
                url = data['url']
                #print('title: {}, url: {}'.format(title,url)) -> title: {title}, url: {url}

                # 記事URLからMarkdownファイルを取得
                res_get_item_md = get_item_md(url)
                md_data_get_item_md = res_get_item_md.content.decode(res_get_item_md.encoding)

                ## ファイル名として無効な文字を削除
                title =  re.sub(r'[\\/:*?"<>|]+','',title)
                filepath = path + "/"+ title + ".md"
                #print(filepath)
                with open(filepath, mode='w') as f:
                    f.write(md_data_get_item_md)


def init():
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    start = time.time()
    print("------start------")
    init()
    with Pool(processes = multi.cpu_count() ) as p :
        p.map(main,range(1,101))
    elapsed_time = time.time() - start
    print("------finished------")
    print("elapsed_time:{0}".format(elapsed_time) + "[sec]")