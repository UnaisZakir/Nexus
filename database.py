"""
Nexus ERP - Comprehensive Database Models
Covers: Users, Plans, Chart of Accounts, Journal Entries, Invoices,
        Bank Transactions, Reconciliation, Payroll, Tax, and Audit Logs
"""
import os, uuid, bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    ForeignKey, Boolean, Text, Date
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.exc import IntegrityError

load_dotenv()

DEFAULT_MSSQL_URL = "mssql+pyodbc://@localhost/NexusERP?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_MSSQL_URL)

def _get_working_engine(url: str):
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    if "mssql" in url:
        try:
            test_url = url + ("&timeout=3" if "?" in url else "?timeout=3")
            eng = create_engine(test_url, connect_args=connect_args, pool_pre_ping=True)
            with eng.connect() as conn:
                pass
            return eng
        except Exception:
            # Fallback to local SQLite if MS SQL Server instance is not accessible
            return create_engine("sqlite:///nexus.db", connect_args={"check_same_thread": False})
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

engine = _get_working_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────
# 1. USERS & SUBSCRIPTION PLANS
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id                  = Column(Integer, primary_key=True, index=True)
    username            = Column(String, unique=True, index=True, nullable=False)
    email               = Column(String, unique=True, index=True, nullable=False)
    password_hash       = Column(String, nullable=False)
    role                = Column(String, default="CEO")       # CEO | CFO | Accountant
    plan                = Column(String, default="corporate") # starter | partnership | corporate
    company_name        = Column(String, default="Nexus Enterprise")
    industry            = Column(String, default="General Services")
    tax_id              = Column(String, nullable=True)       # NTN / Tax ID
    business_type       = Column(String, default="Private Limited") # Sole Proprietor | Partnership | Private Limited
    annual_revenue      = Column(String, default="Rs 1M - 10M")
    currency            = Column(String, default="USD")
    currency_symbol     = Column(String, default="$")
    language            = Column(String, default="en")        # en | es | fr | de | ur | ar
    subscription_status = Column(String, default="trialing")  # trialing | active | expired
    trial_ends_at       = Column(DateTime, nullable=True)
    is_superadmin       = Column(Boolean, default=False)      # App Creator Master Admin
    created_at          = Column(DateTime, server_default=func.now())
    is_active           = Column(Boolean, default=True)


class TeamMember(Base):
    __tablename__ = "team_members"
    id          = Column(Integer, primary_key=True, index=True)
    owner_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    member_name = Column(String, nullable=False)
    email       = Column(String, nullable=False)
    role_title  = Column(String, default="Accountant") # Senior Auditor, Junior Accountant, Payroll Specialist
    permissions = Column(String, default="read_write") # read_only, read_write, full_access
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, server_default=func.now(), index=True)





# ─────────────────────────────────────────────
# 2. CHART OF ACCOUNTS
# ─────────────────────────────────────────────
class Account(Base):
    __tablename__ = "accounts"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code         = Column(String, nullable=False, index=True)
    name         = Column(String, nullable=False)
    account_type = Column(String, nullable=False, index=True)
    sub_type     = Column(String)
    description  = Column(Text)
    is_active    = Column(Boolean, default=True)
    balance      = Column(Float, default=0.0)
    created_at   = Column(DateTime, server_default=func.now())

    lines        = relationship("JournalLine", back_populates="account")


