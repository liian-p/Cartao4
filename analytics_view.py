import customtkinter as ctk
import db_core
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import colormaps # Importação correta para evitar o erro de módulo

class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Cabeçalho Premium
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(10, 20), padx=20)
        
        ctk.CTkLabel(self.header, text="🏆 Ranking de Utilização", 
                     font=("Segoe UI", 28, "bold"), text_color="white").pack(side="left")
        
        self.main_container = ctk.CTkFrame(self, fg_color="#161920", corner_radius=20, border_width=1, border_color="#2b2e35")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=10)

    def load_data(self):
        if not self.winfo_exists(): return
        
        # Limpa o container antes de renderizar novo gráfico
        for w in self.main_container.winfo_children(): w.destroy()
        
        ranking = db_core.get_ranking_data()
        if not ranking:
            ctk.CTkLabel(self.main_container, text="Sem dados para exibir", font=("Segoe UI", 14, "italic")).pack(pady=100)
            return

        # Configuração do gráfico integrada ao tema Dark
        fig, ax = plt.subplots(figsize=(7, 5), facecolor='#161920')
        ax.set_facecolor('#161920')
        
        names = [r[0] for r in ranking]
        values = [r[1] for r in ranking]
        
        # Correção do Colormap (Viridis) - Usando a API atual do Matplotlib
        cmap = colormaps.get_cmap('spring') # 'spring' dá um visual neon premium
        colors = cmap([i/len(names) for i in range(len(names))])
        
        bars = ax.barh(names, values, color=colors)
        ax.invert_yaxis() 
        
        # Estilização de eixos
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(colors='white', labelsize=10)
        ax.set_xlabel("Valor Total (R$)", color="#8a8d91", fontsize=11)
        
        # Adiciona os valores nas pontas das barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (max(values)*0.02), bar.get_y() + bar.get_height()/2,
                    f'R$ {width:,.2f}', va='center', color='white', fontweight='bold')

        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.main_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=30, pady=30)