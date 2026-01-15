import io
from flask import *
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta

app = Flask(__name__)

DB_PATH = f"./database.db"


def drop_db():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        drop table  adc_timer_log
    ''')
    cursor.execute('''
        drop table  servo_event_log
    ''')
    cursor.execute('''
        drop table  water_event_log
    ''')
    cursor.execute('''
        drop table configuration
    ''')
    conn.commit()
    conn.close()

#inicjalizacja bazy danych
def init_db():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # cursor.execute('''
    #         drop table adc_timer_log
    #     ''')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        sensor_name TEXT NOT NULL,
        value INTEGER NOT NULL,
        date TIMESTAMP NOT NULL
    )
    """)
    #Stare czesc bazy danych
    # cursor.execute('''
    #     create table if not exists servo_event_log(
    #         time datetime,
    #         angle float
    #     )
    # ''')

    # cursor.execute('''
    #     create table if not exists water_event_log(
    #         time datetime,
    #         requested_liters float,
    #         delivered_liters float,
    #         water_level float
    #     )
    # ''')

    #konfiguracja
    # Tryb nawadniania (water_mode) TEXT– (auto/manual)
    # Procent Wiglotności (moisture_pct) INT [10-90]% *tylko dla trybu auto
    # Co ile ma być podlewany kwiat (water_time) INT [1-72] *tylko dla trybu manual
    # Ilość podawanej wody (water_mililiters)

    # Tryb obrotu (servo_mode) TEXT– (auto/manual/set)
    # Próg naświetlenia – (auto_threshold) FLOAT *tylko dla trybu auto
    # Czas obrotu (servo_time) INT [1-48] * tylko dla trybu manual
    # Kąt serva (servo_angle) INT [0-180] *tylko dla trybu set

    # Czas Log’ów (log_timer) INT [1 – 180] (sekundy)
    cursor.execute('''
        create table if not exists configuration(
            water_mode TEXT,
            moisture_pct float,
            water_time integer,
            water_mililiters float,
            servo_mode TEXT,
            auto_threshold float,
            servo_time integer,
            servo_angle integer,
            log_timer integer
            
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM configuration")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute("""
            INSERT INTO configuration (
                water_mode,
                moisture_pct,
                water_time,
                water_mililiters,
                servo_mode,
                auto_threshold,
                servo_time,
                servo_angle,
                log_timer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "auto",        # water_mode
            30.0,          # moisture_pct(%)
            5,             # water_time
            10,          # water_mililiters
            "auto",       # servo_mode
            100,            # auto_threshold
            4,            # servo_time
            45,           # servo_angle
            30             # log_timer
        ))

    conn.commit()
    conn.close()

def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sensor_logs ORDER BY date ASC
    """)
    logs = cursor.fetchall()

    return logs

def get_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sensor_name, value, date FROM sensor_logs ORDER BY date ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    foto1_x,foto1_y = [], []
    foto2_x,foto2_y = [], []
    for sensor, value, t in rows:
        t = datetime.fromisoformat(t)
        if sensor == "foto1":
            foto1_x.append(t)
            foto1_y.append(value)
        elif sensor == "foto2":
            foto2_x.append(t)
            foto2_y.append(value)

    return (foto1_x, foto1_y, foto2_x, foto2_y)

@app.route("/get-config")
def get_config():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configuration LIMIT 1")
    config = cursor.fetchone()
    conn.close()
    return config

#             0    "auto",        # water_mode
#             1     30.0,          # moisture_pct(%)
#             2     5,             # water_time
#             3     10,          # water_mililiters
#             4     "auto",       # servo_mode
#             5     100,            # auto_threshold
#             6     4,            # servo_time
#             7     45,           # servo_angle
#             8     30             # log_timer 


@app.route("/update-servo-conf", methods=['POST'])
def update_servo_conf():
    currentConfig = get_config()
    mode = request.form['mode']

    auto_threshold = None
    servo_angle = None
    servo_time = None

    if mode == "auto":
        servo_time = currentConfig[6]
        servo_angle = currentConfig[7]
        auto_threshold = float(request.form['auto-threshold'])

    elif mode == "set":
        servo_time = currentConfig[6]
        servo_angle = int(request.form['servo-angle'])
        auto_threshold = currentConfig[5]
    elif mode == "manual":
        servo_time = int(request.form['servo-timer'])
        servo_angle = currentConfig[7]
        auto_threshold = currentConfig[5]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE configuration SET
            servo_mode = ?,
            auto_threshold = ?, 
            servo_time = ?,
            servo_angle = ?
            
        """,
        (mode, auto_threshold, servo_time, servo_angle)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route("/update-water-conf", methods=['POST'])
def update_water_conf():
    currentConfig = get_config()
    mode = request.form['mode']

    moisture_pct = None
    water_time = None

    if mode == "auto":
        moisture_pct = float(request.form['moisture-pct'])
        water_time = currentConfig[2]
        water_liters = int(request.form['water-amount'])
    elif mode == "manual":
        water_time = int(request.form['timer'])
        moisture_pct = currentConfig[1]
        water_liters = int(request.form['water-amount'])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE configuration SET
            water_mode = ?,
            moisture_pct = ?,
            water_time = ?,
            water_mililiters = ?
        """,
        (mode, moisture_pct, water_time, water_liters)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))



@app.route("/update-other", methods=['POST'])
def update_other():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    log_timer = int(request.form['time'])
    cursor.execute("""
        UPDATE configuration SET
            log_timer = ?
        """,
        (log_timer,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route("/plot.png")
def plot_png():
    foto1_x, foto1_y, foto2_x, foto2_y = get_data()

    plt.figure(figsize=(10,5))
    plt.plot(foto1_x, foto1_y, label="foto1")
    plt.plot(foto2_x, foto2_y, label="foto2")

    plt.xlabel("Czas")
    plt.ylabel("Value")
    plt.title("Wartości value dla fotorezystorów foto1 i foto2")
    plt.legend()
    plt.grid(True)
    plt.margins(0)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close()

    response = make_response(buf.getvalue())
    response.mimetype = 'image/png'
    return response

@app.route("/")
def index():
    config = get_config()
    return render_template("index.html", config=config)


@app.route("/water-config")
def configWater():
    config = get_config()
    return render_template("WaterConfig.html", config=config)

@app.route("/servo-config")
def configFoto():
    config = get_config()
    return render_template("servoConfig.html", config=config)


@app.route("/charts")
def charts():
    return render_template("charts.html")

@app.route("/log")
def logs():
    logs = get_logs()
    return render_template("logs.html", logs=logs)

@app.route("/other-config")
def other():
    config = get_config()
    return render_template("other.html", config=config)


def insert_sample_data(records=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    start_time = datetime.now()

    for i in range(records):
        current_time = start_time + timedelta(minutes=i)

        value = round(random.uniform(0.0, 1.0), 3)
        value2 = round(random.uniform(0.0, 1.0), 3)


        cursor.execute(
            "INSERT INTO sensor_logs (sensor_name, value, date) VALUES (?, ?, ?)",
            ("foto1", value, current_time)
        )

        cursor.execute(
            "INSERT INTO sensor_logs (sensor_name, value, date) VALUES (?, ?, ?)",
            ("foto2", value2/2, current_time)
        )

    conn.commit()

    conn.close()


if __name__ == '__main__':
    init_db()
    insert_sample_data(50)
    app.run(debug=True)