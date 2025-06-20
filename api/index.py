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
from datetime import datetime
from bson import ObjectId
from flask_restful import Api, Resource, reqparse
# import numpy as np
# from tensorflow.keras.models import Sequential, load_model
# from tensorflow.keras.layers import Dense, LSTM
# from sklearn.preprocessing import MinMaxScaler
# import joblib
# from datetime import datetime, timedelta

dotenv.load_dotenv()
API_URL = os.getenv("API_URL")
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")


### ML MODELING

# def get_paths(city):
    # MODEL_PATH = f"lstm_aqi_model_{city}.h5"
    # SCALER_PATH = f"scaler_{city}.pkl"

    # return MODEL_PATH, SCALER_PATH

# def fetch_30days_data_from_api(city):
#     headers = {
#         'Authorization': f'bearer {AUTH_TOKEN}',
#         'Content-Type': 'application/x-www-form-urlencoded',
#         'Accept': 'application/json',
#         'searchtype': "cityId",
#         'locationid': city,
#         'sendevid': "AQI-IN"
#     }
#     try:
#         response = requests.get("https://airquality.aqi.in/api/v1/getLastMonthHistory", headers=headers)
#         if response.status_code == 200:
#             json_data = response.json()
#             print(f"Data fetched for city: {city}")
            
#             # Extract AQI data and timeArray
#             aqi_data = json_data.get("Table", {}).get("Data", {}).get("averageArray", [])
#             time_data = json_data.get("Table", {}).get("Data", {}).get("timeArray", [])

#             latest_date = max(time_data)
            
#             return aqi_data, latest_date
#         else:
#             print(f"Failed to fetch data for city: {city}. Status code: {response.status_code}")
#             return [], []
#     except Exception as e:
#         print(f"Error during API call for city {city}: {e}")
#         return [], []

# def create_and_train_model(aqi_data, MODEL_PATH, SCALER_PATH):
#     # Prepare the data
#     scaler = MinMaxScaler(feature_range=(0, 1))
#     aqi_data_scaled = scaler.fit_transform(np.array(aqi_data).reshape(-1, 1))

#     # Prepare the input-output pairs for training (using last 5 days to predict next day)
#     X, y = [], []
#     for i in range(len(aqi_data_scaled) - 5):
#         X.append(aqi_data_scaled[i:i+5, 0])  # Last 5 days of data
#         y.append(aqi_data_scaled[i+5, 0])    # Next day's data
#     X, y = np.array(X), np.array(y)

#     # Reshape X for LSTM input
#     X = X.reshape(X.shape[0], X.shape[1], 1)

#     # Create the LSTM model
#     model = Sequential()
#     model.add(LSTM(units=50, return_sequences=False, input_shape=(X.shape[1], 1)))
#     model.add(Dense(units=1))
#     model.compile(optimizer='adam', loss='mean_squared_error')

#     # Train the model
#     model.fit(X, y, epochs=10, batch_size=32)

#     # Save the model and scaler
#     model.save(MODEL_PATH)
#     joblib.dump(scaler, SCALER_PATH)

#     print("Model and scaler saved!")
#     return model, scaler

# def load_or_create_model_and_scaler(CITY_ID, MODEL_PATH, SCALER_PATH):
#     if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
#         # Load pre-trained model and scaler
#         model = load_model(MODEL_PATH)
#         scaler = joblib.load(SCALER_PATH)
#         print("Loaded pre-trained model and scaler.")
#     else:
#         # Create and train the model and scaler
#         print("Model or scaler not found. Creating and training a new model.")
#         # Fetch AQI data from the API
#         aqi_data, latest_date = fetch_30days_data_from_api(CITY_ID)
#         if not aqi_data:
#             print("Insufficient data to create the model.")
#             return None, None
#         model, scaler = create_and_train_model(aqi_data, MODEL_PATH, SCALER_PATH)
    
#     return model, scaler

# def predict_aqi(city):
#     MODEL_PATH, SCALER_PATH = get_paths(city)
#     # Load or create the model and scaler
#     model, scaler = load_or_create_model_and_scaler(city, MODEL_PATH, SCALER_PATH)
#     if model is None or scaler is None:
#         return {"error": "Failed to load or create model and scaler."}

#     # Fetch AQI data and corresponding dates for the given city
#     aqi_data, prediction_date = fetch_30days_data_from_api(city)
    
#     if not aqi_data or len(aqi_data) < 5:  # Ensure enough data is available
#         return {"error": "Insufficient data for prediction."}

#     # Scale the data
#     aqi_data_scaled = scaler.transform(np.array(aqi_data).reshape(-1, 1))

