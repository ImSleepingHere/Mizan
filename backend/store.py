import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .fixtures import generate

ROOT=Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def db_path():
    return Path(os.environ.get("MIZAN_DB",str(ROOT/"data"/"mizan.sqlite3")))


@contextmanager
def connect():
    path=db_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=30)
    con.row_factory=sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS scenarios(id TEXT PRIMARY KEY,name TEXT NOT NULL,revision INTEGER NOT NULL,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS versions(scenario_id TEXT,revision INTEGER,data TEXT NOT NULL,created TEXT NOT NULL,PRIMARY KEY(scenario_id,revision));
        CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY,scenario_id TEXT NOT NULL,base_revision INTEGER NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL,analysis TEXT NOT NULL,created TEXT NOT NULL,actor TEXT NOT NULL,reason TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,created TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,subject TEXT NOT NULL,detail TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS requisitions(id TEXT PRIMARY KEY,scenario_id TEXT NOT NULL,revision INTEGER NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,username TEXT NOT NULL,expires REAL NOT NULL);
        ''')
        for kind in ["baseline","diagnostic","shortfall","faculty"]:
            if not con.execute("SELECT 1 FROM scenarios WHERE id=?",(kind,)).fetchone():
                data=generate(kind)
                payload=data.model_dump_json()
                con.execute("INSERT INTO scenarios VALUES(?,?,?,?)",(kind,data.name,1,payload))
                con.execute("INSERT INTO versions VALUES(?,?,?,?)",(kind,1,payload,now()))


def audit(con,actor,action,subject,detail):
    con.execute("INSERT INTO audit(created,actor,action,subject,detail) VALUES(?,?,?,?,?)",(now(),actor,action,subject,json.dumps(detail,ensure_ascii=False)))


def identifier():
    return uuid4().hex[:12]
