import customtkinter as ctk
from datetime import datetime
import db_core
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle # Importação correta do Circle

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_month = datetime.now().month
        self.current_year = 2026 

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(0, 25))
        
        ctk.CTkLabel(self.header, text="Dashboard Analítico", 
                     font=("Segoe UI", 32, "bold"), text_color="white").pack(side="left")
        
        self.controls = ctk.CTkFrame(self.header, fg_color="transparent")
        self.controls.pack(side="right")
        
        self.m_combo = ctk.CTkComboBox(self.controls, values=[str(m) for m in range(1, 13)], 
                                      width=80, corner_radius=10, fg_color="#161920", border_color="#2b2e35")
        self.m_combo.set(str(self.current_month))
        self.m_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(self.controls, text="🔄 ATUALIZAR", width=120, height=35, corner_radius=10,
                      font=("Segoe UI", 12, "bold"), fg_color="#1e90ff", hover_color="#1466b8",
                      command=self.load_data).pack(side="left", padx=5)

        # --- KPI CARDS ---
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", pady=10)
        self.kpi_container.grid_columnconfigure((0, 1, 2), weight=1)

        # --- CONSULTA INDIVIDUAL ---
        self.lookup_card = ctk.CTkFrame(self, height=100, corner_radius=20, fg_color="#161920", border_width=1, border_color="#2b2e35")
        self.lookup_card.pack(fill="x", pady=20)
        
        ctk.CTkLabel(self.lookup_card, text="CONSULTA POR PESSOA", font=("Segoe UI", 12, "bold"), text_color="#1e90ff").place(x=30, y=15)
        
        self.p_combo = ctk.CTkComboBox(self.lookup_card, values=[], width=250, height=40, 
                                      corner_radius=10, fg_color="#0f1115", border_color="#2b2e35",
                                      command=lambda x: self.load_individual())
        self.p_combo.set("Selecione...")
        self.p_combo.place(x=30, y=40)
        
        self.res_val = ctk.CTkLabel(self.lookup_card, text="R$ 0.00", font=("Segoe UI", 34, "bold"), text_color="#00face")
        self.res_val.place(relx=0.95, y=50, anchor="e")

        # --- GRID DE DADOS ---
        self.data_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.data_grid.pack(fill="both", expand=True)
        self.data_grid.grid_columnconfigure(0, weight=4)
        self.data_grid.grid_columnconfigure(1, weight=6)

        self.pending_card = ctk.CTkFrame(self.data_grid, corner_radius=20, fg_color="#161920", border_width=1, border_color="#2b2e35")
        self.pending_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(self.pending_card, text="PENDÊNCIAS POR PESSOA", font=("Segoe UI", 13, "bold"), text_color="#63676e").pack(pady=20)
        self.pending_scroll = ctk.CTkScrollableFrame(self.pending_card, fg_color="transparent")
        self.pending_scroll.pack(fill="both", expand=True, padx=15, pady=5)

        self.chart_card = ctk.CTkFrame(self.data_grid, corner_radius=20, fg_color="#161920", border_width=1, border_color="#2b2e35")
        self.chart_card.grid(row=0, column=1, sticky="nsew")

    def create_kpi_card(self, col, title, value, color):
        card = ctk.CTkFrame(self.kpi_container, fg_color="#161920", height=130, corner_radius=20, border_width=1, border_color="#2b2e35")
        card.grid(row=0, column=col, padx=10, sticky="ew")
        card.grid_propagate(False)
        
        indicator = ctk.CTkFrame(card, width=6, fg_color=color, corner_radius=0)
        indicator.pack(side="left", fill="y", padx=(0, 20))
        
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 14, "bold"), text_color="#63676e").pack(anchor="w", pady=(25, 5))
        ctk.CTkLabel(card, text=f"R$ {value:,.2f}", font=("Segoe UI", 28, "bold"), text_color="white").pack(anchor="w")

    def load_combos(self):
        persons = [p.name for p in db_core.get_persons()]
        if persons:
            self.p_combo.configure(values=persons)
            if self.p_combo.get() in ["Selecione...", "CTkComboBox"]:
                self.p_combo.set(persons[0])

    def load_data(self):
        if not self.winfo_exists(): return
        
        for w in self.kpi_container.winfo_children(): w.destroy()
        for w in self.pending_scroll.winfo_children(): w.destroy()
        for w in self.chart_card.winfo_children(): w.destroy()

        month = int(self.m_combo.get())
        d = db_core.get_dashboard_data(month, self.current_year)
        
        self.create_kpi_card(0, "TOTAL GERAL", d["total_geral"], "#1e90ff")
        self.create_kpi_card(1, "INTER", d["totais_cartoes"].get("INTER", 0), "#FF7A00")
        self.create_kpi_card(2, "NUBANK", d["totais_cartoes"].get("NUBANK", 0), "#8A05BE")

        labels, values = [], []
        for person, total in d["totais_pessoas"].items():
            if total > 0:
                labels.append(person)
                values.append(total)
                
                row = ctk.CTkFrame(self.pending_scroll, fg_color="#1f2229", height=45, corner_radius=10)
                row.pack(fill="x", pady=4, padx=5)
                row.pack_propagate(False)
                ctk.CTkLabel(row, text=person, font=("Segoe UI", 13)).pack(side="left", padx=15)
                ctk.CTkLabel(row, text=f"R$ {total:.2f}", font=("Segoe UI", 13, "bold"), text_color="#ff4c4c").pack(side="right", padx=15)

        if values:
            fig, ax = plt.subplots(figsize=(5, 4), facecolor='#161920')
            ax.set_facecolor('#161920')
            colors = ['#1e90ff', '#00face', '#8a05be', '#ff7a00', '#ff4c4c', '#00ff88']
            
            # CORREÇÃO: Usar um único objeto para receber o retorno e evitar Tuple Size Mismatch
            pie_data = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                             colors=colors, startangle=140, pctdistance=0.85,
                             textprops={'color':"white", 'fontweight':'bold', 'fontsize': 10})
            
            # CORREÇÃO: Circle importado de matplotlib.patches
            centre_circle = Circle((0,0), 0.70, fc='#161920')
            ax.add_artist(centre_circle)
            
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, master=self.chart_card)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        else:
            ctk.CTkLabel(self.chart_card, text="Sem dados para este mês", font=("Segoe UI", 14, "italic")).pack(pady=100)
        
        self.load_individual()

    def load_individual(self):
        p_name = self.p_combo.get()
        if p_name and p_name not in ["Selecione...", "Sem Pessoas"]:
            month = int(self.m_combo.get())
            res = db_core.get_person_debt_details(p_name, month, self.current_year)
            self.res_val.configure(text=f"R$ {res['total']:.2f}")