import sqlite3
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime, timedelta
import random

Base = declarative_base()


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True)
    policy_number = Column(String(50), unique=True, nullable=False)
    policy_type = Column(String(50), nullable=False)
    insured_name = Column(String(200), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    premium_amount = Column(Float, nullable=False)
    status = Column(String(20), default="Active")

    bills = relationship("Bill", back_populates="policy")


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    bill_number = Column(String(50), unique=True, nullable=False)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    bill_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    status = Column(String(20), default="Pending")
    payment_date = Column(DateTime, nullable=True)

    policy = relationship("Policy", back_populates="bills")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    payment_number = Column(String(50), unique=True, nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    transaction_id = Column(String(100))

    bill = relationship("Bill", back_populates="payments")


Bill.payments = relationship("Payment", back_populates="bill")


def create_database(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine


def populate_sample_data(engine):
    Session = sessionmaker(bind=engine)
    session = Session()

    policy_types = [
        "Auto",
        "Homeowners",
        "Commercial Property",
        "General Liability",
        "Workers Compensation",
    ]
    statuses = ["Active", "Active", "Active", "Expired", "Cancelled"]
    bill_statuses = ["Paid", "Paid", "Paid", "Pending", "Overdue"]
    payment_methods = ["Credit Card", "Bank Transfer", "Check", "Online"]

    first_names = [
        "John",
        "Jane",
        "Robert",
        "Mary",
        "Michael",
        "Sarah",
        "David",
        "Emily",
        "James",
        "Lisa",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
    ]
    business_names = [
        "ABC Corp",
        "XYZ Industries",
        "Tech Solutions LLC",
        "Green Gardens Inc",
        "Metro Construction",
        "Digital Dynamics",
        "Premier Retail",
        "Sunrise Healthcare",
        "Pacific Trading",
        "Elite Services",
    ]

    policies = []
    for i in range(20):
        policy_type = random.choice(policy_types)
        if policy_type in [
            "Commercial Property",
            "General Liability",
            "Workers Compensation",
        ]:
            insured_name = random.choice(business_names)
            premium = round(random.uniform(2000, 15000), 2)
        else:
            insured_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            premium = round(random.uniform(500, 3000), 2)

        effective_date = datetime.now() - timedelta(days=random.randint(0, 365))
        expiration_date = effective_date + timedelta(days=365)
        status = random.choice(statuses)

        policy = Policy(
            policy_number=f"POL-{2024001 + i}",
            policy_type=policy_type,
            insured_name=insured_name,
            effective_date=effective_date,
            expiration_date=expiration_date,
            premium_amount=premium,
            status=status,
        )
        policies.append(policy)
        session.add(policy)

    session.commit()

    bills = []
    for i, policy in enumerate(policies):
        num_bills = random.randint(1, 3)
        for j in range(num_bills):
            bill_date = policy.effective_date + timedelta(days=30 * j)
            due_date = bill_date + timedelta(days=30)
            amount_due = round(policy.premium_amount / num_bills, 2)
            status = random.choice(bill_statuses)
            amount_paid = (
                amount_due
                if status == "Paid"
                else round(random.uniform(0, amount_due), 2)
                if status == "Pending"
                else 0
            )
            payment_date = (
                bill_date + timedelta(days=random.randint(1, 25))
                if status == "Paid"
                else None
            )

            bill = Bill(
                bill_number=f"BILL-{2024001 + i * 3 + j}",
                policy_id=policy.id,
                bill_date=bill_date,
                due_date=due_date,
                amount_due=amount_due,
                amount_paid=amount_paid,
                status=status,
                payment_date=payment_date,
            )
            bills.append(bill)
            session.add(bill)

    session.commit()

    for i, bill in enumerate(bills):
        if bill.status == "Paid":
            payment = Payment(
                payment_number=f"PAY-{2024001 + i}",
                bill_id=bill.id,
                payment_date=bill.payment_date,
                amount=bill.amount_paid,
                payment_method=random.choice(payment_methods),
                transaction_id=f"TXN-{random.randint(100000, 999999)}",
            )
            session.add(payment)

    session.commit()
    session.close()


def get_engine(db_path):
    return create_engine(f"sqlite:///{db_path}")


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
