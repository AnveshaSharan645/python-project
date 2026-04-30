# """
# Hostel Management System
# ========================
# A complete desktop application for managing hostel complaints, mess feedback,
# student details, and ragging reports.

# Libraries Used:
# - Tkinter (GUI Frontend)
# - Pandas (Data Handling)
# - Matplotlib (Data Visualization)
# - NumPy (Numerical Operations)
# - JSON file-based storage (no MongoDB required)

# Usage:
#     pip install pandas matplotlib numpy
#     python hostel_management.py
# """

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import random
import json
import os

# Third-party imports
import pandas as pd
import numpy as np

# Optional matplotlib for analytics
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except Exception as e:
    print(f"Note: Matplotlib not available ({type(e).__name__}). Analytics will be limited.")
    MATPLOTLIB_AVAILABLE = False


# ─────────────────────────────────────────────
# JSON File-Based Database
# ─────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostel_data")
os.makedirs(DATA_DIR, exist_ok=True)


class JsonCollection:
    """Simple JSON file-based collection mimicking basic MongoDB operations."""

    def __init__(self, name):
        self.filepath = os.path.join(DATA_DIR, f"{name}.json")
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []

    def _save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def insert_one(self, doc):
        self.data.append(doc)
        self._save()

    def find(self, query=None):
        if not query:
            return list(self.data)
        return [d for d in self.data if all(d.get(k) == v for k, v in query.items())]

    def find_one(self, query):
        for d in self.data:
            if all(d.get(k) == v for k, v in query.items()):
                return d
        return None

    def count_documents(self, query=None):
        return len(self.find(query))

    def update_one(self, query, update):
        set_fields = update.get("$set", {})
        for d in self.data:
            if all(d.get(k) == v for k, v in query.items()):
                d.update(set_fields)
                self._save()
                return True
        return False

    def delete_one(self, query):
        """Delete a single document matching the query."""
        for i, d in enumerate(self.data):
            if all(d.get(k) == v for k, v in query.items()):
                self.data.pop(i)
                self._save()
                return True
        return False

    def aggregate_group(self, group_field, avg_field=None):
        """Simple group-by aggregation."""
        groups = {}
        for d in self.data:
            key = d.get(group_field, "Unknown")
            if key not in groups:
                groups[key] = {"_id": key, "count": 0, "values": []}
            groups[key]["count"] += 1
            if avg_field and avg_field in d:
                groups[key]["values"].append(d[avg_field])
        results = []
        for g in groups.values():
            entry = {"_id": g["_id"], "count": g["count"]}
            if avg_field and g["values"]:
                entry["avg_rating"] = sum(g["values"]) / len(g["values"])
            results.append(entry)
        return results


# Initialize collections
students_col = JsonCollection("students")
complaints_col = JsonCollection("complaints")
mess_feedback_col = JsonCollection("mess_feedback")
ragging_col = JsonCollection("ragging_reports")


# ─────────────────────────────────────────────
# Color Palette & Styling
# ─────────────────────────────────────────────
COLORS = {
    "bg": "#1a1a2e",
    "sidebar": "#16213e",
    "card": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b81",
    "text": "#eaeaea",
    "text_muted": "#a0a0b0",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "input_bg": "#1e2a4a",
    "input_border": "#3a4a6a",
    "table_header": "#0f3460",
    "table_row1": "#1a1a2e",
    "table_row2": "#16213e",
    "white": "#ffffff",
}


