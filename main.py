"""
Nexus Productivity Engine - Backend (FastAPI)
Architecture:
- Hierarchical Nested Documents Engine (Infinite recursion)
- Unified Database Engine (Single source of truth for Table, Kanban, List)
- Natural Language Smart-Parsing (Extracts title, time, tags, priority, duration)
- Autonomous Time-Blocking (Maps parsed items to daily slots automatically)
- Time-Aware State Manager API (Morning / Afternoon / Evening dynamic view rules)
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, time
import re
import uuid
import os

app = FastAPI(
    title="Nexus Productivity Engine",
    description="Minimalist Brutalist Productivity Platform with Zero-Friction Automation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class PageCreate(BaseModel):
    title: str
    content: Optional[str] = ""
    parent_id: Optional[str] = None

class PageUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    parent_id: Optional[str] = None

class Page(BaseModel):
    id: str
    title: str
    content: str
    parent_id: Optional[str] = None
    created_at: str
    updated_at: str
    children: List['Page'] = []

Page.model_rebuild()

class TaskCreate(BaseModel):
    title: str
    status: str = "todo"  # todo | in_progress | done
    tag: Optional[str] = "general"
    scheduled_time: Optional[str] = None  # HH:MM (24-hour format)
    duration_minutes: int = 30
    priority: str = "P2"  # P1 | P2 | P3
    proof_notes: Optional[str] = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    priority: Optional[str] = None
    proof_notes: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    status: str
    tag: str
    scheduled_time: Optional[str] = None
    duration_minutes: int = 30
    priority: str = "P2"
    proof_notes: str = ""
    created_at: str
    completed_at: Optional[str] = None

class NaturalLanguageParseRequest(BaseModel):
    text: str

class ParseResult(BaseModel):
    raw_input: str
    title: str
    scheduled_time: Optional[str] = None
    tag: str
    priority: str
    duration_minutes: int

# ============================================================================
# IN-MEMORY STORE WITH SENSIBLE SEED DATA
# ============================================================================

pages_db: Dict[str, Dict[str, Any]] = {
    "page_root_1": {
        "id": "page_root_1",
        "title": "Master Workspace",
        "content": "# Master Workspace\n\nWelcome to **NEXUS**. Built for absolute execution.\n\n- Zero gray tones\n- Zero rounded corners\n- Pure productivity\n\n### Core Directives\n1. Capture immediately using `Ctrl + Space`\n2. Follow the Time-Aware dynamic view cadence\n3. Engage Pomodoro focus engine for high-friction tasks",
        "parent_id": None,
        "created_at": "2026-10-25T08:00:00",
        "updated_at": "2026-10-25T08:00:00"
    },
    "page_sub_1": {
        "id": "page_sub_1",
        "title": "System Architecture",
        "content": "## System Architecture\n\n### Backend\n- **FastAPI** microservice handling nested trees, tasks, and regex parsing.\n- Autonomous time-blocking allocation algorithms.\n\n### Frontend\n- Single page application using vanilla JavaScript.\n- 1px high-contrast brutalist UI system.",
        "parent_id": "page_root_1",
        "created_at": "2026-10-25T08:30:00",
        "updated_at": "2026-10-25T08:30:00"
    },
    "page_sub_sub_1": {
        "id": "page_sub_sub_1",
        "title": "API Specification",
        "content": "### API Endpoints\n\n```http\nGET    /api/pages\nPOST   /api/pages\nGET    /api/tasks\nPOST   /api/parse\nGET    /api/timeline\n```\n\nAll endpoints return strictly typed JSON.",
        "parent_id": "page_sub_1",
        "created_at": "2026-10-25T09:00:00",
        "updated_at": "2026-10-25T09:00:00"
    },
    "page_root_2": {
        "id": "page_root_2",
        "title": "Product Roadmap",
        "content": "# Product Roadmap // Q4\n\n- [x] Zero-latency Natural Language Parser\n- [x] Time-Aware Dynamic Layouts (Morning / Afternoon / Evening)\n- [x] Fullscreen Pomodoro Focus Engine\n- [ ] Native Electron Desktop Wrapper",
        "parent_id": None,
        "created_at": "2026-10-25T09:15:00",
        "updated_at": "2026-10-25T09:15:00"
    }
}

tasks_db: Dict[str, Dict[str, Any]] = {
    "task_1": {
        "id": "task_1",
        "title": "Refactor FastAPI schema validators",
        "status": "todo",
        "tag": "dev",
        "scheduled_time": "09:00",
        "duration_minutes": 45,
        "priority": "P1",
        "proof_notes": "",
        "created_at": "2026-10-25T07:30:00",
        "completed_at": None
    },
    "task_2": {
        "id": "task_2",
        "title": "Verify brutalist zero-border-radius design tokens",
        "status": "in_progress",
        "tag": "design",
        "scheduled_time": "11:00",
        "duration_minutes": 30,
        "priority": "P1",
        "proof_notes": "",
        "created_at": "2026-10-25T08:00:00",
        "completed_at": None
    },
    "task_3": {
        "id": "task_3",
        "title": "Execute end-to-end NLP parser stress test",
        "status": "todo",
        "tag": "qa",
        "scheduled_time": "14:00",
        "duration_minutes": 60,
        "priority": "P2",
        "proof_notes": "",
        "created_at": "2026-10-25T08:15:00",
        "completed_at": None
    },
    "task_4": {
        "id": "task_4",
        "title": "Synthesize daily progress and log metrics",
        "status": "done",
        "tag": "review",
        "scheduled_time": "18:30",
        "duration_minutes": 30,
        "priority": "P3",
        "proof_notes": "Completed all 4 target sprints. Total focus time: 150 minutes.",
        "created_at": "2026-10-25T08:20:00",
        "completed_at": "2026-10-25T19:00:00"
    }
}

# ============================================================================
# NATURAL LANGUAGE PARSER ENGINE
# ============================================================================

def parse_natural_language(text: str) -> Dict[str, Any]:
    """
    Parses unstructured text into a structured task definition.
    Examples:
      - 'Code Python at 3pm #dev' -> title='Code Python', time='15:00', tag='dev'
      - 'Review PR at 10:30am #code !high' -> title='Review PR', time='10:30', tag='code', priority='P1'
      - 'Sync team at 14:00 #sync 45m' -> title='Sync team', time='14:00', duration=45
    """
    working_text = text.strip()
    extracted_time = None
    extracted_tag = "general"
    extracted_priority = "P2"
    extracted_duration = 30

    # 1. Extract Tag: #tag
    tag_match = re.search(r'#([a-zA-Z0-9_\-]+)', working_text)
    if tag_match:
        extracted_tag = tag_match.group(1).lower()
        working_text = re.sub(r'#[a-zA-Z0-9_\-]+', '', working_text)

    # 2. Extract Priority: !p1, !p2, !p3, !high, !medium, !low
    prio_match = re.search(r'!(p[1-3]|high|med|medium|low)', working_text, re.IGNORECASE)
    if prio_match:
        p_val = prio_match.group(1).lower()
        if p_val in ["p1", "high"]:
            extracted_priority = "P1"
        elif p_val in ["p3", "low"]:
            extracted_priority = "P3"
        else:
            extracted_priority = "P2"
        working_text = re.sub(r'!(p[1-3]|high|med|medium|low)', '', working_text, flags=re.IGNORECASE)

    # 3. Extract Duration: e.g. 45m, 1h, 90min
    dur_match = re.search(r'(\d+)\s*(m|min|mins|h|hr|hours)\b', working_text, re.IGNORECASE)
    if dur_match:
        num = int(dur_match.group(1))
        unit = dur_match.group(2).lower()
        if unit.startswith('h'):
            extracted_duration = num * 60
        else:
            extracted_duration = num
        working_text = re.sub(r'(\d+)\s*(m|min|mins|h|hr|hours)\b', '', working_text, flags=re.IGNORECASE)

    # 4. Extract Time:
    # 4a. 12-hour format: 3pm, 3:30pm, at 9am, at 11:45 am
    time_12_match = re.search(r'(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b', working_text, re.IGNORECASE)
    if time_12_match:
        hour = int(time_12_match.group(1))
        minute = int(time_12_match.group(2)) if time_12_match.group(2) else 0
        meridiem = time_12_match.group(3).lower()

        if meridiem == 'pm' and hour != 12:
            hour += 12
        elif meridiem == 'am' and hour == 12:
            hour = 0

        extracted_time = f"{hour:02d}:{minute:02d}"
        working_text = re.sub(r'(?:at\s+)?\d{1,2}(?::\d{2})?\s*(am|pm)\b', '', working_text, flags=re.IGNORECASE)
    else:
        # 4b. 24-hour format: at 14:00, 09:30
        time_24_match = re.search(r'(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\b', working_text, re.IGNORECASE)
        if time_24_match:
            hour = int(time_24_match.group(1))
            minute = int(time_24_match.group(2))
            extracted_time = f"{hour:02d}:{minute:02d}"
            working_text = re.sub(r'(?:at\s+)?[01]?\d|2[0-3]:[0-5]\d\b', '', working_text, flags=re.IGNORECASE)

    # 5. Clean Remaining Text as Title
    cleaned_title = re.sub(r'\s+', ' ', working_text).strip()
    if not cleaned_title:
        cleaned_title = "Untitled Task"

    return {
        "raw_input": text,
        "title": cleaned_title,
        "scheduled_time": extracted_time,
        "tag": extracted_tag,
        "priority": extracted_priority,
        "duration_minutes": extracted_duration
    }

# ============================================================================
# TIME-AWARE DYNAMIC VIEWS CALCULATOR
# ============================================================================

def determine_dynamic_view(hour: int) -> Dict[str, Any]:
    """
    Morning (06:00-12:00): 'Focus View' (Shows only top 3 tasks)
    Afternoon (12:00-18:00): 'Execution View' (Full Kanban & Timeline)
    Evening (18:00-24:00): 'Review View' (Completed tasks & proofs)
    Late-Night (00:00-06:00): 'Focus View' (Fallback / Quiet mode)
    """
    if 6 <= hour < 12:
        return {
            "view_mode": "morning_focus",
            "title": "FOCUS VIEW",
            "time_window": "06:00 - 12:00",
            "description": "High-impact cognitive bandwidth. Displaying top 3 vital priorities.",
            "enforce_limit": 3
        }
    elif 12 <= hour < 18:
        return {
            "view_mode": "afternoon_execution",
            "title": "EXECUTION VIEW",
            "time_window": "12:00 - 18:00",
            "description": "Maximum throughput. Full Kanban orchestration and active time-blocking.",
            "enforce_limit": None
        }
    else:
        return {
            "view_mode": "evening_review",
            "title": "REVIEW VIEW",
            "time_window": "18:00 - 24:00",
            "description": "Reflective closure. Inspecting completed outputs, proof notes, and velocity.",
            "enforce_limit": None
        }

# ============================================================================
# PAGE HIERARCHY HELPER
# ============================================================================

def build_page_tree(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    tree = []
    for pid, p in pages_db.items():
        if p.get("parent_id") == parent_id:
            node = dict(p)
            node["children"] = build_page_tree(pid)
            tree.append(node)
    return tree

# ============================================================================
# API ROUTES: PAGES (NESTED HIERARCHY)
# ============================================================================

@app.get("/api/pages")
def get_pages(tree: bool = Query(True, description="Return as nested tree or flat list")):
    if tree:
        return build_page_tree(None)
    return list(pages_db.values())

@app.get("/api/pages/{page_id}")
def get_page(page_id: str):
    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")
    return pages_db[page_id]

@app.post("/api/pages", status_code=201)
def create_page(payload: PageCreate):
    page_id = f"page_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    new_page = {
        "id": page_id,
        "title": payload.title or "Untitled Page",
        "content": payload.content or "",
        "parent_id": payload.parent_id,
        "created_at": now,
        "updated_at": now
    }
    pages_db[page_id] = new_page
    return new_page

@app.put("/api/pages/{page_id}")
def update_page(page_id: str, payload: PageUpdate):
    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")
    page = pages_db[page_id]
    if payload.title is not None:
        page["title"] = payload.title
    if payload.content is not None:
        page["content"] = payload.content
    if payload.parent_id is not None:
        page["parent_id"] = payload.parent_id
    page["updated_at"] = datetime.now().isoformat()
    return page

@app.delete("/api/pages/{page_id}")
def delete_page(page_id: str):
    if page_id not in pages_db:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Recursive deletion of subpages
    def collect_descendants(target_id: str) -> List[str]:
        desc = [target_id]
        for pid, p in pages_db.items():
            if p.get("parent_id") == target_id:
                desc.extend(collect_descendants(pid))
        return desc

    to_delete = collect_descendants(page_id)
    for pid in to_delete:
        pages_db.pop(pid, None)

    return {"deleted": to_delete, "count": len(to_delete)}

# ============================================================================
# API ROUTES: TASKS (UNIFIED DATABASE ENGINE)
# ============================================================================

@app.get("/api/tasks")
def get_tasks(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    limit: Optional[int] = None
):
    results = list(tasks_db.values())
    if status:
        results = [t for t in results if t["status"] == status]
    if tag:
        results = [t for t in results if t["tag"] == tag]
    
    # Sort: P1 first, then by scheduled time
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    results.sort(key=lambda x: (priority_order.get(x["priority"], 1), x.get("scheduled_time") or "99:99"))

    if limit:
        results = results[:limit]
    return results

@app.post("/api/tasks", status_code=201)
def create_task(payload: TaskCreate):
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    new_task = {
        "id": task_id,
        "title": payload.title,
        "status": payload.status,
        "tag": payload.tag or "general",
        "scheduled_time": payload.scheduled_time,
        "duration_minutes": payload.duration_minutes,
        "priority": payload.priority,
        "proof_notes": payload.proof_notes or "",
        "created_at": now,
        "completed_at": now if payload.status == "done" else None
    }
    tasks_db[task_id] = new_task
    return new_task

@app.put("/api/tasks/{task_id}")
def update_task(task_id: str, payload: TaskUpdate):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    
    if payload.title is not None:
        task["title"] = payload.title
    if payload.status is not None:
        old_status = task["status"]
        task["status"] = payload.status
        if payload.status == "done" and old_status != "done":
            task["completed_at"] = datetime.now().isoformat()
        elif payload.status != "done":
            task["completed_at"] = None
    if payload.tag is not None:
        task["tag"] = payload.tag
    if payload.scheduled_time is not None:
        task["scheduled_time"] = payload.scheduled_time
    if payload.duration_minutes is not None:
        task["duration_minutes"] = payload.duration_minutes
    if payload.priority is not None:
        task["priority"] = payload.priority
    if payload.proof_notes is not None:
        task["proof_notes"] = payload.proof_notes

    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    deleted = tasks_db.pop(task_id)
    return {"deleted": deleted["id"]}

# ============================================================================
# API ROUTES: NATURAL LANGUAGE & SMART-PARSING
# ============================================================================

@app.post("/api/parse", response_model=ParseResult)
def parse_endpoint(payload: NaturalLanguageParseRequest):
    """Parses natural language string into structured parameters without committing."""
    return parse_natural_language(payload.text)

@app.post("/api/quick-capture", status_code=201)
def quick_capture(payload: NaturalLanguageParseRequest):
    """Zero-friction quick capture: parses string and automatically inserts task."""
    parsed = parse_natural_language(payload.text)
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    now = datetime.now().isoformat()
    new_task = {
        "id": task_id,
        "title": parsed["title"],
        "status": "todo",
        "tag": parsed["tag"],
        "scheduled_time": parsed["scheduled_time"],
        "duration_minutes": parsed["duration_minutes"],
        "priority": parsed["priority"],
        "proof_notes": "",
        "created_at": now,
        "completed_at": None
    }
    tasks_db[task_id] = new_task
    return new_task

# ============================================================================
# API ROUTES: AUTONOMOUS TIME-BLOCKING
# ============================================================================

@app.get("/api/timeline")
def get_timeline():
    """
    Autonomous Time-Blocking:
    Generates daily schedule grid (06:00 to 23:00).
    Maps tasks with explicit scheduled_time into their exact hour slots.
    Identifies unallocated tasks and provides an automated packing recommendation.
    """
    hours = [f"{h:02d}:00" for h in range(6, 24)]
    timeline_slots: Dict[str, List[Dict[str, Any]]] = {h: [] for h in hours}
    unscheduled: List[Dict[str, Any]] = []

    for task in tasks_db.values():
        t_time = task.get("scheduled_time")
        if t_time:
            # Map HH:MM to the nearest hour slot
            try:
                hour_val = int(t_time.split(":")[0])
                slot_key = f"{hour_val:02d}:00"
                if slot_key in timeline_slots:
                    timeline_slots[slot_key].append(task)
                else:
                    unscheduled.append(task)
            except Exception:
                unscheduled.append(task)
        else:
            unscheduled.append(task)

    return {
        "slots": timeline_slots,
        "unscheduled_count": len(unscheduled),
        "unscheduled_tasks": unscheduled
    }

@app.post("/api/timeline/auto-schedule")
def auto_schedule_unscheduled():
    """
    Autonomous Engine: Automatically maps unscheduled tasks into the earliest
    open time slots between 09:00 and 18:00 without manual drag-and-drop.
    """
    # Find occupied hours
    occupied_hours = set()
    for task in tasks_db.values():
        if task.get("scheduled_time"):
            try:
                occupied_hours.add(int(task["scheduled_time"].split(":")[0]))
            except Exception:
                pass

    scheduled_now = []
    # Candidate hours: 9, 10, 11, 13, 14, 15, 16, 17
    candidate_hours = [9, 10, 11, 13, 14, 15, 16, 17]
    avail_hours = [h for h in candidate_hours if h not in occupied_hours]

    for task in tasks_db.values():
        if not task.get("scheduled_time") and task["status"] != "done":
            if avail_hours:
                assigned_hour = avail_hours.pop(0)
                assigned_time = f"{assigned_hour:02d}:00"
                task["scheduled_time"] = assigned_time
                scheduled_now.append({"id": task["id"], "scheduled_time": assigned_time})

    return {
        "allocated_count": len(scheduled_now),
        "allocations": scheduled_now
    }

# ============================================================================
# API ROUTES: TIME-AWARE DYNAMIC VIEW STATE
# ============================================================================

@app.get("/api/system/time-state")
def get_time_state(simulated_hour: Optional[int] = None):
    """
    Returns current system time and the dynamic view layout.
    Accepts optional simulated_hour (0-23) to preview morning/afternoon/evening layouts.
    """
    now = datetime.now()
    active_hour = simulated_hour if simulated_hour is not None else now.hour
    view_meta = determine_dynamic_view(active_hour)
    
    return {
        "current_system_time": now.strftime("%H:%M:%S"),
        "active_hour": active_hour,
        "dynamic_view": view_meta
    }

# ============================================================================
# FRONTEND STATIC SERVING
# ============================================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
index_path = os.path.join(current_dir, "index.html")

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Nexus Backend Active. index.html not found in current directory.</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
