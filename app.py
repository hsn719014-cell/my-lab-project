from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# مفتاح سري لتشفير بيانات الجلسة وحفظ اسم الطالب
app.secret_key = 'MAAQAL_ULTIMATE_LAB_2026_KEY'
# الجلسة تبقى فعالة لمدة شهر كامل
app.permanent_session_lifetime = timedelta(days=30)

# --- إعداد قاعدة البيانات لحفظ بيانات الطلاب الـ 1000 ---
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            login_time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- البيانات الكاملة للفطريات والاختبارات (Logic) ---
# ملاحظة: تم وضع الأجوبة هنا ليتم مطابقتها في الواجهة الثالثة
FUNGI_DATA = {
    "superficial": {
        "T": {"name": "Tinea", "correct": [5, 4, 3, 3, 3]}, # الأرقام تمثل تسلسل الخيارات الصحيحة
        "BP": {"name": "Black Piedra", "correct": [4, 3, 2, 3, 3]}
    },
    "subcutaneous": {
        "M": {"name": "Mycetoma", "correct": [1, 3, 3, 3, 3]},
        "S": {"name": "Sporotrichosis", "correct": [1, 3, 1, 3, 3]}
    },
    "systemic": {
        "P": {"name": "Paracoccidioidomycosis", "correct": [5, 3, 3, 3, 4]},
        "B": {"name": "Blastomycosis", "correct": [5, 3, 2, 4, 4]},
        "C": {"name": "Cryptococcosis", "correct": [3, 1, 2, 1, 4]}
    },
    "opportunistic": {
        "A": {"name": "Aspergillosis", "correct": [4, 4, 3, 3, 4]}
    }
}

# --- المسارات (Routes) ---

@app.route('/')
def index():
    # استرجاع البيانات المحفوظة في المتصفح لملء الحقول تلقائياً
    saved_name = session.get('student_name', "")
    saved_email = session.get('email', "")
    saved_password = session.get('password', "")
    return render_template('login.html', name=saved_name, email=saved_email, password=saved_password, error="")

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('student_name')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # التحقق من البيانات (كلمة المرور الموحدة)
    if not email.lower().endswith("@almaaqal.edu.iq"):
        return render_template('login.html', error="البريد يجب أن ينتهي بـ @almaaqal.edu.iq", name=name, email=email, password=password)
    
    if password != "MLT_2026":
        return render_template('login.html', error="خطأ في كلمة المرور!", name=name, email=email, password=password)
    
    # حفظ البيانات في المتصفح (Session) ليتذكر الطالب عند الرجوع
    session.permanent = True
    session['student_name'] = name
    session['email'] = email
    session['password'] = password

    # حفظ القيد في قاعدة البيانات
    try:
        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO users (name, email, password, login_time) VALUES (?, ?, ?, ?)', 
                       (name, email, password, now))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # التأكد من أن الطالب مسجل دخول
    if 'student_name' not in session:
        return redirect(url_for('index'))
    
    student_name = session.get('student_name')
    return render_template('dashboard.html', student_name=student_name)

@app.route('/lab/<category>/<fungus_id>')
def lab_test(category, fungus_id):
    if 'student_name' not in session:
        return redirect(url_for('index'))
    
    student_name = session.get('student_name')
    # التحقق من وجود الفطر في البيانات
    if category in FUNGI_DATA and fungus_id in FUNGI_DATA[category]:
        fungus_info = FUNGI_DATA[category][fungus_id]
        return render_template('lab.html', 
                               category=category, 
                               fungus_id=fungus_id, 
                               student_name=student_name,
                               correct_answers=fungus_info['correct'])
    
    return redirect(url_for('dashboard'))

# مسار خاص لجلب بيانات الحالة مجهولة للفحص بالـ JavaScript
@app.route('/get_case_data/<category>/<fungus_id>')
def get_case_data(category, fungus_id):
    # هنا يتم إرجاع النصوص التي ستحولها الواجهة لصور
    # هذا المسار يساعد الواجهة الثالثة على معرفة ماذا تعرض
    return jsonify({"status": "success", "id": fungus_id})

# --- إضافة الواجهات الجديدة (Biosafety & Fungi Info) ---

@app.route('/biosafety')
def biosafety():
    if 'student_name' not in session:
        return redirect(url_for('index'))
    return render_template('biosafety.html')

@app.route('/info_fungi')
def info_fungi():
    if 'student_name' not in session:
        return redirect(url_for('index'))
    return render_template('info_fungi.html')

if __name__ == '__main__':
    # تشغيل السيرفر على الشبكة المحلية
    app.run(host='0.0.0.0', port=5000, debug=True)