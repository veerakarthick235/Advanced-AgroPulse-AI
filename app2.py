import os
import base64
import json
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import cloudinary 
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- NEW LIBRARY IMPORT ---
from googleapiclient.discovery import build

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- GETTING ALL API KEYS FROM .env ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
DATA_GOV_API_KEY = os.getenv("DATA_GOV_API_KEY")
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# --- Cloudinary Configuration ---
try:
    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        secure=True
    )
    print("Cloudinary configured successfully.")
except Exception as e:
    print(f"Error configuring Cloudinary: {e}")

# --- Firebase Configuration ---
try:
    if not FIREBASE_CREDENTIALS_PATH or not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"Firebase credentials file not found at path: {FIREBASE_CREDENTIALS_PATH}. Check your .env file.")
    cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firestore initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore: {e}")
    db = None

# --- Gemini API Configuration ---
MODEL_NAME = "gemini-1.5-flash-latest"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"


# --- NEW HELPER FUNCTION TO SEARCH FOR IMAGES ---
def get_image_url_from_google(query):
    """Searches for an image using Google Custom Search API and returns the first result."""
    try:
        if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
            print("WARNING: Google CSE API Key or ID is not set. Cannot search for image.")
            return None
            
        service = build("customsearch", "v1", developerKey=GOOGLE_CSE_API_KEY)
        res = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            searchType='image',
            num=1,
            safe='high'
        ).execute()

        if 'items' in res and len(res['items']) > 0:
            return res['items'][0]['link']
        else:
            return None
    except Exception as e:
        print(f"ERROR during Google Image Search: {e}")
        return None

# --- START OF FLASK ROUTES ---

@app.route("/")
def index():
    """Renders the main page."""
    return render_template("index.html")

@app.route('/buyer')
def buyer_page():
    """Renders the buyer marketplace page."""
    return render_template('index2.html')

@app.route("/ask-agro-assistant", methods=["POST"])
def ask_agro_assistant():
    """Handles chatbot queries using the Gemini API."""
    try:
        data = request.get_json()
        user_question = data.get("question", "").strip()

        if not user_question:
            return jsonify({"error": "No question provided."}), 400

        system_prompt = """
        You are 'Agro Assistant', a friendly and helpful AI chatbot for a web application designed for farmers.
        Your purpose is to answer user questions about the features of the Agro Assistant application.
        Your answers should be concise, helpful, and in a conversational tone.

        Here is a summary of the application's features:
        - *Crop Disease Prediction*: Users can upload an image of a crop leaf, and the AI will identify if it has a disease and suggest remedies.
        - *Weather Forecast*: Provides real-time weather updates for any city or the user's current location.
        - *Market Prices*: Tracks the latest prices of vegetables in local markets.
        - *AI Planner*: Gives intelligent suggestions for crops to plant based on land area and season.
        - *Buy/Sell Marketplace*: A platform for farmers to list their products.
        - *Agri News*: Shows the latest agricultural news from India.
        - *Agri Loan Application*: A form for farmers to apply for loans.
        - *About Us*: Information about the app's mission and the development team.
        """

        gemini_payload = { "contents": [{"parts": [{"text": system_prompt}, {"text": f"User's question: {user_question}"}]}]}
        response = requests.post(GEMINI_API_URL, json=gemini_payload, timeout=45)
        response.raise_for_status()
        result_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"answer": result_text})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to the AI service: {e}"}), 503
    except Exception as e:
        print(f"CHATBOT ERROR: {e}")
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route("/upload-item-image", methods=["POST"])
def upload_item_image():
    if 'item_image' not in request.files:
        return jsonify({"error": "No 'item_image' file part"}), 400
    file_to_upload = request.files['item_image']
    if file_to_upload.filename == '':
        return jsonify({"error": "No file selected"}), 400
    try:
        upload_result = cloudinary.uploader.upload(file_to_upload, folder="agri_assistant_items")
        return jsonify({"imageUrl": upload_result.get('secure_url')})
    except Exception as e:
        return jsonify({"error": f"Failed to upload image: {e}"}), 500

