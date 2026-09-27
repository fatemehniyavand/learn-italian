# full_history.py
import json, sqlite3
from datetime import date, datetime
from db import conn

def init_full_history():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS content_archive(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          day TEXT NOT NULL, section TEXT NOT NULL, subtype TEXT DEFAULT '',
          title TEXT DEFAULT '', source_key TEXT DEFAULT '', content TEXT NOT NULL,
          created_at TEXT NOT NULL,
          UNIQUE(day,section,subtype,source_key)
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS correction_archive(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          day TEXT NOT NULL, section TEXT NOT NULL, ref TEXT DEFAULT '',
          prompt TEXT DEFAULT '', user_answer TEXT DEFAULT '',
          corrected TEXT DEFAULT '', feedback TEXT DEFAULT '',
          score REAL DEFAULT 0, payload TEXT DEFAULT '{}', created_at TEXT NOT NULL
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_archive_day_section ON content_archive(day,section)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_corr_day_section ON correction_archive(day,section)")

def archive_content(section, content, subtype="", title="", source_key="", day=None):
    day=day or date.today().isoformat()
    payload=json.dumps(content,ensure_ascii=False)
    key=source_key or title or subtype or str(abs(hash(payload)))
    with conn() as c:
        c.execute("""INSERT INTO content_archive(day,section,subtype,title,source_key,content,created_at)
          VALUES(?,?,?,?,?,?,?)
          ON CONFLICT(day,section,subtype,source_key) DO UPDATE SET
          title=excluded.title,content=excluded.content""",
          (day,section,subtype,title,key,payload,datetime.now().isoformat(timespec="seconds")))

def archive_correction(section, prompt, user_answer, result, ref="", score=0, day=None):
    day=day or date.today().isoformat()
    corrected=result.get("corrected","") if isinstance(result,dict) else ""
    feedback=result.get("feedback_fa","") if isinstance(result,dict) else ""
    with conn() as c:
        c.execute("""INSERT INTO correction_archive(day,section,ref,prompt,user_answer,corrected,feedback,score,payload,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,?)""",(day,section,str(ref),prompt,user_answer,corrected,feedback,float(score or 0),
        json.dumps(result,ensure_ascii=False),datetime.now().isoformat(timespec="seconds")))

def archive_rows(section=None):
    with conn() as c:
        if section:
            return c.execute("SELECT * FROM content_archive WHERE section=? ORDER BY day DESC,id DESC",(section,)).fetchall()
        return c.execute("SELECT * FROM content_archive ORDER BY day DESC,id DESC").fetchall()

def correction_rows(section=None):
    with conn() as c:
        if section:
            return c.execute("SELECT * FROM correction_archive WHERE section=? ORDER BY day DESC,id DESC",(section,)).fetchall()
        return c.execute("SELECT * FROM correction_archive ORDER BY day DESC,id DESC").fetchall()

def latest_correction(section, ref="", day=None):
    day=day or date.today().isoformat()
    with conn() as c:
        return c.execute("""SELECT * FROM correction_archive
        WHERE day=? AND section=? AND ref=? ORDER BY id DESC LIMIT 1""",(day,section,str(ref))).fetchone()
