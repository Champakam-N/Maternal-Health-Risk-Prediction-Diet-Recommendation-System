from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import joblib
import re
from datetime import datetime
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
import re
from flask import jsonify
import pdfkit
from flask import make_response

app = Flask(__name__)
app.secret_key = "maternal_secret_key"
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# ================= LOAD ML MODEL =================
model = joblib.load("maternal_health_model.joblib")
label_encoder = joblib.load("label_encoder.joblib")

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS health_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        timestamp TEXT,
        age REAL,
        gestational_week REAL,
        systolic REAL,
        diastolic REAL,
        sugar REAL,
        temp REAL,
        heart_rate REAL,
        height REAL,
        weight REAL,
        risk TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()



DIET_RULES = {

    "First Trimester": {
        "bmi_low": {
            "eat": "Frequent small meals, milk, curd, nuts, bananas, dates",
            "avoid": "Skipping meals"
        },
        "bmi_high": {
            "eat": "High-fiber vegetables, fruits, lean protein (dal, eggs)",
            "avoid": "Fried foods, sweets, junk food"
        },

        "bp_low": {
            "eat": "Adequate fluids, light salty snacks (if approved)",
            "avoid": "Sudden posture changes"
        },
        "bp_high": {
            "eat": "Fresh fruits and vegetables",
            "avoid": "High-salt and processed foods"
        },

        "sugar_low": {
            "eat": "Frequent meals with protein and complex carbs",
            "avoid": "Skipping meals"
        },
        "sugar_high": {
            "eat": "Low-GI foods like oats and legumes",
            "avoid": "Refined sugar, sweets, soft drinks"
        },

        "hr_low": {
            "eat": "Adequate calories, iron-rich foods",
            "avoid": "Extreme physical exertion"
        },
        "hr_high": {
            "eat": "Plenty of water, magnesium-rich foods",
            "avoid": "Caffeine and energy drinks"
        },

        "temp_low": {
            "eat": "Warm fluids and balanced meals",
            "avoid": "Cold beverages"
        },
        "temp_high": {
            "eat": "Cooling foods like yogurt and fruits",
            "avoid": "Spicy and oily foods"
        }
    },

    "Second Trimester": {
        "bmi_low": {
            "eat": "Protein-rich foods, healthy fats, iron-rich diet",
            "avoid": "Low-calorie diets"
        },
        "bmi_high": {
            "eat": "Balanced meals with portion control",
            "avoid": "Sugary snacks and fried foods"
        },

        "bp_low": {
            "eat": "Fluids and electrolytes, small frequent meals",
            "avoid": "Dehydration"
        },
        "bp_high": {
            "eat": "Potassium-rich foods (banana, coconut water)",
            "avoid": "Excess salt and packaged foods"
        },

        "sugar_low": {
            "eat": "Protein with meals, whole grains",
            "avoid": "Long fasting"
        },
        "sugar_high": {
            "eat": "Vegetables, low-GI foods",
            "avoid": "Sweet beverages and desserts"
        },

        "hr_low": {
            "eat": "Adequate nutrition and iron",
            "avoid": "Fatigue"
        },
        "hr_high": {
            "eat": "Hydration and relaxation foods",
            "avoid": "Stimulants"
        },

        "temp_low": {
            "eat": "Warm foods and drinks",
            "avoid": "Cold exposure"
        },
        "temp_high": {
            "eat": "Water-rich foods (cucumber, watermelon)",
            "avoid": "Heavy spicy meals"
        }
    },

    "Third Trimester": {
        "bmi_low": {
            "eat": "Nutrient-dense meals, smoothies, calcium-rich foods",
            "avoid": "Meal skipping"
        },
        "bmi_high": {
            "eat": "Small frequent meals, high-fiber foods",
            "avoid": "Excess sugar and heavy meals"
        },

        "bp_low": {
            "eat": "Fluids and small frequent meals",
            "avoid": "Sudden standing"
        },
        "bp_high": {
            "eat": "Fresh home-cooked food",
            "avoid": "Salt-heavy and packaged foods"
        },

        "sugar_low": {
            "eat": "Frequent healthy snacks",
            "avoid": "Skipping meals"
        },
        "sugar_high": {
            "eat": "Controlled carbohydrate meals",
            "avoid": "Sweets and sugary foods"
        },

        "hr_low": {
            "eat": "Adequate calories",
            "avoid": "Overexertion"
        },
        "hr_high": {
            "eat": "Hydration and calming foods",
            "avoid": "Caffeine"
        },

        "temp_low": {
            "eat": "Warm fluids",
            "avoid": "Cold foods"
        },
        "temp_high": {
            "eat": "Cooling foods and fluids",
            "avoid": "Spicy foods"
        }
    }
}


