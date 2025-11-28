import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk 
import os

from admissions_window import AdmissionsWindow
from fees_window import FeesWindow
from login_window import LoginWindow
from database import check_login, update_password # Added database imports

# --- COLORS & FONTS ---
COLOR_PRIMARY = "#003366"     # Navy Blue
COLOR_SECONDARY = "#F0F0F0"   # Light Gray
COLOR_ACCENT = "#4CAF50"      # Green
COLOR_WHITE = "#FFFFFF"
COLOR_TEXT = "#333333"

LOGO_PATH = "logo.png"

class SchoolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("School Management System - Dashboard")
        self.root.geometry("900x600")
        self.root.configure(bg=COLOR_SECONDARY)
        
        self.center_window()
        
        # --- Main Layout ---
        # Header Bar
        self.header = tk.Frame(self.root, bg=COLOR_PRIMARY, height=80)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False) # Force height
        
        # Header Content
        if os.path.exists(LOGO_PATH):
            try:
                img = Image.open(LOGO_PATH)
                img.thumbnail((60, 60))
                self.logo_icon = ImageTk.PhotoImage(img)
                tk.Label(self.header, image=self.logo_icon, bg=COLOR_PRIMARY).pack(side=tk.LEFT, padx=20)
            except: pass
            
        tk.Label(self.header, text="School Management System", font=("Segoe UI", 20, "bold"), bg=COLOR_PRIMARY, fg=COLOR_WHITE).pack(side=tk.LEFT, padx=10)
        
        # Header Buttons (Right Side)
        btn_frame = tk.Frame(self.header, bg=COLOR_PRIMARY)
        btn_frame.pack(side=tk.RIGHT, padx=20)

        tk.Button(btn_frame, text="Change Password", command=self.open_change_password, 
                  bg="#F39C12", fg="white", relief=tk.FLAT, 
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side=tk.LEFT, padx=10)

        tk.Button(btn_frame, text="Logout / Exit", command=self.root.destroy, 
                  bg="#c0392b", fg="white", relief=tk.FLAT, 
                  font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side=tk.LEFT)

        # Dashboard Content
        self.container = tk.Frame(self.root, bg=COLOR_SECONDARY)
        self.container.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Welcome Message
        tk.Label(self.container, text="Welcome, Admin", font=("Segoe UI", 24), bg=COLOR_SECONDARY, fg=COLOR_TEXT).pack(anchor="w")
        tk.Label(self.container, text="Select a module to continue", font=("Segoe UI", 12), bg=COLOR_SECONDARY, fg="#666").pack(anchor="w", pady=(0, 30))
        
        # Cards Container
        cards_frame = tk.Frame(self.container, bg=COLOR_SECONDARY)
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Dashboard Cards (Admissions & Fees)
        self.create_card(cards_frame, "Manage Admissions", "Register new students, edit profiles,\nand print admission forms.", 
                         "#2196F3", self.open_admissions, 0)
                         
        self.create_card(cards_frame, "Fees & Accounts", "Generate monthly vouchers, manage dues,\nand print fee reports.", 
                         "#4CAF50", self.open_fees, 1)

    def create_card(self, parent, title, desc, color, command, col):
        # A "Card" is just a frame with a border and styling
        card = tk.Frame(parent, bg=COLOR_WHITE, relief=tk.RAISED, bd=1)
        card.grid(row=0, column=col, padx=20, pady=10, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        
        # Color strip at the top
        tk.Frame(card, bg=color, height=5).pack(fill=tk.X)
        
        # Content
        tk.Label(card, text=title, font=("Segoe UI", 16, "bold"), bg=COLOR_WHITE, fg=COLOR_TEXT).pack(pady=(20, 10))
        tk.Label(card, text=desc, font=("Segoe UI", 10), bg=COLOR_WHITE, fg="#666", justify=tk.CENTER).pack(pady=(0, 20), padx=10)
        
        # Action Button
        btn = tk.Button(card, text="Open Module", command=command, 
                        bg=color, fg=COLOR_WHITE, font=("Segoe UI", 11, "bold"), 
                        relief=tk.FLAT, padx=20, pady=8, cursor="hand2")
        btn.pack(pady=(0, 30))

    def open_admissions(self):
        AdmissionsWindow(tk.Toplevel(self.root))
        
    def open_fees(self):
        FeesWindow(tk.Toplevel(self.root))

    def open_change_password(self):
        """Opens a window to change the user password."""
        cp_win = tk.Toplevel(self.root)
        cp_win.title("Change Password")
        cp_win.geometry("400x350")
        cp_win.configure(bg=COLOR_WHITE)
        
        # UI Elements
        tk.Label(cp_win, text="Change Password", font=("Segoe UI", 14, "bold"), bg=COLOR_WHITE, fg=COLOR_PRIMARY).pack(pady=20)
        
        tk.Label(cp_win, text="Username:", font=("Segoe UI", 10), bg=COLOR_WHITE).pack(anchor="w", padx=40)
        user_entry = tk.Entry(cp_win, font=("Segoe UI", 10), bg=COLOR_SECONDARY)
        user_entry.pack(fill="x", padx=40, pady=(0, 10))
        user_entry.insert(0, "admin") # Default
        
        tk.Label(cp_win, text="Old Password:", font=("Segoe UI", 10), bg=COLOR_WHITE).pack(anchor="w", padx=40)
        old_pass_entry = tk.Entry(cp_win, font=("Segoe UI", 10), bg=COLOR_SECONDARY, show="•")
        old_pass_entry.pack(fill="x", padx=40, pady=(0, 10))
        
        tk.Label(cp_win, text="New Password:", font=("Segoe UI", 10), bg=COLOR_WHITE).pack(anchor="w", padx=40)
        new_pass_entry = tk.Entry(cp_win, font=("Segoe UI", 10), bg=COLOR_SECONDARY, show="•")
        new_pass_entry.pack(fill="x", padx=40, pady=(0, 20))
        
        def save_password():
            user = user_entry.get()
            old = old_pass_entry.get()
            new = new_pass_entry.get()
            
            if not user or not old or not new:
                messagebox.showerror("Error", "All fields are required.", parent=cp_win)
                return
                
            if check_login(user, old):
                update_password(user, new)
                messagebox.showinfo("Success", "Password updated successfully.", parent=cp_win)
                cp_win.destroy()
            else:
                messagebox.showerror("Error", "Incorrect Old Password or Username.", parent=cp_win)

        tk.Button(cp_win, text="Update Password", command=save_password, bg=COLOR_ACCENT, fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT).pack(fill="x", padx=40, pady=10)

        
    def center_window(self):
        self.root.update_idletasks()
        width = 900
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() # Hide main window initially
    
    def show_main_app():
        root.deiconify()
        app = SchoolApp(root)
        
    # Pass root to keep app alive
    login = LoginWindow(root, on_success_callback=show_main_app)
    
    root.mainloop()