from flask import Flask, jsonify
import os
import requests
import Bot

app = Flask(__name__)


@app.route('/')
def index():
    url = "https://www.subito.it/annunci-lazio/vendita/moto-e-scooter/roma"
    payload = ""
    headers = {
        "authority": "www.subito.it",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en,ur;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "cache-control": "max-age=0",
        "device-memory": "8",
        "ect": "4g",

        "sec-ch-ua-mobile": "?0",

        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    return jsonify({"Choo Choo": f"Welcome to your Flask app 🚅 {response.status_code}!"})


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
