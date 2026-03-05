from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "medtrack_secret_key"

# ==============================
# MongoDB Connection
# ==============================
client = MongoClient("mongodb://localhost:27017/")
db = client["medtrack_db"]

users = db["users"]
patients = db["patients"]


# ==============================
# HOME
# ==============================
@app.route('/')
def home():
    return render_template("login.html")


# ==============================
# REGISTER
# ==============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        user_data = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"],
            "role": request.form["role"]
        }
        users.insert_one(user_data)
        return redirect('/')
    return render_template("register.html")


# ==============================
# LOGIN
# ==============================
@app.route('/login', methods=['POST'])
def login():
    email = request.form["email"]
    password = request.form["password"]

    user = users.find_one({"email": email, "password": password})

    if user:
        session["user_id"] = str(user["_id"])
        session["name"] = user["name"]
        session["role"] = user["role"]

        # Redirect based on role
        if user["role"] == "admin":
            return redirect('/admin_dashboard')
        elif user["role"] == "doctor":
            return redirect('/doctor_dashboard')
        else:
            return redirect('/patient_dashboard')

    return "Invalid Email or Password"


# ==============================
# ADMIN DASHBOARD
# ==============================
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect('/')

    all_users = list(users.find())
    return render_template("admin_dashboard.html", users=all_users)


# ==============================
# DOCTOR DASHBOARD
# ==============================
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if session.get("role") != "doctor":
        return redirect('/')

    all_patients = list(patients.find())
    return render_template("doctor_dashboard.html", patients=all_patients)


# ==============================
# PATIENT DASHBOARD
# ==============================
@app.route('/patient_dashboard')
def patient_dashboard():
    if session.get("role") != "patient":
        return redirect('/')

    patient = patients.find_one({"user_id": session.get("user_id")})
    return render_template("patient_dashboard.html", patient=patient)


# ==============================
# ADD PATIENT (Doctor/Admin)
# ==============================
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if session.get("role") not in ["admin", "doctor"]:
        return redirect('/')

    if request.method == "POST":
        patient_data = {
            "name": request.form["name"],
            "age": request.form["age"],
            "disease": request.form["disease"],
            "user_id": session.get("user_id")
        }
        patients.insert_one(patient_data)
        return redirect('/doctor_dashboard')

    return render_template("add_patient.html")


# ==============================
# DELETE USER
# ==============================
@app.route('/delete_user/<id>')
def delete_user(id):
    if session.get("role") != "admin":
        return redirect('/')

    users.delete_one({"_id": ObjectId(id)})
    return redirect('/admin_dashboard')


# ==============================
# EDIT USER
# ==============================
@app.route('/edit_user/<id>')
def edit_user(id):
    if session.get("role") != "admin":
        return redirect('/')

    user = users.find_one({"_id": ObjectId(id)})
    return render_template("edit_user.html", user=user)


@app.route('/update_user/<id>', methods=['POST'])
def update_user(id):
    if session.get("role") != "admin":
        return redirect('/')

    users.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "name": request.form["name"],
            "email": request.form["email"],
            "role": request.form["role"]
        }}
    )

    return redirect('/admin_dashboard')


# ==============================
# LOGOUT
# ==============================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ==============================
# MAIN
# ==============================
if __name__ == '__main__':
    app.run(debug=True)