NORMAL_RANGES = {
    "bmi": (18.5, 24.9),
    "systolic_bp": (90, 120),
    "diastolic_bp": (60, 80),
    "blood_sugar": (70, 99),
    "heart_rate": (60, 100),
    "temperature": (36.1, 37.2)
}

def get_trimester(week):
    if 1 <= week <= 13:
        return "First Trimester"
    elif 14 <= week <= 26:
        return "Second Trimester"
    elif 27 <= week <= 40:
        return "Third Trimester"
    else:
        return "Invalid Week"


def get_diet_recommendation(week, bmi, sys_bp, dia_bp, sugar, hr, temp):

    trimester = get_trimester(week)

    if trimester == "Invalid Week":
        return {"eat": [], "avoid": ["Invalid pregnancy week"]}

    rules = DIET_RULES[trimester]

    eat_items = []
    avoid_items = []

    # BMI
    if bmi < NORMAL_RANGES["bmi"][0]:
        eat_items.append(rules["bmi_low"]["eat"])
        avoid_items.append(rules["bmi_low"]["avoid"])
    elif bmi > NORMAL_RANGES["bmi"][1]:
        eat_items.append(rules["bmi_high"]["eat"])
        avoid_items.append(rules["bmi_high"]["avoid"])

    # Blood Pressure
    if sys_bp < NORMAL_RANGES["systolic_bp"][0] or dia_bp < NORMAL_RANGES["diastolic_bp"][0]:
        eat_items.append(rules["bp_low"]["eat"])
        avoid_items.append(rules["bp_low"]["avoid"])
    elif sys_bp > NORMAL_RANGES["systolic_bp"][1] or dia_bp > NORMAL_RANGES["diastolic_bp"][1]:
        eat_items.append(rules["bp_high"]["eat"])
        avoid_items.append(rules["bp_high"]["avoid"])

    # Blood Sugar
    if sugar < NORMAL_RANGES["blood_sugar"][0]:
        eat_items.append(rules["sugar_low"]["eat"])
        avoid_items.append(rules["sugar_low"]["avoid"])
    elif sugar > NORMAL_RANGES["blood_sugar"][1]:
        eat_items.append(rules["sugar_high"]["eat"])
        avoid_items.append(rules["sugar_high"]["avoid"])

    # Heart Rate
    if hr < NORMAL_RANGES["heart_rate"][0]:
        eat_items.append(rules["hr_low"]["eat"])
        avoid_items.append(rules["hr_low"]["avoid"])
    elif hr > NORMAL_RANGES["heart_rate"][1]:
        eat_items.append(rules["hr_high"]["eat"])
        avoid_items.append(rules["hr_high"]["avoid"])

    # Temperature
    if temp < NORMAL_RANGES["temperature"][0]:
        eat_items.append(rules["temp_low"]["eat"])
        avoid_items.append(rules["temp_low"]["avoid"])
    elif temp > NORMAL_RANGES["temperature"][1]:
        eat_items.append(rules["temp_high"]["eat"])
        avoid_items.append(rules["temp_high"]["avoid"])

    # CLEAN + UNIQUE
    eat_items = sorted(set(filter(None, eat_items)))
    avoid_items = sorted(set(filter(None, avoid_items)))

    return {
        "eat": eat_items,
        "avoid": avoid_items
    }



# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?",
                    (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/home")
        else:
            error = "Incorrect credentials"

    return render_template("landing.html", error=error)

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    if request.method == "POST":
        fname = request.form["first_name"]
        lname = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]

        if not fname.isalpha() or not lname.isalpha():
            error = "Name must contain only letters"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = "Invalid email format"
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email=?", (email,))
            if cur.fetchone():
                error = "User already exists"
            else:
                cur.execute(
                    "INSERT INTO users VALUES (?,?,?,?)",
                    (email, fname, lname, password)
                )
                conn.commit()
                conn.close()
                return redirect("/")

    return render_template("register.html", error=error)

# ================= HOME =================
@app.route("/home")
def home():
    if "user" not in session:
        return redirect("/")
    return render_template("home.html")

# ================= ASSESSMENT =================
@app.route("/assessment", methods=["GET", "POST"])
def assessment():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":

        age = float(request.form["age"])
        week = int(request.form["gestational_week"])
        systolic = float(request.form["systolic"])
        diastolic = float(request.form["diastolic"])
        sugar = float(request.form["sugar"])
        temp = float(request.form["temp"])
        hr = float(request.form["heart_rate"])
        height = float(request.form["height"])
        weight = float(request.form["weight"])

        # ---------------- ML Prediction ----------------
        data = [[age, systolic, diastolic, sugar, temp, hr]]
        pred = model.predict(data)
        raw_risk = label_encoder.inverse_transform(pred)[0].lower()

        if "high" in raw_risk:
            risk = "High"
        elif "mid" in raw_risk or "medium" in raw_risk:
            risk = "Medium"
        else:
            risk = "Low"


        # ---------------- Save to DB ----------------
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO health_records 
        (email, timestamp, age, gestational_week, systolic, diastolic,
         sugar, temp, heart_rate, height, weight, risk)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            session["user"],
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            age, week, systolic, diastolic,
            sugar, temp, hr, height, weight, risk
        ))
        conn.commit()
        conn.close()

        # ---------------- SAVE DATA FOR DIET ----------------
        height_m = height / 100
        bmi = round(weight / (height_m * height_m), 2)

        session["diet_data"] = {
            "week": week,
            "bmi": bmi,
            "sys": systolic,
            "dia": diastolic,
            "sugar": sugar,
            "hr": hr,
            "temp": temp
        }

        session["predicted_risk"] = risk

        # ✅ Redirect ONLY after POST
        return redirect("/alert")

    # ✅ GET request stays on assessment page
    return render_template("assessment.html")



@app.route("/diet")
def diet():
    if "user" not in session or "diet_data" not in session:
        return redirect("/assessment")

    d = session["diet_data"]

    plan = get_diet_recommendation(
        d["week"], d["bmi"], d["sys"], d["dia"],
        d["sugar"], d["hr"], d["temp"]
    )

    return render_template(
        "diet.html",
        week=d["week"],
        trimester=get_trimester(d["week"]),
        bmi=d["bmi"],
        systolic=d["sys"],
        diastolic=d["dia"],
        sugar=d["sugar"],
        hr=d["hr"],
        temp=d["temp"],
        eat_list=plan["eat"],
        avoid_list=plan["avoid"]
    )

# ================= RESULT =================
@app.route("/result")
def result():
    if "user" not in session:
        return redirect("/")

    risk = session.get("predicted_risk")
    if not risk:
        return redirect("/home")

    return render_template("result.html", risk=risk)