@app.route('/upload-profile-image', methods=['POST'])
def upload_profile_image():
    if 'profile_image' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    try:
        upload_result = cloudinary.uploader.upload(file, folder="agro_assistant_profiles")
        secure_url = upload_result.get('secure_url')
        return jsonify({'message': 'Image uploaded successfully', 'secure_url': secure_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add-item', methods=['POST'])
def add_item():
    if not db: return jsonify({"error": "Database not initialized"}), 500
    try:
        data = request.get_json()
        db.collection('products').add(data)
        return jsonify({"success": True, "message": "Item added successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add item: {e}"}), 500

@app.route('/get-items', methods=['GET'])
def get_items():
    if not db: return jsonify({"error": "Database not initialized"}), 500
    try:
        products_ref = db.collection('products').stream()
        products_list = [doc.to_dict() for doc in products_ref]
        return jsonify(products_list)
    except Exception as e:
        return jsonify({"error": f"Failed to get items: {e}"}), 500

@app.route("/agri-news", methods=["GET"])
def agri_news():
    if not NEWS_API_KEY: return jsonify({"error": "News API key is not configured."}), 500
    search_query = '("agriculture" OR "farming" OR "horticulture") AND "india"'
    url = f"https://newsapi.org/v2/everything?q={search_query}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        news_data = response.json()
        return jsonify({"articles": news_data.get("articles", [])[:20]})
    except Exception as e:
        return jsonify({"error": f"Could not retrieve news data: {e}"}), 502

@app.route("/predict", methods=["POST"])
def predict():
    if 'leaf' not in request.files: return jsonify({"error": "No 'leaf' file part"}), 400
    file = request.files['leaf']
    if file.filename == '': return jsonify({"error": "No file selected"}), 400
    try:
        image_b64 = base64.b64encode(file.read()).decode("utf-8")
        prompt_text = """Analyze the provided plant leaf image for Indian farming conditions and generate a complete farming guide. The entire output must be a single block of plain text. Use these exact headings:
### DISEASE ANALYSIS ###
- Identify the disease or state if healthy. Provide 3 remedies.
### HEALTHY LEAF TIPS ###
- If healthy, provide 3 care tips. Otherwise, skip.
### SOIL SUITABILITY ###
- Ideal soil type and pH.
### WATERING GUIDE ###
- Watering schedule and moisture check method.
### FERTILIZER RECOMMENDATION ###
- Suitable NPK ratio/manure and application frequency.
### PEST CONTROL ###
- 2-3 common pests and their organic/chemical control.
### PLANTING GUIDE ###
- Ideal spacing and planting depth."""
        gemini_payload = {"contents": [{"parts": [{"inlineData": {"mime_type": "image/jpeg", "data": image_b64}}, {"text": prompt_text}]}]}
        response = requests.post(GEMINI_API_URL, json=gemini_payload, timeout=60)
        response.raise_for_status()
        prediction_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"prediction_text": prediction_text})
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

@app.route("/weather", methods=["GET"])
def weather():
    lat, lon, city = request.args.get("lat"), request.args.get("lon"), request.args.get("city")
    if not OPENWEATHER_API_KEY: return jsonify({"error": "Weather API key not configured"}), 500
    try:
        if city:
            geo_data = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}").json()
            if not geo_data: return jsonify({"error": f"City '{city}' not found."}), 404
            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
        elif not lat or not lon:
            return jsonify({"error": "City name or coordinates are required"}), 400
        
        one_call_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={OPENWEATHER_API_KEY}"
        weather_data = requests.get(one_call_url).json()
        air_pollution_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        air_data = requests.get(air_pollution_url).json()
        
        weather_data['air_quality'] = air_data.get('list', [{}])[0]
        weather_data['city_name'] = city or weather_data.get('timezone', 'Unknown').split('/')[-1].replace('_', ' ')
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": f"Could not connect to weather service: {e}"}), 502

