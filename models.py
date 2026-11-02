import enum
from sqlalchemy import (Column, Integer, String, Date, Time, Enum,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relationship
from database import Base


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False)

    attendance = relationship("Attendance", back_populates="employee",
                              cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(
        Enum(AttendanceStatus, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)

    employee = relationship("Employee", back_populates="attendance")

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_employee_date"),
    )