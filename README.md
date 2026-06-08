#  Maternal Health Risk Prediction & Diet Recommendation System

This project is a Flask-based web application that predicts maternal health risk using Machine Learning and provides personalized diet recommendations based on medical parameters.

##  Features

* User Authentication (Login/Register)
* Machine Learning Risk Prediction (Low / Medium / High)
* Trimester-based Diet Recommendation System
* Health Record Storage & History Tracking
* PDF Report Generation
* Upload Medical Reports (OCR + Text Extraction)
* BMI Calculation & Analysis

##  Machine Learning Model

* Algorithm: Random Forest Classifier
* Pipeline:

  * StandardScaler
  * RandomForestClassifier (200 estimators)
* Features Used:

  * Age
  * Systolic BP
  * Diastolic BP
  * Blood Sugar (BS)
  * Body Temperature
  * Heart Rate

##  Project Structure

project/
│
├── app.py
├── train.py
│
├── templates/
│   ├── landing.html
│   ├── register.html
│   ├── home.html
│   ├── assessment.html
│   ├── result.html
│   ├── diet.html
│   ├── history.html
│   ├── alert.html
│   ├── download_report.html
│
├── static/
│
└── README.md

##  Installation

1. Clone the repository
   git clone <your-repo-link>
   cd project

2. Create virtual environment (recommended)
   python -m venv venv
   venv\Scripts\activate

3. Install dependencies
   pip install -r requirements.txt

##  Running the Application

python app.py

Open browser:
http://127.0.0.1:5000

##  Model Training

python train_model.py

This generates:

* maternal_health_model.joblib
* label_encoder.joblib
* model_features.joblib

##  OCR Setup

Install Tesseract OCR and update path in app.py:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

##  PDF Setup

Install wkhtmltopdf and update path in app.py:
wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"

##  Database

* SQLite database (database.db)
* Tables: users, health_records

##  Diet Recommendation Logic

Based on:

* Trimester
* BMI
* Blood Pressure
* Sugar Levels
* Heart Rate
* Temperature

##  Author

Champakam N

##  License

This project is for academic and research purposes.

