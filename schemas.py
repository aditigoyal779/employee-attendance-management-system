import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models import AttendanceStatus


# ---------- Employee ----------
class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    department: str = Field(..., min_length=2, max_length=100)


class EmployeeResponse(EmployeeCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ---------- Attendance ----------
class AttendanceMark(BaseModel):
    employee_id: int
    date: Optional[dt.date] = None        # defaults to today
    status: AttendanceStatus


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    date: dt.date
    status: AttendanceStatus
    check_in: Optional[dt.time] = None
    check_out: Optional[dt.time] = None
    model_config = ConfigDict(from_attributes=True)


class DailyAttendanceItem(BaseModel):
    employee_id: int
    name: str
    department: str
    status: str                            # Present / Absent / Not Marked
    check_in: Optional[dt.time] = None
    check_out: Optional[dt.time] = None
    hours_worked: Optional[float] = None


class AttendanceSummary(BaseModel):
    employee_id: int
    name: str
    start_date: Optional[dt.date] = None
    end_date: Optional[dt.date] = None
    present_days: int
    absent_days: int
    total_marked_days: int


# ---------- Reports ----------
class MonthlyReportItem(BaseModel):
    employee_id: int
    name: str
    department: str
    present_days: int
    absent_days: int
    total_hours: float


class MonthlyReport(BaseModel):
    month: int
    year: int
    employees: List[MonthlyReportItem]


class EmployeeReportRecord(BaseModel):
    date: dt.date
    status: AttendanceStatus
    check_in: Optional[dt.time] = None
    check_out: Optional[dt.time] = None
    hours_worked: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)


class EmployeeReport(BaseModel):
    employee_id: int
    name: str
    department: str
    start_date: dt.date
    end_date: dt.date
    present_days: int
    absent_days: int
    total_hours: float
    records: List[EmployeeReportRecord]