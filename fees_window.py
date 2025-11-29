import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import os
import calendar 
import webbrowser
import subprocess
import sys
import sqlite3
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.graphics.barcode import code39

# Import ALL database functions
from database import (
    get_students, get_student_by_id, get_challans_by_student_id,
    get_challan_details_by_id, get_unpaid_challans, pay_challan,
    create_challan, get_student_fee_summary, get_classwise_defaulter_list,
    get_classwise_posting_sheet, get_collection_summary,
    get_new_admissions_list, get_struck_off_list, get_active_students
)

# --- CONSTANTS & STYLES ---
MONTH_NAMES = [None, 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
LOGO_PATH = "logo.png"
SETTINGS_FILE = "fee_settings.json"

CLASS_LIST = [
    "Playgroup", "Nursery", "Prep",
    "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
    "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
    "O-Level", "A-Level", "Hifz", "Passed Out"
]

# Define automatic promotion path
PROMOTION_MAP = {
    "Playgroup": "Nursery",
    "Nursery": "Prep",
    "Prep": "Grade 1",
    "Grade 1": "Grade 2",
    "Grade 2": "Grade 3",
    "Grade 3": "Grade 4",
    "Grade 4": "Grade 5",
    "Grade 5": "Grade 6",
    "Grade 6": "Grade 7",
    "Grade 7": "Grade 8",
    "Grade 8": "Grade 9",
    "Grade 9": "Grade 10",
    "Grade 10": "Passed Out",
    "O-Level": "Passed Out",
    "A-Level": "Passed Out",
    "Hifz": "Hifz"
}

COLOR_PRIMARY = "#003366"     # Navy Blue
COLOR_SECONDARY = "#F0F0F0"   # Light Gray
COLOR_ACCENT = "#4CAF50"      # Green
COLOR_WARNING = "#FF9800"     # Orange
COLOR_DANGER = "#F44336"      # Red
COLOR_TEXT = "#333333"
COLOR_WHITE = "#FFFFFF"

FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_ENTRY = ("Segoe UI", 10)

class FeesWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Fee Management & Accounting")
        self.master.geometry("1150x750")
        self.master.grab_set()
        self.master.transient(master.master)
        self.master.configure(bg=COLOR_SECONDARY)

        self.current_student_id = None
        self.current_student_data = None
        self.current_month = datetime.date.today().month
        self.current_year = datetime.date.today().year

        self._setup_styles()
        
        # --- Main Container ---
        self.main_container = tk.Frame(self.master, bg=COLOR_SECONDARY)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Top Section: Title ---
        self.top_section = tk.Frame(self.main_container, bg=COLOR_SECONDARY)
        self.top_section.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        tk.Label(self.top_section, text="Fee & Accounts Management", font=("Segoe UI", 20, "bold"), bg=COLOR_SECONDARY, fg=COLOR_PRIMARY).pack(side=tk.LEFT)

        # --- Tabs ---
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Dashboard
        self.dashboard_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.dashboard_tab, text="Dashboard Overview")
        self._create_dashboard_ui(self.dashboard_tab)

        # Tab 2: Class Wise Fees
        self.class_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.class_tab, text="Class-Wise Status & Generation")
        self._create_class_list_ui(self.class_tab)

        # Tab 3: Manage Individual
        self.individual_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.individual_tab, text="Manage Individual Student")
        self._create_individual_ui(self.individual_tab)

        # Tab 4: Reports
        self.reports_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.reports_tab, text="Accounting Reports")
        self._create_reports_ui(self.reports_tab)
        
        # Tab 5: Auto-Debit
        self.scheduler_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.scheduler_tab, text="Auto-Debit Settings")
        self._create_scheduler_ui(self.scheduler_tab)
        
        # Tab 6: Promotion
        self.promotion_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.promotion_tab, text="Promote Students")
        self._create_promotion_ui(self.promotion_tab)
        
        # Tab 7: Passed Out
        self.passed_out_tab = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.passed_out_tab, text="Passed Out / Alumni")
        self._create_passed_out_ui(self.passed_out_tab)
        
        # Load Data
        self._refresh_dashboard()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=COLOR_SECONDARY)
        style.configure("White.TFrame", background=COLOR_WHITE)
        style.configure("TNotebook", background=COLOR_SECONDARY, tabposition='nw')
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 5], background="#E0E0E0")
        style.map("TNotebook.Tab", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", COLOR_WHITE)])
        style.configure("Treeview", background=COLOR_WHITE, fieldbackground=COLOR_WHITE, foreground=COLOR_TEXT, font=("Segoe UI", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E0E0E0", foreground="black")
        style.map("Treeview", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", COLOR_WHITE)])

    # ===================================================================
    # TAB 1: DASHBOARD
    # ===================================================================
    def _create_dashboard_ui(self, parent):
        container = tk.Frame(parent, bg=COLOR_WHITE)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        cards_frame = tk.Frame(container, bg=COLOR_WHITE)
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        self.card_unpaid = self._make_card(cards_frame, "Total Pending Dues", "Rs. 0", COLOR_DANGER)
        self.card_unpaid.pack(side=tk.LEFT, padx=(0, 20), fill=tk.X, expand=True)
        self.card_paid = self._make_card(cards_frame, "Total Collected", "Rs. 0", COLOR_ACCENT)
        self.card_paid.pack(side=tk.LEFT, fill=tk.X, expand=True)
        list_frame = tk.Frame(container, bg=COLOR_WHITE)
        list_frame.pack(fill=tk.BOTH, expand=True)
        def_frame = tk.LabelFrame(list_frame, text="Top Defaulters", bg=COLOR_WHITE, font=FONT_HEADER, fg=COLOR_DANGER)
        def_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.def_tree = self._create_dash_tree(def_frame, ["ID", "Name", "Class", "Due"])
        clr_frame = tk.LabelFrame(list_frame, text="Recent Payments", bg=COLOR_WHITE, font=FONT_HEADER, fg=COLOR_ACCENT)
        clr_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        self.clr_tree = self._create_dash_tree(clr_frame, ["ID", "Name", "Class", "Contact"])
        tk.Button(container, text="Refresh Dashboard", command=self._refresh_dashboard, bg="#2196F3", fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(pady=10)

    def _create_dash_tree(self, parent, cols):
        tree = ttk.Treeview(parent, columns=cols, show="headings", style="Treeview")
        for c in cols:
            tree.heading(c, text=c)
            if c == "ID": tree.column(c, width=50)
            elif c == "Name": tree.column(c, width=150)
            else: tree.column(c, width=100)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree

    def _make_card(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=color, padx=2, pady=2) 
        inner = tk.Frame(frame, bg="white", padx=20, pady=20)
        inner.pack(fill=tk.BOTH, expand=True)
        tk.Label(inner, text=title, font=("Segoe UI", 12), bg="white", fg="#666").pack(anchor="w")
        lbl = tk.Label(inner, text=value, font=("Segoe UI", 24, "bold"), bg="white", fg=color)
        lbl.pack(anchor="w")
        frame.lbl_val = lbl
        return frame

    def _refresh_dashboard(self):
        for i in self.def_tree.get_children(): self.def_tree.delete(i)
        for i in self.clr_tree.get_children(): self.clr_tree.delete(i)
        data = get_student_fee_summary()
        total_unpaid = 0
        for row in data:
            due = row[4]
            if due > 0:
                total_unpaid += due
                self.def_tree.insert("", "end", values=(row[0], row[1], row[2], f"{due:,.0f}"))
            else:
                self.clr_tree.insert("", "end", values=(row[0], row[1], row[2], row[3]))
        conn = sqlite3.connect('school.db')
        cur = conn.cursor()
        cur.execute("SELECT SUM(total_amount) FROM challans WHERE status='Paid'")
        res = cur.fetchone()[0]
        total_paid = res if res else 0
        conn.close()
        self.card_unpaid.lbl_val.config(text=f"Rs. {total_unpaid:,.0f}")
        self.card_paid.lbl_val.config(text=f"Rs. {total_paid:,.0f}")

    # --- TAB 2: CLASS WISE ---
    def _create_class_list_ui(self, parent):
        paned = tk.PanedWindow(parent, orient=tk.HORIZONTAL, bg=COLOR_SECONDARY, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left = tk.Frame(paned, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        paned.add(left, minsize=200)
        tk.Label(left, text="Select Class", font=FONT_HEADER, bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=10)
        self.class_listbox = tk.Listbox(left, font=("Segoe UI", 11), bg="#FAFAFA", selectbackground=COLOR_PRIMARY, selectforeground="white", relief=tk.FLAT)
        self.class_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        for cls in CLASS_LIST: self.class_listbox.insert(tk.END, cls)
        right = tk.Frame(paned, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        paned.add(right, minsize=600)
        self.class_notebook = ttk.Notebook(right)
        self.class_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tab_cls_gen = tk.Frame(self.class_notebook, bg=COLOR_WHITE)
        self.class_notebook.add(self.tab_cls_gen, text="Student List (Generate)")
        self._setup_class_generate_tab(self.tab_cls_gen)
        self.tab_cls_unpaid = tk.Frame(self.class_notebook, bg=COLOR_WHITE)
        self.class_notebook.add(self.tab_cls_unpaid, text="Unpaid (Due)")
        self.tree_cls_unpaid = self._create_class_status_tree(self.tab_cls_unpaid, "Unpaid")
        self.tab_cls_defaulter = tk.Frame(self.class_notebook, bg=COLOR_WHITE)
        self.class_notebook.add(self.tab_cls_defaulter, text="Defaulters (Overdue)")
        self.tree_cls_defaulter = self._create_class_status_tree(self.tab_cls_defaulter, "Defaulter")
        self.tab_cls_paid = tk.Frame(self.class_notebook, bg=COLOR_WHITE)
        self.class_notebook.add(self.tab_cls_paid, text="Paid History")
        self.tree_cls_paid = self._create_class_status_tree(self.tab_cls_paid, "Paid")
        self.class_listbox.bind("<<ListboxSelect>>", self._load_class_data)

    def _setup_class_generate_tab(self, parent):
        ctrl_frame = tk.Frame(parent, bg="white", pady=10)
        ctrl_frame.pack(fill=tk.X)
        tk.Button(ctrl_frame, text="Select All", command=self.select_all_class_students, bg="#ddd", relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        tk.Button(ctrl_frame, text="Generate Vouchers", command=self.open_class_voucher_window, bg=COLOR_ACCENT, fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(side=tk.RIGHT, padx=5)
        tk.Label(ctrl_frame, text="Select students:", bg="white", font=("Segoe UI", 10, "italic")).pack(side=tk.LEFT, padx=5)
        self.tree_cls_students = ttk.Treeview(parent, columns=("ID", "Name", "Father", "Contact"), show="headings", selectmode="extended", style="Treeview")
        for c in ("ID", "Name", "Father", "Contact"): self.tree_cls_students.heading(c, text=c)
        self.tree_cls_students.column("ID", width=50); self.tree_cls_students.column("Name", width=150)
        self.tree_cls_students.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_class_status_tree(self, parent, tag_name):
        cols = ("ID", "Name", "Challan", "Due", "Amt", "Status")
        tree = ttk.Treeview(parent, columns=cols, show="headings", style="Treeview")
        for c in cols: tree.heading(c, text=c)
        tree.column("ID", width=50); tree.column("Amt", width=80, anchor="e")
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        if tag_name == "Paid": tree.tag_configure("Paid", background="#E8F5E9", foreground="green")
        if tag_name == "Unpaid": tree.tag_configure("Unpaid", background="#FFF3E0", foreground="#E65100")
        if tag_name == "Defaulter": tree.tag_configure("Defaulter", background="#FFEBEE", foreground="#C62828")
        return tree

    def _load_class_data(self, event):
        sel = self.class_listbox.curselection()
        if not sel: return
        cls_name = self.class_listbox.get(sel[0])
        for t in [self.tree_cls_students, self.tree_cls_unpaid, self.tree_cls_defaulter, self.tree_cls_paid]:
            for i in t.get_children(): t.delete(i)
        conn = sqlite3.connect('school.db')
        cur = conn.cursor()
        cur.execute("SELECT student_id, full_name, father_name, contact_details FROM students WHERE class_into_which_admission_is_sought=? AND status='Active'", (cls_name,))
        for s in cur.fetchall(): self.tree_cls_students.insert("", "end", values=s, iid=s[0])
        cur.execute("""SELECT s.student_id, s.full_name, c.challan_id, c.due_date, c.total_amount, c.status 
            FROM challans c JOIN students s ON c.student_id = s.student_id 
            WHERE s.class_into_which_admission_is_sought=? ORDER BY c.due_date DESC""", (cls_name,))
        for c in cur.fetchall():
            sid, name, cid, due_str, amt, status = c
            vals = (sid, name, cid, due_str, f"Rs. {amt:,.0f}", status)
            if status == "Paid": self.tree_cls_paid.insert("", "end", values=vals, tags=("Paid",))
            else:
                try:
                    if datetime.date.today() > datetime.datetime.strptime(due_str, "%Y-%m-%d").date():
                        self.tree_cls_defaulter.insert("", "end", values=vals, tags=("Defaulter",))
                    else: self.tree_cls_unpaid.insert("", "end", values=vals, tags=("Unpaid",))
                except: self.tree_cls_unpaid.insert("", "end", values=vals)
        conn.close()

    def select_all_class_students(self):
        for item in self.tree_cls_students.get_children(): self.tree_cls_students.selection_add(item)
        
    def open_class_voucher_window(self):
        selected = self.tree_cls_students.selection()
        if not selected: return messagebox.showwarning("Info", "Select students first.")
        top = tk.Toplevel(self.master); top.title("Bulk Generate")
        tk.Label(top, text=f"Generate for {len(selected)} Students").pack(pady=10)
        tk.Button(top, text="Confirm & Generate", command=lambda: self._run_bulk_gen(selected, top)).pack(pady=10)
        
    def _run_bulk_gen(self, selected, top):
        issue = datetime.date.today().strftime("%Y-%m-%d")
        due = (datetime.date.today() + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
        for sid in selected:
            create_challan(int(sid), issue, due, "Unpaid", [("Tuition Fee", 5000)], 0, 0)
        messagebox.showinfo("Success", "Generated"); top.destroy(); self.class_listbox.event_generate("<<ListboxSelect>>")
        self._refresh_dashboard()

    # --- TAB 3: MANAGE INDIVIDUAL ---
    def _create_individual_ui(self, parent):
        top = tk.Frame(parent, bg=COLOR_SECONDARY, pady=10); top.pack(fill=tk.X)
        tk.Label(top, text="Search:", bg=COLOR_SECONDARY).pack(side=tk.LEFT, padx=10)
        self.search_entry = tk.Entry(top); self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.filter_students)
        mid = tk.Frame(parent); mid.pack(fill=tk.X)
        self.student_listbox = tk.Listbox(mid, height=5); self.student_listbox.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        self.student_listbox.bind("<<ListboxSelect>>", self.on_student_select)
        self.fee_frame = tk.Frame(parent); self.fee_frame.pack(fill=tk.BOTH, expand=True)
        
    def filter_students(self, event=None):
        search = self.search_entry.get().lower()
        self.student_listbox.delete(0, tk.END)
        for s in get_students(search): self.student_listbox.insert(tk.END, f"ID: {s[0]} - {s[1]}")

    def on_student_select(self, event):
        sel = self.student_listbox.curselection()
        if not sel: return
        self.current_student_id = int(self.student_listbox.get(sel[0]).split(" ")[1])
        self.current_student_data = get_student_by_id(self.current_student_id)
        self._show_challan_ui()

    def _show_challan_ui(self):
        for w in self.fee_frame.winfo_children(): w.destroy()
        ctrl = tk.Frame(self.fee_frame); ctrl.pack(fill=tk.X)
        tk.Button(ctrl, text="Print Challan", command=self.print_challan).pack(side=tk.LEFT)
        tk.Button(ctrl, text="Pay", command=self.record_payment).pack(side=tk.LEFT)
        self.challan_tree = ttk.Treeview(self.fee_frame, columns=("ID", "Issue", "Due", "Total", "Status"), show="headings")
        for c in ("ID", "Issue", "Due", "Total", "Status"): self.challan_tree.heading(c, text=c)
        self.challan_tree.pack(fill=tk.BOTH, expand=True)
        self.load_student_challans()

    def load_student_challans(self):
        for i in self.challan_tree.get_children(): self.challan_tree.delete(i)
        for c in get_challans_by_student_id(self.current_student_id):
             self.challan_tree.insert("", "end", values=(c[0], c[2], c[3], c[6], c[4]))

    def record_payment(self):
        sel = self.challan_tree.selection()
        if sel: 
            pay_challan(int(self.challan_tree.item(sel[0])['values'][0]), datetime.date.today().strftime("%Y-%m-%d"))
            self.load_student_challans()
            self._refresh_dashboard()

    # --- TAB 4: REPORTS ---
    def _create_reports_ui(self, parent):
        tk.Button(parent, text="Defaulters List", command=self.gen_class_defaulter).pack(pady=5)

    def gen_class_defaulter(self):
        data = get_classwise_defaulter_list()
        if not data: return messagebox.showinfo("Info", "No Data")
        # ... generate PDF logic ...

    # --- TAB 5: AUTO DEBIT ---
    def _create_scheduler_ui(self, parent):
        tk.Label(parent, text="Auto-Debit Settings").pack()

    # --- TAB 6: PROMOTION ---
    def _create_promotion_ui(self, parent):
        container = tk.Frame(parent, bg=COLOR_WHITE)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        tk.Label(container, text="Promote Class to Next Level", font=FONT_HEADER, bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=10)
        
        # Selection Frame
        sel_frame = tk.Frame(container, bg=COLOR_WHITE)
        sel_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(sel_frame, text="Select Current Class:", bg=COLOR_WHITE).pack(side=tk.LEFT, padx=10)
        self.promo_class_var = tk.StringVar()
        self.promo_class_cb = ttk.Combobox(sel_frame, textvariable=self.promo_class_var, values=CLASS_LIST[:-1]) 
        self.promo_class_cb.pack(side=tk.LEFT, padx=10)
        self.promo_class_cb.bind("<<ComboboxSelected>>", self._update_promotion_target)
        
        tk.Label(sel_frame, text="Promote To ->", font=("Arial", 12, "bold"), bg=COLOR_WHITE).pack(side=tk.LEFT, padx=20)
        self.promo_target_lbl = tk.Label(sel_frame, text="[Select Class]", font=("Arial", 11, "bold"), fg=COLOR_ACCENT, bg=COLOR_WHITE)
        self.promo_target_lbl.pack(side=tk.LEFT, padx=10)
        
        # Student List
        self.promo_tree = ttk.Treeview(container, columns=("ID", "Name", "Status"), show="headings", selectmode="extended")
        self.promo_tree.heading("ID", text="ID"); self.promo_tree.column("ID", width=50)
        self.promo_tree.heading("Name", text="Name"); self.promo_tree.column("Name", width=200)
        self.promo_tree.heading("Status", text="Current Status")
        self.promo_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Action Button
        btn_frame = tk.Frame(container, bg=COLOR_WHITE)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Promote Selected Students", command=self.run_promotion, bg=COLOR_ACCENT, fg="white", font=("Segoe UI", 11, "bold"), padx=20).pack(side=tk.RIGHT)
        tk.Button(btn_frame, text="Select All", command=self._promo_select_all, bg="#ddd").pack(side=tk.RIGHT, padx=10)

    def _update_promotion_target(self, event):
        current = self.promo_class_var.get()
        target = PROMOTION_MAP.get(current, "Unknown")
        self.promo_target_lbl.config(text=target)
        
        # Load students
        for i in self.promo_tree.get_children(): self.promo_tree.delete(i)
        conn = sqlite3.connect('school.db')
        cur = conn.cursor()
        cur.execute("SELECT student_id, full_name, status FROM students WHERE class_into_which_admission_is_sought=? AND status='Active'", (current,))
        for s in cur.fetchall():
            self.promo_tree.insert("", "end", values=s, iid=s[0])
        conn.close()

    def _promo_select_all(self):
        for item in self.promo_tree.get_children(): self.promo_tree.selection_add(item)

    def run_promotion(self):
        selected = self.promo_tree.selection()
        if not selected: return messagebox.showwarning("Info", "Select students to promote.")
        
        target_class = self.promo_target_lbl.cget("text")
        if target_class == "[Select Class]" or target_class == "Unknown": return
        
        confirm = messagebox.askyesno("Confirm Promotion", f"Promote {len(selected)} students to {target_class}?\nThis will update their class record.")
        if confirm:
            conn = sqlite3.connect('school.db')
            cur = conn.cursor()
            count = 0
            for sid in selected:
                # If target is "Passed Out", we might want to change status too
                if target_class == "Passed Out":
                    cur.execute("UPDATE students SET class_into_which_admission_is_sought=?, status='Passed Out' WHERE student_id=?", (target_class, sid))
                else:
                    cur.execute("UPDATE students SET class_into_which_admission_is_sought=? WHERE student_id=?", (target_class, sid))
                count += 1
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", f"Promoted {count} students.")
            self._update_promotion_target(None) # Refresh list
            self._refresh_passed_out_list() # Update passed out tab

    # --- TAB 7: PASSED OUT ---
    def _create_passed_out_ui(self, parent):
        container = tk.Frame(parent, bg=COLOR_WHITE)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(container, text="Passed Out / Alumni Students", font=FONT_HEADER, bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=10)
        
        cols = ("ID", "Name", "Father Name", "Passed From", "Contact")
        self.po_tree = ttk.Treeview(container, columns=cols, show="headings")
        for c in cols: self.po_tree.heading(c, text=c)
        self.po_tree.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(container, text="Refresh List", command=self._refresh_passed_out_list).pack(pady=10)
        self._refresh_passed_out_list()

    def _refresh_passed_out_list(self):
        for i in self.po_tree.get_children(): self.po_tree.delete(i)
        conn = sqlite3.connect('school.db')
        cur = conn.cursor()
        # We assume students promoted to "Passed Out" have that as class OR status='Passed Out'
        cur.execute("SELECT student_id, full_name, father_name, class_into_which_admission_is_sought, contact_details FROM students WHERE status='Passed Out' OR class_into_which_admission_is_sought='Passed Out'")
        for s in cur.fetchall():
            self.po_tree.insert("", "end", values=s)
        conn.close()

    # --- CHALLAN PRINTING (Using Exact A4 Vertical Logic) ---
    def print_challan(self):
        sel = self.challan_tree.selection()
        if not sel: return
        cid = int(self.challan_tree.item(sel[0])['values'][0])
        
        conn = sqlite3.connect('school.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM challans WHERE challan_id=?", (cid,))
        challan = cur.fetchone()
        cur.execute("SELECT description, amount FROM challan_items WHERE challan_id=?", (cid,))
        items = cur.fetchall()
        conn.close()
        
        if challan[7] > 0: items.append(("Arrears", challan[7]))
        if challan[8] > 0: items.append(("Fine", challan[8]))
        
        unique_10_digit = f"{(1000000000 + cid)}"
        filename = f"Challan_{cid}.pdf"
        
        c = pdfcanvas.Canvas(filename, pagesize=A4)
        width, height = A4
        h_copy = height / 3
        copies = ["Bank Copy", "School Copy", "Student Copy"]
        
        for i in range(3):
            y_start = height - (i * h_copy)
            self._draw_exact_voucher(c, width, h_copy, y_start, copies[i], challan, items, unique_10_digit)
            if i < 2:
                cut_y = y_start - h_copy
                c.setDash(3, 3)
                c.line(0, cut_y, width, cut_y)
                c.setFont("Helvetica", 8)
                c.drawString(10, cut_y + 2, "Cut Here -----------------------------------------------------------------")
                c.setDash()
        
        c.save()
        try: os.startfile(filename)
        except: pass

    def _draw_exact_voucher(self, c, w, h, y_top, copy_name, challan, items, unique_num):
        margin = 0.4 * inch
        content_w = w - (2 * margin)
        s = self.current_student_data # 1:Name, 4:Class, 7:Father, 0:ID
        curr_y = y_top - 0.4 * inch
        
        # Header
        try:
            if os.path.exists(LOGO_PATH):
                c.drawImage(LOGO_PATH, margin, curr_y - 0.4*inch, width=0.6*inch, height=0.6*inch, mask='auto', preserveAspectRatio=True)
        except: pass
        
        c.setFont("Helvetica-Bold", 12); c.drawCentredString(w/2, curr_y, "IIUI SCHOOLS")
        curr_y -= 0.15*inch
        c.setFont("Helvetica", 9); c.drawCentredString(w/2, curr_y, "International Islamic University Islamabad")
        curr_y -= 0.15*inch
        c.setFont("Helvetica-Bold", 10); c.drawCentredString(w/2, curr_y, "Ali Pur Chattha Campus")
        c.setFont("Helvetica-Bold", 9); c.drawRightString(w - margin, y_top - 0.4*inch, copy_name)
        
        curr_y -= 0.3*inch
        c.setFont("Helvetica-Bold", 10); c.drawString(margin, curr_y, "FEE VOUCHER")
        c.drawRightString(w - margin, curr_y, f"Challan No: {unique_num}")
        
        curr_y -= 0.2*inch
        c.setFont("Helvetica", 8); c.drawString(margin, curr_y, "HBL P.M.C Branch, Faisalabad")
        c.drawRightString(w - margin, curr_y, f"Date: {datetime.date.today().strftime('%d-%b-%Y')}")
        
        curr_y -= 0.15*inch
        c.setFont("Helvetica-Bold", 9); c.drawString(margin, curr_y, "A/C No: 13497901233403")
        
        # Student Box
        curr_y -= 0.15*inch
        box_top = curr_y
        box_h = 0.7 * inch
        c.rect(margin, box_top - box_h, content_w, box_h)
        
        ty = box_top - 0.2*inch
        c.setFont("Helvetica", 9); c.drawString(margin+5, ty, "Student:")
        c.setFont("Helvetica-Bold", 9); c.drawString(margin+60, ty, f"{s[1]} S/O {s[7]}")
        
        ty -= 0.2*inch
        c.setFont("Helvetica", 9); c.drawString(margin+5, ty, "Class:")
        c.setFont("Helvetica-Bold", 9); c.drawString(margin+60, ty, s[4])
        c.drawRightString(w-margin-5, ty, f"Roll: {s[0]:04d}")
        
        ty -= 0.2*inch
        due_dt = datetime.datetime.strptime(challan[3], "%Y-%m-%d").strftime("%d-%b-%Y")
        c.setFont("Helvetica", 9); c.drawString(margin+5, ty, "Due Date:")
        c.setFont("Helvetica-Bold", 9); c.drawString(margin+60, ty, due_dt)

        # Table
        curr_y = box_top - box_h - 0.1*inch
        c.setFillColor(colors.lightgrey)
        c.rect(margin, curr_y - 0.2*inch, content_w, 0.2*inch, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(margin+5, curr_y - 0.14*inch, "Description")
        c.drawRightString(w-margin-5, curr_y - 0.14*inch, "Amount (Rs)")
        
        curr_y -= 0.2*inch
        c.setFont("Helvetica", 9)
        for desc, amt in items:
            curr_y -= 0.15*inch
            c.drawString(margin+5, curr_y, desc)
            c.drawRightString(w-margin-5, curr_y, f"{amt:,.0f}")
            
        curr_y -= 0.1*inch
        c.line(margin, curr_y, w-margin, curr_y)
        curr_y -= 0.15*inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin+5, curr_y, "Total Payable")
        c.drawRightString(w-margin-5, curr_y, f"Rs. {challan[6]:,.0f}")
        
        fy = y_top - h + 0.3*inch
        c.setFont("Helvetica", 8)
        c.drawString(margin, fy, "Officer Signature")
        c.drawRightString(w-margin, fy, "Cashier")

    def _open_file(self, filename):
        try: os.startfile(filename)
        except: pass