# 🌿 AI Agri Assistant

An intelligent, full-stack web application designed to be a modern farmer's digital companion. AI Agri Assistant leverages the power of AI and real-time data to provide crucial insights, from crop disease detection to market price analysis, helping farmers make informed decisions and improve productivity.

---

## ✨ Core Features

* 🤖 **AI-Powered Crop Guide**: Upload an image of a plant leaf and get an instant analysis of its health, potential diseases, and a complete guide covering soil, water, fertilizer, and pest control.

* 🌦️ **Real-time Weather Hub**: Get current weather, hourly/daily forecasts, and air quality data for any location. Includes historical weather data for the past 7 days.

* 📈 **Dynamic Market Prices**: Fetches real-time vegetable prices from government APIs (data.gov.in) and uses AI fallback for estimations.

* 🌱 **Intelligent Crop Planner**: Detailed, customized farming plans based on crop type, land area, and location, including cost-profit analysis and step-by-step timeline.

* 🛒 **Buy/Sell Marketplace**: Platform for farmers to sell produce directly and buyers to purchase fresh goods.

* 📰 **Agri News Feed**: Stay updated with the latest agricultural news from India and worldwide.

* 💵 **Agri Loan Assistance**: Check loan eligibility and apply by submitting necessary documents.

* 💬 **Conversational AI Assistant**: Chatbot powered by Google Gemini to answer any questions about the application.

---

## 🛠️ Technology Stack

* **Backend:** Python with Flask
* **Frontend:** HTML5, CSS3, JavaScript
* **Database:** Google Firebase (Firestore)
* **Authentication & User Management:** Google Firebase (Authentication)
* **Image Storage:** Cloudinary
* **AI & Machine Learning:** Google Gemini Pro & Gemini Flash

**External APIs:**

* OpenWeatherMap API
* NewsAPI
* Google Custom Search Engine (CSE) API
* Data.gov.in API

**Deployment:** Ready for Vercel or any WSGI server.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+ and Pip
* Node.js (for frontend tooling)
* Firebase project with Firestore and Authentication enabled
* Cloudinary account

### Installation & Setup

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

2. **Set up Python Backend:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

3. **Configure Environment Variables:**

* Create a `.env` file in the root directory.
* Fill in your API keys and credentials for each service.

4. **Firebase Credentials:**

* Generate a new private key for the Firebase Service Account.
* Rename the JSON file to `serviceAccountKey.json` and place it in the project's root directory.

5. **Run the Flask Application:**

```bash
python app.py
```

The application will be running at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 📄 License

MIT License
