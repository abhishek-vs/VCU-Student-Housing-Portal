from flask import Flask, request, render_template, redirect, url_for, session, flash
import psycopg2
import config
from models import db

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'secret123'

# Set config first
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:18628@VSAbhi@localhost:5432/vcu_student_housing_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db
db.init_app(app)


# Connect to PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=config.DB_HOST,
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
        port=config.DB_PORT
    )
    return conn

# ---------------------
# Home Route
# ---------------------
@app.route('/')
def home():
    return render_template('home.html')

# ---------------------
# Register Route
# ---------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        # 🚨 Check if email already exists
        cur.execute('SELECT * FROM Student WHERE email = %s', (email,))
        existing_student = cur.fetchone()

        if existing_student:
            cur.close()
            conn.close()
            flash("Email already registered. Please use a different email.", "danger")
            return redirect(url_for('register'))


        # 🚀 If not existing, insert new student
        cur.execute('INSERT INTO Student (name, email, phone, password) VALUES (%s, %s, %s, %s)',
                    (name, email, phone, password))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('register_success'))
    return render_template('register.html')


# ---------------------
# Login Route
# ---------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM Student WHERE email = %s AND password = %s', (email, password))
        student = cur.fetchone()
        cur.close()
        conn.close()

        if student:
            session['student_id'] = student[0]
            session['student_name'] = student[1]  # Save name in session too!
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

# ---------------------
# Search Available Rooms Route
# ---------------------
@app.route('/search_rooms')
def search_rooms():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT r.room_number, h.address, h.monthly_rent, r.room_id
        FROM Room r
        JOIN Housing h ON r.housing_id = h.housing_id
        WHERE r.available = TRUE
    ''')
    all_rooms = cur.fetchall()
    cur.close()
    conn.close()

    # Pagination logic
    page = int(request.args.get('page', 1))
    per_page = 6
    start = (page - 1) * per_page
    end = start + per_page
    rooms = all_rooms[start:end]

    total_pages = (len(all_rooms) + per_page - 1) // per_page

    return render_template('search.html', rooms=rooms, page=page, total_pages=total_pages)


# ---------------------
# Book Room Route
# ---------------------
@app.route('/book_room/<int:room_id>')
def book_room(room_id):
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Insert into Booking table
    cur.execute('''
        INSERT INTO Booking (student_id, room_id, booking_date, payment_status)
        VALUES (%s, %s, CURRENT_DATE, 'Pending')
    ''', (session['student_id'], room_id))

    # Update Room table to mark as unavailable
    cur.execute('''
        UPDATE Room
        SET available = FALSE
        WHERE room_id = %s
    ''', (room_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('booking_success'))


# ---------------------
# Find Matches Route
# ---------------------
@app.route('/find_matches')
def find_matches():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    student_id = session['student_id']

    conn = get_db_connection()
    cur = conn.cursor()

    # Get logged-in student's preferences
    cur.execute('SELECT * FROM Preferences WHERE student_id = %s', (student_id,))
    my_preferences = cur.fetchone()

    if not my_preferences:
        flash("Please set your preferences first.", "warning")
        return redirect(url_for('preferences'))

    my_budget_min = my_preferences[2]
    my_budget_max = my_preferences[3]
    my_cleanliness = my_preferences[4]
    my_smoking = my_preferences[5]
    my_sleep = my_preferences[6]

    # Get other students' preferences
    cur.execute('''
        SELECT p.student_id, s.name, p.budget_min, p.budget_max, p.cleanliness_level, p.smoking_preference, p.sleep_schedule
        FROM Preferences p
        JOIN Student s ON p.student_id = s.student_id
        WHERE p.student_id != %s
    ''', (student_id,))
    other_students = cur.fetchall()

    matches = []

    for other in other_students:
        other_id, other_name, budget_min, budget_max, cleanliness, smoking, sleep = other

        # Compatibility calculations
        budget_score = 100 if (my_budget_min <= budget_max and my_budget_max >= budget_min) else 50
        cleanliness_score = max(0, 100 - (abs(my_cleanliness - cleanliness) * 20))  # lose 20% per point difference
        smoking_score = 100 if my_smoking == smoking else 0
        sleep_score = 100 if my_sleep == sleep else 0

        # Weighted average score
        final_score = (0.4 * budget_score) + (0.3 * cleanliness_score) + (0.2 * smoking_score) + (0.1 * sleep_score)
        final_score = round(final_score, 2)

        matches.append((other_name, final_score))

    # Sort matches by score descending
    matches.sort(key=lambda x: x[1], reverse=True)

    cur.close()
    conn.close()

    return render_template('matches.html', matches=matches)


# ---------------------
# Register Success Route
# ---------------------
@app.route('/register_success')
def register_success():
    return render_template('register_success.html')


# ---------------------
# Login Success Route
# ---------------------
@app.route('/login_success')
def login_success():
    return render_template('login_success.html')


# ---------------------
# Booking Success Route
# ---------------------
@app.route('/booking_success')
def booking_success():
    return render_template('booking_success.html')

# ---------------------
# Preferences Route
# ---------------------
@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        budget_min = request.form['budget_min']
        budget_max = request.form['budget_max']
        cleanliness_level = request.form['cleanliness_level']
        smoking_preference = request.form['smoking_preference']
        sleep_schedule = request.form['sleep_schedule']

        # Check if preferences exist
        cur.execute('SELECT * FROM Preferences WHERE student_id = %s', (session['student_id'],))
        existing_preferences = cur.fetchone()

        if existing_preferences:
            # Update
            cur.execute('''
                UPDATE Preferences
                SET budget_min = %s,
                    budget_max = %s,
                    cleanliness_level = %s,
                    smoking_preference = %s,
                    sleep_schedule = %s
                WHERE student_id = %s
            ''', (budget_min, budget_max, cleanliness_level, smoking_preference, sleep_schedule, session['student_id']))
        else:
            # Insert
            cur.execute('''
                INSERT INTO Preferences (student_id, budget_min, budget_max, cleanliness_level, smoking_preference, sleep_schedule)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (session['student_id'], budget_min, budget_max, cleanliness_level, smoking_preference, sleep_schedule))

        conn.commit()
        cur.close()
        conn.close()

        flash('Preferences saved successfully!', 'success')
        return redirect(url_for('dashboard'))

    # For GET request (load current preferences)
    cur.execute('SELECT * FROM Preferences WHERE student_id = %s', (session['student_id'],))
    pref_data = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('preferences.html', pref=pref_data)



# ---------------------
# Dashboard Route
# ---------------------
@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    student_id = session['student_id']
    student_name = session['student_name']

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch booked rooms
    cur.execute('''
        SELECT r.room_number, h.address, h.monthly_rent
        FROM Booking b
        JOIN Room r ON b.room_id = r.room_id
        JOIN Housing h ON r.housing_id = h.housing_id
        WHERE b.student_id = %s
    ''', (student_id,))
    bookings = cur.fetchall()

    # Fetch roommate matches
    cur.execute('''
        SELECT s2.name, rm.compatibility_score
        FROM Roommate_Match rm
        JOIN Student s1 ON rm.student1_id = s1.student_id
        JOIN Student s2 ON rm.student2_id = s2.student_id
        WHERE s1.student_id = %s
    ''', (student_id,))
    matches = cur.fetchall()

    cur.close()
    conn.close()

    return render_template('dashboard.html', student_name=student_name, bookings=bookings, matches=matches)


# ---------------------
# Run the app
# ---------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))


# ---------------------
# Run the app
# ---------------------
if __name__ == '__main__':
    app.run(debug=True)
