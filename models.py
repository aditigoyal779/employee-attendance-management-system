import enum
import datetime as dt
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"


class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field(max_length=100, nullable=False)
    email: str = Field(max_length=120, unique=True, index=True, nullable=False)
    department: str = Field(max_length=100, nullable=False)

    attendance: List["Attendance"] = Relationship(
        back_populates="employee",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    employee_id: int = Field(foreign_key="employees.id", ondelete="CASCADE", index=True)

    # Field name is 'date', but type is 'dt.date' to avoid Pydantic collision
    date: dt.date = Field(index=True, nullable=False)

    status: AttendanceStatus = Field(nullable=False)
    check_in: Optional[dt.time] = Field(default=None)
    check_out: Optional[dt.time] = Field(default=None)

    employee: Optional[Employee] = Relationship(back_populates="attendance")

    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_employee_date"),
    )