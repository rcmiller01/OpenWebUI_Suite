from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
import sqlite3
import time
import uuid

DB_PATH = os.getenv("GATEWAY_DB", "/data/gateway.db")
router = APIRouter(prefix="/projects", tags=["projects"])


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def _init():
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS projects(
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        created_at INTEGER NOT NULL
    );"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS project_items(
        project_id TEXT NOT NULL,
        convo_id TEXT NOT NULL,
        PRIMARY KEY (project_id, convo_id),
        FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
    );"""
    )
    conn.commit()
    conn.close()

_init()


class Project(BaseModel):
    id: str
    name: str
    created_at: int

class CreateProjectReq(BaseModel):
    name: str

class ProjectItemReq(BaseModel):
    convo_id: str

@router.get("", response_model=List[Project])
def list_projects():
    conn = _conn()
    cur = conn.execute(
        "SELECT id,name,created_at FROM projects ORDER BY created_at DESC"
    )
    rows = [
        Project(id=r[0], name=r[1], created_at=r[2]) for r in cur.fetchall()
    ]
    conn.close()
    return rows

@router.post("", response_model=Project)
def create_project(req: CreateProjectReq):
    pid = str(uuid.uuid4())
    now = int(time.time())
    conn = _conn()
    conn.execute(
        "INSERT INTO projects(id,name,created_at) VALUES(?,?,?)",
        (pid, req.name, now),
    )
    conn.commit()
    conn.close()
    return Project(id=pid, name=req.name, created_at=now)

@router.delete("/{project_id}")
def delete_project(project_id: str):
    conn = _conn()
    cur = conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        raise HTTPException(404, "project not found")
    return {"status": "ok"}

@router.post("/{project_id}/items")
def add_item(project_id: str, req: ProjectItemReq):
    conn = _conn()
    conn.execute(
        "INSERT OR IGNORE INTO project_items(project_id,convo_id) VALUES(?,?)",
        (project_id, req.convo_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@router.delete("/{project_id}/items/{convo_id}")
def remove_item(project_id: str, convo_id: str):
    conn = _conn()
    conn.execute(
        "DELETE FROM project_items WHERE project_id=? AND convo_id=?",
        (project_id, convo_id),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@router.get("/{project_id}/items", response_model=List[str])
def list_items(project_id: str):
    conn = _conn()
    cur = conn.execute(
        (
            "SELECT convo_id FROM project_items WHERE project_id=? "
            "ORDER BY convo_id"
        ),
        (project_id,),
    )
    out = [r[0] for r in cur.fetchall()]
    conn.close()
    return out
