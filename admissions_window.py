import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
import shutil
import platform
import subprocess

# --- Import libraries for PDF and Images ---
try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    messagebox.showerror("Error", "Pillow library not found!\nPlease run: pip install Pillow")

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Image as ReportLabImage
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    messagebox.showerror("Error", "ReportLab library not found!\nPlease run: pip install reportlab")
# --- End Imports ---

from database import add_student, get_students, update_student, delete_student, get_student_by_id

LOGO_PATH = "logo.png"

# --- DEFINE CLASS LIST HERE ---
CLASS_LIST = [
    "Playgroup", 
    "Nursery", 
    "Prep",
    "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
    "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
    "O-Level", "A-Level", "Hifz"
]

# --- COLORS & FONTS ---
COLOR_PRIMARY = "#003366"     # Navy Blue
COLOR_SECONDARY = "#F0F0F0"   # Light Gray
COLOR_ACCENT = "#4CAF50"      # Green
COLOR_DANGER = "#F44336"      # Red
COLOR_TEXT = "#333333"
COLOR_WHITE = "#FFFFFF"

FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_LABEL = ("Segoe UI", 10)
FONT_ENTRY = ("Segoe UI", 10)

class AdmissionsWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Manage Admissions")
        
        # --- FIX: Maximize window automatically ---
        # This solves the issue of buttons being cut off at the bottom
        try:
            self.master.state('zoomed') # Works on Windows
        except:
            # Fallback for other systems
            w, h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
            self.master.geometry(f"{w}x{h}+0+0")
            
        # --- FIX: Remove 'transient' and 'grab_set' ---
        # Removing these lines restores the Minimize/Maximize buttons in the title bar
        # self.master.grab_set() 
        # self.master.transient(master.master)
        
        self.master.configure(bg=COLOR_SECONDARY)

        self.current_photo_path = None
        self.photo_preview_image = None
        self.current_student_id = None 

        self._setup_styles()

        # --- Main Container ---
        self.main_container = tk.Frame(self.master, bg=COLOR_SECONDARY)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # --- Top Section: Title & Search ---
        self.top_section = tk.Frame(self.main_container, bg=COLOR_SECONDARY)
        self.top_section.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))
        
        tk.Label(self.top_section, text="Student Admission Management", font=("Segoe UI", 20, "bold"), bg=COLOR_SECONDARY, fg=COLOR_PRIMARY).pack(side=tk.LEFT)

        # Search Bar (Right aligned)
        search_frame = tk.Frame(self.top_section, bg=COLOR_SECONDARY)
        search_frame.pack(side=tk.RIGHT)
        tk.Label(search_frame, text="Search Name:", font=FONT_LABEL, bg=COLOR_SECONDARY).pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.load_students)


        # --- Middle Section: Form & Photo (Left) vs List (Right) ---
        self.content_pane = tk.PanedWindow(self.main_container, orient=tk.HORIZONTAL, bg=COLOR_SECONDARY, sashwidth=5)
        self.content_pane.pack(fill=tk.BOTH, expand=True)

        # Left Side: The Form Notebook
        self.left_panel = tk.Frame(self.content_pane, bg=COLOR_SECONDARY)
        self.content_pane.add(self.left_panel, minsize=600)

        self._create_notebook_ui()
        self._create_buttons_ui()

        # Right Side: The Treeview List
        self.right_panel = tk.Frame(self.content_pane, bg=COLOR_WHITE, bd=1, relief=tk.RIDGE)
        self.content_pane.add(self.right_panel, minsize=400)
        
        self._create_treeview()

        self.load_students() 

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styling
        style.configure("TFrame", background=COLOR_SECONDARY)
        style.configure("White.TFrame", background=COLOR_WHITE)
        
        # Notebook styling
        style.configure("TNotebook", background=COLOR_SECONDARY, tabposition='nw')
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[15, 5], background="#E0E0E0")
        style.map("TNotebook.Tab", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", COLOR_WHITE)])

        # Label styling
        style.configure("TLabel", background=COLOR_WHITE, font=FONT_LABEL, foreground=COLOR_TEXT)
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"), foreground=COLOR_PRIMARY, background=COLOR_WHITE)

        # Entry styling
        style.configure("TEntry", padding=5)

        # Treeview styling
        style.configure("Treeview", 
                        background=COLOR_WHITE,
                        fieldbackground=COLOR_WHITE,
                        foreground=COLOR_TEXT,
                        font=("Segoe UI", 10),
                        rowheight=25)
        style.configure("Treeview.Heading", 
                        font=("Segoe UI", 10, "bold"), 
                        background="#E0E0E0", 
                        foreground="black")
        style.map("Treeview", background=[("selected", COLOR_PRIMARY)], foreground=[("selected", COLOR_WHITE)])

    def _create_notebook_ui(self):
        self.notebook = ttk.Notebook(self.left_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(0, 10))

        # Tab 1: Student & Parent
        self.tab1 = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.tab1, text="Student & Parent Details")
        
        # Use grid layout inside tab for better alignment
        form_container = ttk.Frame(self.tab1, style="White.TFrame")
        form_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # --- Photo Section ---
        self.photo_frame = tk.Frame(form_container, bg=COLOR_WHITE, bd=1, relief=tk.RIDGE)
        self.photo_frame.place(relx=1.0, rely=0.0, anchor="ne", width=140, height=180)
        
        self.photo_lbl = tk.Label(self.photo_frame, text="No Photo", bg="#F5F5F5", fg="#888888")
        self.photo_lbl.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        btn_upload = tk.Button(self.photo_frame, text="Upload Photo", command=self.upload_photo, 
                               bg="#E0E0E0", relief=tk.FLAT, font=("Segoe UI", 8))
        btn_upload.pack(fill=tk.X, side=tk.BOTTOM)

        # --- Form Fields ---
        self._build_form_fields(form_container)
        
        # Tab 2: Additional Info
        self.tab2 = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.tab2, text="Additional Info & Status")
        self._build_additional_fields(self.tab2)

        # Tab 3: Class Lists
        self.tab3 = ttk.Frame(self.notebook, style="White.TFrame")
        self.notebook.add(self.tab3, text="Class Lists")
        self._build_class_lists_tab(self.tab3)

    def _build_form_fields(self, parent):
        self.entries = {}
        
        # --- Section Header: Student ---
        ttk.Label(parent, text="Student Information", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        labels_1 = ["Full Name", "Date of Birth", "Place of Birth", "Class", "Last School", "Reason for Leaving"]
        
        curr_row = 1
        for text in labels_1:
            ttk.Label(parent, text=text).grid(row=curr_row, column=0, sticky="w", pady=5)
            
            key = text.lower().replace(" ", "_")
            
            if text == "Class":
                e = ttk.Combobox(parent, values=CLASS_LIST, width=38)
            else:
                e = ttk.Entry(parent, width=40)
            
            e.grid(row=curr_row, column=1, sticky="w", padx=(10, 0), pady=5)
            self.entries[key] = e
            curr_row += 1

        # --- Section Header: Parents ---
        ttk.Label(parent, text="Parent / Guardian Information", style="Header.TLabel").grid(row=curr_row, column=0, sticky="w", pady=(20, 10))
        curr_row += 1
        
        labels_2 = ["Father Name", "Father Occupation", "Father Address", "Mother Name", "Mother Occupation", 
                  "Mother Address", "Guardian", "Res Address", "Contact"]
        
        for text in labels_2:
            ttk.Label(parent, text=text).grid(row=curr_row, column=0, sticky="w", pady=5)
            key = text.lower().replace(" ", "_")
            e = ttk.Entry(parent, width=40)
            e.grid(row=curr_row, column=1, sticky="w", padx=(10, 0), pady=5)
            self.entries[key] = e
            curr_row += 1

    def _build_additional_fields(self, parent_tab):
        container = ttk.Frame(parent_tab, style="White.TFrame", padding=30)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Grid layout
        ttk.Label(container, text="Siblings in School:", style="Header.TLabel").grid(row=0, column=0, sticky="w", pady=(0,5))
        self.entries['siblings'] = ttk.Entry(container, width=50)
        self.entries['siblings'].grid(row=1, column=0, sticky="w", pady=(0, 20))
        
        ttk.Label(container, text="Medical Information (Allergies, etc.):", style="Header.TLabel").grid(row=2, column=0, sticky="w", pady=(0,5))
        self.entries['medical'] = ttk.Entry(container, width=50)
        self.entries['medical'].grid(row=3, column=0, sticky="w", pady=(0, 20))
        
        ttk.Label(container, text="Admission Date (YYYY-MM-DD):", style="Header.TLabel").grid(row=4, column=0, sticky="w", pady=(0,5))
        self.entries['adm_date'] = ttk.Entry(container, width=25)
        self.entries['adm_date'].insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entries['adm_date'].grid(row=5, column=0, sticky="w", pady=(0, 20))
        
        ttk.Label(container, text="Student Status:", style="Header.TLabel").grid(row=6, column=0, sticky="w", pady=(0,5))
        self.status_var = tk.StringVar(value="Active")
        status_cb = ttk.OptionMenu(container, self.status_var, "Active", "Active", "Inactive", "Withdrawn", "Graduated")
        status_cb.grid(row=7, column=0, sticky="w")

    def _build_class_lists_tab(self, parent_tab):
        # Split pane inside the tab
        paned = tk.PanedWindow(parent_tab, orient=tk.HORIZONTAL, bg=COLOR_SECONDARY, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Classes List
        left_frame = tk.Frame(paned, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        paned.add(left_frame, minsize=150)
        
        tk.Label(left_frame, text="Select Class", font=FONT_HEADER, bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=5)
        
        self.class_listbox = tk.Listbox(left_frame, font=("Segoe UI", 11), bg="#FAFAFA", selectbackground=COLOR_ACCENT, selectforeground="white", relief=tk.FLAT)
        self.class_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for cls in CLASS_LIST:
            self.class_listbox.insert(tk.END, cls)
            
        # Right: Students Treeview
        right_frame = tk.Frame(paned, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        paned.add(right_frame, minsize=400)
        
        tk.Label(right_frame, text="Students in Section", font=FONT_HEADER, bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=5)
        
        cols = ("ID", "Name", "Father Name", "Contact")
        self.class_tree = ttk.Treeview(right_frame, columns=cols, show="headings", style="Treeview")
        
        self.class_tree.column("ID", width=50, anchor="center")
        self.class_tree.column("Name", width=150)
        self.class_tree.column("Father Name", width=150)
        self.class_tree.column("Contact", width=120)
        
        for c in cols: self.class_tree.heading(c, text=c)
        
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=self.class_tree.yview)
        self.class_tree.configure(yscrollcommand=scrollbar.set)
        
        self.class_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Logic to load students when class is selected
        self.class_listbox.bind("<<ListboxSelect>>", self.load_students_by_class)

    def load_students_by_class(self, event):
        sel = self.class_listbox.curselection()
        if not sel: return
        
        selected_class = self.class_listbox.get(sel[0])
        
        # Clear tree
        for item in self.class_tree.get_children(): 
            self.class_tree.delete(item)
        
        # Get all students and filter
        all_students = get_students("") 
        
        for s in all_students:
            if s[4] == selected_class: # Check class match
                    self.class_tree.insert("", tk.END, values=(s[0], s[1], s[7], s[15]))

    def _create_treeview(self):
        # Title for list
        header_frame = tk.Frame(self.right_panel, bg=COLOR_PRIMARY, height=30)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="Registered Students", bg=COLOR_PRIMARY, fg=COLOR_WHITE, font=("Segoe UI", 10, "bold")).pack(pady=5)

        cols = ("ID", "Name", "Class", "Father", "Contact")
        self.tree = ttk.Treeview(self.right_panel, columns=cols, show="headings", style="Treeview")
        
        # Columns
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Name", width=120)
        self.tree.column("Class", width=70)
        self.tree.column("Father", width=120)
        self.tree.column("Contact", width=100)
        
        for c in cols: 
            self.tree.heading(c, text=c)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.right_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        self.tree.bind("<Double-1>", self.edit_student)
        self.tree.bind("<<TreeviewSelect>>", self.select_student)

    def _create_buttons_ui(self):
        # Button Bar at the bottom of Left Panel
        btn_bar = tk.Frame(self.left_panel, bg=COLOR_SECONDARY, pady=10)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Custom Button Style helper
        def make_btn(parent, text, cmd, bg_color, fg_color="white"):
            return tk.Button(parent, text=text, command=cmd, 
                             bg=bg_color, fg=fg_color, 
                             font=("Segoe UI", 10, "bold"), 
                             relief=tk.FLAT, bd=0, padx=15, pady=8, cursor="hand2")

        # Left aligned buttons
        make_btn(btn_bar, "New / Clear", self.clear_form, "#757575").pack(side=tk.LEFT, padx=(0, 5))
        make_btn(btn_bar, "Delete", self.delete_student, COLOR_DANGER).pack(side=tk.LEFT, padx=5)
        
        # Right aligned buttons
        make_btn(btn_bar, "Print Form", self.print_form, "#2196F3").pack(side=tk.RIGHT, padx=(5, 0))
        make_btn(btn_bar, "Save Student", self.save_student, COLOR_ACCENT).pack(side=tk.RIGHT, padx=5)

    # --- LOGIC FUNCTIONS ---

    def upload_photo(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if f:
            self.current_photo_path = f
            self.show_photo(f)

    def show_photo(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((140, 180))
            self.photo_preview_image = ImageTk.PhotoImage(img)
            self.photo_lbl.config(image=self.photo_preview_image, text="")
        except Exception as e: 
            print(e)
            self.photo_lbl.config(image="", text="Error")

    def select_student(self, event):
        try:
            item = self.tree.selection()[0]
            self.current_student_id = int(self.tree.item(item, "values")[0])
        except: self.current_student_id = None

    def load_students(self, event=None):
        for i in self.tree.get_children(): self.tree.delete(i)
        term = self.search_entry.get()
        for s in get_students(term):
            self.tree.insert("", tk.END, values=(s[0], s[1], s[4], s[7], s[15]))

    def save_student(self):
        d = self.entries
        data_list = [
            d['full_name'].get(), d['date_of_birth'].get(), d['place_of_birth'].get(), d['class'].get(),
            d['last_school'].get(), d['reason_for_leaving'].get(), d['father_name'].get(), d['father_occupation'].get(),
            d['father_address'].get(), d['mother_name'].get(), d['mother_occupation'].get(), d['mother_address'].get(),
            d['guardian'].get(), d['res_address'].get(), d['contact'].get(), d['siblings'].get(), d['medical'].get(),
            d['adm_date'].get(), self.status_var.get()
        ]
        
        if not data_list[0] or not data_list[3]:
            messagebox.showerror("Error", "Name and Class are mandatory.")
            return

        if self.current_student_id:
            old_data = get_student_by_id(self.current_student_id)
            final_photo = old_data[20]
            if self.current_photo_path and self.current_photo_path != final_photo:
                os.makedirs("student_photos", exist_ok=True)
                ext = os.path.splitext(self.current_photo_path)[1]
                final_photo = f"student_photos/student_{self.current_student_id}{ext}"
                shutil.copy(self.current_photo_path, final_photo)
            update_student(self.current_student_id, *data_list, final_photo)
            messagebox.showinfo("Success", "Student Updated")
        else:
            new_id = add_student(*data_list, None)
            if self.current_photo_path:
                os.makedirs("student_photos", exist_ok=True)
                ext = os.path.splitext(self.current_photo_path)[1]
                final_photo = f"student_photos/student_{new_id}{ext}"
                shutil.copy(self.current_photo_path, final_photo)
                update_student(new_id, *data_list, final_photo)
            messagebox.showinfo("Success", "Student Added")
            
        self.clear_form()
        self.load_students()

    def edit_student(self, event=None):
        if not self.current_student_id: return
        s = get_student_by_id(self.current_student_id)
        if not s: return
        
        self.clear_form()
        self.current_student_id = s[0]
        
        key_order = ['full_name', 'date_of_birth', 'place_of_birth', 'class', 'last_school', 'reason_for_leaving',
                     'father_name', 'father_occupation', 'father_address', 'mother_name', 'mother_occupation', 'mother_address',
                     'guardian', 'res_address', 'contact', 'siblings', 'medical', 'adm_date']
        
        for i, key in enumerate(key_order):
            if key == 'class':
                 self.entries[key].set(s[i+1] or "")
            else:
                 self.entries[key].delete(0, tk.END)
                 self.entries[key].insert(0, s[i+1] or "")
            
        self.status_var.set(s[19] or "Active")
        
        photo_path = s[20]
        if photo_path and os.path.exists(photo_path):
            self.current_photo_path = photo_path
            self.show_photo(photo_path)

    def delete_student(self):
        if self.current_student_id and messagebox.askyesno("Confirm", "Delete this student?"):
            delete_student(self.current_student_id)
            self.clear_form()
            self.load_students()

    def clear_form(self):
        self.current_student_id = None
        self.current_photo_path = None
        self.photo_lbl.config(image="", text="No Photo")
        for e in self.entries.values(): 
             e.delete(0, tk.END)
             if isinstance(e, ttk.Combobox): e.set("")
        self.status_var.set("Active")
        self.entries['adm_date'].insert(0, datetime.date.today().strftime("%Y-%m-%d"))

    def print_form(self):
        if not self.current_student_id: 
            messagebox.showwarning("Select", "Please select a student to print.")
            return
        s = get_student_by_id(self.current_student_id)
        fname = f"{s[1].replace(' ', '_')}_AdmissionForm.pdf"
        try:
            c = canvas.Canvas(fname, pagesize=A4)
            c.setTitle(f"{s[1]} ({s[0]}) - Admission Form")
            w, h = A4
            margin = 40
            try:
                if os.path.exists(LOGO_PATH):
                    c.drawImage(LOGO_PATH, margin, h - 100, width=80, height=80, mask='auto', preserveAspectRatio=True)
            except: pass
            
            c.setFont("Helvetica-Bold", 18)
            c.setFillColorRGB(0, 0.2, 0.4)
            c.drawString(margin + 100, h - 50, "INTERNATIONAL ISLAMIC UNIVERSITY")
            c.drawString(margin + 100, h - 75, "ISLAMABAD SCHOOLS")
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.black)
            c.drawString(margin + 100, h - 95, "Ali Pur Chatha Campus")
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(margin + 100, h - 110, "Student Admission Form")
            
            photo_x = w - margin - 100
            photo_y = h - 140
            c.rect(photo_x, photo_y, 100, 120)
            if s[20] and os.path.exists(s[20]):
                try: c.drawImage(s[20], photo_x, photo_y, width=100, height=120, preserveAspectRatio=True)
                except: c.drawString(photo_x + 10, photo_y + 60, "Photo Error")
            else:
                c.setFont("Helvetica", 8)
                c.drawCentredString(photo_x + 50, photo_y + 60, "Passport Size Photo")

            y_pos = h - 160
            def draw_section_header(title, y):
                c.setFillColorRGB(0.9, 0.9, 0.9)
                c.rect(margin, y, w - 2*margin, 20, fill=1, stroke=0)
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 11)
                c.drawString(margin + 10, y + 6, title)
                return y - 25

            def draw_field_row(labels_values, y):
                x_curr = margin
                col_width = (w - 2*margin) / len(labels_values)
                for lbl, val in labels_values:
                    c.setFont("Helvetica-Bold", 9)
                    c.drawString(x_curr, y, lbl)
                    c.setFont("Helvetica", 10)
                    val_str = str(val) if val else ""
                    c.drawString(x_curr, y - 15, val_str)
                    c.setStrokeColor(colors.lightgrey)
                    c.line(x_curr, y - 18, x_curr + col_width - 20, y - 18)
                    x_curr += col_width
                return y - 35

            y_pos = draw_section_header("STUDENT INFORMATION", y_pos)
            y_pos = draw_field_row([("Full Name:", s[1]), ("Date of Birth:", s[2])], y_pos)
            y_pos = draw_field_row([("Place of Birth:", s[3]), ("Admission Date:", s[18])], y_pos)
            y_pos = draw_field_row([("Class Admitted:", s[4]), ("Student ID:", s[0])], y_pos)
            y_pos -= 10
            y_pos = draw_section_header("PREVIOUS EDUCATION", y_pos)
            y_pos = draw_field_row([("Last School Attended:", s[5])], y_pos)
            y_pos = draw_field_row([("Reason for Leaving:", s[6])], y_pos)
            y_pos -= 10
            y_pos = draw_section_header("PARENT / GUARDIAN INFORMATION", y_pos)
            y_pos = draw_field_row([("Father's Name:", s[7]), ("Occupation:", s[8])], y_pos)
            y_pos = draw_field_row([("Father's Office Address:", s[9])], y_pos)
            y_pos -= 5
            y_pos = draw_field_row([("Mother's Name:", s[10]), ("Occupation:", s[11])], y_pos)
            y_pos = draw_field_row([("Mother's Office Address:", s[12])], y_pos)
            if s[13]: y_pos = draw_field_row([("Guardian Name:", s[13])], y_pos)
            y_pos -= 10
            y_pos = draw_section_header("CONTACT DETAILS", y_pos)
            y_pos = draw_field_row([("Residential Address:", s[14])], y_pos)
            y_pos = draw_field_row([("Emergency Contact:", s[15])], y_pos)
            y_pos -= 10
            y_pos = draw_section_header("ADDITIONAL INFORMATION", y_pos)
            y_pos = draw_field_row([("Siblings in School:", s[16])], y_pos)
            y_pos = draw_field_row([("Medical Information:", s[17])], y_pos)

            c.setStrokeColor(colors.black)
            y_pos -= 20
            c.rect(margin, y_pos - 60, w - 2*margin, 60)
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margin + 10, y_pos - 20, "FOR OFFICE USE ONLY")
            c.setFont("Helvetica", 9)
            c.drawString(margin + 10, y_pos - 45, "Status: " + (s[19] or ""))
            c.drawString(margin + 200, y_pos - 45, "Approved By: __________________")
            c.drawString(margin + 400, y_pos - 45, "Date: __________________")

            c.setFont("Helvetica-Oblique", 8)
            c.drawCentredString(w/2, 30, "This is a computer generated document.")

            c.showPage() 
            text = c.beginText(margin, h - margin - 20)
            text.setFont("Helvetica", 10)
            text.setLeading(14)
            terms_content = """
            TERMS & CONDITIONS
            
            Note: Parents are requested to carefully read the following before signing the form.
            
            1. Admission Fee Challan will be issued by the school. No cash payment will be accepted.
            2. Parents are requested to submit copies of admission fee challan in the school.
            3. Fees are charged on monthly basis, except at the time of admission or summer vacations (i.e. June & July).
            4. Monthly tuition fee is payable in advance by the 10th of each month. After due date a daily fine of Rs. 10/- will be charged.
            5. Final date of payment of monthly tuition fee is the last day of each month thereafter name of the student will be struck off.
            6. Original school leaving certificate will only be issued against written request.
            7. School management takes utmost care about safety of all the children. School management shall take no responsibility in case of any accident.
            8. Parents are requested to cooperate with the school management and admissions are made on the basis of merit.
            9. In case, the child remains absent from school for consecutive five days without intimation, the name of the child will be struck off.
            
            CERTIFICATE FROM THE PARENTS
            
            1. I certified that the particulars, especially date of birth given is correct to the best of my knowledge or belief.
            2. I have read and understood above instructions, rules about payment of fees and will abide by them.
            3. I understand that the admission will be provisional.
            4. I understand that the annual re-admission of this section will be determined through periodical evaluation by the Headmistress.
            """
            for line in terms_content.split('\n'): text.textLine(line.strip())
            c.drawText(text)
            y_sig = h - margin - 400
            c.line(margin, y_sig, margin + 200, y_sig)
            c.drawString(margin, y_sig - 15, "Name of Parent/Guardian")
            c.line(w - margin - 200, y_sig, w - margin, y_sig)
            c.drawString(w - margin - 200, y_sig - 15, "Signature of Parent/Guardian")
            c.save()
            
            try: 
                if platform.system() == "Windows": os.startfile(fname)
                else: subprocess.call(["open", fname])
            except: pass
        except Exception as e:
            messagebox.showerror("PDF Error", f"Could not create PDF: {e}")