def generate_id(prefix="CMP"):
    return f"{prefix}-{random.randint(10000, 99999)}"


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────
class HostelManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏨 Hostel Management System")
        self.root.geometry("1200x750")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(1100, 700)

        self.mode = tk.StringVar(value="student")
        self._build_ui()

    def _build_ui(self):
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(main, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(main, bg=COLORS["bg"])
        self.content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self.show_dashboard()

    def _build_sidebar(self):
        tk.Label(
            self.sidebar, text="🏨 HMS", font=("Segoe UI", 22, "bold"),
            bg=COLORS["sidebar"], fg=COLORS["accent"]
        ).pack(pady=(25, 5))
        tk.Label(
            self.sidebar, text="Hostel Management", font=("Segoe UI", 10),
            bg=COLORS["sidebar"], fg=COLORS["text_muted"]
        ).pack(pady=(0, 20))

        mode_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        mode_frame.pack(fill="x", padx=15, pady=(0, 15))

        for val, label in [("admin", "👑 Admin"), ("student", "🎓 Student")]:
            rb = tk.Radiobutton(
                mode_frame, text=label, variable=self.mode, value=val,
                font=("Segoe UI", 11), bg=COLORS["sidebar"], fg=COLORS["text"],
                selectcolor=COLORS["card"], activebackground=COLORS["sidebar"],
                activeforeground=COLORS["accent"], indicatoron=0,
                relief="flat", bd=0, padx=15, pady=8,
                command=self._refresh_sidebar
            )
            rb.pack(fill="x", pady=2)

        tk.Frame(self.sidebar, bg=COLORS["input_border"], height=1).pack(fill="x", padx=15, pady=10)

        self.nav_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        self.nav_frame.pack(fill="x")

        self._refresh_sidebar()

    def _refresh_sidebar(self):
        for w in self.nav_frame.winfo_children():
            w.destroy()

        if self.mode.get() == "admin":
            buttons = [
                ("📊 Dashboard", self.show_dashboard),
                ("👥 All Students", self.show_all_students),
                ("📋 All Complaints", self.show_all_complaints),
                ("🍽️ Mess Feedback", self.show_all_mess_feedback),
                ("🚨 Ragging Reports", self.show_all_ragging),
                ("📈 Analytics", self.show_analytics),
            ]
        else:
            buttons = [
                ("📊 Dashboard", self.show_dashboard),
                ("📝 Register", self.show_student_register),
                ("📋 File Complaint", self.show_file_complaint),
                ("🍽️ Mess Feedback", self.show_mess_feedback),
                ("🚨 Report Ragging", self.show_ragging_report),
            ]

        for text, cmd in buttons:
            btn = tk.Button(
                self.nav_frame, text=text, font=("Segoe UI", 11),
                bg=COLORS["sidebar"], fg=COLORS["text"], bd=0, relief="flat",
                anchor="w", padx=20, pady=10, activebackground=COLORS["card"],
                activeforeground=COLORS["accent"], cursor="hand2", command=cmd
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["card"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLORS["sidebar"]))

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _make_header(self, title, subtitle=""):
        header = tk.Frame(self.content, bg=COLORS["bg"])
        header.pack(fill="x", padx=30, pady=(25, 15))
        tk.Label(header, text=title, font=("Segoe UI", 20, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w")
        if subtitle:
            tk.Label(header, text=subtitle, font=("Segoe UI", 10),
                     bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(anchor="w")

    def _make_input(self, parent, label, row, col=0, width=30):
        tk.Label(parent, text=label, font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=row, column=col * 2, sticky="w", padx=(15, 5), pady=6)
        entry = tk.Entry(parent, font=("Segoe UI", 11), width=width,
                         bg=COLORS["input_bg"], fg=COLORS["text"],
                         insertbackground=COLORS["text"], relief="flat",
                         bd=0, highlightthickness=1,
                         highlightcolor=COLORS["accent"],
                         highlightbackground=COLORS["input_border"])
        entry.grid(row=row, column=col * 2 + 1, padx=(0, 15), pady=6, sticky="ew")
        return entry

    def _make_button(self, parent, text, command, color=None):
        bg = color or COLORS["accent"]
        btn = tk.Button(parent, text=text, font=("Segoe UI", 11, "bold"),
                        bg=bg, fg=COLORS["white"], bd=0, relief="flat",
                        padx=25, pady=10, cursor="hand2", command=command,
                        activebackground=COLORS["accent_hover"],
                        activeforeground=COLORS["white"])
        return btn

    def _stat_card(self, parent, title, value, color, col):
        card = tk.Frame(parent, bg=color, padx=20, pady=15)
        card.grid(row=0, column=col, padx=8, pady=5, sticky="nsew")
        tk.Label(card, text=title, font=("Segoe UI", 9),
                 bg=color, fg="#a0a0b0").pack(anchor="w")
        tk.Label(card, text=str(value), font=("Segoe UI", 26, "bold"),
                 bg=color, fg=COLORS["white"]).pack(anchor="w")

    # ─── DASHBOARD ───
    def show_dashboard(self):
        self._clear_content()
        self._make_header("Dashboard", "Overview of hostel management system")

        stats_frame = tk.Frame(self.content, bg=COLORS["bg"])
        stats_frame.pack(fill="x", padx=30, pady=10)
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        total_students = students_col.count_documents()
        total_complaints = complaints_col.count_documents()
        resolved = complaints_col.count_documents({"status": "Resolved"})
        pending = complaints_col.count_documents({"status": "Pending"})
        total_feedback = mess_feedback_col.count_documents()
        total_ragging = ragging_col.count_documents()

        self._stat_card(stats_frame, "Total Students", total_students, "#2563eb", 0)
        self._stat_card(stats_frame, "Total Complaints", total_complaints, COLORS["accent"], 1)
        self._stat_card(stats_frame, "Resolved", resolved, COLORS["success"], 2)
        self._stat_card(stats_frame, "Pending", pending, COLORS["warning"], 3)

        stats_frame2 = tk.Frame(self.content, bg=COLORS["bg"])
        stats_frame2.pack(fill="x", padx=30, pady=5)
        for i in range(4):
            stats_frame2.columnconfigure(i, weight=1)
        self._stat_card(stats_frame2, "Mess Feedback", total_feedback, "#8b5cf6", 0)
        self._stat_card(stats_frame2, "Ragging Reports", total_ragging, "#dc2626", 1)

        resolution_rate = (resolved / total_complaints * 100) if total_complaints > 0 else 0
        self._stat_card(stats_frame2, "Resolution Rate", f"{resolution_rate:.0f}%", "#059669", 2)

        today_complaints = complaints_col.count_documents({"date": datetime.now().strftime("%Y-%m-%d")})
        self._stat_card(stats_frame2, "Today's Complaints", today_complaints, "#d97706", 3)

        # Recent complaints
        recent_frame = tk.Frame(self.content, bg=COLORS["card"], padx=15, pady=15)
        recent_frame.pack(fill="both", expand=True, padx=30, pady=15)
        tk.Label(recent_frame, text="📋 Recent Complaints", font=("Segoe UI", 13, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        cols = ("ID", "Student", "Category", "Status", "Date")
        tree = ttk.Treeview(recent_frame, columns=cols, show="headings", height=8)
        self._style_treeview(tree)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120)
        tree.pack(fill="both", expand=True)

        recent = complaints_col.find()
        recent.reverse()
        for r in recent[:10]:
            tree.insert("", "end", values=(
                r.get("complaint_id", ""), r.get("student_name", ""),
                r.get("category", ""), r.get("status", ""), r.get("date", ""),
            ))

    # ─── STUDENT REGISTRATION ───
    def show_student_register(self):
        self._clear_content()
        self._make_header("Student Registration", "Fill in your details to register")

        form = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=20)
        form.pack(fill="x", padx=30, pady=10)

        self.reg_name = self._make_input(form, "Full Name", 0)
        self.reg_sap = self._make_input(form, "SAP ID", 1)
        self.reg_room = self._make_input(form, "Room No.", 2)
        self.reg_phone = self._make_input(form, "Phone Number", 3)
        self.reg_email = self._make_input(form, "Email", 4)
        self.reg_course = self._make_input(form, "Course", 5)
        self.reg_year = self._make_input(form, "Year", 6)
        self.reg_hostel = self._make_input(form, "Hostel Block", 7)

        btn_frame = tk.Frame(self.content, bg=COLORS["bg"])
        btn_frame.pack(pady=15)
        self._make_button(btn_frame, "✅ Register Student", self._register_student).pack()

    def _register_student(self):
        data = {
            "name": self.reg_name.get().strip(),
            "sap_id": self.reg_sap.get().strip(),
            "room_no": self.reg_room.get().strip(),
            "phone": self.reg_phone.get().strip(),
            "email": self.reg_email.get().strip(),
            "course": self.reg_course.get().strip(),
            "year": self.reg_year.get().strip(),
            "hostel_block": self.reg_hostel.get().strip(),
            "registered_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if not data["name"] or not data["sap_id"] or not data["room_no"] or not data["phone"]:
            messagebox.showwarning("Validation", "Name, SAP ID, Room No, and Phone are required.")
            return
        if students_col.find_one({"sap_id": data["sap_id"]}):
            messagebox.showerror("Error", "A student with this SAP ID already exists.")
            return
        students_col.insert_one(data)
        messagebox.showinfo("Success", f"Student {data['name']} registered successfully!")
        self.show_student_register()

    # ─── FILE COMPLAINT ───
    def show_file_complaint(self):
        self._clear_content()
        self._make_header("File a Complaint", "Select category and describe your issue")

        form = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=20)
        form.pack(fill="x", padx=30, pady=10)

        self.cmp_sap = self._make_input(form, "Your SAP ID", 0)

        tk.Label(form, text="Category", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=1, column=0, sticky="w", padx=(15, 5), pady=6)
        self.cmp_category = ttk.Combobox(form, values=[
            "Electricity Issue", "Room Damage", "Plumbing Problem",
            "Furniture Damage", "Internet/WiFi Issue", "Cleanliness",
            "Water Supply", "Security Issue", "Pest Control", "Other"
        ], state="readonly", font=("Segoe UI", 11), width=28)
        self.cmp_category.grid(row=1, column=1, padx=(0, 15), pady=6, sticky="ew")
        self.cmp_category.set("Electricity Issue")

        tk.Label(form, text="Priority", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=2, column=0, sticky="w", padx=(15, 5), pady=6)
        self.cmp_priority = ttk.Combobox(form, values=["Low", "Medium", "High", "Urgent"],
                                         state="readonly", font=("Segoe UI", 11), width=28)
        self.cmp_priority.grid(row=2, column=1, padx=(0, 15), pady=6, sticky="ew")
        self.cmp_priority.set("Medium")

        tk.Label(form, text="Description", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=3, column=0, sticky="nw", padx=(15, 5), pady=6)
        self.cmp_desc = scrolledtext.ScrolledText(
            form, font=("Segoe UI", 11), width=40, height=5,
            bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0)
        self.cmp_desc.grid(row=3, column=1, padx=(0, 15), pady=6, sticky="ew")

        btn_frame = tk.Frame(self.content, bg=COLORS["bg"])
        btn_frame.pack(pady=15)
        self._make_button(btn_frame, "📋 Submit Complaint", self._submit_complaint).pack()

    def _submit_complaint(self):
        sap = self.cmp_sap.get().strip()
        if not sap:
            messagebox.showwarning("Validation", "Please enter your SAP ID.")
            return
        student = students_col.find_one({"sap_id": sap})
        if not student:
            messagebox.showerror("Error", "Student not found. Please register first.")
            return

        complaint = {
            "complaint_id": generate_id("CMP"),
            "sap_id": sap,
            "student_name": student["name"],
            "room_no": student.get("room_no", ""),
            "category": self.cmp_category.get(),
            "priority": self.cmp_priority.get(),
            "description": self.cmp_desc.get("1.0", "end").strip(),
            "status": "Pending",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "resolved_on": None,
        }
        complaints_col.insert_one(complaint)
        messagebox.showinfo("Success",
                            f"Complaint filed!\nID: {complaint['complaint_id']}\nCategory: {complaint['category']}")
        self.show_file_complaint()

    # ─── MESS FEEDBACK ───
    def show_mess_feedback(self):
        self._clear_content()
        self._make_header("Mess Feedback", "Rate your meals and share feedback")

        form = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=20)
        form.pack(fill="x", padx=30, pady=10)

        self.fb_sap = self._make_input(form, "Your SAP ID", 0)

        tk.Label(form, text="Meal Type", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=1, column=0, sticky="w", padx=(15, 5), pady=6)
        self.fb_meal = ttk.Combobox(form, values=["Breakfast", "Lunch", "Dinner", "Snacks"],
                                    state="readonly", font=("Segoe UI", 11), width=28)
        self.fb_meal.grid(row=1, column=1, padx=(0, 15), pady=6, sticky="ew")
        self.fb_meal.set("Lunch")

        tk.Label(form, text="Rating (1-5)", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=2, column=0, sticky="w", padx=(15, 5), pady=6)
        self.fb_rating = tk.Scale(form, from_=1, to=5, orient="horizontal",
                                  bg=COLORS["card"], fg=COLORS["text"],
                                  highlightthickness=0, troughcolor=COLORS["input_bg"],
                                  activebackground=COLORS["accent"])
        self.fb_rating.set(3)
        self.fb_rating.grid(row=2, column=1, padx=(0, 15), pady=6, sticky="ew")

        tk.Label(form, text="Comments", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=3, column=0, sticky="nw", padx=(15, 5), pady=6)
        self.fb_comment = scrolledtext.ScrolledText(
            form, font=("Segoe UI", 11), width=40, height=4,
            bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0)
        self.fb_comment.grid(row=3, column=1, padx=(0, 15), pady=6, sticky="ew")

        btn_frame = tk.Frame(self.content, bg=COLORS["bg"])
        btn_frame.pack(pady=15)
        self._make_button(btn_frame, "🍽️ Submit Feedback", self._submit_feedback).pack()

    def _submit_feedback(self):
        sap = self.fb_sap.get().strip()
        if not sap:
            messagebox.showwarning("Validation", "Please enter your SAP ID.")
            return
        student = students_col.find_one({"sap_id": sap})
        if not student:
            messagebox.showerror("Error", "Student not found. Please register first.")
            return

        feedback = {
            "sap_id": sap,
            "student_name": student["name"],
            "meal_type": self.fb_meal.get(),
            "rating": self.fb_rating.get(),
            "comments": self.fb_comment.get("1.0", "end").strip(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        mess_feedback_col.insert_one(feedback)
        messagebox.showinfo("Success", "Mess feedback submitted! Thank you.")
        self.show_mess_feedback()

    # ─── RAGGING REPORT ───
    def show_ragging_report(self):
        self._clear_content()
        self._make_header("Report Ragging Incident", "All reports are kept confidential")

        form = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=20)
        form.pack(fill="x", padx=30, pady=10)

        self.rag_sap = self._make_input(form, "Your SAP ID (optional)", 0)
        self.rag_victim = self._make_input(form, "Victim Name", 1)
        self.rag_accused = self._make_input(form, "Accused Name(s)", 2)
        self.rag_location = self._make_input(form, "Location", 3)

        tk.Label(form, text="Severity", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=4, column=0, sticky="w", padx=(15, 5), pady=6)
        self.rag_severity = ttk.Combobox(form, values=["Minor", "Moderate", "Severe", "Critical"],
                                         state="readonly", font=("Segoe UI", 11), width=28)
        self.rag_severity.grid(row=4, column=1, padx=(0, 15), pady=6, sticky="ew")
        self.rag_severity.set("Moderate")

        tk.Label(form, text="Description", font=("Segoe UI", 10),
                 bg=COLORS["card"], fg=COLORS["text_muted"]).grid(
            row=5, column=0, sticky="nw", padx=(15, 5), pady=6)
        self.rag_desc = scrolledtext.ScrolledText(
            form, font=("Segoe UI", 11), width=40, height=5,
            bg=COLORS["input_bg"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0)
        self.rag_desc.grid(row=5, column=1, padx=(0, 15), pady=6, sticky="ew")

        btn_frame = tk.Frame(self.content, bg=COLORS["bg"])
        btn_frame.pack(pady=15)
        self._make_button(btn_frame, "🚨 Submit Report", self._submit_ragging, "#dc2626").pack()

    def _submit_ragging(self):
        victim = self.rag_victim.get().strip()
        accused = self.rag_accused.get().strip()
        if not victim or not accused:
            messagebox.showwarning("Validation", "Victim and accused names are required.")
            return

        report = {
            "report_id": generate_id("RAG"),
            "reporter_sap": self.rag_sap.get().strip() or "Anonymous",
            "victim_name": victim,
            "accused_names": accused,
            "location": self.rag_location.get().strip(),
            "severity": self.rag_severity.get(),
            "description": self.rag_desc.get("1.0", "end").strip(),
            "status": "Under Investigation",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        ragging_col.insert_one(report)
        messagebox.showinfo("Success", f"Ragging report submitted.\nReport ID: {report['report_id']}")
        self.show_ragging_report()

    # ─── ADMIN: ALL STUDENTS ───
    def show_all_students(self):
        self._clear_content()
        self._make_header("All Registered Students", "View and manage student records")

        table_frame = tk.Frame(self.content, bg=COLORS["card"], padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=10)

        cols = ("Name", "SAP ID", "Room", "Phone", "Course", "Year", "Block")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=18)
        self._style_treeview(tree)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=100)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        students = sorted(students_col.find(), key=lambda x: x.get("name", ""))
        for s in students:
            tree.insert("", "end", values=(
                s.get("name", ""), s.get("sap_id", ""), s.get("room_no", ""),
                s.get("phone", ""), s.get("course", ""), s.get("year", ""),
                s.get("hostel_block", ""),
            ))

        btn_frame = tk.Frame(self.content, bg=COLORS["bg"])
        btn_frame.pack(pady=10)
        self._make_button(btn_frame, "📥 Export to CSV", self._export_students, "#2563eb").pack(side="left", padx=5)
        self._make_button(btn_frame, "🗑️ Delete Student", lambda: self._delete_student(tree), "#dc2626").pack(side="left", padx=5)

    def _export_students(self):
        data = students_col.find()
        if not data:
            messagebox.showinfo("Info", "No student data to export.")
            return
        df = pd.DataFrame(data)
        filename = f"students_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Exported", f"Student data exported to {filename}")

    def _delete_student(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a student to delete.")
            return
        
        # Get the selected student data
        item = selected[0]
        student_data = tree.item(item)["values"]
        student_name = student_data[0]
        sap_id = student_data[1]
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {student_name} (SAP: {sap_id})? This action cannot be undone."
        )
        
        if not confirm:
            return
        
        # Delete the student
        if students_col.delete_one({"sap_id": sap_id}):
            messagebox.showinfo("Success", f"Student {student_name} has been deleted successfully.")
            self.show_all_students()  # Refresh the list
        else:
            messagebox.showerror("Error", "Failed to delete student.")

    # ─── ADMIN: ALL COMPLAINTS ───
    def show_all_complaints(self):
        self._clear_content()
        self._make_header("All Complaints", "Manage and resolve student complaints")

        filter_frame = tk.Frame(self.content, bg=COLORS["bg"])
        filter_frame.pack(fill="x", padx=30, pady=(0, 5))

        tk.Label(filter_frame, text="Filter:", font=("Segoe UI", 10),
                 bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(side="left", padx=(0, 5))
        self.filter_status = ttk.Combobox(filter_frame, values=["All", "Pending", "Resolved", "In Progress"],
                                          state="readonly", font=("Segoe UI", 10), width=12)
        self.filter_status.set("All")
        self.filter_status.pack(side="left", padx=5)

        table_frame = tk.Frame(self.content, bg=COLORS["card"], padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=5)

        cols = ("ID", "Student", "Room", "Category", "Priority", "Status", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        self._style_treeview(tree)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._make_button(filter_frame, "Apply", lambda: self._load_complaints(tree), "#2563eb").pack(side="left", padx=5)

        self._load_complaints(tree)

        action_frame = tk.Frame(self.content, bg=COLORS["bg"])
        action_frame.pack(pady=10)
        self._make_button(action_frame, "✅ Mark Resolved",
                          lambda: self._mark_resolved(tree), COLORS["success"]).pack(side="left", padx=5)
        self._make_button(action_frame, "🔄 Mark In Progress",
                          lambda: self._mark_in_progress(tree), COLORS["warning"]).pack(side="left", padx=5)
        self._make_button(action_frame, "📥 Export CSV",
                          self._export_complaints, "#2563eb").pack(side="left", padx=5)

    def _load_complaints(self, tree):
        tree.delete(*tree.get_children())
        status_filter = self.filter_status.get()
        if status_filter != "All":
            complaints = complaints_col.find({"status": status_filter})
        else:
            complaints = complaints_col.find()

        complaints.reverse()
        for c in complaints:
            tree.insert("", "end", values=(
                c.get("complaint_id", ""), c.get("student_name", ""),
                c.get("room_no", ""), c.get("category", ""),
                c.get("priority", ""), c.get("status", ""), c.get("date", ""),
            ))

    def _mark_resolved(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a complaint to mark as resolved.")
            return
        for item in selected:
            cmp_id = tree.item(item)["values"][0]
            complaints_col.update_one(
                {"complaint_id": str(cmp_id)},
                {"$set": {"status": "Resolved", "resolved_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
            )
        messagebox.showinfo("Updated", f"{len(selected)} complaint(s) marked as Resolved.")
        self._load_complaints(tree)

    def _mark_in_progress(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a complaint.")
            return
        for item in selected:
            cmp_id = tree.item(item)["values"][0]
            complaints_col.update_one(
                {"complaint_id": str(cmp_id)},
                {"$set": {"status": "In Progress"}}
            )
        messagebox.showinfo("Updated", f"{len(selected)} complaint(s) marked as In Progress.")
        self._load_complaints(tree)

    def _export_complaints(self):
        data = complaints_col.find()
        if not data:
            messagebox.showinfo("Info", "No complaints to export.")
            return
        df = pd.DataFrame(data)
        filename = f"complaints_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        messagebox.showinfo("Exported", f"Complaints exported to {filename}")

    # ─── ADMIN: ALL MESS FEEDBACK ───
    def show_all_mess_feedback(self):
        self._clear_content()
        self._make_header("Mess Feedback Overview", "All student mess feedback and ratings")

        table_frame = tk.Frame(self.content, bg=COLORS["card"], padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=10)

        cols = ("Student", "SAP ID", "Meal", "Rating", "Comments", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        self._style_treeview(tree)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120)
        tree.column("Comments", width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        feedback = mess_feedback_col.find()
        feedback.reverse()
        for f in feedback:
            tree.insert("", "end", values=(
                f.get("student_name", ""), f.get("sap_id", ""),
                f.get("meal_type", ""), f.get("rating", ""),
                str(f.get("comments", ""))[:50], f.get("date", ""),
            ))

        summary = tk.Frame(self.content, bg=COLORS["card"], padx=15, pady=15)
        summary.pack(fill="x", padx=30, pady=10)
        tk.Label(summary, text="📊 Average Ratings by Meal", font=("Segoe UI", 13, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 8))

        results = mess_feedback_col.aggregate_group("meal_type", "rating")
        for result in results:
            meal = result["_id"]
            avg = result.get("avg_rating", 0)
            count = result["count"]
            stars = "⭐" * round(avg)
            tk.Label(summary,
                     text=f"{meal}: {avg:.1f}/5 {stars}  ({count} reviews)",
                     font=("Segoe UI", 11), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")

    # ─── ADMIN: ALL RAGGING REPORTS ───
    def show_all_ragging(self):
        self._clear_content()
        self._make_header("Ragging Reports", "⚠️ Confidential – Handle with care")

        table_frame = tk.Frame(self.content, bg=COLORS["card"], padx=10, pady=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=10)

        cols = ("ID", "Victim", "Accused", "Severity", "Location", "Status", "Date")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)
        self._style_treeview(tree)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=110)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        reports = ragging_col.find()
        reports.reverse()
        for r in reports:
            tree.insert("", "end", values=(
                r.get("report_id", ""), r.get("victim_name", ""),
                r.get("accused_names", ""), r.get("severity", ""),
                r.get("location", ""), r.get("status", ""), r.get("date", ""),
            ))

        action_frame = tk.Frame(self.content, bg=COLORS["bg"])
        action_frame.pack(pady=10)
        self._make_button(action_frame, "✅ Mark Resolved",
                          lambda: self._resolve_ragging(tree), COLORS["success"]).pack(side="left", padx=5)

    def _resolve_ragging(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select", "Please select a report.")
            return
        for item in selected:
            rid = tree.item(item)["values"][0]
            ragging_col.update_one(
                {"report_id": str(rid)},
                {"$set": {"status": "Resolved"}}
            )
        messagebox.showinfo("Updated", "Report(s) marked as resolved.")
        self.show_all_ragging()

    # ─── ADMIN: ANALYTICS ───
    def show_analytics(self):
        self._clear_content()
        self._make_header("Analytics Dashboard", "Visual insights using Matplotlib & NumPy")

        if not MATPLOTLIB_AVAILABLE:
            # Fallback: Show text-based statistics
            stats_frame = tk.Frame(self.content, bg=COLORS["card"], padx=20, pady=20)
            stats_frame.pack(fill="both", expand=True, padx=30, pady=10)
            
            tk.Label(stats_frame, text="📊 Analytics Summary", font=("Segoe UI", 14, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, 15))
            
            # Complaints by Category
            cat_data = complaints_col.aggregate_group("category")
            tk.Label(stats_frame, text="Complaints by Category:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(10, 5))
            if cat_data:
                for cat in cat_data:
                    tk.Label(stats_frame, text=f"  • {cat['_id']}: {cat['count']} complaints",
                             font=("Segoe UI", 10), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            else:
                tk.Label(stats_frame, text="  No data available", font=("Segoe UI", 10),
                         bg=COLORS["card"], fg=COLORS["text_muted"]).pack(anchor="w")
            
            # Complaint Status
            status_data = complaints_col.aggregate_group("status")
            tk.Label(stats_frame, text="\nComplaint Status:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(10, 5))
            if status_data:
                for status in status_data:
                    percentage = (status["count"] / complaints_col.count_documents() * 100) if complaints_col.count_documents() > 0 else 0
                    tk.Label(stats_frame, text=f"  • {status['_id']}: {status['count']} ({percentage:.1f}%)",
                             font=("Segoe UI", 10), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            else:
                tk.Label(stats_frame, text="  No data available", font=("Segoe UI", 10),
                         bg=COLORS["card"], fg=COLORS["text_muted"]).pack(anchor="w")
            
            # Mess Feedback
            all_feedback = mess_feedback_col.find()
            ratings = [f["rating"] for f in all_feedback if "rating" in f]
            tk.Label(stats_frame, text="\nMess Feedback:", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(10, 5))
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                tk.Label(stats_frame, text=f"  • Average Rating: {avg_rating:.1f}/5 ⭐",
                         font=("Segoe UI", 10), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
                tk.Label(stats_frame, text=f"  • Total Reviews: {len(ratings)}",
                         font=("Segoe UI", 10), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            else:
                tk.Label(stats_frame, text="  No reviews yet", font=("Segoe UI", 10),
                         bg=COLORS["card"], fg=COLORS["text_muted"]).pack(anchor="w")
            
            # Daily Stats
            tk.Label(stats_frame, text="\nDaily Complaints (Last 7 Days):", font=("Segoe UI", 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["accent"]).pack(anchor="w", pady=(10, 5))
            for i in range(6, -1, -1):
                d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                count = complaints_col.count_documents({"date": d})
                date_label = d[5:] if i > 0 else "Today"
                tk.Label(stats_frame, text=f"  • {date_label}: {count} complaints",
                         font=("Segoe UI", 10), bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            
            return

        fig, axes = plt.subplots(2, 2, figsize=(10, 6), facecolor=COLORS["bg"])
        fig.subplots_adjust(hspace=0.4, wspace=0.3)

        for ax in axes.flat:
            ax.set_facecolor(COLORS["sidebar"])
            ax.tick_params(colors=COLORS["text_muted"], labelsize=8)
            for spine in ax.spines.values():
                spine.set_color(COLORS["input_border"])

        # 1. Complaints by Category
        cat_data = complaints_col.aggregate_group("category")
        if cat_data:
            categories = [d["_id"] for d in cat_data]
            counts = np.array([d["count"] for d in cat_data])
            colors_bar = plt.cm.Set2(np.linspace(0, 1, len(categories)))
            axes[0, 0].barh(categories, counts, color=colors_bar)
        else:
            axes[0, 0].text(0.5, 0.5, "No Data", ha="center", va="center", color=COLORS["text_muted"])
        axes[0, 0].set_title("Complaints by Category", color=COLORS["text"], fontsize=10)

        # 2. Complaint Status Pie
        status_data = complaints_col.aggregate_group("status")
        if status_data:
            labels = [d["_id"] for d in status_data]
            sizes = [d["count"] for d in status_data]
            pie_colors = ["#2ecc71", "#f39c12", "#e94560", "#3498db"]
            axes[0, 1].pie(sizes, labels=labels, colors=pie_colors[:len(labels)],
                           autopct="%1.0f%%", textprops={"color": COLORS["text"], "fontsize": 8})
        else:
            axes[0, 1].text(0.5, 0.5, "No Data", ha="center", va="center", color=COLORS["text_muted"])
        axes[0, 1].set_title("Complaint Status", color=COLORS["text"], fontsize=10)

        # 3. Mess Rating Distribution
        all_feedback = mess_feedback_col.find()
        ratings = [f["rating"] for f in all_feedback if "rating" in f]
        if ratings:
            ratings_np = np.array(ratings)
            axes[1, 0].hist(ratings_np, bins=[0.5, 1.5, 2.5, 3.5, 4.5, 5.5],
                            color=COLORS["accent"], edgecolor=COLORS["bg"], rwidth=0.8)
            axes[1, 0].set_xlabel("Rating", color=COLORS["text_muted"], fontsize=8)
            axes[1, 0].set_ylabel("Count", color=COLORS["text_muted"], fontsize=8)
            mean_rating = np.mean(ratings_np)
            axes[1, 0].axvline(mean_rating, color="#2ecc71", linestyle="--", label=f"Mean: {mean_rating:.1f}")
            axes[1, 0].legend(fontsize=7, facecolor=COLORS["sidebar"], edgecolor=COLORS["input_border"],
                              labelcolor=COLORS["text"])
        axes[1, 0].set_title("Mess Rating Distribution", color=COLORS["text"], fontsize=10)

        # 4. Daily Complaints (7 days)
        dates = []
        daily_counts = []
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            count = complaints_col.count_documents({"date": d})
            dates.append(d[5:])
            daily_counts.append(count)

        daily_np = np.array(daily_counts)
        axes[1, 1].plot(dates, daily_np, marker="o", color=COLORS["accent"], linewidth=2, markersize=6)
        axes[1, 1].fill_between(dates, daily_np, alpha=0.2, color=COLORS["accent"])
        axes[1, 1].set_title("Daily Complaints (7 days)", color=COLORS["text"], fontsize=10)
        axes[1, 1].tick_params(axis="x", rotation=45)

        canvas_frame = tk.Frame(self.content, bg=COLORS["bg"])
        canvas_frame.pack(fill="both", expand=True, padx=30, pady=10)
        canvas = FigureCanvasTkAgg(fig, canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ─── TREEVIEW STYLING ───
    def _style_treeview(self, tree):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=COLORS["table_row1"],
                        foreground=COLORS["text"],
                        fieldbackground=COLORS["table_row1"],
                        font=("Segoe UI", 10),
                        rowheight=28)
        style.configure("Treeview.Heading",
                        background=COLORS["table_header"],
                        foreground=COLORS["text"],
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", COLORS["accent"])])


# ─────────────────────────────────────────────
# Run Application
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = HostelManagementApp(root)
    root.mainloop()