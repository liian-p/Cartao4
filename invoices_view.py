import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
import pandas as pd
import db_core

class InvoicesView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_items = []

        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(10, 20), padx=20)
        
        ctk.CTkLabel(self.header, text="Extrato Detalhado", 
                     font=("Segoe UI", 28, "bold"), text_color="white").pack(side="left")

        # --- BARRA DE FILTROS (STYLE PREMIUM) ---
        self.filter_bar = ctk.CTkFrame(self, fg_color="#161920", height=70, corner_radius=15, border_width=1, border_color="#2b2e35")
        self.filter_bar.pack(fill="x", padx=20, pady=10)
        self.filter_bar.pack_propagate(False)

        # Filtro Cartão
        self.card_combo = ctk.CTkComboBox(self.filter_bar, values=[], width=180, height=35, corner_radius=10, fg_color="#0f1115", border_color="#2b2e35")
        self.card_combo.set("Selecionar Cartão")
        self.card_combo.pack(side="left", padx=15, pady=17)
        
        # Filtro Mês
        self.month_combo = ctk.CTkComboBox(self.filter_bar, values=[str(m) for m in range(1, 13)], width=70, height=35, corner_radius=10, fg_color="#0f1115")
        self.month_combo.set(str(datetime.now().month))
        self.month_combo.pack(side="left", padx=5)
        
        # Filtro Ano
        self.year_combo = ctk.CTkComboBox(self.filter_bar, values=["2025", "2026", "2027"], width=90, height=35, corner_radius=10, fg_color="#0f1115")
        self.year_combo.set("2026")
        self.year_combo.pack(side="left", padx=5)

        # Botões de Ação
        ctk.CTkButton(self.filter_bar, text="🔍 FILTRAR", width=100, height=35, corner_radius=10, font=("Segoe UI", 12, "bold"),
                      fg_color="#1e90ff", hover_color="#1466b8", command=self.load_data).pack(side="left", padx=20)
        
        ctk.CTkButton(self.filter_bar, text="📊 EXPORTAR EXCEL", width=140, height=35, corner_radius=10, font=("Segoe UI", 11, "bold"),
                      fg_color="#28a745", hover_color="#1e7e34", command=self.export_excel).pack(side="right", padx=15)

        # --- TABELA DE LANÇAMENTOS ---
        self.table_container = ctk.CTkFrame(self, fg_color="#161920", corner_radius=20, border_width=1, border_color="#2b2e35")
        self.table_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Cabeçalho da Tabela
        self.table_header = ctk.CTkFrame(self.table_container, fg_color="transparent", height=40)
        self.table_header.pack(fill="x", padx=20, pady=(15, 5))
        
        cols = [("DATA", 100), ("DESCRIÇÃO", 300), ("PARCELA", 100), ("PESSOA", 150), ("VALOR", 120)]
        for text, width in cols:
            ctk.CTkLabel(self.table_header, text=text, font=("Segoe UI", 11, "bold"), text_color="#63676e", width=width, anchor="w").pack(side="left")

        # Área de Scroll
        self.list_scroll = ctk.CTkScrollableFrame(self.table_container, fg_color="transparent")
        self.list_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # --- FOOTER: TOTALIZADOR ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.footer.pack(fill="x", padx=20, pady=(10, 20))
        
        self.total_label = ctk.CTkLabel(self.footer, text="TOTAL DA FATURA: R$ 0.00", font=("Segoe UI", 22, "bold"), text_color="#1e90ff")
        self.total_label.pack(side="right", padx=10)

    def load_combos(self):
        cards = db_core.get_cards()
        self.cards_map = {c.name: c.id for c in cards}
        self.card_combo.configure(values=list(self.cards_map.keys()))
        if cards: self.card_combo.set(cards[0].name)

    def load_data(self):
        # Limpa lista atual
        for w in self.list_scroll.winfo_children(): w.destroy()
        
        card_name = self.card_combo.get()
        c_id = self.cards_map.get(card_name)
        
        if not c_id:
            messagebox.showwarning("Aviso", "Selecione um cartão para visualizar.")
            return

        self.current_items = db_core.get_invoice_items(c_id, int(self.year_combo.get()), int(self.month_combo.get()))
        total = 0.0
        
        if not self.current_items:
            ctk.CTkLabel(self.list_scroll, text="Nenhum lançamento para este período.", font=("Segoe UI", 14, "italic"), text_color="#63676e").pack(pady=40)
        else:
            for item in self.current_items:
                self.add_table_row(item)
                total += item['amount']
        
        self.total_label.configure(text=f"TOTAL DA FATURA: R$ {total:.2f}")

    def add_table_row(self, item):
        # Frame da linha com efeito hover simulado pela cor de fundo
        row = ctk.CTkFrame(self.list_scroll, fg_color="#1f2229", height=45, corner_radius=8)
        row.pack(fill="x", pady=3, padx=5)
        row.pack_propagate(False)

        # Status de Pago (opcional, se quiser destacar)
        text_color = "#8a8d91" if item.get('is_paid') else "white"

        ctk.CTkLabel(row, text=item['date'], width=100, font=("Segoe UI", 12), text_color=text_color, anchor="w").pack(side="left", padx=(15, 0))
        ctk.CTkLabel(row, text=item['desc'][:35], width=300, font=("Segoe UI", 13, "bold"), text_color=text_color, anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=f"{item['inst_num']}/{item['inst_tot']}", width=100, font=("Segoe UI", 12), text_color="#1e90ff", anchor="w").pack(side="left")
        ctk.CTkLabel(row, text=item['person'], width=150, font=("Segoe UI", 12), text_color=text_color, anchor="w").pack(side="left")
        
        # Valor com destaque
        val_color = "#00face" if not item.get('is_paid') else "#28a745"
        ctk.CTkLabel(row, text=f"R$ {item['amount']:.2f}", width=120, font=("Segoe UI", 14, "bold"), text_color=val_color, anchor="w").pack(side="left")

    def export_excel(self):
        if not self.current_items:
            messagebox.showwarning("Aviso", "Não há dados para exportar.")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Excel Files", "*.xlsx")],
                                               title="Salvar Fatura como Excel",
                                               initialfile=f"Fatura_{self.card_combo.get()}_{self.month_combo.get()}.xlsx")
        if file_path:
            try:
                df = pd.DataFrame(self.current_items)
                # Tradução de colunas para o Excel ficar profissional
                df = df.rename(columns={
                    'date': 'Data', 'desc': 'Descrição', 'inst_num': 'Parc. Atual',
                    'inst_tot': 'Total Parc.', 'person': 'Pessoa', 'amount': 'Valor (R$)', 'is_paid': 'Status Pago'
                })
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Sucesso", "Fatura exportada com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha na exportação: {e}")