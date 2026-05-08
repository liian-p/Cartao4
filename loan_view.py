import os
import customtkinter as ctk
from tkinter import messagebox
from collections import defaultdict
from typing import TYPE_CHECKING, cast
import db_core

if TYPE_CHECKING:
    from main import App


class LoanView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="#161920", corner_radius=12,
                                   border_width=1, border_color="#1f2229")
        self.header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.header, text="💰 Gestão de Empréstimos e Débitos",
                     font=("Segoe UI", 20, "bold")).pack(side="left", padx=20, pady=18)

        ctk.CTkButton(self.header, text="👤 Ver por Pessoa", width=160, height=36,
                      fg_color="#1e3a5f", hover_color="#2a5298",
                      command=self.open_person_view).pack(side="right", padx=20, pady=18)

        # --- CONTAINER PRINCIPAL ---
        self.main_container = ctk.CTkFrame(self, fg_color="#161920", corner_radius=12,
                                           border_width=1, border_color="#2b2e35")
        self.main_container.pack(fill="both", expand=True, padx=2, pady=2)

        # --- FORMULÁRIO ---
        self.form_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.form_frame.pack(fill="x", padx=20, pady=20)

        self.desc_entry = ctk.CTkEntry(self.form_frame,
                                       placeholder_text="Descrição (Ex: Empréstimo Nubank)",
                                       width=260, height=40)
        self.desc_entry.grid(row=0, column=0, padx=5)

        self.val_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Valor Total (R$)",
                                      width=130, height=40)
        self.val_entry.grid(row=0, column=1, padx=5)

        self.debtor_combo = ctk.CTkComboBox(self.form_frame, width=170, height=40,
                                             values=self._get_person_names())
        self.debtor_combo.set("Devedor (opcional)")
        self.debtor_combo.grid(row=0, column=2, padx=5)

        self.save_btn = ctk.CTkButton(self.form_frame, text="Cadastrar Dívida",
                                      fg_color="#28a745", hover_color="#1e7e34",
                                      width=150, height=40, font=("Segoe UI", 12, "bold"),
                                      command=self.save_loan)
        self.save_btn.grid(row=0, column=3, padx=10)

        # --- LISTA ---
        ctk.CTkLabel(self.main_container, text="Dívidas Ativas",
                     font=("Segoe UI", 16, "bold"), text_color="#8a8d91").pack(
            anchor="w", padx=25, pady=(10, 0))

        self.scroll_list = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=15, pady=(5, 0))

        # --- RODAPÉ TOTAL ---
        footer = ctk.CTkFrame(self.main_container, fg_color="#0d1117", corner_radius=8)
        footer.pack(fill="x", padx=15, pady=10)

        self.total_label = ctk.CTkLabel(footer, text="Total em Dívidas: R$ 0,00",
                                        font=("Segoe UI", 15, "bold"), text_color="#e74c3c")
        self.total_label.pack(pady=10)

    # ------------------------------------------------------------------ helpers
    def _app(self) -> "App":
        return cast("App", self.winfo_toplevel())

    def _get_person_names(self) -> list:
        return [""] + [p.name for p in db_core.get_persons()]

    # ------------------------------------------------------------------ dados
    def load_data(self):
        for child in self.scroll_list.winfo_children():
            child.destroy()

        self.debtor_combo.configure(values=self._get_person_names())

        loans = db_core.get_active_loans()

        if not loans:
            ctk.CTkLabel(self.scroll_list, text="Nenhum empréstimo ativo.",
                         font=("Segoe UI", 13, "italic")).pack(pady=20)
            self.total_label.configure(text="Total em Dívidas: R$ 0,00")
            return

        total = sum(l.remaining_amount for l in loans)

        for loan in loans:
            item = ctk.CTkFrame(self.scroll_list, fg_color="#1c1f26", corner_radius=10)
            item.pack(fill="x", pady=5, padx=5)

            debtor_line = f"  👤 {loan.debtor_name}" if loan.debtor_name else ""
            info_text = f"{loan.description}{debtor_line}\nData: {loan.loan_date.strftime('%d/%m/%Y')}"
            ctk.CTkLabel(item, text=info_text, font=("Segoe UI", 13, "bold"),
                         justify="left").pack(side="left", padx=20, pady=12)

            val_text = f"Total: R$ {loan.total_amount:.2f}\nRestante: R$ {loan.remaining_amount:.2f}"
            ctk.CTkLabel(item, text=val_text, font=("Consolas", 12),
                         text_color="#1e90ff").pack(side="left", padx=30, pady=12)

            btn_frame = ctk.CTkFrame(item, fg_color="transparent")
            btn_frame.pack(side="right", padx=10, pady=10)

            ctk.CTkButton(btn_frame, text="Abater", width=75, height=34,
                          fg_color="#3d4147", hover_color="#52575e",
                          command=lambda l=loan: self.open_abate_dialog(l)).pack(side="left", padx=3)

            ctk.CTkButton(btn_frame, text="✏️", width=38, height=34,
                          fg_color="#1e3a5f", hover_color="#2a5298",
                          command=lambda l=loan: self.open_edit_dialog(l)).pack(side="left", padx=3)

            ctk.CTkButton(btn_frame, text="📷", width=38, height=34,
                          fg_color="#1a3a2a", hover_color="#1e7e34",
                          command=lambda l=loan: self.export_png(l)).pack(side="left", padx=3)

            ctk.CTkButton(btn_frame, text="🗑", width=38, height=34,
                          fg_color="#5a1a1a", hover_color="#8b0000",
                          command=lambda l=loan: self.confirm_delete(l)).pack(side="left", padx=3)

        self.total_label.configure(text=f"Total em Dívidas: R$ {total:.2f}")

    # ------------------------------------------------------------------ ações
    def save_loan(self):
        desc = self.desc_entry.get().strip()
        val = self.val_entry.get().strip()
        debtor = self.debtor_combo.get().strip()
        if debtor == "Devedor (opcional)":
            debtor = ""

        if not desc or not val:
            self._app().show_toast("Preencha descrição e valor!", "error")
            return
        try:
            val_float = float(val.replace(",", "."))
            if db_core.add_loan(desc, val_float, debtor or None):
                self._app().show_toast("Empréstimo salvo!", "success")
                self.desc_entry.delete(0, "end")
                self.val_entry.delete(0, "end")
                self.debtor_combo.set("Devedor (opcional)")
                self.load_data()
            else:
                self._app().show_toast("Erro ao salvar no banco.", "error")
        except ValueError:
            self._app().show_toast("Valor inválido!", "error")

    def confirm_delete(self, loan):
        ok = messagebox.askyesno(
            "Excluir Dívida",
            f"Tem certeza que deseja excluir '{loan.description}'?\nEsta ação não pode ser desfeita."
        )
        if ok:
            if db_core.delete_loan(loan.id):
                self._app().show_toast("Dívida excluída!", "success")
                self.load_data()
            else:
                self._app().show_toast("Erro ao excluir.", "error")

    def open_abate_dialog(self, loan):
        dialog = ctk.CTkInputDialog(
            text=f"Quanto deseja pagar de '{loan.description}'?", title="Abater Valor")
        value = dialog.get_input()
        if value:
            try:
                val_pay = float(value.replace(",", "."))
                if db_core.abate_loan(loan.id, val_pay):
                    self._app().show_toast("Pagamento registrado!", "success")
                    self.load_data()
            except ValueError:
                self._app().show_toast("Valor inválido!", "error")

    # ------------------------------------------------------------------ editar
    def open_edit_dialog(self, loan):
        win = ctk.CTkToplevel(self)
        win.title("Editar Dívida")
        win.geometry("420x310")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(win, text="✏️  Editar Dívida",
                     font=("Segoe UI", 16, "bold")).pack(pady=(20, 15))

        desc_entry = ctk.CTkEntry(win, width=360, height=40, placeholder_text="Descrição")
        desc_entry.insert(0, loan.description)
        desc_entry.pack(pady=5)

        val_entry = ctk.CTkEntry(win, width=360, height=40, placeholder_text="Valor Total (R$)")
        val_entry.insert(0, str(loan.total_amount))
        val_entry.pack(pady=5)

        debtor_entry = ctk.CTkEntry(win, width=360, height=40,
                                    placeholder_text="Devedor (opcional)")
        if loan.debtor_name:
            debtor_entry.insert(0, loan.debtor_name)
        debtor_entry.pack(pady=5)

        def save_edit():
            new_desc   = desc_entry.get().strip()
            new_val    = val_entry.get().strip()
            new_debtor = debtor_entry.get().strip()
            if not new_desc or not new_val:
                self._app().show_toast("Preencha descrição e valor!", "error")
                return
            try:
                new_val_f = float(new_val.replace(",", "."))
                if db_core.update_loan(loan.id, new_desc, new_val_f, new_debtor or None):
                    win.destroy()
                    self._app().show_toast("Dívida atualizada!", "success")
                    self.load_data()
                else:
                    self._app().show_toast("Erro ao atualizar.", "error")
            except ValueError:
                self._app().show_toast("Valor inválido!", "error")

        ctk.CTkButton(win, text="Salvar Alterações", fg_color="#28a745", hover_color="#1e7e34",
                      width=360, height=40, command=save_edit).pack(pady=15)

    # ------------------------------------------------------------------ PNG
    def export_png(self, loan):
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self._app().show_toast("Instale Pillow: pip install Pillow", "error")
            return

        try:
            W, H   = 620, 300
            BG     = (13,  17,  23)
            CARD   = (22,  25,  32)
            ACCENT = (30,  144, 255)
            RED    = (231, 76,  60)
            WHITE  = (255, 255, 255)
            MUTED  = (138, 141, 145)
            HEADER = (20,  40,  80)

            img  = Image.new("RGB", (W, H), BG)
            draw = ImageDraw.Draw(img)

            draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=18,
                                   fill=CARD, outline=ACCENT, width=2)
            draw.rounded_rectangle([15, 15, W - 15, 68], radius=18, fill=HEADER)
            draw.rectangle([15, 50, W - 15, 68], fill=HEADER)

            def font(size):
                for name in ["segoeuib.ttf", "segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]:
                    try:
                        return ImageFont.truetype(name, size)
                    except Exception:
                        pass
                return ImageFont.load_default()

            draw.text((30, 28), "ELN Finance — Comprovante de Divida",
                      fill=WHITE, font=font(17))

            draw.text((30, 85),  "DEVEDOR",    fill=MUTED, font=font(11))
            draw.text((30, 102), loan.debtor_name or "—", fill=WHITE, font=font(20))

            draw.text((30, 142), "DESCRICAO",  fill=MUTED, font=font(11))
            draw.text((30, 159), loan.description, fill=WHITE, font=font(16))

            draw.line([(30, 200), (W - 30, 200)], fill=(45, 50, 60), width=1)

            draw.text((30,  215), "VALOR TOTAL", fill=MUTED,  font=font(11))
            draw.text((30,  232), f"R$ {loan.total_amount:.2f}",
                      fill=ACCENT, font=font(20))

            draw.text((320, 215), "RESTANTE",   fill=MUTED, font=font(11))
            draw.text((320, 232), f"R$ {loan.remaining_amount:.2f}",
                      fill=RED,   font=font(20))

            draw.text((30,  268), f"{loan.loan_date.strftime('%d/%m/%Y')}",
                      fill=MUTED, font=font(12))
            draw.text((W - 120, 268), "ELN Finance", fill=(60, 65, 71), font=font(12))

            safe = "".join(c for c in (loan.debtor_name or loan.description)
                           if c.isalnum() or c in " _-").strip().replace(" ", "_")
            filename  = f"divida_{safe}_{loan.id}.png"
            save_path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
            img.save(save_path)
            self._app().show_toast("PNG salvo na Área de Trabalho!", "success")

        except Exception as e:
            self._app().show_toast(f"Erro ao exportar: {e}", "error")

    # ------------------------------------------------------------------ por pessoa
    def open_person_view(self):
        loans = db_core.get_active_loans()

        win = ctk.CTkToplevel(self)
        win.title("Resumo por Pessoa")
        win.geometry("520x540")
        win.resizable(False, False)
        win.grab_set()

        ctk.CTkLabel(win, text="👤  Acumulado por Pessoa",
                     font=("Segoe UI", 18, "bold")).pack(pady=(20, 15))

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        grouped = defaultdict(list)
        for loan in loans:
            grouped[loan.debtor_name or "Sem identificação"].append(loan)

        if not grouped:
            ctk.CTkLabel(scroll, text="Nenhuma dívida ativa.",
                         font=("Segoe UI", 13, "italic")).pack(pady=20)
        else:
            for person, person_loans in sorted(grouped.items()):
                total = sum(l.remaining_amount for l in person_loans)

                card = ctk.CTkFrame(scroll, fg_color="#1c1f26", corner_radius=10)
                card.pack(fill="x", pady=5)

                ctk.CTkLabel(card, text=person,
                             font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=15, pady=(10, 3))

                for l in person_loans:
                    ctk.CTkLabel(card,
                                 text=f"  • {l.description}  →  R$ {l.remaining_amount:.2f}",
                                 font=("Consolas", 12),
                                 text_color="#8a8d91").pack(anchor="w", padx=15)

                ctk.CTkLabel(card,
                             text=f"Total devedor: R$ {total:.2f}",
                             font=("Segoe UI", 13, "bold"),
                             text_color="#1e90ff").pack(anchor="e", padx=15, pady=(6, 10))

        total_geral = sum(l.remaining_amount for l in loans)
        footer = ctk.CTkFrame(win, fg_color="#0d1117", corner_radius=8)
        footer.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(footer, text=f"Total Geral em Aberto: R$ {total_geral:.2f}",
                     font=("Segoe UI", 14, "bold"), text_color="#e74c3c").pack(pady=10)