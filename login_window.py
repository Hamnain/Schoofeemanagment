import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from database import check_login

# Colors & Fonts
COLOR_PRIMARY = "#003366"     # Navy Blue
COLOR_SECONDARY = "#F0F0F0"   # Light Gray
COLOR_ACCENT = "#4CAF50"      # Green
COLOR_WHITE = "#FFFFFF"
FONT_ENTRY = ("Segoe UI", 11)

LOGO_PATH = "logo.png"

class LoginWindow:
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success_callback = on_success_callback
        
        # Create a Toplevel window for login
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("School System Login")
        self.login_win.geometry("450x550")
        self.login_win.resizable(False, False)
        self.login_win.configure(bg=COLOR_SECONDARY)
        
        # Handle close
        self.login_win.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.center_window()
        self._create_ui()

    def center_window(self):
        self.login_win.update_idletasks()
        width = self.login_win.winfo_width()
        height = self.login_win.winfo_height()
        x = (self.login_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.login_win.winfo_screenheight() // 2) - (height // 2)
        self.login_win.geometry(f'{width}x{height}+{x}+{y}')

    def _create_ui(self):
        # Main Container (Card style)
        main_frame = tk.Frame(self.login_win, bg=COLOR_WHITE, relief=tk.RIDGE, bd=1)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        # Logo
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((100, 100))
                self.logo_img = ImageTk.PhotoImage(img)
                tk.Label(main_frame, image=self.logo_img, bg=COLOR_WHITE).pack(pady=(30, 10))
            except: pass
        
        # Title
        tk.Label(main_frame, text="Welcome Back", font=("Segoe UI", 18, "bold"), bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack()
        tk.Label(main_frame, text="Sign in to continue", font=("Segoe UI", 10), bg=COLOR_WHITE, fg="#777").pack(pady=(0, 20))

        # Username Field
        tk.Label(main_frame, text="Username", font=("Segoe UI", 9, "bold"), bg=COLOR_WHITE, fg=COLOR_PRIMARY, anchor="w").pack(fill=tk.X, padx=40)
        self.user_entry = tk.Entry(main_frame, font=FONT_ENTRY, relief=tk.FLAT, bg=COLOR_SECONDARY, bd=5)
        self.user_entry.pack(fill=tk.X, padx=40, pady=5, ipady=3)
        self.user_entry.focus_set()

        # Password Field
        tk.Label(main_frame, text="Password", font=("Segoe UI", 9, "bold"), bg=COLOR_WHITE, fg=COLOR_PRIMARY, anchor="w").pack(fill=tk.X, padx=40, pady=(15, 0))
        self.pass_entry = tk.Entry(main_frame, font=FONT_ENTRY, relief=tk.FLAT, bg=COLOR_SECONDARY, bd=5, show="•")
        self.pass_entry.pack(fill=tk.X, padx=40, pady=5, ipady=3)

        # Login Button
        btn_login = tk.Button(main_frame, text="LOGIN", command=self.verify, 
                              font=("Segoe UI", 11, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE, 
                              activebackground="#002244", activeforeground=COLOR_WHITE,
                              relief=tk.FLAT, cursor="hand2")
        btn_login.pack(fill=tk.X, padx=40, pady=30, ipady=5)
        
        self.login_win.bind('<Return>', lambda event: self.verify())

    def verify(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if check_login(username, password):
            self.login_win.destroy()
            self.on_success_callback()
        else:
            messagebox.showerror("Login Failed", "Invalid Username or Password", parent=self.login_win)

    def on_close(self):
        self.root.destroy()