import requests
import json, config
from requests_oauthlib import OAuth1Session
from bs4 import BeautifulSoup
from pytz import timezone
from datetime import datetime
import time
import schedule
import re

# URL = "https://www.gogojungle.co.jp/systemtrade/fx/14352"
URL = "https://www.gogojungle.co.jp/systemtrade/fx/15802"
numberOfPositions = 0
now = datetime.now(timezone("UTC"))
previousJobTime = str(now.month) + "/" + str(now.day) + " " + str(now.hour) + ":" + str(now.minute)

class ForwardTest():
    def __init__(self):
        self.trade = [
            None,       #  0: 約定日時
            None,       #  1: 通貨ペア
            None,       #  2: 買/売
            None,       #  3: レート
            None,       #  4: ストップ
            None,       #  5: リミット
            None,       #  6: 決済日時
            None,       #  7: 決済レート
            None,       #  8: ロット
            None,       #  9: 手数料
            None,       # 10: 税金
            None,       # 11: スワップ
            None,       # 12: 結果
            None        # 13: 損益
        ]

    def setTrade(self, data):
        pattern = r"[0-9]{2}\/[0-9]{2}\s[0-9]{2}:[0-9]{2}"
        match = re.compile(pattern).match(data[0].string)
        self.trade[0] = match.group()[0] if match is not None else match

        for index in range(1, len(data)):
            if index == 2:
                self.trade[index] = "ロング" if data[index].find("b").string == "↗" else "ショート"
            else:
                self.trade[index] = data[index].string

def getForwardState():
    html = requests.get(URL)

    soup = BeautifulSoup(html.text, "html.parser")
    table = soup.find_all("table", {"class": "table table-striped w-full forward-table"})[0]
    rows = table.find_all("tr")

    unsettledCount = settledCount = 0
    unsettledPosition = settledPosition = []
    for index, row in enumerate(rows):
        if index == 0:
            continue

        data = row.find_all("td")

        # 約定日時が日時ではない、もしくは決済日時が日時ではない場合は、ポジション保持と判断
        forwardTest = ForwardTest()
        forwardTest.setTrade(data)
        if forwardTest.trade[0] is None or forwardTest.trade[6] == "-":
            unsettledPosition.append(forwardTest)
            unsettledCount += 1
            continue

        if previousJobTime > forwardTest.trade[0] or \
            ( previousJobTime[0:2] == "01" and forwardTest.trade[0] == "12"):
            break

        # 以下は決済済みの場合の処理
        settledPosition.append(forwardTest)
        settledCount += 1

    return unsettledCount, settledCount, unsettledPosition, settledPosition

def getTweetMessage(state, positions, newUnsettledCount=0):
    new = ["決済", "注文"]
    message = "フォワード新規" + new[state] + "更新情報\n"
    for index, position in enumerate(positions):
        if state == 1 and index == newUnsettledCount:
            break
        message += str(index + 1) + ":\n"
        if position.trade[1] is None:
            message += " 実績更新中もしくは逆指値注文中\n"
            continue
        message += " 約定日時:" + position.trade[0] + "\n"
        message += " L/S:" + position.trade[2] + "\n"
        message += " レート:" + position.trade[3] + "\n"
        message += " 決済日時:" + position.trade[6] + "\n"
        message += " 決済レート:" + position.trade[7] + "\n"
        message += " 結果:" + position.trade[12] + "\n"
    return message

def tweet(message):
    print(message)

def job():
    global previousJobTime, numberOfPositions

    # 対象のURLの未決済のポジション数、L/S等を取得
    # 前回ジョブ実行時より新しい決済済みのポジションの損益を取得
    unsettledCount, settledCount, unsettledPosition, settledPosition = getForwardState()
    sumOfTradeCount = unsettledCount + settledCount
    newUnsettledCount = sumOfTradeCount - numberOfPositions
    message = ""

    if settledCount > 0:
        # 決済済み情報が追加された場合
        message += tweet(0, settledPosition)
        if newUnsettledCount > 0:
            # 新しいポジション情報追加された場合
            message += tweet(1, unsettledPosition, newUnsettledCount)
    else:
        if newUnsettledCount > 0:
            # 新しいポジション情報追加された場合
            message += tweet(1, unsettledPosition, newUnsettledCount)

    if message != "":
        tweet(message)

    numberOfPositions = unsettledCount

    # 現在時間更新
    now = datetime.now(timezone("UTC"))
    previousJobTime = str(now.month) + "/" + str(now.day) + " " + str(now.hour) + ":" + str(now.minute)

if __name__ == "__main__":
    schedule.every().minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
