#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import shutil
import configparser
import pickle
from selenium import webdriver

DEBUG = False

url = "https://moneyforward.com/accounts"

# パスが取得できない場合のみ手動書き換えしてください
use_chromedriver = False  # True: Chrome または　False: Firefox
driver_name = "chromedirver" if use_chromedriver else "geckodriver"
path = f"/usr/local/bin/{driver_name}"

# ChromeDriverのパスを自動取得
try:
    path = shutil.which(driver_name)
except:
    pass

# iniファイルの書き込み
config = configparser.ConfigParser()


def create_conf():
    print("ログイン情報を入力してください。次回以降の入力は不要です。\n情報は平文でconfig.iniに保存されます。")
    config["INFO"] = {
        'email': input("メールアドレス: "),
        'password': input("パスワード: ")
    }
    with open('config.ini', 'w') as config_file:
        config.write(config_file)


if not os.path.isfile("./config.ini"):
    create_conf()

# iniファイルの読み込み
try:
    config.read('config.ini')
    email = config['INFO']['email']
    password = config['INFO']['password']
except:
    print("config.iniを再設定します。入力後再度起動してください。")
    create_conf()
    exit()

if use_chromedriver:
    options = webdriver.ChromeOptions()
else:
    options = webdriver.FirefoxOptions()
if not DEBUG:
    options.add_argument("--headless")

try:
    if use_chromedriver:
        driver = webdriver.Chrome(executable_path=path, options=options)
    else:
        driver = webdriver.Firefox(executable_path=path, options=options)
except:
    print(f"{driver_name}が見つかりません。パスをこのファイルに直接記載してください。")
    exit()
driver.implicitly_wait(5)
print("実行中...")

driver.get(url)

# ログイン処理
# cookie を読み込む
if os.path.isfile("cookies.pkl"):
    # 2回目以降は、自動でメールでログインの画面が開かれ、メールアドレスが打ち込まれている
    cookies = pickle.load(open("cookies.pkl", "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get(url)
else:
    # 初回はメールでログインを開く
    driver.find_element_by_xpath(
        "/html/body/main/div/div/div/div/div[1]/section/"
        "div/div/div[2]/div/a[1]").click()
    # メールを入力
    driver.find_element_by_xpath(
        "/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/"
        "input").send_keys(email)
driver.find_element_by_xpath(
    "/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/"
    "div[3]/input").submit()


# 関数を宣言
def bye():
    print("終了します...")
    driver.quit()
    exit()

# パスワードを入力
driver.find_element_by_xpath("/html/body/main/div/div/div/div/div["
                             "1]/section/form/div[2]/div/input[2]") \
    .send_keys(password)
driver.find_element_by_xpath(
    "/html/body/main/div/div/div/div/div[1]/section/form/div[2]/div/div["
    "3]/input").submit()
print("ログイン中...")

# ログインメッセージ関連
if driver.find_elements_by_xpath(
        "//*[contains(text(), 'メールアドレスもしくはパスワードが間違っています')]"):
    print("メールアドレスもしくはパスワードが間違っています。\n再設定完了後、再度起動してください。")
    create_conf()
    bye()
elif driver.find_elements_by_xpath(
        "//*[contains(text(), 'マネーフォワードに登録されていない端末・ブラウザからのログインです。')]"):
    print("二段階認証が必要です。メールを確認し、10分以内に認証コードを入力してください。")
    two_factor_auth_code = input("認証コード: ")
    driver.find_element_by_id("verification_code").send_keys(
        two_factor_auth_code)
    driver.find_element_by_class_name("form-submit-code").submit()
    if driver.find_elements_by_xpath(
            "//*[contains(text(), '認証コードが無効です。')]") or len(
        two_factor_auth_code) == 0:
        print("認証コードが無効です。")
        bye()
    else:
        driver.get(url)
else:
    pass

# 二段階認証設定画面の回避
try:
    not_now_button = str(
        "javascript:document.getElementByClassName('not-now').click();")
    driver.execute_script(not_now_button)
except:
    pass

# 更新すべき対象の数を計算
account = len(driver.find_elements_by_xpath(
    "//form[starts-with(@action, '/faggregation_queue2/')]"))
needauth = len(driver.find_elements_by_link_text(
    "要画像認証") + driver.find_elements_by_link_text(
    "要ワンタイムパスワード") + driver.find_elements_by_xpath(
    "//*[contains(text(), '重要なお知らせ')]"))

if account == 0:
    print("口座が一つもないか、ログインできませんでした。\n再設定後、再度起動してください。")
    create_conf()
    bye()
elif needauth != 0:
    print("認証が必要な口座が" + str(needauth) + "つあります。これらは更新されません。\n" + str(
        account) + "つの口座情報を更新します...")
else:
    print(str(account) + "つの口座情報を更新します...")

# 更新処理
refreshed = 0
for i in range(account):
    refreshed += 1
    remaining = account - refreshed
    if remaining == 0:
        remaining = "なし"
    print(str(refreshed) + "番目を更新中..." + "(残り" + str(remaining) + ")")
    driver.find_elements_by_xpath(
        "//form[starts-with(@action, '/faggregation_queue2/')]")[
        refreshed - 1].submit()
print("待機中・・・")
driver.implicitly_wait(10)
print("更新が完了しました!")

# cookie の保存
pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

bye()
