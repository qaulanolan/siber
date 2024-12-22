from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash  # B.1
from html import escape # B.2 Import fungsi escape untuk sanitasi input
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key' # B.1
db = SQLAlchemy(app)
login_manager = LoginManager(app) # B.1
login_manager.login_view = 'login' # B.1

class User(UserMixin, db.Model): # B.1 line 17-20
    id = db.Column(db.Integer, primary_key=True) 
    username = db.Column(db.String(100), unique=True, nullable=False) 
    password = db.Column(db.String(200), nullable=False) 

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

@login_manager.user_loader # B.1 (line 31-33)
def load_user(user_id): 
    return User.query.get(int(user_id)) 

@app.route('/')
@login_required # B.1
def index():
    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)

@app.route('/register', methods=['GET', 'POST']) # B.1 line 42-80
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required # B.1
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add', methods=['POST'])
@login_required # B.1
def add_student():
    # B.2 (line 86-95) Fungsi untuk memvalidasi input pengguna
    def validate_input(name, age, grade):
        if not name.isalnum() or not grade.isalpha():  # Memastikan nama alfanumerik dan grade hanya huruf
            raise ValueError("Invalid input format")  # Mengembalikan error jika input tidak valid
        if not age.isdigit() or int(age) < 0 or int(age) > 150:  # Memastikan usia valid 
            raise ValueError("Invalid age")  # Mengembalikan error jika usia tidak valid

    name = escape(request.form['name']) # Membersihkan input dari karakter HTML berbahaya untuk mencegah XSS
    age = request.form['age']
    grade = request.form['grade']
    validate_input(name, age, grade)
    # name = request.form['name']
    # age = request.form['age']
    # grade = request.form['grade']
    

    connection = sqlite3.connect('instance/students.db')
    cursor = connection.cursor()

    # RAW Query
    # B.4 (line 106-110) Menggunakan parameterisasi query untuk mencegah SQL Injection
    db.session.execute(
        text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
        {'name': name, 'age': age, 'grade': grade} # Parameter yang aman
    )
    db.session.commit() # Menyimpan perubahan ke database
    # query = f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    # cursor.execute(query)
    # connection.commit()
    connection.close()
    return redirect(url_for('index'))


@app.route('/delete/<string:id>') 
@login_required # B.1
def delete_student(id):
    # B.4 line 122-126
    db.session.execute( 
        text("DELETE FROM student WHERE id=:id"),
        {'id': id}  # Parameter aman
    )
    db.session.commit()  # Menyimpan perubahan ke database
    # db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    # db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required # B.1
def edit_student(id):
    if request.method == 'POST':
        # B.2 (line 137-146) Fungsi untuk memvalidasi input pengguna
        def validate_input(name, age, grade):
            if not name.isalnum() or not grade.isalpha():  # Memastikan nama alfanumerik dan grade hanya huruf
                raise ValueError("Invalid input format")  # Mengembalikan error jika input tidak valid
            if not age.isdigit() or int(age) < 0 or int(age) > 150:  # Memastikan usia valid 
                raise ValueError("Invalid age")  # Mengembalikan error jika usia tidak valid
    
        name = escape(request.form['name']) # Membersihkan input dari karakter HTML berbahaya untuk mencegah XSS
        age = request.form['age']
        grade = request.form['grade']
        validate_input(name, age, grade)
        # name = request.form['name']
        # age = request.form['age']
        # grade = request.form['grade']
        
        # RAW Query
        # B.4 (line 153-157) Menggunakan parameterisasi query untuk mencegah SQL Injection
        db.session.execute(
            text("UPDATE student SET name=:name, age=:age, grade=:grade WHERE id=:id"),
            {'name': name, 'age': age, 'grade': grade, 'id': id}  # Parameter yang aman
        )
        db.session.commit()  # Menyimpan perubahan ke database
        # db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        # db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query
        student = db.session.execute(text(f"SELECT * FROM student WHERE id={id}")).fetchone()
        return render_template('edit.html', student=student)

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
