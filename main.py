import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import os
import threading
import json
from datetime import datetime, timedelta

# Importação das views
from ui.dashboard_view import DashboardView
from ui.purchases_view import PurchasesView
from ui.invoices_view import InvoicesView
from ui.payments_view import PaymentsView
from ui.settings_view import SettingsView
from ui.history_view import HistoryView      
from ui.analytics_view import AnalyticsView  
# PASSO 1: Importar a nova view de Empréstimos
from ui.loan_view import LoanView 

CONFIG_FILE = "session_config.json"

# --- CLASSE DE NOTIFICAÇÃO TOAST ---
class ToastNotification(ctk.CTkFrame):
    def __init__(self, master, message, color="#1e90ff", **kwargs):
        super().__init__(master, corner_radius=10, fg_color="#161920", 
                         border_width=1, border_color=color, **kwargs)
        
        # Ícone e Mensagem
        self.label = ctk.CTkLabel(self, text=f"  ⓘ  {message}", 
                                  font=("Segoe UI", 13, "bold"), 
                                  text_color="white", padx=20, pady=10)
        self.label.pack()

        # Posicionamento inicial (fora da tela à direita)
        self.place(relx=1.1, rely=0.92, anchor="e")
        self.animate_in()

    def animate_in(self):
        """Desliza a notificação para dentro da tela"""
        x = 1.1
        def step():
            nonlocal x
            if x > 0.98:
                x -= 0.01
                self.place(relx=x)
                self.after(10, step)
            else:
                self.after(3000, self.animate_out) # Exibe por 3 segundos

        step()

    def animate_out(self):
        """Desliza a notificação para fora e remove o widget"""
        x = 0.98
        def step():
            nonlocal x
            if x < 1.2:
                x += 0.01
                self.place(relx=x)
                self.after(10, step)
            else:
                self.destroy()

        step()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ELN Finance - Terminal de Gestão Premium")
        self.geometry("1300x850")
        self.configure(fg_color="#0f1115") 
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # INCREMENTO: Carregar cor de destaque salva ou usar padrão
        self.accent_color = self.load_accent_color()
        
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#161920", border_width=1, border_color="#1f2229")
        self.frames = {}
        self.nav_buttons = [] 
        self.login_attempts = 0
        
        if self.check_session():
            self.setup_main_ui()
        else:
            self.show_login_screen()

        # Atalhos de Teclado
        self.bind("<F1>", lambda e: self.show_frame("DashboardView"))
        self.bind("<F2>", lambda e: self.show_frame("PurchasesView"))
        self.bind("<F3>", lambda e: self.show_frame("InvoicesView"))
        self.bind("<F4>", lambda e: self.show_frame("PaymentsView"))
        self.bind("<F5>", lambda e: self.show_frame("HistoryView"))
        self.bind("<F6>", lambda e: self.show_frame("AnalyticsView"))
        self.bind("<F7>", lambda e: self.show_frame("LoanView")) # Atalho para Empréstimos
        self.bind("<F8>", lambda e: self.show_frame("SettingsView"))

    def show_toast(self, message, type="info"):
        """Dispara uma notificação flutuante elegante"""
        colors = {
            "info": self.accent_color,
            "success": "#28a745",
            "error": "#dc3545",
            "warning": "#ffc107"
        }
        ToastNotification(self, message, color=colors.get(type, self.accent_color))

    def load_accent_color(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("accent_color", "#1e90ff")
            except: pass
        return "#1e90ff"

    def change_accent_color(self, new_color):
        self.accent_color = new_color
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f: data = json.load(f)
        
        data["accent_color"] = new_color
        with open(CONFIG_FILE, "w") as f: json.dump(data, f)
        
        self.title_label.configure(text_color=new_color)
        for btn in self.nav_buttons:
            if "transparent" not in btn.cget("fg_color"):
                btn.configure(text_color=new_color)

        self.show_toast("Tema atualizado com sucesso!", "success")

    def check_session(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    last_login = datetime.fromisoformat(data.get("last_login"))
                    if datetime.now() < last_login + timedelta(hours=24): return True
            except: pass
        return False

    def save_session(self):
        data = {"accent_color": self.accent_color}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f: data = json.load(f)
        data["last_login"] = datetime.now().isoformat()
        with open(CONFIG_FILE, "w") as f: json.dump(data, f)

    def show_login_screen(self):
        self.login_container = ctk.CTkFrame(self, corner_radius=0)
        self.login_container.place(relx=0, rely=0, relwidth=1, relheight=1)

        bg_path = "backgroundlogin.png"
        if os.path.exists(bg_path):
            img_bg = Image.open(bg_path)
            self.bg_image = ctk.CTkImage(light_image=img_bg, dark_image=img_bg, size=(1300, 850))
            self.bg_label = ctk.CTkLabel(self.login_container, image=self.bg_image, text="")
            self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.login_card = ctk.CTkFrame(self.login_container, width=450, height=650, corner_radius=30, fg_color="#161920", border_width=2, border_color="#2b2e35")
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")
        self.login_card.pack_propagate(False)

        logo_path = "logo.png"
        if os.path.exists(logo_path):
            img_pill = Image.open(logo_path)
            self.logo_image = ctk.CTkImage(light_image=img_pill, dark_image=img_pill, size=(300, 120))
            ctk.CTkLabel(self.login_card, image=self.logo_image, text="").pack(pady=(50, 10))

        ctk.CTkLabel(self.login_card, text="Bem-vindo", font=("Segoe UI", 28, "bold"), text_color="white").pack(pady=(5, 15))

        self.pass_entry = ctk.CTkEntry(self.login_card, placeholder_text="Senha de Acesso", show="*", width=320, height=55, corner_radius=15, fg_color="#0f1115", border_color="#1f2229", font=("Segoe UI", 16), justify="center")
        self.pass_entry.pack(pady=10)
        self.pass_entry.bind("<Return>", lambda e: self.attempt_login())

        self.remember_me = ctk.CTkCheckBox(self.login_card, text="Lembrar-me por 24h", font=("Segoe UI", 12), text_color="#8a8d91", hover_color=self.accent_color, fg_color=self.accent_color, border_color="#2b2e35")
        self.remember_me.pack(pady=10)

        self.loading_bar = ctk.CTkProgressBar(self.login_card, width=320, height=4, fg_color="#0f1115", progress_color=self.accent_color, mode="indeterminate")

        self.login_btn = ctk.CTkButton(self.login_card, text="ACESSAR TERMINAL", width=320, height=55, corner_radius=15, font=("Segoe UI", 14, "bold"), fg_color=self.accent_color, hover_color="#1466b8", command=self.attempt_login)
        self.login_btn.pack(pady=(10, 20))

        self.status_label = ctk.CTkLabel(self.login_card, text="Conexão Criptografada", font=("Segoe UI", 11), text_color="#454950")
        self.status_label.pack(pady=10)

    def attempt_login(self):
        if self.login_attempts >= 5:
            self.show_toast("Excesso de tentativas. Bloqueado.", "error")
            self.after(2000, self.destroy)
            return

        if self.pass_entry.get() == "12345":
            if self.remember_me.get(): self.save_session()
            self.show_toast("Acesso autorizado!", "success")
            self.login_btn.configure(state="disabled", text="AUTENTICANDO...")
            self.loading_bar.pack(pady=(0, 15), before=self.login_btn)
            self.loading_bar.start()
            self.status_label.configure(text="SINCRONIZANDO DADOS...", text_color=self.accent_color)
            self.after(1500, self.finish_login)
        else:
            self.login_attempts += 1
            self.shake_card(self.login_card)
            self.show_toast(f"Senha incorreta! ({5 - self.login_attempts} restates)", "warning")

    def finish_login(self):
        self.login_container.destroy()
        self.setup_main_ui()

    def setup_main_ui(self):
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.title_label = ctk.CTkLabel(self.sidebar, text="ELN FINANCE", font=("Segoe UI", 18, "bold"), text_color=self.accent_color)
        self.title_label.grid(row=0, column=0, padx=20, pady=30)

        # PASSO 2: Adicionar "💰 Empréstimos" à lista de menus
        menus = [("📊 Dashboard", "DashboardView"), ("➕ Nova Compra", "PurchasesView"), 
                 ("📑 Faturas", "InvoicesView"), ("💸 Pagar", "PaymentsView"), 
                 ("🕒 Histórico", "HistoryView"), ("🏆 Ranking", "AnalyticsView"), 
                 ("💰 Empréstimos", "LoanView"), ("⚙️ Ajustes", "SettingsView")]
        
        for i, (txt, view) in enumerate(menus, 1):
            self.add_nav_button(txt, view, i)

        status_footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        status_footer.grid(row=9, column=0, pady=(40, 20), sticky="s") # Ajustado o row para 9
        ctk.CTkLabel(status_footer, text="●", text_color="#28a745", font=("Segoe UI", 14)).pack(side="left", padx=5)
        ctk.CTkLabel(status_footer, text="TERMINAL ONLINE", font=("Segoe UI", 10, "bold"), text_color="#8a8d91").pack(side="left")

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.init_frames()

    def add_nav_button(self, text, view_name, row):
        btn = ctk.CTkButton(self.sidebar, text=text, height=45, corner_radius=10, font=("Segoe UI", 14), fg_color="transparent", text_color="#d1d1d1", hover_color="#1f2229", anchor="w", command=lambda: self.show_frame(view_name))
        btn.grid(row=row, column=0, padx=15, pady=8, sticky="ew")
        self.nav_buttons.append(btn)

    def init_frames(self):
        # PASSO 3: Registrar a LoanView no dicionário de frames
        self.frames = {
            "DashboardView": DashboardView(self.main_area),
            "PurchasesView": PurchasesView(self.main_area),
            "InvoicesView": InvoicesView(self.main_area),
            "PaymentsView": PaymentsView(self.main_area),
            "HistoryView": HistoryView(self.main_area),
            "AnalyticsView": AnalyticsView(self.main_area),
            "LoanView": LoanView(self.main_area),
            "SettingsView": SettingsView(self.main_area, app_instance=self)
        }
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("DashboardView")

    def show_frame(self, page):
        if not self.frames: return
        frame = self.frames[page]
        frame.tkraise()
        
        for btn in self.nav_buttons:
            if page in str(btn.cget("command")):
                btn.configure(fg_color="#1f2229", text_color=self.accent_color)
            else:
                btn.configure(fg_color="transparent", text_color="#d1d1d1")
                
        threading.Thread(target=self._async_load, args=(frame,), daemon=True).start()

    def _async_load(self, frame):
        if hasattr(frame, 'load_combos'): frame.load_combos()
        if hasattr(frame, 'load_data'): frame.load_data()

    def shake_card(self, widget):
        for i, pos in enumerate([0.505, 0.495, 0.505, 0.495, 0.5]):
            self.after(i * 50, lambda p=pos: widget.place(relx=p))

if __name__ == "__main__":
    app = App()
    app.mainloop()