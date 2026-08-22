from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/create-trip")
def create_trip():
    return render_template("create_trip.html")

@app.route("/trip-sections")
def trip_sections():
    return render_template("trip_sections.html")

@app.route("/my-trips")
def my_trips():
    return render_template("my_trips.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/itinerary")
def itinerary():
    return render_template("itinerary.html")

@app.route("/community")
def community():
    return render_template("community.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)