# ================= HISTORY =================
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            timestamp,
            age,
            gestational_week,
            height,
            weight,
            systolic,
            diastolic,
            sugar,
            temp,
            heart_rate,
            risk
        FROM health_records
        WHERE email=?
        ORDER BY timestamp DESC
    """, (session["user"],))
    
    records = cur.fetchall()
    conn.close()

    return render_template("history.html", records=records)

@app.route("/download_report")
def download_report_pdf():
    if "user" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT first_name, last_name, email
        FROM users WHERE email=?
    """, (session["user"],))
    u = cur.fetchone()

    cur.execute("""
        SELECT timestamp, age, gestational_week, height, weight,
               systolic, diastolic, sugar, temp, heart_rate, risk
        FROM health_records
        WHERE email=?
        ORDER BY timestamp
    """, (session["user"],))
    records = cur.fetchall()
    conn.close()

    user_data = {
        "first_name": u[0],
        "last_name": u[1],
        "email": u[2],
        "age": int(round(records[-1][1])) if records else "-"
    }

    html = render_template(
        "download_report.html",
        user=user_data,
        records=records
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdf = pdfkit.from_string(html, False, configuration=config)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=MamaCare_Report.pdf"

    return response

@app.route("/alert")
def alert():
    if "user" not in session or "predicted_risk" not in session:
        return redirect("/home")

    return render_template(
        "alert.html",
        risk=session["predicted_risk"]
    )
@app.route("/upload_report", methods=["POST"])
def upload_report():
    try:
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        file = request.files.get("report")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        # ---------- OPEN PDF ----------
        pdf = fitz.open(stream=file.read(), filetype="pdf")

        # ---------- CASE DETECTION ----------
        sample_text = pdf[0].get_text("text").strip()

        text = ""

        if len(sample_text) > 50:
            # ================= CASE 2 =================
            # Text-based / MamaCare generated PDF
            for page in pdf:
                text += page.get_text("text")
        else:
            # ================= CASE 1 =================
            # Scanned / hospital original PDF (OCR)
            for page in pdf:
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = img.convert("L")
                text += pytesseract.image_to_string(
                    img, config="--oem 3 --psm 6"
                )

        # ---------- NORMALIZE ----------
        text = text.upper()
        text = re.sub(r'\s+', ' ', text)

        print("EXTRACTED TEXT:", text)

        # ---------- AGE ----------
        age = None
        m = re.search(r'AGE[:\s]+(\d{1,2})', text)
        if m:
            age = int(m.group(1))

        # ---------- TRY CASE 2 (TABLE FORMAT) ----------
        rows = re.findall(
            r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+'
            r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+'
            r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+'
            r'(\d+\.?\d*)\s+(\d+\.?\d*)',
            text
        )

        week = systolic = diastolic = sugar = temp = heart_rate = height = weight = None

        if rows:
            # ================= CASE 2 PARSING =================
            latest = rows[-1]
            week, systolic, diastolic, sugar, temp, heart_rate, height, weight = map(
                float, latest[2:]
            )

        else:
            # ================= CASE 1 PARSING =================
            # Paragraph-based hospital reports

            def find(pattern):
                m = re.search(pattern, text)
                return float(m.group(1)) if m else None

            def find_pair(pattern):
                m = re.search(pattern, text)
                return (
                    float(m.group(1)),
                    float(m.group(2))
                ) if m else (None, None)

            week = find(r'GESTATIONAL WEEK[:\s]+(\d+)')

            systolic, diastolic = find_pair(
                r'BLOOD PRESSURE[:\s]+(\d+)\s*/\s*(\d+)'
            )

            sugar = find(r'BLOOD SUGAR[:\s]+(\d+)')

            temp = find(r'BODY TEMPERATURE[:\s]+([\d.]+)')

            heart_rate = find(r'HEART RATE[:\s]+(\d+)')

            height = find(r'HEIGHT[:\s]+(\d+)')

            weight = find(r'WEIGHT[:\s]+(\d+)')

        # ---------- RETURN JSON ----------
        return jsonify({
            "age": age,
            "week": week,
            "systolic": systolic,
            "diastolic": diastolic,
            "sugar": sugar,
            "temp": temp,
            "heart_rate": heart_rate,
            "height": height,
            "weight": weight
        })

    except Exception as e:
        print("UPLOAD ERROR:", e)
        return jsonify({"error": str(e)}), 500

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
