from flask import Flask, render_template, request, redirect, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
import json
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and SocketIO
db = SQLAlchemy(app)
socketio = SocketIO(app)

# OpenAI API Key (Stored in environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

# Sample lessons with descriptions
LESSONS = {
    "Math Basics": "Algebra, equations, arithmetic",
    "Advanced Math": "Calculus, integrals, derivatives",
    "Python Basics": "Variables, loops, functions",
    "Data Science": "Machine learning, AI, statistics",
    "Web Development": "HTML, CSS, JavaScript, Flask",
    "Blockchain": "Ethereum, smart contracts, Solidity"
}

# AI-based Recommendation Function
def recommend_lessons(completed_lessons):
    if not completed_lessons:
        return list(LESSONS.keys())[:3]  # Return first 3 lessons if no history

    all_lessons = list(LESSONS.keys())
    descriptions = list(LESSONS.values())

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    last_lesson = completed_lessons[-1]
    if last_lesson not in LESSONS:
        return list(LESSONS.keys())[:3]

    last_lesson_index = all_lessons.index(last_lesson)
    similarity_scores = cosine_similarity(tfidf_matrix[last_lesson_index], tfidf_matrix)

    sorted_indices = similarity_scores.argsort()[0][::-1]
    return [all_lessons[i] for i in sorted_indices if all_lessons[i] not in completed_lessons][:3]

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    progress = db.Column(db.Text, default='[]')  # Stores completed lessons in JSON format

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_progress(self):
        return json.loads(self.progress) if self.progress else []

    def update_progress(self, lesson):
        progress = self.get_progress()
        if lesson not in progress:
            progress.append(lesson)
            self.progress = json.dumps(progress)
            db.session.commit()

# Routes
@app.route('/')
def home():
    return redirect('/dashboard') if 'user_id' in session else render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect('/dashboard')
        flash("Invalid username or password!", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        if User.query.filter_by(username=username).first():
            flash("User already exists!", "warning")
            return redirect('/register')
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return redirect('/login')

    completed_lessons = user.get_progress()
    recommendations = recommend_lessons(completed_lessons)
    
    return render_template('dashboard.html', user=user.username, progress=completed_lessons, recommendations=recommendations)

@app.route('/complete_lesson', methods=['POST'])
def complete_lesson():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 401

    data = request.get_json()
    lesson = data.get('lesson')

    if lesson and lesson in LESSONS:
        user.update_progress(lesson)
        return jsonify({"message": f"Lesson '{lesson}' marked as completed!", "progress": user.get_progress()})
    
    return jsonify({"error": "Invalid lesson"}), 400

@app.route('/get_recommendations')
def get_recommendations():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = User.query.get(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 401

    return jsonify({"recommendations": recommend_lessons(user.get_progress())})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "info")
    return redirect('/')

# AI Chatbot Function
def get_ai_response(user_input):
    """ Function to get response from OpenAI API """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI tutor."},
                {"role": "user", "content": user_input}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return "Error: Could not fetch AI response."

# WebSocket Event Handling
@socketio.on("message")
def handle_message(data):
    user_message = data["message"]
    bot_response = get_ai_response(user_message)
    emit("response", {"message": bot_response}, broadcast=True)

# Run the App
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures database tables are created
    socketio.run(app, debug=True)

