from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Ma'lumotlar bazasini yaratish
def init_db():
    os.makedirs('database', exist_ok=True)
    os.makedirs('static/images/projects', exist_ok=True)
    os.makedirs('static/images/team', exist_ok=True)
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Loyihalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Arizalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            business_type TEXT NOT NULL,
            phone TEXT NOT NULL,
            budget TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Jamoa a'zolari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            image_path TEXT,
            description TEXT
        )
    ''')
    
    # Qo'shimcha: demo admin foydalanuvchisini yaratish (username: admin, password: admin123)
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                       ('admin', 'admin123', 1))
    
    conn.commit()
    conn.close()

init_db()

# Har bir sahifadan oldin login tekshirish
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint and request.endpoint not in allowed_routes and not session.get('user_id'):
        return redirect(url_for('login'))

# Telegramga xabar yuborish
def send_telegram_message(message):
    try:
        for i in app.config['TELEGRAM_CHAT_ID'].split(","):
            url = f"https://api.telegram.org/bot{app.config['TELEGRAM_BOT_TOKEN']}/sendMessage"
            
            data = {
                'chat_id': i.strip(),
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=10)
            
        return response.status_code == 200
    
    except Exception as e:
        print(f"Telegram xatosi: {e}")
        return False

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM team_members')
    team_members = cursor.fetchall()
    conn.close()
    return render_template('about.html', team_members=team_members)

@app.route('/projects')
def projects():
    category = request.args.get('category', '')
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    
    if category:
        cursor.execute('SELECT * FROM projects WHERE category = ?', (category,))
    else:
        cursor.execute('SELECT * FROM projects')
    
    projects = cursor.fetchall()
    conn.close()
    return render_template('projects.html', projects=projects, current_category=category)

@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        full_name = request.form['full_name']
        business_type = request.form['business_type']
        phone = request.form['phone']
        budget = request.form['budget']
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO applications (full_name, business_type, phone, budget)
            VALUES (?, ?, ?, ?)
        ''', (full_name, business_type, phone, budget))
        conn.commit()
        conn.close()
        
        # Telegramga xabar
        message = f"""
🎯 Yangi Ariza

👤 Ism: {full_name}
🏢 Biznes: {business_type}
📞 Telefon: {phone}
💰 Byudjet: {budget}
        """
        send_telegram_message(message)
        
        return jsonify({'success': True, 'message': '✅ Arizangiz yuborildi'})
    
    return render_template('form.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Agar allaqachon login qilgan bo'lsa, homega yo'naltirish
    if session.get('user_id'):
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = bool(user[3])  # Convert to boolean
            flash('Muvaffaqiyatli kirildi!', 'success')
            # Agar admin bo'lsa, admin panelga yo'naltirish
            if session['is_admin']:
                return redirect(url_for('admin_panel'))
            return redirect(url_for('home'))
        else:
            flash('Login yoki parol xato!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Roʻyxatdan muvaffaqiyatli oʻtdingiz!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Bu foydalanuvchi nomi band!', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        flash('Admin huquqi yoʻq!', 'error')
        return redirect(url_for('home'))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    
    # Asosiy statistika
    cursor.execute('SELECT COUNT(*) FROM applications WHERE date(created_at) >= date("now", "-30 days")')
    monthly_applications = cursor.fetchone()[0]
    
    # Bugungi arizalar
    cursor.execute('SELECT COUNT(*) FROM applications WHERE date(created_at) = date("now")')
    today_applications = cursor.fetchone()[0]
    
    # Haftalik arizalar
    cursor.execute('SELECT COUNT(*) FROM applications WHERE date(created_at) >= date("now", "-7 days")')
    weekly_applications = cursor.fetchone()[0]
    
    # Loyihalar statistikasi
    cursor.execute('SELECT COUNT(*) FROM projects WHERE category = "SMM"')
    smm_projects = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM projects WHERE category = "Target"')
    target_projects = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM projects WHERE category = "Branding"')
    branding_projects = cursor.fetchone()[0]
    
    # Jami loyihalar
    cursor.execute('SELECT COUNT(*) FROM projects')
    total_projects = cursor.fetchone()[0]
    
    # Jami arizalar
    cursor.execute('SELECT COUNT(*) FROM applications')
    total_applications = cursor.fetchone()[0]
    
    # So'nggi arizalar
    cursor.execute('SELECT * FROM applications ORDER BY created_at DESC LIMIT 5')
    recent_applications = cursor.fetchall()
    
    cursor.execute('SELECT * FROM applications ORDER BY created_at DESC')
    applications = cursor.fetchall()
    
    cursor.execute('SELECT * FROM projects')
    projects = cursor.fetchall()
    
    cursor.execute('SELECT * FROM team_members')
    team_members = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', 
                         monthly_applications=monthly_applications,
                         today_applications=today_applications,
                         weekly_applications=weekly_applications,
                         total_projects=total_projects,
                         total_applications=total_applications,
                         smm_projects=smm_projects,
                         target_projects=target_projects,
                         branding_projects=branding_projects,
                         recent_applications=recent_applications,
                         applications=applications,
                         projects=projects,
                         team_members=team_members)

@app.route('/admin/add_project', methods=['POST'])
def add_project():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    title = request.form['title']
    description = request.form['description']
    category = request.form['category']
    image_file = request.files.get('image')
    
    image_path = None
    if image_file and image_file.filename:
        filename = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_file.filename}"
        image_path = filename
        image_file.save(os.path.join('static/images/projects', filename))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (title, description, category, image_path)
        VALUES (?, ?, ?, ?)
    ''', (title, description, category, image_path))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/delete_project/<int:project_id>')
def delete_project(project_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    
    flash('Loyiha muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/add_team_member', methods=['POST'])
def add_team_member():
    if not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    name = request.form['name']
    position = request.form['position']
    description = request.form['description']
    image_file = request.files.get('image')
    
    image_path = None
    if image_file and image_file.filename:
        filename = f"team_{name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = filename
        image_file.save(os.path.join('static/images/team', filename))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO team_members (name, position, description, image_path)
        VALUES (?, ?, ?, ?)
    ''', (name, position, description, image_path))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/delete_team_member/<int:member_id>')
def delete_team_member(member_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    cursor = conn.cursor()
    cursor.execute('DELETE FROM team_members WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()
    
    flash('Jamoa a\'zosi muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Siz tizimdan chiqdingiz!', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)