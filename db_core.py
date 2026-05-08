import os
import shutil
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine, Integer, String, Float, Date, ForeignKey, func, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from typing import Optional

# --- CONFIGURAÇÃO DE NUVEM (ONEDRIVE) ---
onedrive = os.environ.get('OneDrive') or os.environ.get('OneDriveConsumer')
LOCAL_DOCS = os.path.join(os.path.expanduser("~"), "Documents", "CARTAO")

if onedrive:
    DOCS_DIR = os.path.join(onedrive, "Documentos", "MeuPDV_Dados")
    old_db = os.path.join(LOCAL_DOCS, "faturas.db")
    new_db = os.path.join(DOCS_DIR, "faturas.db")
    if os.path.exists(old_db) and not os.path.exists(new_db):
        os.makedirs(DOCS_DIR, exist_ok=True)
        shutil.copy2(old_db, new_db)
else:
    DOCS_DIR = LOCAL_DOCS

os.makedirs(DOCS_DIR, exist_ok=True)
DB_PATH = os.path.join(DOCS_DIR, "faturas.db")

# --- BACKUP HISTÓRICO ---
def perform_daily_backup():
    backup_dir = os.path.join(DOCS_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    if os.path.exists(DB_PATH):
        try:
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M")
            backup_path = os.path.join(backup_dir, f"faturas_backup_{timestamp}.db")
            shutil.copy2(DB_PATH, backup_path)
            backups = sorted(
                [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')],
                key=os.path.getmtime)
            while len(backups) > 10:
                os.remove(backups.pop(0))
        except Exception as e:
            print(f"Erro ao gerar backup: {e}")

perform_daily_backup()

# --- BANCO ---
engine       = create_engine(f"sqlite:///{DB_PATH}",
                              connect_args={"check_same_thread": False, "timeout": 10})
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()

# --- MODELOS EXISTENTES ---
class Person(Base):
    __tablename__ = "persons"
    id:   Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

class Card(Base):
    __tablename__ = "cards"
    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    name:        Mapped[str] = mapped_column(String, nullable=False)
    closing_day: Mapped[int] = mapped_column(Integer, nullable=False)

class Purchase(Base):
    __tablename__ = "purchases"
    id:                 Mapped[int]   = mapped_column(Integer, primary_key=True)
    description:        Mapped[str]   = mapped_column(String)
    total_amount:       Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date:      Mapped[date]  = mapped_column(Date, nullable=False)
    installments_count: Mapped[int]   = mapped_column(Integer, default=1)
    person_id:          Mapped[int]   = mapped_column(Integer, ForeignKey("persons.id"))
    card_id:            Mapped[int]   = mapped_column(Integer, ForeignKey("cards.id"))

class Installment(Base):
    __tablename__ = "installments"
    id:                 Mapped[int]   = mapped_column(Integer, primary_key=True)
    purchase_id:        Mapped[int]   = mapped_column(Integer, ForeignKey("purchases.id"))
    installment_number: Mapped[int]   = mapped_column(Integer)
    amount:             Mapped[float] = mapped_column(Float)
    invoice_month:      Mapped[int]   = mapped_column(Integer)
    invoice_year:       Mapped[int]   = mapped_column(Integer)
    is_paid:            Mapped[bool]  = mapped_column(Boolean, default=False)
    purchase = relationship("Purchase")

# --- MODELO DE EMPRÉSTIMOS ---
class Loan(Base):
    __tablename__ = "loans"
    id:               Mapped[int]           = mapped_column(Integer, primary_key=True)
    description:      Mapped[str]           = mapped_column(String, nullable=False)
    total_amount:     Mapped[float]         = mapped_column(Float, nullable=False)
    remaining_amount: Mapped[float]         = mapped_column(Float, nullable=False)
    loan_date:        Mapped[date]          = mapped_column(Date, nullable=False)
    is_active:        Mapped[bool]          = mapped_column(Boolean, default=True)
    debtor_name:      Mapped[Optional[str]] = mapped_column(String, nullable=True)

Base.metadata.create_all(engine)

# --- MIGRAÇÃO: adiciona colunas novas em tabelas já existentes ---
def _run_migrations():
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        existing = [col["name"] for col in inspect(engine).get_columns("loans")]
        if "debtor_name" not in existing:
            conn.execute(text("ALTER TABLE loans ADD COLUMN debtor_name VARCHAR"))
            conn.commit()

_run_migrations()

def init_db():
    db = SessionLocal()
    try:
        if not db.query(Card).first():
            db.add_all([Card(name="INTER", closing_day=14), Card(name="NUBANK", closing_day=7)])
            db.commit()
    except:
        db.rollback()
    finally:
        db.close()

init_db()

# --- OPERAÇÕES EXISTENTES ---

def get_persons():
    db  = SessionLocal()
    res = db.query(Person).all()
    db.close()
    return res

def get_cards():
    db  = SessionLocal()
    res = db.query(Card).all()
    db.close()
    return res

def add_person(name: str):
    db = SessionLocal()
    try:
        if not db.query(Person).filter(Person.name == name).first():
            db.add(Person(name=name))
            db.commit()
            return True
        return False
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_person(person_id):
    db = SessionLocal()
    try:
        if db.query(Purchase).filter(Purchase.person_id == person_id).first():
            return False, "Não é possível excluir: existem compras vinculadas."
        db.query(Person).filter(Person.id == person_id).delete()
        db.commit()
        return True, "Pessoa removida."
    except:
        db.rollback()
        return False, "Erro ao excluir."
    finally:
        db.close()

def process_purchase(description, total_amount, purchase_date_str, installments_count, person_id, card_id):
    db = SessionLocal()
    try:
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card: return False
        p_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
        nova   = Purchase(description=description, total_amount=total_amount, purchase_date=p_date,
                          installments_count=installments_count, person_id=person_id, card_id=card_id)
        db.add(nova)
        db.commit()
        db.refresh(nova)
        inst_val  = round(total_amount / installments_count, 2)
        diff      = round(total_amount - (inst_val * installments_count), 2)
        base_date = (p_date.replace(day=1) if p_date.day <= card.closing_day
                     else (p_date + relativedelta(months=1)).replace(day=1))
        for i in range(1, installments_count + 1):
            curr = base_date + relativedelta(months=(i - 1))
            val  = inst_val + diff if i == installments_count else inst_val
            db.add(Installment(purchase_id=nova.id, installment_number=i, amount=val,
                               invoice_month=curr.month, invoice_year=curr.year))
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_recent_purchases(limit=10):
    db   = SessionLocal()
    data = (db.query(Purchase, Person, Card).select_from(Purchase)
              .join(Person).join(Card).order_by(Purchase.id.desc()).limit(limit).all())
    res  = [{"id": d.Purchase.id, "desc": d.Purchase.description,
             "date": d.Purchase.purchase_date.strftime("%d/%m/%Y"),
             "amount": d.Purchase.total_amount, "person": d.Person.name, "card": d.Card.name}
            for d in data]
    db.close()
    return res

def delete_purchase(pid):
    db = SessionLocal()
    try:
        db.query(Installment).filter(Installment.purchase_id == pid).delete()
        db.query(Purchase).filter(Purchase.id == pid).delete()
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_dashboard_data(month, year):
    db   = SessionLocal()
    data = {"total_geral": 0.0, "totais_cartoes": {}, "totais_pessoas": {},
            "detalhes_pessoas_cartoes": {}}
    for c in db.query(Card).all():
        val = (db.query(func.sum(Installment.amount)).select_from(Installment).join(Purchase)
                 .filter(Purchase.card_id == c.id, Installment.invoice_month == month,
                         Installment.invoice_year == year, Installment.is_paid == False)
                 .scalar() or 0.0)
        data["totais_cartoes"][c.name]  = round(val, 2)
        data["total_geral"]            += val
    for p in db.query(Person).all():
        total_p = 0.0
        data["detalhes_pessoas_cartoes"][p.name] = {}
        for c in db.query(Card).all():
            val_c = (db.query(func.sum(Installment.amount)).select_from(Installment).join(Purchase)
                       .filter(Purchase.person_id == p.id, Purchase.card_id == c.id,
                               Installment.invoice_month == month, Installment.invoice_year == year,
                               Installment.is_paid == False).scalar() or 0.0)
            data["detalhes_pessoas_cartoes"][p.name][c.name] = round(val_c, 2)
            total_p += val_c
        data["totais_pessoas"][p.name] = round(total_p, 2)
    db.close()
    return data

def get_person_debt_details(name, m, y):
    db  = SessionLocal()
    p   = db.query(Person).filter(Person.name == name).first()
    res = {"total": 0.0, "INTER": 0.0, "NUBANK": 0.0}
    if p:
        for c in db.query(Card).all():
            val = (db.query(func.sum(Installment.amount)).select_from(Installment).join(Purchase)
                     .filter(Purchase.person_id == p.id, Purchase.card_id == c.id,
                             Installment.invoice_month == m, Installment.invoice_year == y,
                             Installment.is_paid == False).scalar() or 0.0)
            res[c.name]  = round(val, 2)
            res["total"] += val
    db.close()
    return res

def get_invoice_items(cid, y, m):
    db    = SessionLocal()
    items = (db.query(Installment, Purchase, Person).select_from(Installment)
               .join(Purchase).join(Person)
               .filter(Purchase.card_id == cid, Installment.invoice_year == y,
                       Installment.invoice_month == m).all())
    res   = [{"date": i.Purchase.purchase_date.strftime("%d/%m/%Y"),
              "desc": i.Purchase.description, "inst_num": i.Installment.installment_number,
              "inst_tot": i.Purchase.installments_count, "person": i.Person.name,
              "amount": i.Installment.amount, "is_paid": i.Installment.is_paid} for i in items]
    db.close()
    return res

def get_installments_for_payment(name, m, y):
    db = SessionLocal()
    p  = db.query(Person).filter(Person.name == name).first()
    if not p: return []
    items = (db.query(Installment, Purchase, Card).select_from(Installment)
               .join(Purchase).join(Card)
               .filter(Purchase.person_id == p.id, Installment.invoice_month == m,
                       Installment.invoice_year == y).all())
    res   = [{"inst_id": i.Installment.id, "desc": i.Purchase.description,
              "card": i.Card.name, "inst_num": i.Installment.installment_number,
              "inst_tot": i.Purchase.installments_count, "amount": i.Installment.amount,
              "is_paid": i.Installment.is_paid} for i in items]
    db.close()
    return res

def toggle_payment(iid):
    db = SessionLocal()
    try:
        inst = db.query(Installment).filter(Installment.id == iid).first()
        if inst:
            inst.is_paid = not inst.is_paid
            db.commit()
    except:
        db.rollback()
    finally:
        db.close()

def get_paid_history():
    db   = SessionLocal()
    data = (db.query(Installment, Purchase, Person)
              .select_from(Installment)
              .join(Purchase, Installment.purchase_id == Purchase.id)
              .join(Person,   Purchase.person_id    == Person.id)
              .filter(Installment.is_paid == True)
              .order_by(Installment.id.desc()).all())
    res  = [{"date": i.Purchase.purchase_date.strftime("%d/%m/%Y"),
             "desc": i.Purchase.description, "person": i.Person.name,
             "amount": i.Installment.amount,
             "inst": f"{i.Installment.installment_number}/{i.Purchase.installments_count}"}
            for i in data]
    db.close()
    return res

def get_ranking_data():
    db  = SessionLocal()
    res = (db.query(Person.name, func.sum(Installment.amount))
             .join(Purchase,    Purchase.person_id    == Person.id)
             .join(Installment, Installment.purchase_id == Purchase.id)
             .group_by(Person.name)
             .order_by(func.sum(Installment.amount).desc()).all())
    db.close()
    return res

# --- OPERAÇÕES DE EMPRÉSTIMOS ---

def add_loan(description: str, total_amount: float,
             debtor_name: Optional[str] = None) -> bool:
    """Cadastra uma nova dívida/empréstimo."""
    db = SessionLocal()
    try:
        db.add(Loan(
            description=description,
            total_amount=total_amount,
            remaining_amount=total_amount,
            loan_date=date.today(),
            is_active=True,
            debtor_name=debtor_name,
        ))
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao salvar empréstimo: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def get_active_loans() -> list:
    """Retorna todas as dívidas ainda não quitadas."""
    db    = SessionLocal()
    loans = (db.query(Loan).filter(Loan.is_active == True)
               .order_by(Loan.loan_date.desc()).all())
    for loan in loans:
        db.expunge(loan)
    db.close()
    return loans

def update_loan(loan_id: int, description: str, total_amount: float,
                debtor_name: Optional[str] = None) -> bool:
    """Edita descrição, valor total e devedor de uma dívida."""
    db = SessionLocal()
    try:
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            return False
        # Ajusta remaining proporcionalmente se o total mudar
        if loan.total_amount > 0:
            ratio = loan.remaining_amount / loan.total_amount
        else:
            ratio = 1.0
        loan.description      = description
        loan.total_amount     = total_amount
        loan.remaining_amount = round(total_amount * ratio, 2)
        loan.debtor_name      = debtor_name
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao atualizar empréstimo: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def abate_loan(loan_id: int, value: float) -> bool:
    """Abate um valor da dívida. Marca como inativa se quitar tudo."""
    db = SessionLocal()
    try:
        loan = db.query(Loan).filter(Loan.id == loan_id).first()
        if not loan:
            return False
        loan.remaining_amount = max(0.0, round(loan.remaining_amount - value, 2))
        if loan.remaining_amount == 0.0:
            loan.is_active = False
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao abater empréstimo: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def delete_loan(loan_id: int) -> bool:
    """Remove permanentemente uma dívida do banco."""
    db = SessionLocal()
    try:
        db.query(Loan).filter(Loan.id == loan_id).delete()
        db.commit()
        return True
    except Exception as e:
        print(f"Erro ao excluir empréstimo: {e}")
        db.rollback()
        return False
    finally:
        db.close()