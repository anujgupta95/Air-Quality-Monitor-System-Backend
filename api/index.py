import requests
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import dotenv
import os
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

dotenv.load_dotenv()

API_URL = os.getenv("API_URL")
CITY_FILE_PATH = os.getenv("CITY_FILE_PATH")
CITY_COUNT = int(os.getenv("CITY_COUNT", 5))
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def connect_to_mongodb(uri):
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return client
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return None

def fetch_data_from_api(city):
    headers = {
        'Authorization': 'your_auth_token_here',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'searchString': city
    }
    try:
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            print(f"Data fetched for city: {city}")
            return city, json_data
        else:
            print(f"Failed to fetch data for city: {city}. Status code: {response.status_code}")
            return city, None
    except Exception as e:
        print(f"Error during API call for city {city}: {e}")
        return city, None

def insert_data_into_collection(db, collection_name, data):
    try:
        collection = db[collection_name]
        if isinstance(data, list):
            collection.insert_many(data)
        else:
            collection.insert_one(data)
        print(f"Data inserted into collection: {collection_name}")
    except Exception as e:
        print(f"Error inserting data into collection {collection_name}: {e}")

def fetch_cities_from_csv(file_path, count=5):
    cities = []
    try:
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for i, row in enumerate(csv_reader):
                if i >= count:
                    break
                cities.append(row[0])
            print(f"Top {count} cities fetched from CSV file.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return cities

def send_discord_notification(webhook_url, message):
    try:
        data = {"content": message}
        response = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        if response.status_code == 204:
            print("Notification sent successfully.")
        else:
            print(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def execute_periodically(interval, func, *args, **kwargs):
    while True:
        start_time = time.time()
        func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        time.sleep(max(0, interval - elapsed_time))

def main_task():
    cities = fetch_cities_from_csv(CITY_FILE_PATH, count=CITY_COUNT)
    client = connect_to_mongodb(MONGODB_URI)
    if not client:
        return
    db = client[DB_NAME]

    fetched_cities = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_city = {executor.submit(fetch_data_from_api, city): city for city in cities}
        for future in as_completed(future_to_city):
            city, api_data = future.result()
            if api_data:
                insert_data_into_collection(db, city, api_data)
                fetched_cities.append(city)

    if fetched_cities:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        message = f"Data fetched at {timestamp} for cities: {', '.join(fetched_cities)}"
        send_discord_notification(DISCORD_WEBHOOK, message)

if __name__ == "__main__":
    threading.Thread(target=execute_periodically, args=(3600, main_task)).start()
    app.run(debug=True)