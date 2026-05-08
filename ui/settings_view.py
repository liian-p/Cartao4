import customtkinter as ctk
from tkinter import messagebox
import db_core

class SettingsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        # Captura a referência do App enviada pelo main.py
        self.app = kwargs.pop("app_instance", None)
        
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Cabeçalho
        ctk.CTkLabel(self, text="Configurações", font=("Segoe UI", 24, "bold"), text_color="white").pack(pady=20, padx=20, anchor="w")

        # --- SEÇÃO: GERENCIAR PESSOAS ---
        self.person_section = ctk.CTkFrame(self, corner_radius=12, fg_color="#161920", border_width=1, border_color="#2b2e35")
        self.person_section.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.person_section, text="Gerenciar Pessoas", font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", padx=20, pady=15)
        
        self.entry_row = ctk.CTkFrame(self.person_section, fg_color="transparent")
        self.entry_row.pack(fill="x", padx=20, pady=5)
        
        self.name_entry = ctk.CTkEntry(self.entry_row, placeholder_text="Nome da Pessoa", width=300, height=35, fg_color="#0f1115", border_color="#2b2e35")
        self.name_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(self.entry_row, text="Adicionar", fg_color="#28a745", hover_color="#1e7e34", width=100, height=35, font=("Segoe UI", 12, "bold"), command=self.save_person).pack(side="left")

        self.list_frame = ctk.CTkScrollableFrame(self.person_section, height=200, fg_color="transparent")
        self.list_frame.pack(fill="x", padx=15, pady=15)

        # --- SEÇÃO: PERSONALIZAÇÃO DO TEMA (DINÂMICO) ---
        self.theme_section = ctk.CTkFrame(self, corner_radius=12, fg_color="#161920", border_width=1, border_color="#2b2e35")
        self.theme_section.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(self.theme_section, text="Tema do Terminal", font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w", padx=20, pady=15)
        
        colors_frame = ctk.CTkFrame(self.theme_section, fg_color="transparent")
        colors_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        themes = [
            ("Azul", "#1e90ff"),
            ("Roxo", "#8a2be2"),
            ("Verde", "#00ff7f"),
            ("Laranja", "#ff4500"),
            ("Rosa", "#ff1493")
        ]
        
        for name, color in themes:
            btn = ctk.CTkButton(
                colors_frame, 
                text=name, 
                fg_color=color, 
                hover_color=color, 
                width=100, 
                height=32, 
                corner_radius=8, 
                text_color="white",
                font=("Segoe UI", 11, "bold"),
                command=lambda c=color: self.apply_theme(c)
            )
            btn.pack(side="left", padx=5)

    def apply_theme(self, color):
        """Chama o método de troca no App principal via referência direta"""
        if self.app:
            self.app.change_accent_color(color)
        else:
            print("Erro: Referência ao App não encontrada no SettingsView.")

    def save_person(self):
        nome = self.name_entry.get().strip()
        if nome:
            if db_core.add_person(nome):
                self.name_entry.delete(0, 'end')
                self.load_persons()
            else:
                messagebox.showwarning("Aviso", "Nome já existe.")

    def load_persons(self):
        for w in self.list_frame.winfo_children(): w.destroy()
        for p in db_core.get_persons():
            row = ctk.CTkFrame(self.list_frame, fg_color="#1f2229", height=45, corner_radius=8)
            row.pack(fill="x", pady=3, padx=5)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=f"• {p.name}", font=("Segoe UI", 13), text_color="white").pack(side="left", padx=15)
            ctk.CTkButton(row, text="Excluir", fg_color="#dc3545", width=70, height=28, command=lambda pid=p.id: self.confirm_delete(pid)).pack(side="right", padx=10)

    def confirm_delete(self, pid):
        if messagebox.askyesno("Confirmar", "Deseja remover esta pessoa?"):
            ok, msg = db_core.delete_person(pid)
            if ok: self.load_persons()
            else: messagebox.showwarning("Aviso", msg)

    def load_combos(self):
        self.load_persons()