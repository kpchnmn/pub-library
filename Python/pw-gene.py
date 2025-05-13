import string
import secrets


num = input("生成するパスワードの文字数を入力してください。")

print(num + "文字で作成します。")
def pass_gen(size=int(num)):
  # 記号が必要な場合は末尾のコメント部分を適宜利用
  chars = string.ascii_uppercase + string.ascii_lowercase + string.digits \
          + '%&$#()'
  return ''.join(secrets.choice(chars) for x in range(size))

print("パスワード：" + pass_gen())

input("何かキーを押すと終了します")