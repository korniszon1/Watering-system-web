import io
import math
from flask import *
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import random
from datetime import datetime, timedelta
import numpy as np
from main import Donica

app = Flask(__name__)

DB_PATH = f"./database.db"

# ===============================
# Konfiguracja Strony
# ===============================
MIN_WATER = 5 #procent przy którym jest pokazywany komunikat o wodzie


# ===============================
# Konfiguracja Bazy danych
# ===============================

#usuwanie bazy danych
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
    cursor.execute('''
        drop table zone_logs
    ''')
    cursor.execute('''
        drop table sensor_logs
    ''')
    conn.commit()
    conn.close()

@app.route("/delete-data", methods=['POST'])
def drop_data():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        delete from  servo_logs
    ''')
    cursor.execute('''
        delete from  water_logs
    ''')
    cursor.execute('''
        delete from zone_logs
    ''')
    cursor.execute('''
        delete from sensor_logs
    ''')
    conn.commit()
    conn.close()
    init_db()
    return redirect(url_for('index'))


@app.route("/delete-all", methods=['POST'])
def drop_all():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        delete from  servo_logs
    ''')
    cursor.execute('''
        delete from  water_logs
    ''')
    cursor.execute('''
        delete from configuration
    ''')
    cursor.execute('''
        delete from zone_logs
    ''')
    cursor.execute('''
        delete from sensor_logs
    ''')
    conn.commit()
    conn.close()
    init_db()
    return redirect(url_for('index'))

#inicjalizacja bazy danych
def init_db():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #logi sensorow
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_logs (
        sensor_name TEXT NOT NULL,
        value INTEGER NOT NULL,
        date TIMESTAMP NOT NULL
    )
    """)
    cursor.execute("SELECT COUNT(*) FROM sensor_logs")
    count = cursor.fetchone()[0]


    #init log
    if count == 0:
        print("INIT")
        for name in ["moisture","water","foto1", "foto2"]:
            cursor.execute("""
                INSERT INTO sensor_logs (
                    sensor_name,
                    value,
                    date
                ) VALUES (?, ?, ?)
            """, (
                name,
                10 if name == "water" else 0,
                datetime.now()
            ))

    #////////////////////////
    # Logi eventowe
    #////////////////////////
    #logi serwa
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servo_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        old_angle INTEGER,
        new_angle INTEGER,
        mode TEXT,
        date DATETIME
    )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
           mililiters INTEGER,
           date DATETIME
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM water_logs")
    count = cursor.fetchone()[0]


    #init log
    if count == 0:
        cursor.execute("""
            INSERT INTO water_logs (
                mililiters,
                date
            ) VALUES (?, ?)
        """, (
            0,
            datetime.now()
        ))


    #////////////////////////

    #logi stref
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS zone_logs (
        zone_id INT NOT NULL,
        value FLOAT NOT NULL
    )
    """)
    cursor.execute("SELECT COUNT(*) FROM zone_logs")
    count = cursor.fetchone()[0]


    #init config
    if count == 0:
        for i in range(6):
            value = 1
            cursor.execute("""
                INSERT INTO zone_logs (
                    zone_id,
                    value
                ) VALUES (?, ?)
            """, (
                i,
                value
            ))

    #Konfiguracja
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
            15,          # water_mililiters
            "auto",       # servo_mode
            800,            # auto_threshold
            4,            # servo_time
            0,           # servo_angle
            10             # log_timer
        ))

    conn.commit()
    conn.close()

# ===============================
# Gettery danych
# ===============================

def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT sensor_name, value,
               strftime('%Y-%m-%d %H:%M:%S', date) as formatted_date
        FROM sensor_logs
        ORDER BY date DESC
    """)
    logs = cursor.fetchall()

    return logs

def sortByDate(e):
    return e[0]

def get_events():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
               "water", strftime('%Y-%m-%d %H:%M:%S', date) as formatted_date,
                   mililiters
        FROM water_logs
        ORDER BY date DESC
    """)
    water_logs = cursor.fetchall()
    cursor.execute("""
            SELECT "servo", strftime('%Y-%m-%d %H:%M:%S', date) as formatted_date, old_angle, new_angle, mode
            FROM servo_logs
            ORDER BY date DESC
        """)
    servo_logs = cursor.fetchall()
    logs = water_logs+servo_logs
    logs.sort(reverse=True,key=sortByDate)
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

def get_basic_info():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT sensor_name, value, date
                    FROM sensor_logs
                    WHERE (sensor_name, date) IN (
                        SELECT sensor_name, MAX(date)
                        FROM sensor_logs
                        WHERE sensor_name IN ('moisture', 'foto1', 'foto2', 'water')
                        GROUP BY sensor_name
                    ) 
                    ORDER BY sensor_name                
                   """)
    info = cursor.fetchall()
    conn.close()
    return info

def get_zone_info():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT zone_id, value from zone_logs DESC LIMIT 6      
                   """)
    info = cursor.fetchall()
    conn.close()
    return info

