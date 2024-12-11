import datetime
import dotenv
import os
from flask import Flask, jsonify, request, send_file
from flask_caching import Cache
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import requests
import csv
import json
from flask_cors import CORS, cross_origin

dotenv.load_dotenv()
API_URL = os.getenv("API_URL")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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
            return json_data
        else:
           return f"Failed to fetch data for city: {city}. Status code: {response.status_code}"
    except Exception as e:
        return f"Error during API call for city {city}: {e}"

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

def fetch_cities_from_csv(file_path, start, count=5):
    cities = []
    try:
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            for i, row in enumerate(csv_reader):
                if i < start:
                    continue
                if len(cities) >= count:
                    break
                cities.append(row[0])
        print(f"Top {count} cities fetched from CSV file starting from index {start}.")
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

# Function to get healthcare instructions from Gemini API
def get_health_instructions_from_gemini(city, aqi, health_issues=None, api_key="your_gemini_api_key_here"):
    # Gemini API URL
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    # Prepare the prompt text
    user_input = f"City: {city}\nAQI: {aqi}\nHealth Condition: {health_issues if health_issues else 'None'}\n\nProvide personalized healthcare recommendations based on the AQI level and health condition."

    # Construct the payload according to the correct structure
    payload = {
        "contents": [{
            "parts": [{
                "text": user_input
            }]
        }]
    }

    # Set headers for the API request
    headers = {
        "Content-Type": "application/json"
    }

    # Send the request to the Gemini API
    response = requests.post(api_url, json=payload, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Directly extract the 'content' from the response
        content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "No personalized health instructions available.")
        return content
    else:
        raise ValueError(f"Error fetching content: {response.status_code} - {response.text}")

# Function to generate the markdown output
def generate_markdown_output(city, aqi, health_issues=None, api_key="your_gemini_api_key_here"):
    try:
        # Get health instructions from Gemini API
        health_instructions = get_health_instructions_from_gemini(city, aqi, health_issues, api_key)
        
        # Create the Markdown formatted string
        markdown_content = f"""
# AQI Health Advisory for {city}

**AQI Level**: {aqi}

### Healthcare Recommendations:

{health_instructions}

"""
        return markdown_content

    except Exception as e:
        return f"Error: {str(e)}"

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'  # Use in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 1800  # Cache timeout in seconds
cache = Cache(app)
CORS(app)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/sensor/wifi', methods=['POST'])
def sensor_wifi():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        client = connect_to_mongodb(MONGODB_URI)
        if not client:
            return jsonify({"error": "Failed to connect to MongoDB"}), 500

        db = client['sensor_wifi']
        print(data.get('deviceID'))
        collection = data.get('deviceID')

        if collection is None:
            return jsonify({"error": "Insufficient Data"}), 400
        
        data["timestamp"] = datetime.datetime.now()

        insert_data_into_collection(db, collection, data)
        return jsonify({"message": "Data stored successfully"}), 201
    except Exception as e:
        send_discord_notification(DISCORD_WEBHOOK, e)
        return jsonify({"error": "Something went wrong"}), 500

@app.route('/fetch/hw/<deviceId>', methods=['GET'])
@cross_origin()
@cache.cached(timeout=5)
def fetch_all_hw(deviceId):
    try:
        client = connect_to_mongodb(MONGODB_URI)
        if not client:
            return jsonify({"error": "Failed to connect to MongoDB"}), 500
        db = client['sensor_wifi']
        cursor = db[deviceId].find().sort("timestamp", -1).limit(15)
        response = list(cursor)

        for doc in response:
            doc['_id'] = str(doc['_id'])
        return jsonify(response), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong"}), 400
    
@app.route('/csv/hw/<device_id>', methods=['GET'])
@cross_origin()
def export_to_csv(device_id):
    try:
        client = connect_to_mongodb(MONGODB_URI)
        if not client:
            return jsonify({"error": "Failed to connect to MongoDB"}), 500
        db = client['sensor_wifi']
        cursor = db[device_id].find().sort("timestamp", -1)
        data = list(cursor)

        if not data:
            return jsonify({"error": "No data found for device: " + device_id}), 404

        # Create CSV file
        csv_file_path = os.path.join(os.getcwd(), f"{device_id}_data.csv")
        os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Write headers
            headers = data[0].keys()
            writer.writerow(headers)
            # Write data rows
            for document in data:
                writer.writerow(document.values())

        # Send CSV file in response
        response = send_file(csv_file_path, as_attachment=True)
        # os.remove(csv_file_path)  # Delete the CSV file after sending
        return response, 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Something went wrong"}), 500
    
@app.route('/fetch/<city>', methods=['GET'])
@cross_origin()
@cache.cached(timeout=1800) 
def fetch(city):
    city = city.lower()
    try:
        # client = connect_to_mongodb(MONGODB_URI)
        # if not client:
        #     return "Failed to connect to MongoDB", 500
        # db = client[DB_NAME]
        response = fetch_data_from_api(city)
        if not isinstance(response, dict) or response['data']['stations'] is None:
            return jsonify({"error": "No data found for city: " + city}), 404

        # if '_id' in response: 
        #     print(f"Deleting _id from response: {response['_id']}")
        #     del response['_id']
        # insert_data_into_collection(db, city, response)
        # if response:
        #     response['_id'] = str(response['_id'])
        if isinstance(response, dict):
            response = json.loads(json.dumps(response, default=str))
        return jsonify(response), 200
    except Exception as e:
        print(f"Error: {e}")
        return "Something went wrong", 400
    
@app.route('/gemini', methods=['POST'])
@cross_origin()
def get_gemini():
    data = request.get_json()
    if not data or 'city' not in data or 'aqi' not in data or 'health_issues' not in data:
        return jsonify({"error": "Missing required fields"}), 400

    city = data['city']
    aqi = data['aqi']
    health_issues = data['health_issues']
    return generate_markdown_output(city, aqi, health_issues, GEMINI_API_KEY)
    
if __name__ == "__main__":
    # threading.Thread(target=execute_periodically, args=(3600, main_task)).start()
    app.run(debug=True,host="0.0.0.0")
