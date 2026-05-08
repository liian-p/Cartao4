import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import db_core
import os

class PaymentsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_items = []
        
        # --- UI INTERFACE ---
        self.h = ctk.CTkFrame(self, corner_radius=12, fg_color="#161920", border_width=1, border_color="#1f2229")
        self.h.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(self.h, text="Gestão de Pagamentos", font=("Segoe UI", 20, "bold")).pack(side="left", padx=20, pady=20)
        
        self.p_combo = ctk.CTkComboBox(self.h, values=[], width=180, corner_radius=8)
        self.p_combo.pack(side="left", padx=10)
        
        self.m_combo = ctk.CTkComboBox(self.h, values=[str(m) for m in range(1, 13)], width=70, corner_radius=8)
        self.m_combo.set(str(datetime.now().month))
        self.m_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(self.h, text="Filtrar", width=90, height=35, font=("Segoe UI", 12, "bold"), 
                      command=self.load_data).pack(side="left", padx=5)
        
        # Botões de Exportação (PNG Mantido e PDF Adicionado)
        ctk.CTkButton(self.h, text="PNG", width=60, fg_color="#2b2e35", hover_color="#3e424b",
                      command=lambda: self.export_document("png")).pack(side="right", padx=10)
        
        ctk.CTkButton(self.h, text="EXPORTAR PDF", width=140, fg_color="#1e90ff", hover_color="#1466b8",
                      font=("Segoe UI", 12, "bold"),
                      command=lambda: self.export_document("pdf")).pack(side="right", padx=5)

        self.list = ctk.CTkScrollableFrame(self, corner_radius=12, fg_color="#161920", border_width=1, border_color="#1f2229")
        self.list.pack(fill="both", expand=True)

    def load_combos(self):
        ps = [p.name for p in db_core.get_persons()]
        if ps:
            self.p_combo.configure(values=ps)
            if self.p_combo.get() in ["CTkComboBox", "", "Selecione a Pessoa"]:
                self.p_combo.set(ps[0])

    def load_data(self):
        for w in self.list.winfo_children(): w.destroy()
        p = self.p_combo.get()
        if p and p != "Cadastre Pessoas":
            ano_atual = 2026
            self.current_items = db_core.get_installments_for_payment(p, int(self.m_combo.get()), ano_atual)
            
            if not self.current_items:
                ctk.CTkLabel(self.list, text="Nenhuma parcela encontrada.", font=("Segoe UI", 14, "italic"), text_color="gray").pack(pady=40)
                return

            for i in self.current_items:
                bg_color = "#1f2229" if not i['is_paid'] else "#121418"
                r = ctk.CTkFrame(self.list, height=55, fg_color=bg_color, corner_radius=8)
                r.pack(fill="x", pady=4, padx=10)
                r.pack_propagate(False)
                
                card_color = "#FF7A00" if i['card'] == "INTER" else "#8A05BE"
                ctk.CTkFrame(r, width=4, fg_color=card_color).pack(side="left", fill="y")

                txt_main = f"{i['desc']} ({i['inst_num']}/{i['inst_tot']})"
                ctk.CTkLabel(r, text=txt_main, font=("Segoe UI", 13, "bold"), text_color="#d1d1d1" if not i['is_paid'] else "gray").pack(side="left", padx=15)
                ctk.CTkLabel(r, text=f"R$ {i['amount']:.2f}", font=("Segoe UI", 14, "bold"), text_color="#00face" if not i['is_paid'] else "gray").pack(side="right", padx=150)
                
                btn_txt = "Reabrir" if i['is_paid'] else "Confirmar"
                btn_color = "#343a40" if i['is_paid'] else "#1e90ff"
                ctk.CTkButton(r, text=btn_txt, width=100, height=30, fg_color=btn_color, command=lambda id=i['inst_id']: self.pay(id)).pack(side="right", padx=10)

    def pay(self, id):
        db_core.toggle_payment(id)
        self.load_data()

    def export_document(self, fmt="pdf"):
        if not self.current_items:
            messagebox.showwarning("Aviso", "Busque os dados antes de exportar.")
            return

        nome = self.p_combo.get()
        mes = self.m_combo.get()
        pendentes = [i for i in self.current_items if not i['is_paid']]
        
        if not pendentes:
            messagebox.showinfo("Aviso", "Não há valores pendentes para este mês.")
            return

        por_banco = {}
        for item in pendentes:
            b = item['card']
            if b not in por_banco: por_banco[b] = []
            por_banco[b].append(item)

        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[("PDF Document", "*.pdf")] if fmt == "pdf" else [("PNG Image", "*.png")],
            initialfile=f"Extrato_{nome}_M{mes}.{fmt}"
        )
        if not file_path: return

        try:
            # Cálculo de altura dinâmica para o documento
            h_header, h_footer = 300, 150
            canvas_w = 900
            canvas_h = h_header + h_footer + (len(por_banco) * 60) + (len(pendentes) * 65)
            
            img = Image.new('RGB', (canvas_w, canvas_h), color=(15, 17, 21))
            draw = ImageDraw.Draw(img)

            # Carregamento de fontes
            try:
                f_title = ImageFont.truetype("arialbd.ttf", 45)
                f_bold = ImageFont.truetype("arialbd.ttf", 24)
                f_reg = ImageFont.truetype("arial.ttf", 18)
            except:
                f_title = f_bold = f_reg = ImageFont.load_default()

            # --- DESENHO DO CABEÇALHO ---
            draw.rectangle([(0, 0), (canvas_w, 220)], fill=(22, 25, 32))
            
            # Inclusão da LOGO (Busca logo.png no diretório raiz)
            logo_path = "logo.png"
            if os.path.exists(logo_path):
                logo_file = Image.open(logo_path).convert("RGBA")
                l_w = 200 # Largura da logo no documento
                l_h = int((l_w / logo_file.size[0]) * logo_file.size[1])
                logo_resized = logo_file.resize((l_w, l_h), Image.Resampling.LANCZOS)
                # Cola a logo no canto superior direito
                img.paste(logo_resized, (canvas_w - l_w - 50, 50), logo_resized)

            draw.text((50, 60), "ELN FINANCE", fill=(30, 144, 255), font=f_title)
            draw.text((50, 130), f"CLIENTE: {nome.upper()}", fill=(240, 240, 240), font=f_bold)
            draw.text((50, 170), f"COMPETÊNCIA: {mes}/2026", fill=(160, 160, 160), font=f_reg)

            # --- CONTEÚDO DINÂMICO ---
            y = 260
            total_geral = 0.0

            for banco, itens in por_banco.items():
                b_color = (255, 122, 0) if banco == "INTER" else (138, 5, 190)
                draw.text((50, y), f"LANÇAMENTOS {banco}", fill=b_color, font=f_bold)
                y += 50
                
                for i in itens:
                    draw.rectangle([(50, y), (canvas_w - 50, y + 55)], fill=(22, 25, 32), outline=(45, 48, 56))
                    draw.rectangle([(50, y), (56, y + 55)], fill=b_color)
                    
                    draw.text((75, y + 15), i['desc'][:45], fill=(240, 240, 240), font=f_reg)
                    draw.text((500, y + 18), f"Parc. {i['inst_num']}/{i['inst_tot']}", fill=(160, 160, 160), font=f_reg)
                    
                    val_txt = f"R$ {i['amount']:.2f}"
                    draw.text((canvas_w - 220, y + 12), val_txt, fill=(240, 240, 240), font=f_bold)
                    
                    total_geral += i['amount']
                    y += 65
                y += 40

            # --- RODAPÉ ---
            draw.rectangle([(0, canvas_h - 100), (canvas_w, canvas_h)], fill=(22, 25, 32))
            resumo = f"TOTAL A PAGAR: R$ {total_geral:.2f}"
            draw.text((canvas_w // 2 - 180, canvas_h - 75), resumo, fill=(30, 144, 255), font=f_bold)

            # Salvamento Dual (PDF ou PNG)
            if fmt == "pdf":
                img.save(file_path, "PDF", resolution=100.0)
            else:
                img.save(file_path)

            messagebox.showinfo("Sucesso", f"Extrato {fmt.upper()} gerado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {e}")