#     # Prepare the input sequence (last 5 days of data)
#     sequence_length = 5
#     input_sequence = np.array(aqi_data_scaled[-sequence_length:]).reshape(1, sequence_length, 1)

#     # Make the prediction
#     prediction_scaled = model.predict(input_sequence)
#     prediction = scaler.inverse_transform(prediction_scaled)[0][0]


#     date_obj = datetime.strptime(prediction_date.split()[0], "%Y-%m-%d")

#     next_date_obj = date_obj + timedelta(days=1)

#     # Convert back to string
#     next_date = next_date_obj.strftime("%Y-%m-%d")

#     # Return the prediction as a dictionary
#     return {
#         "city": city,
#         "prediction": round(prediction, 2),
#         "unit": "AQI",
#         "prediction_date": next_date
#     }

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

def get_health_instructions_from_gemini(city, aqi, health_issues=None, api_key="your_gemini_api_key_here"):
    # Gemini API URL
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    # Prepare the prompt text
    user_input = f"""
City: {city}
AQI: {aqi}
Health Condition: {health_issues if health_issues else 'None'}

Provide clear and simple healthcare recommendations based on the AQI level and health condition. Keep the points short, easy to understand, and actionable.
"""


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

client = connect_to_mongodb(MONGODB_URI)
db = client[DB_NAME]
collection = db['blogs']
api = Api(app)

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
        # print(data.get('deviceID'))
        col = data.get('deviceID')
        # collection = None

        if col is None:
            return jsonify({"error": "Insufficient Data"}), 400
        
        data["timestamp"] = datetime.now()
        print(data)

        insert_data_into_collection(db, col, data)
        return jsonify({"message": "Data stored successfully"}), 201
    except Exception as e:
        return jsonify({"error": "Something went wrong"}), 500

@app.route('/fetch/hw/<deviceId>', methods=['GET'])
@cross_origin()
# @cache.cached(timeout=5)
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
        csv_file_path = os.path.join(os.getcwd(), f"/tmp/{device_id}_data.csv")
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
    

@app.route('/fetch/<city>/history', methods=['GET'])
def fetch_history(city):
    headers = {
        'Authorization': f'bearer {AUTH_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'searchtype': "cityId",
        'locationid': city,
        'sendevid': "AQI-IN"
    }
    try:
        response = requests.get("https://airquality.aqi.in/api/v1/getLastMonthHistory", headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            return json_data
        else:
            print(f"Failed to fetch data for city: {city}. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error during API call for city {city}: {e}")
        return []

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

@app.route('/devices', methods=['GET'])
def get_devices():
    client = connect_to_mongodb(MONGODB_URI)
    if not client:
        return jsonify({"error": "Failed to connect to MongoDB"}), 500
    db = client['sensor_wifi']
    collections = db.list_collection_names()
    return jsonify(collections), 200

class BlogResource(Resource):
    # @cache.cached(timeout=1800)
    def get(self, blog_id=None):
        if blog_id:
            blog = collection.find_one({"_id": ObjectId(blog_id)})
            if not blog:
                return {"error": "Blog not found"}, 404
            blog["_id"] = str(blog["_id"])
            return blog, 200
        else:
            blogs = list(collection.find())
            for blog in blogs:
                blog["_id"] = str(blog["_id"])
            return blogs, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('author', required=True)
        parser.add_argument('content', required=True)
        parser.add_argument('imageurl', required=False)
        args = parser.parse_args()

        blog = {
            "title": args['title'],
            "author": args['author'],
            "content": args['content'],
            "imageurl": args['imageurl']
        }
        result = collection.insert_one(blog)
        blog["_id"] = str(result.inserted_id)
        return blog, 201

    def put(self, blog_id):
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True)
        parser.add_argument('author', required=True)
        parser.add_argument('content', required=True)
        parser.add_argument('imageurl', required=False)
        args = parser.parse_args()

        updated_blog = {
            "title": args['title'],
            "author": args['author'],
            "content": args['content'],
            "imageurl": args.get('imageurl')
        }
        result = collection.update_one({"_id": ObjectId(blog_id)}, {"$set": updated_blog})
        if result.matched_count == 0:
            return {"error": "Blog not found"}, 404
        updated_blog["_id"] = blog_id
        return updated_blog, 200

    def delete(self, blog_id):
        blog = collection.find_one_and_delete({"_id": ObjectId(blog_id)})
        if not blog:
            return {"error": "Blog not found"}, 404
        blog["_id"] = str(blog["_id"])
        return blog, 200

api.add_resource(BlogResource, '/blogs', '/blogs/<string:blog_id>')
    
if __name__ == "__main__":
    # threading.Thread(target=execute_periodically, args=(3600, main_task)).start()
    app.run(debug=True,host="0.0.0.0")
