
import sqlite3, json
from datetime import date, datetime, timedelta
DB="italian_coach.db"
SECTIONS=["vocab","idioms","grammar","exercises","reading","writing","speaking","review"]

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS daily_progress(day TEXT PRIMARY KEY,vocab INTEGER DEFAULT 0,
        idioms INTEGER DEFAULT 0,grammar INTEGER DEFAULT 0,exercises INTEGER DEFAULT 0,reading INTEGER DEFAULT 0,
        writing INTEGER DEFAULT 0,speaking INTEGER DEFAULT 0,review INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS daily_content(day TEXT,kind TEXT,content TEXT,
        PRIMARY KEY(day,kind))""")
        c.execute("""CREATE TABLE IF NOT EXISTS activity_log(id INTEGER PRIMARY KEY AUTOINCREMENT,day TEXT,ts TEXT,
        section TEXT,action TEXT,points INTEGER DEFAULT 0,detail TEXT DEFAULT '')""")
        c.execute("""CREATE TABLE IF NOT EXISTS grammar_progress(unit INTEGER PRIMARY KEY,status TEXT DEFAULT 'not_started',
        best_score INTEGER DEFAULT 0,last_score INTEGER DEFAULT 0,attempts INTEGER DEFAULT 0,last_seen TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS grammar_lessons(unit INTEGER PRIMARY KEY,content TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,day TEXT,kind TEXT,
        ref TEXT,answers TEXT,result TEXT,score INTEGER DEFAULT 0,ts TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY AUTOINCREMENT,day TEXT,topic TEXT,
        original TEXT,corrected TEXT,feedback TEXT,score INTEGER DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS speaking_sessions(id INTEGER PRIMARY KEY AUTOINCREMENT,day TEXT,topic TEXT,
        user_text TEXT,tutor_text TEXT)""")
        # migrations for older DB
        cols=[r["name"] for r in c.execute("PRAGMA table_info(daily_progress)").fetchall()]
        for name in SECTIONS:
            if name not in cols: c.execute(f"ALTER TABLE daily_progress ADD COLUMN {name} INTEGER DEFAULT 0")
    ensure_today()
def ensure_today():
    with conn() as c: c.execute("INSERT OR IGNORE INTO daily_progress(day) VALUES(?)",(date.today().isoformat(),))
def put_daily(kind,obj,day=None):
    day=day or date.today().isoformat()
    with conn() as c: c.execute("""INSERT INTO daily_content(day,kind,content) VALUES(?,?,?)
    ON CONFLICT(day,kind) DO UPDATE SET content=excluded.content""",(day,kind,json.dumps(obj,ensure_ascii=False)))
def get_daily(kind,day=None):
    day=day or date.today().isoformat()
    with conn() as c: r=c.execute("SELECT content FROM daily_content WHERE day=? AND kind=?",(day,kind)).fetchone()
    return json.loads(r["content"]) if r else None
def put_lesson(unit,obj):
    with conn() as c: c.execute("""INSERT INTO grammar_lessons(unit,content) VALUES(?,?)
    ON CONFLICT(unit) DO UPDATE SET content=excluded.content""",(unit,json.dumps(obj,ensure_ascii=False)))
def get_lesson(unit):
    with conn() as c:r=c.execute("SELECT content FROM grammar_lessons WHERE unit=?",(unit,)).fetchone()
    return json.loads(r["content"]) if r else None
def mark(section,action="completed",points=10,detail=""):
    ensure_today()
    with conn() as c:
        c.execute(f"UPDATE daily_progress SET {section}=1 WHERE day=?",(date.today().isoformat(),))
        c.execute("INSERT INTO activity_log(day,ts,section,action,points,detail) VALUES(?,?,?,?,?,?)",
        (date.today().isoformat(),datetime.now().isoformat(timespec="seconds"),section,action,points,detail))
def log(section,action,points=1,detail=""):
    with conn() as c:c.execute("INSERT INTO activity_log(day,ts,section,action,points,detail) VALUES(?,?,?,?,?,?)",
    (date.today().isoformat(),datetime.now().isoformat(timespec="seconds"),section,action,points,detail))
def progress(days=180):
    ensure_today()
    with conn() as c:return c.execute("SELECT * FROM daily_progress ORDER BY day DESC LIMIT ?",(days,)).fetchall()
def today_row(): return dict(progress(1)[0])
def streak():
    rows={r["day"]:dict(r) for r in progress(365)}; s=0; d=date.today()
    while d.isoformat() in rows and any(rows[d.isoformat()].get(k,0) for k in SECTIONS):
        s+=1; d-=timedelta(days=1)
    return s
def activity_today():
    with conn() as c:return c.execute("SELECT * FROM activity_log WHERE day=? ORDER BY id DESC",(date.today().isoformat(),)).fetchall()
def grammar_status():
    with conn() as c:return {r["unit"]:dict(r) for r in c.execute("SELECT * FROM grammar_progress").fetchall()}
def save_attempt(kind,ref,answers,result,score):
    with conn() as c:c.execute("INSERT INTO attempts(day,kind,ref,answers,result,score,ts) VALUES(?,?,?,?,?,?,?)",
    (date.today().isoformat(),kind,str(ref),answers,json.dumps(result,ensure_ascii=False),score,datetime.now().isoformat(timespec="seconds")))
def attempts(kind=None):
    with conn() as c:
        if kind:return c.execute("SELECT * FROM attempts WHERE kind=? ORDER BY id DESC",(kind,)).fetchall()
        return c.execute("SELECT * FROM attempts ORDER BY id DESC").fetchall()
def set_grammar_score(unit,score):
    with conn() as c:c.execute("""INSERT INTO grammar_progress(unit,status,best_score,last_score,attempts,last_seen)
    VALUES(?,?,?,?,?,?) ON CONFLICT(unit) DO UPDATE SET status='completed',
    best_score=MAX(best_score,excluded.best_score),last_score=excluded.last_score,attempts=attempts+1,last_seen=excluded.last_seen""",
    (unit,"completed",score,score,1,date.today().isoformat()))
def save_journal(topic,original,corrected,feedback,score=0):
    with conn() as c:c.execute("INSERT INTO journal(day,topic,original,corrected,feedback,score) VALUES(?,?,?,?,?,?)",
    (date.today().isoformat(),topic,original,corrected,feedback,score))
def save_speaking(topic,user_text,tutor_text):
    with conn() as c:c.execute("INSERT INTO speaking_sessions(day,topic,user_text,tutor_text) VALUES(?,?,?,?)",
    (date.today().isoformat(),topic,user_text,tutor_text))