# ─────────────────────────────────────────────
# 3. JOURNAL ENTRIES (Double-Entry Core)
# ─────────────────────────────────────────────
class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date        = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    reference   = Column(String)
    entry_type  = Column(String, default="manual")
    created_at  = Column(DateTime, server_default=func.now(), index=True)

    lines       = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"
    id         = Column(Integer, primary_key=True, index=True)
    entry_id   = Column(Integer, ForeignKey("journal_entries.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    debit      = Column(Float, default=0.0)
    credit     = Column(Float, default=0.0)
    description = Column(String)

    entry   = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="lines")


# ─────────────────────────────────────────────
# 4. CUSTOMERS & SUPPLIERS
# ─────────────────────────────────────────────
class Contact(Base):
    __tablename__ = "contacts"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact_type = Column(String, nullable=False, index=True)
    name         = Column(String, nullable=False, index=True)
    email        = Column(String)
    phone        = Column(String)
    address      = Column(Text)
    tax_number   = Column(String)
    created_at   = Column(DateTime, server_default=func.now())

    invoices     = relationship("Invoice", back_populates="contact")


# ─────────────────────────────────────────────
# 5. INVOICES (Accounts Receivable)
# ─────────────────────────────────────────────
class Invoice(Base):
    __tablename__ = "invoices"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    contact_id   = Column(Integer, ForeignKey("contacts.id"), index=True)
    invoice_no   = Column(String, nullable=False, index=True)
    date         = Column(String, nullable=False)
    due_date     = Column(String)
    status       = Column(String, default="draft", index=True)
    subtotal     = Column(Float, default=0.0)
    tax_amount   = Column(Float, default=0.0)
    total        = Column(Float, default=0.0)
    amount_paid  = Column(Float, default=0.0)
    notes        = Column(Text)
    created_at   = Column(DateTime, server_default=func.now(), index=True)

    user         = relationship("User", foreign_keys=[user_id])
    contact      = relationship("Contact", back_populates="invoices")
    lines        = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"
    id          = Column(Integer, primary_key=True, index=True)
    invoice_id  = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    description = Column(String, nullable=False)
    quantity    = Column(Float, default=1.0)
    unit_price  = Column(Float, default=0.0)
    tax_rate    = Column(Float, default=0.0)
    amount      = Column(Float, default=0.0)

    invoice     = relationship("Invoice", back_populates="lines")


# ─────────────────────────────────────────────
# 6. BANK TRANSACTIONS & RECONCILIATION
# ─────────────────────────────────────────────
class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date        = Column(String, nullable=False)
    description = Column(String)
    reference   = Column(String)
    amount      = Column(Float, nullable=False)
    balance     = Column(Float)
    status      = Column(String, default="unmatched", index=True)
    match_id    = Column(String)
    source      = Column(String, default="bank")
    imported_at = Column(DateTime, server_default=func.now())


class ReconciliationMatch(Base):
    __tablename__ = "reconciliation_matches"
    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_type       = Column(String)
    confidence_score = Column(Float)
    created_at       = Column(DateTime, server_default=func.now())


# ─────────────────────────────────────────────
# 7. PAYROLL (Partnership & Corporate Plans)
# ─────────────────────────────────────────────
class Employee(Base):
    __tablename__ = "employees"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name         = Column(String, nullable=False, index=True)
    designation  = Column(String)
    salary       = Column(Float, nullable=False)
    tax_rate     = Column(Float, default=0.0)
    is_active    = Column(Boolean, default=True)
    joined_date  = Column(String)

    payrolls     = relationship("Payroll", back_populates="employee")


class Payroll(Base):
    __tablename__ = "payroll"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    employee_id   = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    period        = Column(String, nullable=False, index=True)
    gross_salary  = Column(Float, default=0.0)
    deductions    = Column(Float, default=0.0)
    tax_withheld  = Column(Float, default=0.0)
    net_salary    = Column(Float, default=0.0)
    paid          = Column(Boolean, default=False)
    paid_on       = Column(String)

    employee      = relationship("Employee", back_populates="payrolls")


# ─────────────────────────────────────────────
# 8. AUDIT TRAIL
# ─────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action     = Column(String, nullable=False, index=True)
    entity     = Column(String)
    details    = Column(Text)
    ip_address = Column(String)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name          = Column(String, nullable=False)
    cost          = Column(Float, nullable=False)
    salvage_value = Column(Float, default=0.0)
    useful_life   = Column(Integer, nullable=False)
    purchase_date = Column(String, nullable=False)
    accumulated_depreciation = Column(Float, default=0.0)
    created_at    = Column(DateTime, server_default=func.now())


# ─────────────────────────────────────────────
# 9. EXECUTIVE COMMUNICATION & THOUGHT SYSTEM
# ─────────────────────────────────────────────
class CommunicationMessage(Base):
    __tablename__ = "communication_messages"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company_name    = Column(String, default="Nexus Enterprise")
    sender_username = Column(String, nullable=False, index=True)
    sender_role     = Column(String, nullable=False, index=True)
    recipient_role  = Column(String, default="ALL", index=True)
    subject         = Column(String, nullable=False)
    message         = Column(Text, nullable=False)
    category        = Column(String, default="General Exchange", index=True)
    urgency         = Column(String, default="Normal")
    status          = Column(String, default="Pending", index=True)
    amount          = Column(Float, default=0.0)
    parent_id       = Column(Integer, ForeignKey("communication_messages.id"), nullable=True)
    created_at      = Column(DateTime, server_default=func.now(), index=True)

    parent          = relationship("CommunicationMessage", remote_side=[id], backref="replies")


# ─────────────────────────────────────────────
# 10. SAAS BILLING & PAYMENT TRANSACTIONS
# ─────────────────────────────────────────────
class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount          = Column(Float, nullable=False)
    currency        = Column(String, default="USD")
    plan_name       = Column(String, nullable=False)
    gateway         = Column(String, default="Stripe")     # Stripe | CreditCard | PayPal
    status          = Column(String, default="success")    # success | failed
    transaction_ref = Column(String, nullable=False)
    created_at      = Column(DateTime, server_default=func.now(), index=True)


CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "PKR": "Rs",
    "INR": "₹", "AED": "AED", "SAR": "SAR", "CAD": "$",
    "AUD": "$", "JPY": "¥"
}

EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "PKR": 278.5,
    "INR": 83.5,
    "AED": 3.67,
    "SAR": 3.75,
    "CAD": 1.36,
    "AUD": 1.52,
    "JPY": 155.0
}


# ─────────────────────────────────────────────
# DB Helpers
# ─────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine():
    return engine


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────
def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "CEO",
    plan: str = "corporate",
    company: str = "Nexus Enterprise",
    industry: str = "General Services",
    tax_id: str = "",
    business_type: str = "Private Limited",
    annual_revenue: str = "Rs 1M - 10M",
    currency: str = "USD",
    language: str = "en",
    is_superadmin: bool = False
):
    db = SessionLocal()
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        trial_ends = datetime.utcnow() + timedelta(days=30)
        symbol = CURRENCY_SYMBOLS.get(currency, "$")
        user = User(
            username=username,
            email=email,
            password_hash=hashed,
            role=role,
            plan=plan,
            company_name=company,
            industry=industry,
            tax_id=tax_id,
            business_type=business_type,
            annual_revenue=annual_revenue,
            currency=currency,
            currency_symbol=symbol,
            language=language,
            subscription_status="trialing",
            trial_ends_at=trial_ends,
            is_superadmin=is_superadmin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # Seed default chart of accounts
        _seed_accounts(db, user.id)
        _log(db, user.id, "REGISTERED", f"User {username} registered as {role} on 30-day Free Trial ({plan} plan)")
        return user.id
    except IntegrityError:
        db.rollback()
        return None
    finally:
        db.close()

def authenticate_user(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            user_role = getattr(user, 'role', None) or "CEO"
            trial_ends = user.trial_ends_at or (datetime.utcnow() + timedelta(days=30))
            days_left = max(0, (trial_ends - datetime.utcnow()).days)
            symbol = getattr(user, 'currency_symbol', None) or CURRENCY_SYMBOLS.get(user.currency, "$")
            lang = getattr(user, 'language', None) or "en"
            sub_status = getattr(user, 'subscription_status', None) or "trialing"
            rate = EXCHANGE_RATES.get(user.currency, 1.0)

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user_role,
                "plan": user.plan,
                "company": user.company_name,
                "industry": getattr(user, 'industry', 'General Services') or 'General Services',
                "tax_id": getattr(user, 'tax_id', '') or '',
                "business_type": getattr(user, 'business_type', 'Private Limited') or 'Private Limited',
                "currency": user.currency,
                "currency_symbol": symbol,
                "exchange_rate": rate,
                "language": lang,
                "subscription_status": sub_status,
                "trial_days_left": days_left,
                "is_superadmin": getattr(user, 'is_superadmin', False) or False
            }
        return None
    finally:
        db.close()



def _seed_accounts(db, user_id: int):
    """Seed standard chart of accounts for a new user."""
    accounts = [
        # Assets
        Account(user_id=user_id, code="1000", name="Cash at Bank",           account_type="Asset",     sub_type="Current Asset", balance=145000.0),
        Account(user_id=user_id, code="1010", name="Petty Cash",              account_type="Asset",     sub_type="Current Asset", balance=5000.0),
        Account(user_id=user_id, code="1200", name="Accounts Receivable",     account_type="Asset",     sub_type="Current Asset", balance=62000.0),
        Account(user_id=user_id, code="1300", name="Inventory",               account_type="Asset",     sub_type="Current Asset", balance=38000.0),
        Account(user_id=user_id, code="1400", name="Prepaid Expenses",        account_type="Asset",     sub_type="Current Asset", balance=12000.0),
        Account(user_id=user_id, code="1500", name="Property & Equipment",    account_type="Asset",     sub_type="Fixed Asset", balance=210000.0),
        Account(user_id=user_id, code="1510", name="Accumulated Depreciation",account_type="Asset",     sub_type="Fixed Asset", balance=-25000.0),
        # Liabilities
        Account(user_id=user_id, code="2000", name="Accounts Payable",        account_type="Liability", sub_type="Current Liability", balance=28000.0),
        Account(user_id=user_id, code="2100", name="Accrued Liabilities",     account_type="Liability", sub_type="Current Liability", balance=14000.0),
        Account(user_id=user_id, code="2200", name="VAT / Sales Tax Payable", account_type="Liability", sub_type="Current Liability", balance=9500.0),
        Account(user_id=user_id, code="2300", name="Payroll Tax Payable",     account_type="Liability", sub_type="Current Liability", balance=11200.0),
        Account(user_id=user_id, code="2500", name="Long-term Loans",         account_type="Liability", sub_type="Long-term Liability", balance=75000.0),
        # Equity
        Account(user_id=user_id, code="3000", name="Owner's Capital",         account_type="Equity",    sub_type="Capital", balance=200000.0),
        Account(user_id=user_id, code="3100", name="Retained Earnings",       account_type="Equity",    sub_type="Retained Earnings", balance=109300.0),
        Account(user_id=user_id, code="3200", name="Drawings / Dividends",    account_type="Equity",    sub_type="Drawings", balance=0.0),
        # Revenue
        Account(user_id=user_id, code="4000", name="Sales Revenue",           account_type="Revenue",   sub_type="Operating Revenue", balance=240000.0),
        Account(user_id=user_id, code="4100", name="Service Revenue",         account_type="Revenue",   sub_type="Operating Revenue", balance=95000.0),
        Account(user_id=user_id, code="4200", name="Other Income",            account_type="Revenue",   sub_type="Other Income", balance=8500.0),
        Account(user_id=user_id, code="4300", name="Interest Income",         account_type="Revenue",   sub_type="Other Income", balance=1200.0),
        # Expenses
        Account(user_id=user_id, code="5000", name="Cost of Goods Sold",      account_type="Expense",   sub_type="Cost of Sales", balance=110000.0),
        Account(user_id=user_id, code="5100", name="Salaries & Wages",        account_type="Expense",   sub_type="Operating Expense", balance=85000.0),
        Account(user_id=user_id, code="5200", name="Rent Expense",            account_type="Expense",   sub_type="Operating Expense", balance=18000.0),
        Account(user_id=user_id, code="5300", name="Utilities",               account_type="Expense",   sub_type="Operating Expense", balance=6200.0),
        Account(user_id=user_id, code="5400", name="Office Supplies",         account_type="Expense",   sub_type="Operating Expense", balance=3400.0),
        Account(user_id=user_id, code="5500", name="Marketing & Advertising", account_type="Expense",   sub_type="Operating Expense", balance=14500.0),
        Account(user_id=user_id, code="5600", name="Depreciation Expense",    account_type="Expense",   sub_type="Operating Expense", balance=5000.0),
        Account(user_id=user_id, code="5700", name="Bank Charges",            account_type="Expense",   sub_type="Finance Cost", balance=850.0),
        Account(user_id=user_id, code="5800", name="Interest Expense",        account_type="Expense",   sub_type="Finance Cost", balance=1800.0),
        Account(user_id=user_id, code="5900", name="Income Tax Expense",      account_type="Expense",   sub_type="Tax", balance=0.0),
    ]
    db.bulk_save_objects(accounts)
    db.commit()

def _log(db, user_id, action, details=""):
    log = AuditLog(user_id=user_id, action=action, details=details)
    db.add(log)
    db.commit()

# ─────────────────────────────────────────────
# Initialize DB & Migration
# ─────────────────────────────────────────────
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Safe schema migration for MS SQL Server and SQLite
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("users")]
            with engine.connect() as conn:
                if "role" not in columns:
                    conn.execute(text("ALTER TABLE users ADD role VARCHAR(50) DEFAULT 'CEO'"))
                if "industry" not in columns:
                    conn.execute(text("ALTER TABLE users ADD industry VARCHAR(100) DEFAULT 'General Services'"))
                if "tax_id" not in columns:
                    conn.execute(text("ALTER TABLE users ADD tax_id VARCHAR(100) DEFAULT ''"))
                if "business_type" not in columns:
                    conn.execute(text("ALTER TABLE users ADD business_type VARCHAR(100) DEFAULT 'Private Limited'"))
                if "annual_revenue" not in columns:
                    conn.execute(text("ALTER TABLE users ADD annual_revenue VARCHAR(100) DEFAULT 'Rs 1M - 10M'"))
                if "currency_symbol" not in columns:
                    conn.execute(text("ALTER TABLE users ADD currency_symbol VARCHAR(10) DEFAULT '$'"))
                if "language" not in columns:
                    conn.execute(text("ALTER TABLE users ADD language VARCHAR(10) DEFAULT 'en'"))
                if "subscription_status" not in columns:
                    conn.execute(text("ALTER TABLE users ADD subscription_status VARCHAR(50) DEFAULT 'trialing'"))
                if "trial_ends_at" not in columns:
                    conn.execute(text("ALTER TABLE users ADD trial_ends_at DATETIME NULL"))
                if "is_superadmin" not in columns:
                    conn.execute(text("ALTER TABLE users ADD is_superadmin BOOLEAN DEFAULT 0"))
                conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")



    # Seed Executive Demo Users & SuperAdmin Creator if missing
    db = SessionLocal()
    try:
        demos = [
            ("ceo", "ceo@nexus.com", "password123", "CEO", "corporate", "Nexus Enterprise", False),
            ("cfo", "cfo@nexus.com", "password123", "CFO", "corporate", "Nexus Enterprise", False),
            ("accountant", "accountant@nexus.com", "password123", "Accountant", "corporate", "Nexus Enterprise", False),
            ("admin", "admin@nexus.com", "admin123", "CEO", "corporate", "Nexus Global Master HQ", True)
        ]

        for username, email, pwd, role, plan, company, is_sa in demos:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                create_user(username=username, email=email, password=pwd, role=role, plan=plan, company=company, is_superadmin=is_sa)
            else:
                if not getattr(existing, 'role', None):
                    existing.role = role
                if is_sa:
                    existing.is_superadmin = True
                db.commit()

                
        # Seed initial tri-party thoughts and communication messages if none exist
        msg_count = db.query(CommunicationMessage).count()
        if msg_count == 0:
            ceo_user = db.query(User).filter(User.username == "ceo").first()
            uid = ceo_user.id if ceo_user else 1
            
            demo_msgs = [
                CommunicationMessage(
                    user_id=uid,
                    company_name="Nexus Enterprise",
                    sender_username="ceo",
                    sender_role="CEO",
                    recipient_role="ALL",
                    subject="Q3 Executive Growth & Cost Alignment",
                    message="Team, let's accelerate our enterprise market expansion in Q3 while maintaining a minimum 25% profit margin. CFO, please present the capital allocation proposal for engineering hires.",
                    category="Strategic Directive",
                    urgency="Important",
                    status="Acknowledged"
                ),
                CommunicationMessage(
                    user_id=uid,
                    company_name="Nexus Enterprise",
                    sender_username="cfo",
                    sender_role="CFO",
                    recipient_role="CEO",
                    subject="Capital Expenditure Approval Request for AI Infrastructure",
                    message="Proposed $45,000 budget for upgrading financial analytics compute clusters. Cash reserves stand strong at $150,000, keeping our current ratio at a healthy 2.45.",
                    category="Financial Proposal",
                    urgency="Urgent",
                    status="Pending",
                    amount=45000.0
                ),
                CommunicationMessage(
                    user_id=uid,
                    company_name="Nexus Enterprise",
                    sender_username="accountant",
                    sender_role="Accountant",
                    recipient_role="CFO",
                    subject="Monthly Reconciliation & Tax Provision Clearance",
                    message="All June journal entries and bank reconciliations are completed with 0 unmatched items. Ready for CFO final audit sign-off.",
                    category="Audit Inquiry",
                    urgency="Normal",
                    status="Approved"
                )
            ]
            db.bulk_save_objects(demo_msgs)
            db.commit()
    except Exception as e:
        print(f"Error seeding demo users/messages: {e}")
        db.rollback()
    finally:
        db.close()

