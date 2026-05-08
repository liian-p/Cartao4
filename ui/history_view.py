import customtkinter as ctk
import db_core

class HistoryView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(10, 20), padx=20)
        
        ctk.CTkLabel(self.header, text="Histórico de Recebimentos", 
                     font=("Segoe UI", 28, "bold"), text_color="white").pack(side="left")
        
        ctk.CTkButton(self.header, text="🔄 ATUALIZAR", width=120, height=35, corner_radius=10,
                      font=("Segoe UI", 12, "bold"), fg_color="#2b2e35", hover_color="#1e90ff",
                      command=self.load_data).pack(side="right", pady=(10,0))

        # --- CARDS DE RESUMO RÁPIDO ---
        self.summary_container = ctk.CTkFrame(self, fg_color="transparent")
        self.summary_container.pack(fill="x", padx=20, pady=10)
        
        self.total_card = self.create_summary_item(self.summary_container, "TOTAL RECUPERADO", "R$ 0.00", "#28a745")
        self.count_card = self.create_summary_item(self.summary_container, "TRANSAÇÕES", "0", "#1e90ff")

        # --- CONTAINER DA TABELA ---
        self.main_card = ctk.CTkFrame(self, fg_color="#161920", corner_radius=20, border_width=1, border_color="#2b2e35")
        self.main_card.pack(fill="both", expand=True, padx=20, pady=10)

        # Cabeçalho da Tabela
        self.table_header = ctk.CTkFrame(self.main_card, fg_color="transparent", height=40)
        self.table_header.pack(fill="x", padx=20, pady=(20, 10))
        
        cols = [("DATA", 120), ("DESCRIÇÃO", 300), ("PARCELA", 100), ("PESSOA", 150), ("VALOR", 120)]
        for text, width in cols:
            ctk.CTkLabel(self.table_header, text=text, font=("Segoe UI", 11, "bold"), 
                         text_color="#63676e", width=width, anchor="w").pack(side="left")

        # Área de Scroll
        self.scroll = ctk.CTkScrollableFrame(self.main_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=5)

    def create_summary_item(self, master, label, value, color):
        card = ctk.CTkFrame(master, fg_color="#161920", height=80, width=280, corner_radius=15, border_width=1, border_color="#2b2e35")
        card.pack(side="left", padx=(0, 20))
        card.pack_propagate(False)
        
        indicator = ctk.CTkFrame(card, width=4, fg_color=color, corner_radius=0)
        indicator.pack(side="left", fill="y", padx=(0, 15))
        
        lbl = ctk.CTkLabel(card, text=label, font=("Segoe UI", 10, "bold"), text_color="#63676e")
        lbl.pack(anchor="w", pady=(15, 0))
        
        val = ctk.CTkLabel(card, text=value, font=("Segoe UI", 20, "bold"), text_color="white")
        val.pack(anchor="w")
        return val

    def load_data(self):
        # Limpar registros atuais
        for w in self.scroll.winfo_children(): w.destroy()
        
        history = db_core.get_paid_history()
        total_acumulado = 0.0
        
        if not history:
            ctk.CTkLabel(self.scroll, text="Nenhum pagamento registrado no histórico.", 
                         font=("Segoe UI", 14, "italic"), text_color="#63676e").pack(pady=50)
            self.total_card.configure(text="R$ 0.00")
            self.count_card.configure(text="0")
            return

        for item in history:
            total_acumulado += item['amount']
            self.add_row(item)
            
        # Atualizar Cards de Resumo
        self.total_card.configure(text=f"R$ {total_acumulado:.2f}")
        self.count_card.configure(text=str(len(history)))

    def add_row(self, item):
        row = ctk.CTkFrame(self.scroll, fg_color="#1f2229", height=50, corner_radius=10)
        row.pack(fill="x", pady=3, padx=5)
        row.pack_propagate(False)

        # Estilização das colunas
        ctk.CTkLabel(row, text=item['date'], width=120, font=("Segoe UI", 12), text_color="#8a8d91", anchor="w").pack(side="left", padx=(15, 0))
        
        # Descrição com ícone de check
        desc_frame = ctk.CTkFrame(row, fg_color="transparent")
        desc_frame.pack(side="left", width=300)
        ctk.CTkLabel(desc_frame, text="✅", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(desc_frame, text=item['desc'][:30], font=("Segoe UI", 13, "bold"), text_color="white", anchor="w").pack(side="left")
        
        ctk.CTkLabel(row, text=item['inst'], width=100, font=("Segoe UI", 12), text_color="#1e90ff", anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=item['person'], width=150, font=("Segoe UI", 12), text_color="white", anchor="w").pack(side="left")
        
        # Valor em verde para indicar entrada/recebimento
        ctk.CTkLabel(row, text=f"R$ {item['amount']:.2f}", width=120, font=("Segoe UI", 15, "bold"), text_color="#28a745", anchor="w").pack(side="left")