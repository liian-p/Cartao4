import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import db_core

class PurchasesView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.editing_id = None  # Armazena o ID se estivermos editando

        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(10, 20), padx=20)
        
        ctk.CTkLabel(self.header, text="Gestão de Compras", 
                     font=("Segoe UI", 28, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(self.header, text="TERMINAL DE ALTA PERFORMANCE", 
                     font=("Segoe UI", 10, "bold"), text_color="#1e90ff").pack(side="right", pady=(15,0))

        # --- CONTAINER PRINCIPAL ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20)

        # --- COLUNA ESQUERDA: FORMULÁRIO (GLASS STYLE) ---
        self.form_card = ctk.CTkFrame(self.main_container, fg_color="#161920", corner_radius=20, border_width=1, border_color="#2b2e35")
        self.form_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.form_title = ctk.CTkLabel(self.form_card, text="📝 NOVO LANÇAMENTO", font=("Segoe UI", 14, "bold"), text_color="#1e90ff")
        self.form_title.pack(pady=(25, 15))

        self.inner_form = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.inner_form.pack(fill="x", padx=40)

        # Inputs Customizados
        self.desc_entry = self.create_input("O que você comprou?", "Descrição")
        self.amount_entry = self.create_input("Valor (R$)", "0,00")
        
        # Row: Data e Parcelas
        row_dp = ctk.CTkFrame(self.inner_form, fg_color="transparent")
        row_dp.pack(fill="x", pady=10)
        
        self.date_entry = self.create_input("Data", "", master=row_dp, width=160)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", padx=(0,10))
        
        self.install_combo = ctk.CTkComboBox(row_dp, values=[f"{i}x" for i in range(1, 13)], height=45, corner_radius=12, fg_color="#0f1115", border_color="#2b2e35")
        self.install_combo.set("1x")
        self.install_combo.pack(side="left", fill="x", expand=True)

        # Row: Cartão e Pessoa
        row_cp = ctk.CTkFrame(self.inner_form, fg_color="transparent")
        row_cp.pack(fill="x", pady=10)
        
        self.card_combo = ctk.CTkComboBox(row_cp, values=[], height=45, corner_radius=12, fg_color="#0f1115", border_color="#2b2e35")
        self.card_combo.pack(side="left", fill="x", expand=True, padx=(0,10))
        
        self.person_combo = ctk.CTkComboBox(row_cp, values=[], height=45, corner_radius=12, fg_color="#0f1115", border_color="#2b2e35")
        self.person_combo.pack(side="left", fill="x", expand=True)

        # Botões de Ação
        self.btn_save = ctk.CTkButton(self.form_card, text="CONFIRMAR LANÇAMENTO", height=55, corner_radius=15, 
                                      font=("Segoe UI", 16, "bold"), fg_color="#1e90ff", hover_color="#1466b8", command=self.submit)
        self.btn_save.pack(pady=(30, 10), padx=40, fill="x")

        self.btn_cancel = ctk.CTkButton(self.form_card, text="CANCELAR EDIÇÃO", height=35, corner_radius=10, 
                                        font=("Segoe UI", 12), fg_color="transparent", border_width=1, border_color="#ff4c4c", 
                                        text_color="#ff4c4c", hover_color="#321a1a", command=self.cancel_edit)
        # Escondido por padrão, aparece só na edição

        # --- COLUNA DIREITA: FEED DE ATIVIDADE ---
        self.feed_card = ctk.CTkFrame(self.main_container, fg_color="#161920", width=420, corner_radius=20, border_width=1, border_color="#2b2e35")
        self.feed_card.pack(side="right", fill="both", padx=(10, 0))
        self.feed_card.pack_propagate(False)

        ctk.CTkLabel(self.feed_card, text="🕒 ÚLTIMOS REGISTROS", font=("Segoe UI", 12, "bold"), text_color="#63676e").pack(pady=20)
        
        self.scroll = ctk.CTkScrollableFrame(self.feed_card, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

    def create_input(self, label, placeholder, master=None, width=None):
        target = master if master else self.inner_form
        entry = ctk.CTkEntry(target, placeholder_text=placeholder, height=45, width=width if width else 400,
                             corner_radius=12, fg_color="#0f1115", border_color="#2b2e35", font=("Segoe UI", 14))
        entry.pack(pady=5, fill="x" if not width else "none")
        entry.bind("<FocusIn>", lambda e: entry.configure(border_color="#1e90ff"))
        entry.bind("<FocusOut>", lambda e: entry.configure(border_color="#2b2e35"))
        return entry

    def load_combos(self):
        self.cards_map = {c.name: c.id for c in db_core.get_cards()}
        self.person_map = {p.name: p.id for p in db_core.get_persons()}
        self.card_combo.configure(values=list(self.cards_map.keys()))
        self.person_combo.configure(values=list(self.person_map.keys()))
        if self.cards_map: self.card_combo.set(list(self.cards_map.keys())[0])
        if self.person_map: self.person_combo.set(list(self.person_map.keys())[0])

    def load_data(self):
        for w in self.scroll.winfo_children(): w.destroy()
        purchases = db_core.get_recent_purchases(limit=15)
        
        for p in purchases:
            item = ctk.CTkFrame(self.scroll, fg_color="#1f2229", height=85, corner_radius=15)
            item.pack(fill="x", pady=6, padx=5)
            item.pack_propagate(False)
            
            # Info Lado Esquerdo
            left = ctk.CTkFrame(item, fg_color="transparent")
            left.pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(left, text=p['desc'][:22], font=("Segoe UI", 14, "bold"), text_color="white").pack(anchor="w")
            ctk.CTkLabel(left, text=f"{p['date']} • {p['person']}", font=("Segoe UI", 11), text_color="#8a8d91").pack(anchor="w")
            
            # Ações e Valor Lado Direito
            right = ctk.CTkFrame(item, fg_color="transparent")
            right.pack(side="right", padx=15)
            
            ctk.CTkLabel(right, text=f"R$ {p['amount']:.2f}", font=("Segoe UI", 15, "bold"), text_color="#1e90ff").pack()
            
            actions = ctk.CTkFrame(right, fg_color="transparent")
            actions.pack()
            
            # Botão Editar
            ctk.CTkButton(actions, text="✎", width=30, height=25, fg_color="#2b2e35", hover_color="#1e90ff", 
                          command=lambda data=p: self.start_edit(data)).pack(side="left", padx=2)
            # Botão Excluir
            ctk.CTkButton(actions, text="✕", width=30, height=25, fg_color="#2b2e35", hover_color="#ff4c4c", 
                          command=lambda pid=p['id']: self.delete_purchase(pid)).pack(side="left", padx=2)

    def start_edit(self, data):
        """Preenche o formulário com os dados para edição"""
        self.editing_id = data['id']
        self.form_title.configure(text="📝 EDITANDO LANÇAMENTO", text_color="#ffcc00")
        self.btn_save.configure(text="SALVAR ALTERAÇÕES", fg_color="#ffcc00", hover_color="#cca300", text_color="black")
        self.btn_cancel.pack(pady=5, padx=40, fill="x")
        
        self.desc_entry.delete(0, 'end'); self.desc_entry.insert(0, data['desc'])
        self.amount_entry.delete(0, 'end'); self.amount_entry.insert(0, str(data['amount']))
        self.date_entry.delete(0, 'end'); self.date_entry.insert(0, data['date'])
        self.install_combo.set(f"{data['installments']}x")
        self.card_combo.set(data['card'])
        self.person_combo.set(data['person'])
        
        self.desc_entry.focus()

    def cancel_edit(self):
        self.editing_id = None
        self.form_title.configure(text="📝 NOVO LANÇAMENTO", text_color="#1e90ff")
        self.btn_save.configure(text="CONFIRMAR LANÇAMENTO", fg_color="#1e90ff", hover_color="#1466b8", text_color="white")
        self.btn_cancel.pack_forget()
        self.desc_entry.delete(0, 'end')
        self.amount_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def delete_purchase(self, pid):
        if messagebox.askyesno("Confirmar", "Deseja excluir este registro?\nIsso apagará todas as parcelas associadas."):
            if db_core.delete_purchase(pid):
                self.load_data()

    def submit(self):
        desc = self.desc_entry.get()
        val_str = self.amount_entry.get().replace(",", ".")
        data_str = self.date_entry.get()
        
        try:
            val = float(val_str)
            parc = int(self.install_combo.get().replace("x", ""))
            p_id = self.person_map.get(self.person_combo.get())
            c_id = self.cards_map.get(self.card_combo.get())

            if self.editing_id:
                # Lógica de Edição: Primeiro removemos a antiga e criamos a nova com o mesmo ID ou atualizamos
                # Para simplificar e garantir a integridade das parcelas, vamos deletar e reinserir:
                db_core.delete_purchase(self.editing_id)
                db_core.process_purchase(desc, val, data_str, parc, p_id, c_id)
                messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
            else:
                db_core.process_purchase(desc, val, data_str, parc, p_id, c_id)
                messagebox.showinfo("Sucesso", "Nova compra registrada!")

            self.cancel_edit()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Erro", f"Verifique os dados: {e}")