from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from datetime import datetime
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

client = MongoClient(config.MONGO_URI)
db = client.medtrack

users = db.users
doctors = db.doctors
patients = db.patients
appointments = db.appointments
diagnosis = db.diagnosis
notifications = db.notifications


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == "POST":

        role = request.form["role"]

        user = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"],
            "phone": request.form["phone"],
            "role": role
        }

        uid = users.insert_one(user).inserted_id

        if role == "doctor":

            doctors.insert_one({
                "user_id": uid,
                "specialization": request.form["specialization"],
                "experience": request.form["experience"]
            })

        if role == "patient":

            patients.insert_one({
                "user_id": uid,
                "age": request.form["age"],
                "medical_history": ""
            })

        return redirect("/")

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():

    email = request.form["email"]
    password = request.form["password"]

    user = users.find_one({
        "email": email,
        "password": password
    })

    if user:

        session["user"] = user["name"]
        session["id"] = str(user["_id"])
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect("/admin")

        if user["role"] == "doctor":
            return redirect("/doctor")

        if user["role"] == "patient":
            return redirect("/patient")

    return "Invalid Login"


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():

    all_users = users.find()

    return render_template(
        "admin_dashboard.html",
        users=all_users
    )


# ---------------- PATIENT DASHBOARD ----------------
@app.route('/patient')
def patient():

    myappointments = appointments.find({
        "patient_id": session["id"]
    })

    return render_template(
        "patient_dashboard.html",
        appointments=myappointments
    )


# ---------------- DOCTOR DASHBOARD ----------------
@app.route('/doctor')
def doctor():

    myappointments = appointments.find({
        "doctor_id": session["id"]
    })

    return render_template(
        "doctor_dashboard.html",
        appointments=myappointments
    )


# ---------------- BOOK APPOINTMENT ----------------
@app.route('/book', methods=['GET','POST'])
def book():

    if request.method == "POST":

        data = {
            "patient_id": session["id"],
            "doctor_id": request.form["doctor"],
            "date": request.form["date"],
            "time": request.form["time"],
            "status": "Pending"
        }

        appointments.insert_one(data)

        notifications.insert_one({
            "user_id": request.form["doctor"],
            "message": "New Appointment Booked",
            "timestamp": datetime.now()
        })

        return redirect("/patient")

    all_doctors = doctors.find()

    return render_template(
        "book_appointment.html",
        doctors=all_doctors
    )


# ---------------- ADD DIAGNOSIS ----------------
@app.route('/add_diagnosis/<id>', methods=["POST"])
def add_diagnosis(id):

    report = request.form["report"]

    diagnosis.insert_one({

        "appointment_id": id,
        "doctor_id": session["id"],
        "patient_id": request.form["patient"],
        "report": report,
        "date": datetime.now()
    })

    return redirect("/doctor")


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)