def get_moisture():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
                    SELECT value, date from sensor_logs where sensor_name = 'moisture' order by date DESC               
                   """)
    moisture = cursor.fetchall()
    conn.close()
    x,y = [], []
    for value, t in moisture:
        t = datetime.fromisoformat(t)
        x.append(t)
        y.append(value)
    return (x,y)

def get_last_servo_log():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, old_angle, new_angle, mode, date
        FROM servo_logs
        ORDER BY date DESC
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    conn.close()
    return row

@app.route("/get-config")
def get_config():
    conn =sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM configuration LIMIT 1")
    config = cursor.fetchone()
    conn.close()
    return config

# ===============================
# Struktura bazy danych
# ===============================

#             0    "auto",        # water_mode
#             1     30.0,          # moisture_pct(%)
#             2     5,             # water_time
#             3     10,          # water_mililiters
#             4     "auto",       # servo_mode
#             5     100,            # auto_threshold
#             6     4,            # servo_time
#             7     45,           # servo_angle
#             8     30             # log_timer 


# ===============================
# Aktualizowanie Konfiguracji
# ===============================

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

# =======================================================
# Obsługa wykresów i generacja obrazów
# =======================================================

@app.route("/foto.png")
def plot_foto():
    plt.clf()
    plt.close('all')
    foto1_x, foto1_y, foto2_x, foto2_y = get_data()

    chart_color = ["#0aebfc", "#fc930a"]
    text_color = "#bfcae5"
    border_color = "#bfcae5f2"

    fig, ax = plt.subplots(figsize=(15,7), facecolor='none')
    ax.plot(foto1_x, foto1_y, label="foto1", color = chart_color[0])
    ax.plot(foto2_x, foto2_y, label="foto2", color = chart_color[1])

    ax.set_xlabel("Czas" , color=text_color)
    ax.set_ylabel("Value", color=text_color)
    
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    
    legend = ax.legend()
    ax.get_legend().set_title("Nazwa fotorezystora")
    # Tło legendy
    legend.get_frame().set_facecolor("#092975")   # kolor tła legendy
    legend.get_frame().set_edgecolor("#bfcae5")   # kolor obramówki legendy
    for text in legend.get_texts():
        text.set_color(text_color)
    legend.get_frame().set_linewidth(1.5) 
    legend.get_title().set_color(text_color)

    for spine in ax.spines.values():
        spine.set_color("#bfcae5")

    ax.grid(True, color=border_color)
    ax.set_facecolor('none')
    ax.margins(0)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    plt.close(fig)

    response = make_response(buf.getvalue())
    response.mimetype = 'image/png'

    return response


# funkcja do testowania zmian w wykresach
def change_zone():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    ran = round(random.uniform(0.0, 1000.0), 1)
    cursor.execute("""
        UPDATE zone_logs set value = ? where zone_id = 1
            
        """,
        (ran,)
    )
    conn.commit()
    conn.close()

@app.route("/zone.png")
def plot_zone():
    plt.clf()
    plt.close('all')
    zone = get_zone_info()
    config = get_config()
    chart_color = ["#092975", "#15337A"]
    text_color = "#bfcae5"
    border_color = "#bfcae5f2"

    values = []
    print(zone)
    for z in zone:
        if z[1] <  config[5]:
            values.append(z[1] / config[5])
        else:
            values.append(1)
    
    n = len(values)
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})

    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.set_yticklabels([])

    rotation = math.radians(get_last_servo_log()[2])
    print(f"ROTACJA - > {rotation}")
    ax.set_theta_offset(-rotation)

    ax.set_xticks([])

    for i, v in enumerate(values):
        theta_start = 2*np.pi * i / n
        theta_end   = 2*np.pi * (i+1) / n
        theta_mid = (theta_start + theta_end) / 2

        theta_sector = np.linspace(theta_start, theta_end, 50)
        r_sector = np.linspace(0, v, 50)
        T, R = np.meshgrid(theta_sector, r_sector)
        ax.pcolormesh(T, R, np.zeros_like(T), shading='auto', color= chart_color[i%2], alpha=0.6)

        percent_text = f"{round(v*100)}%"
        ax.text(theta_mid, 1/2, percent_text,ha='center', va='center', fontsize=10, color=text_color,fontweight='bold')

        ax.text(theta_mid, 1.05, f"Strefa {i+1}",
                ha='center', va='center',
                fontsize=10, color=text_color)

    for i in range(n):
        theta = 2*np.pi * i / n
        ax.plot([theta, theta], [0, 1], color = border_color, linewidth= 0.5)

    theta_circle = np.linspace(0, 2*np.pi, 200)
    ax.plot(theta_circle, np.ones_like(theta_circle), color=border_color)

    ax.set_ylim(0, 1)
    plt.grid(color="#32487A")

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    fig.clear()
    plt.close(fig)
    
    response = make_response(buf.getvalue())
    response.mimetype = 'image/png'

    return response

@app.route("/moisture.png")
def plot_moisture():
    plt.clf()
    plt.close('all')
    x,y = get_moisture()

    chart_color = ["#0aebfc", "#fc930a"]
    text_color = "#bfcae5"
    border_color = "#bfcae5f2"

    fig, ax = plt.subplots(figsize=(15,7), facecolor='none')
    ax.plot(x, y, label="Wilgotności", color = chart_color[0])

    ax.set_xlabel("Czas" , color=text_color)
    ax.set_ylabel("Value", color=text_color)
    
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    ax.set_ylim([0, 100])
    legend = ax.legend()
    ax.get_legend().set_title("Pomiar czujnika")

    legend.get_frame().set_facecolor("#092975")
    legend.get_frame().set_edgecolor("#bfcae5")
    for text in legend.get_texts():
        text.set_color(text_color)
    legend.get_frame().set_linewidth(1.5) 
    legend.get_title().set_color(text_color)

    for spine in ax.spines.values():
        spine.set_color("#bfcae5")

    ax.grid(True, color=border_color)
    ax.set_facecolor('none')
    ax.margins(0)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    plt.close(fig)

    response = make_response(buf.getvalue())
    response.mimetype = 'image/png'

    return response

# =======================================================
# Obsługa strony
# =======================================================

@app.route("/")
def index():
    check_for_water()
    config = get_config()
    info = get_basic_info()
    zone = get_zone_info()
    return render_template("index.html", config=config, info=info, zone=zone)


@app.route("/water-config")
def configWater(e = 0):
    check_for_water()
    if (e == -1):
        print("BLAD")
    config = get_config()
    info = get_basic_info()
    return render_template("WaterConfig.html", config=config, info=info)

@app.route("/servo-config")
def configFoto():
    check_for_water()
    config = get_config()
    servo=get_last_servo_log()
    return render_template("servoConfig.html", config=config, servo=servo)


@app.route("/charts")
def charts():
    check_for_water()
    return render_template("charts.html")

@app.route("/log")
def logs():
    check_for_water()
    logs = get_logs()
    return render_template("logs.html", logs=logs)

@app.route("/log-event")
def event_logs():
    check_for_water()
    logs = get_events()
    return render_template("event.html", logs=logs)

@app.route("/other-config")
def other():
    check_for_water()
    config = get_config()
    check_for_water()
    return render_template("other.html", config=config)

def check_for_water():
    water = get_basic_info()[3][1]
    print(get_basic_info())
    if(water < MIN_WATER):
        flash("Uwaga poziom wody jest niski!", "error")

# =======================================================
# testowe dane
# =======================================================
def insert_sample_data(records=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    start_time = datetime.now()

    for i in range(records):
        current_time = start_time + timedelta(minutes=i)

        value = round(random.uniform(0.0, 100.0), 1)
        value2 = round(random.uniform(0.0, 1.0), 1)


        cursor.execute(
            "INSERT INTO sensor_logs (sensor_name, value, date) VALUES (?, ?, ?)",
            ("water", value, current_time)
        )

    conn.commit()

    conn.close()


#Funkcja do debug'owania
def insert_example(n=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    modes = ["auto", "manual", "set"]

    for i in range(n):
        old_angle = random.randint(10, 100)
        new_angle = random.randint(0, 180)
        mode = random.choice(modes)
        now = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO water_logs (mililiters, date)
            VALUES (?, ?)
        """, (old_angle, now))

    conn.commit()
    conn.close()
    print(f"[DONE] Dodano {n} przykładowych wpisów do servo_logs.")

# =======================================================
# Obsługa żądań
# =======================================================
from flask import flash
app.secret_key= "test" 
donica = Donica()
@app.route("/water", methods=["POST"])
def force_water():
    try:
        mililiters = int(request.form["mili"])
        d = donica.water(mililiters)
        if (d == -1):
            flash("Poziom wody jest zbyt niski! Podlewanie przerwane.", "error")
            return redirect(url_for("configWater"))
    except Exception as e:
        print("Błąd podlewania:", e)

    return redirect(url_for("configWater"))

# =======================================================
# main init
# =======================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)