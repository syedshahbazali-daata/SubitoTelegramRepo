from flask import Flask, jsonify
import os
import requests
import pandas as pd  # pip install pandas
import time
import threading
from requests_html import HTMLSession  # pip install requests-html
from xextract import String  # pip install xextract
import gspread  # pip install gspread oauth2client
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

creds_sheet = ServiceAccountCredentials.from_json_keyfile_name(
    r"sheetsAPI.json", scope)
client = gspread.authorize(creds_sheet)
sheet_url = "https://docs.google.com/spreadsheets/d/14B9Bg3TVyU3Lvz8qiBKw8dkfrbKw0Jd40dsBzWwZN6Q/edit?usp=sharing"
sheet = client.open_by_url(sheet_url)

token = "6770314577:AAExkccZRhRU5TZ924NBwTbP-ACY7EFldU0"


def get_all_data(sheet_name: str):
    while True:
        try:
            data = sheet.worksheet(sheet_name).get_all_values()
            time.sleep(1)
            break
        except:
            time.sleep(10)
            pass
    return data


def insert_row(row, sheet_name: str):
    while True:
        try:
            sheet.worksheet(sheet_name).append_row(row)
            time.sleep(1)
            break
        except:
            time.sleep(10)
            pass
    return None


def update_cell(row, col, value, sheet_name: str):
    while True:
        try:
            sheet.worksheet(sheet_name).update_cell(row, col, value)
            time.sleep(1)
            break
        except:
            time.sleep(10)
            pass
    return None


def get_cell(row, col, sheet_name: str):
    while True:
        try:
            value = sheet.worksheet(sheet_name).cell(row, col).value
            time.sleep(1)
            return value
        except:
            time.sleep(10)
            pass


def get_file_data(file_name):
    with open(file_name, "r", encoding="utf-8") as txt_file:
        data_file = txt_file.read().strip().split("\n")
    return data_file


def send_message(chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    res = requests.get(url)
    print(f"Message sent to {chat_id} with status code {res.status_code}")
    return None


def scraper():
    print("Checking for new vehicles")

    complete_data = get_all_data("Sheet1")
    already_scraped_data = get_all_data("AlreadyScraped")

    columns = complete_data[0]
    already_scraped_data_columns = already_scraped_data[0]
    df = pd.DataFrame(complete_data[1:], columns=columns)
    already_scraped_df = pd.DataFrame(already_scraped_data[1:], columns=already_scraped_data_columns)

    already_done = get_file_data("already-done.txt")

    session = HTMLSession()
    for index, single_row in df.iterrows():
        if "www.subito.it" not in str(
                single_row["url"]):  # skip if url is not subito.it
            continue

        # send_message(single_row["chat_id"], "Checking for new vehicles")

        res = session.get(single_row["url"])
        page_source = str(res.text)

        vehicle_names = String(xpath='//div/a//h2').parse_html(page_source)
        vehicle_links = String(xpath='//div/a//h2/../../../../..',
                               attr='href').parse_html(page_source)

        for vehicle_name, vehicle_link in zip(vehicle_names, vehicle_links):
            record = f"{vehicle_link}:{single_row['chat_id']}"
            if record in list(already_done):
                continue

            already_scraped_df_chat_ids = already_scraped_df["chat_id"].tolist()
            already_scraped_df_chat_ids = [str(x).replace(".0", "") for x in already_scraped_df_chat_ids]
            already_scraped_df_urls = already_scraped_df["url"].tolist()

            if not str(single_row["chat_id"]).replace(".0", "") in already_scraped_df_chat_ids:
                insert_row([single_row["chat_id"], vehicle_link], "AlreadyScraped")
                print("Inserted new chat_id")
                break

            # check chat_id in already_scraped_df and get the url of that chat_id

            last_url = already_scraped_df_urls[
                already_scraped_df_chat_ids.index(str(single_row["chat_id"]).replace(".0", ""))]
            if last_url == vehicle_link:
                break

            print(record)

            #
            send_message(
                single_row["chat_id"],
                f"Vehicle found: {vehicle_name}")

            with open("already-done.txt", "a") as txt_file:
                txt_file.write(record + "\n")
    session.close()


# FLASK APP -
app = Flask(__name__)


@app.route('/')
def index():
    url = "https://www.subito.it/annunci-lazio/vendita/moto-e-scooter/roma"
    payload = ""
    headers = {
        "authority":
            "www.subito.it",
        "accept":
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language":
            "en,ur;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "cache-control":
            "max-age=0",
        "device-memory":
            "8",
        "ect":
            "4g",
        "sec-ch-ua-mobile":
            "?0",
        "sec-fetch-dest":
            "document",
        "sec-fetch-mode":
            "navigate",
        "sec-fetch-site":
            "none",
        "sec-fetch-user":
            "?1",
        "upgrade-insecure-requests":
            "1",
        "user-agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    return jsonify({
        "Choo Choo":
            f"Welcome to your new Flask app 🚅 {response.status_code}!"
    })


@app.route('/data', methods=['GET'])
def scrape_data():
    # update last time with UTC time

    scraper()
    last_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    update_cell(1, 2, str(last_time), "Sheet2")

    return jsonify({"Choo Choo": f"Welcome to your new scraper Flask app 🚅!"})


if __name__ == '__main__':
    # threading.Thread(target=scraper).start()
    app.run(debug=False, port=os.getenv("PORT", default=5000))
