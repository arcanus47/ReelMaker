import sqlite3
from app.config import DATABASE_PATH

class Database:
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE_PATH)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def initialize(self):
        self.connection.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            source_video TEXT, duration REAL DEFAULT 0, resolution TEXT,
            fps REAL DEFAULT 0, status TEXT DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL,
            title TEXT, start_time REAL, end_time REAL, score REAL DEFAULT 0,
            output_path TEXT, status TEXT DEFAULT 'pending',
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER NOT NULL,
            start_time REAL, end_time REAL, text TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """)
        self.connection.commit()

    def create_project(self, name, source_video=None, duration=0, resolution=None, fps=0):
        cur=self.connection.execute(
            "INSERT INTO projects(name,source_video,duration,resolution,fps) VALUES(?,?,?,?,?)",
            (name,source_video,duration,resolution,fps))
        self.connection.commit()
        return cur.lastrowid

    def get_projects(self):
        return self.connection.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()

    def get_project(self, project_id):
        return self.connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()

    def delete_project(self, project_id):
        self.connection.execute("DELETE FROM clips WHERE project_id=?", (project_id,))
        self.connection.execute("DELETE FROM transcripts WHERE project_id=?", (project_id,))
        self.connection.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self.connection.commit()

    def save_transcript(self, project_id, segments):
        self.connection.execute("DELETE FROM transcripts WHERE project_id=?", (project_id,))
        self.connection.executemany(
            "INSERT INTO transcripts(project_id,start_time,end_time,text) VALUES(?,?,?,?)",
            [(project_id,s["start"],s["end"],s["text"]) for s in segments])
        self.connection.commit()

    def get_transcript(self, project_id):
        return self.connection.execute(
            "SELECT * FROM transcripts WHERE project_id=? ORDER BY start_time", (project_id,)).fetchall()

    def save_clips(self, project_id, clips):
        self.connection.execute("DELETE FROM clips WHERE project_id=?", (project_id,))
        self.connection.executemany(
            "INSERT INTO clips(project_id,title,start_time,end_time,score,status) VALUES(?,?,?,?,?,'pending')",
            [(project_id,c["title"],c["start"],c["end"],c.get("score",0)) for c in clips])
        self.connection.commit()

    def get_clips(self, project_id=None):
        if project_id is None:
            return self.connection.execute("SELECT * FROM clips ORDER BY id DESC").fetchall()
        return self.connection.execute("SELECT * FROM clips WHERE project_id=? ORDER BY start_time", (project_id,)).fetchall()

    def update_clip(self, clip_id, title, start, end):
        self.connection.execute("UPDATE clips SET title=?,start_time=?,end_time=? WHERE id=?",
                                (title,start,end,clip_id))
        self.connection.commit()

    def mark_clip_exported(self, clip_id, path):
        self.connection.execute("UPDATE clips SET output_path=?,status='exported' WHERE id=?", (path,clip_id))
        self.connection.commit()

    def close(self):
        self.connection.close()