@app.route("/prices", methods=["GET"])
def prices():
    location = request.args.get('location', '').strip()
    vegetable = request.args.get('vegetable', '').strip()
    if not location or not vegetable: return jsonify({"error": "Location and vegetable are required."}), 400

    try: # Attempt real-time data first
        resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
        gov_api_url = f"https://api.data.gov.in/resource/{resource_id}?api-key={DATA_GOV_API_KEY}&format=json&filters[market]={location.title()}&filters[commodity]={vegetable.title()}"
        response = requests.get(gov_api_url, timeout=10)
        if response.ok and response.json().get('records'):
            record = response.json()['records'][-1]
            return jsonify({"prices": [{"name": record.get('commodity'), "location": record.get('market'), "price": f"₹ {record.get('modal_price', 'N/A')} per Quintal"}]})
    except requests.exceptions.RequestException:
        pass # Fallback to AI if real-time fails

    try: # AI Fallback
        prompt = f'Provide an average market price for "{vegetable}" in "{location}, India". Respond in this exact JSON format: {{"estimated_price": "Approx. ₹X per Kg"}}'
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
        response = requests.post(GEMINI_API_URL, json=payload, timeout=45)
        response.raise_for_status()
        price_data = json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
        return jsonify({"prices": [{"name": vegetable.title(), "location": location.title(), "price": f"{price_data.get('estimated_price')} (Estimated)"}]})
    except Exception as e:
        return jsonify({"error": f"Sorry, could not estimate the price for {vegetable}."}), 500

@app.route("/vegetable-info", methods=["GET"])
def vegetable_info():
    vegetable_name = request.args.get('name', '').strip()
    if not vegetable_name: return jsonify({"error": "Vegetable name is required."}), 400
    try:
        prompt = f"""
        Provide a detailed guide for the vegetable '{vegetable_name}'. Respond in this exact JSON format:
        {{
          "name": "{vegetable_name.title()}",
          "image_search_term": "High quality photo of fresh {vegetable_name}",
          "history": "A brief history of the vegetable's origin and journey to India (2-3 sentences).",
          "cultivation": {{
            "soil": "Ideal soil type and pH range.", "water": "Watering requirements.", "climate": "Suitable climate conditions."
          }},
          "nutrition": [
            {{"nutrient": "Calories", "value": "Approx. per 100g"}}, {{"nutrient": "Vitamin C", "value": "Approx. % of Daily Value"}},
            {{"nutrient": "Potassium", "value": "Approx. per 100g"}}, {{"nutrient": "Fiber", "value": "Approx. per 100g"}}
          ]
        }}
        """
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
        response = requests.post(GEMINI_API_URL, json=payload, timeout=45)
        response.raise_for_status()
        veg_data = json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
        
        search_term = veg_data.get("image_search_term", vegetable_name)
        image_url = get_image_url_from_google(search_term)
        
        veg_data["image_url"] = image_url or "https://i.pinimg.com/564x/12/37/c4/1237c44565d7595d52f3e8b0f24c322b.jpg"
        return jsonify(veg_data)
    except Exception as e:
        return jsonify({"error": f"Could not retrieve details for {vegetable_name}."}), 500

def get_current_indian_season():
    month = datetime.now().month
    if 6 <= month <= 10: return "Kharif (Monsoon Crop)"
    if 11 <= month or month <= 3: return "Rabi (Winter Crop)"
    return "Zaid (Summer Crop)"

@app.route("/planner", methods=["GET"])
def planner():
    crop, area, location = request.args.get("crop"), request.args.get("area"), request.args.get("location")
    if not all([crop, area, location]): return jsonify({"error": "Crop, area, and location are required"}), 400
    season = get_current_indian_season()
    prompt = f"""
    Create a practical farming plan for: Crop: {crop}, Area: {area} acres, Location: {location}, India, Season: {season}.
    Respond ONLY with a JSON object in this exact structure:
    {{
      "plan_summary": {{"title": "Catchy Plan Title", "suitability": "Brief suitability analysis."}},
      "cost_and_profit_estimation": {{
        "total_estimated_cost": "Total cost range, e.g., 'Approx. ₹X - ₹Y total'.",
        "cost_breakdown": [{{"item": "Seeds", "cost": "e.g., ₹X"}}, {{"item": "Labor", "cost": "e.g., ₹Y"}}],
        "estimated_yield": "e.g., 'X-Y Tonnes'", "estimated_profit": "e.g., 'Approx. ₹X - ₹Y'"
      }},
      "step_by_step_guide": {{
        "timeline_weeks": "e.g., '12-14 Weeks'",
        "steps": [{{"stage": "Week 1-2: Prep", "action": "Details."}}, {{"stage": "Week 3: Planting", "action": "Details."}}]
      }}
    }}
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}
    try:
        response = requests.post(GEMINI_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        plan_data = json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
        return jsonify(plan_data)
    except Exception as e:
        return jsonify({"error": f"Failed to generate plan: {e}"}), 500

if __name__ == "__main__":
    print("Starting Flask server...")

    app.run(host='0.0.0.0', port=5000, debug=True)
