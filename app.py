from flask import Flask, render_template, request
import cv2
import os
from deepface import DeepFace
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Directory containing known face images
KNOWN_FACES_DIR = "known_faces"

# MySQL configuration
db_config = {
    "host": "localhost",
    "user": "root",  # Update if your MySQL username is different
    "password": "",  # Update with your MySQL password if set
    "database": "visitor_db"
}

# Home route - handles face recognition
@app.route('/')
def home():
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        return "Unable to access the camera."

    ret, frame = cam.read()
    cam.release()

    if not ret:
        return "Failed to capture image from the camera."

    img_path = "captured.jpg"
    cv2.imwrite(img_path, frame)

    # Compare captured image with known faces
    for filename in os.listdir(KNOWN_FACES_DIR):
        known_img_path = os.path.join(KNOWN_FACES_DIR, filename)
        try:
            result = DeepFace.verify(img1_path=img_path, img2_path=known_img_path, enforce_detection=False)
            if result["verified"]:
                name = os.path.splitext(filename)[0]
                print(f"Match found: {name}")
                return render_template("entry_short.html", name=name)
        except Exception as e:
            print(f"Error comparing with {filename}: {e}")
            continue

    print("No match found.")
    return render_template("entry_full.html")

# Route for recognized visitors (short entry form)
@app.route('/entry_short', methods=['POST'])
def entry_short():
    name = request.form['name']
    purpose = request.form['purpose']
    whom_to_meet = request.form['whom_to_meet']
    entry_time = datetime.now()

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO visitors (name, purpose, whom_to_meet, status, entry_time) VALUES (%s, %s, %s, %s, %s)",
        (name, purpose, whom_to_meet, "IN", entry_time)
    )
    conn.commit()
    conn.close()

    return f"Welcome back, {name}. Your entry has been recorded."

# Route for new visitors (full entry form)
@app.route('/entry_full', methods=['POST'])
def entry_full():
    name = request.form['name']
    contact = request.form['contact']
    purpose = request.form['purpose']
    whom_to_meet = request.form['whom_to_meet']
    entry_time = datetime.now()

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO visitors (name, contact, purpose, whom_to_meet, status, entry_time) VALUES (%s, %s, %s, %s, %s, %s)",
        (name, contact, purpose, whom_to_meet, "IN", entry_time)
    )
    conn.commit()
    conn.close()

    return f"Hello {name}, your entry has been recorded."

# Route to handle visitor exit
@app.route('/exit', methods=['GET', 'POST'])
def exit():
    if request.method == 'POST':
        name = request.form['name']
        exit_time = datetime.now()

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE visitors SET status = 'OUT', exit_time = %s WHERE name = %s AND status = 'IN'",
            (exit_time, name)
        )
        conn.commit()
        conn.close()

        return f"{name}, your exit has been recorded."
    return render_template("exit.html")

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)
