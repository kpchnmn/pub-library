'''
    Qiita API v2 を利用したストック記事の取得
'''
import requests
import json
import os
import re
import time
from pprint import pprint

user_id = "user_id"                                  # QiitaユーザーID
token = "******************************"             # Qiita個人用アクセストークン
path = "./md"                                        # アウトプット用ディレクトリパス

def get_stocks(user_id,tokenm,count):
    '''
        description : ユーザーのストック一覧を取得
    '''
    url = 'https://qiita.com/api/v2/users/{}/stocks?page={}&per_page=20'.format(user_id,count)
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(url, headers=headers)

    return response

def get_item_md(url):
    '''
        特定記事のMarkdownフォーマットを取得
    '''
    md_url = url +".md"
    response = requests.get(md_url)

    return response

def main(count):
    '''
        Main関数
    '''
    # ストック一覧(json形式)の取得
    res_get_stocks = get_stocks(user_id,token,count)

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
            print(filepath)

            with open(filepath, mode='w') as f:
                f.write(md_data_get_item_md)

def init():
    os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    start = time.time()
    print("------start------")
    init()
    for count in range(1,101):
        main(str(count))
    elapsed_time = time.time() - start
    print("------finished------")
    print("elapsed_time:{0}".format(elapsed_time) + "[sec]")
