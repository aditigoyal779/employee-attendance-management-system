import calendar
import datetime as dt
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db
from models import AttendanceStatus

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Employee Attendance Management System", version="1.0.0")


# ================= Helper functions =================
def get_employee_or_404(db: Session, employee_id: int) -> models.Employee:
    emp = db.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


def calc_hours(record: models.Attendance) -> Optional[float]:
    """Hours between check-in and check-out (None if either is missing)."""
    if record is None or record.check_in is None or record.check_out is None:
        return None
    start = dt.datetime.combine(record.date, record.check_in)
    end = dt.datetime.combine(record.date, record.check_out)
    return round((end - start).total_seconds() / 3600, 2)


def current_time() -> dt.time:
    return dt.datetime.now().time().replace(microsecond=0)


# ================= 1. EMPLOYEES =================
@app.post("/employees", response_model=schemas.EmployeeResponse,
          status_code=status.HTTP_201_CREATED, tags=["Employees"])
def add_employee(employee: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    if db.query(models.Employee).filter(models.Employee.email == employee.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_emp = models.Employee(**employee.model_dump())
    db.add(new_emp)
    db.commit()
    db.refresh(new_emp)
    return new_emp


@app.get("/employees", response_model=List[schemas.EmployeeResponse], tags=["Employees"])
def list_employees(db: Session = Depends(get_db)):
    return db.query(models.Employee).all()


@app.get("/employees/{employee_id}", response_model=schemas.EmployeeResponse,
         tags=["Employees"])
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return get_employee_or_404(db, employee_id)


# ================= 2. MARK ATTENDANCE =================
@app.post("/attendance", response_model=schemas.AttendanceResponse,
          status_code=status.HTTP_201_CREATED, tags=["Attendance"])
def mark_attendance(data: schemas.AttendanceMark, db: Session = Depends(get_db)):
    get_employee_or_404(db, data.employee_id)
    day = data.date or dt.date.today()

    if day > dt.date.today():
        raise HTTPException(status_code=400, detail="Cannot mark attendance for a future date")

    record = db.query(models.Attendance).filter(
        models.Attendance.employee_id == data.employee_id,
        models.Attendance.date == day).first()

    if record:   # already marked today -> update the status
        record.status = data.status
        if data.status == AttendanceStatus.ABSENT:   # absent people have no times
            record.check_in = None
            record.check_out = None
    else:
        record = models.Attendance(employee_id=data.employee_id,
                                   date=day, status=data.status)
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


# ================= 3. CHECK-IN / CHECK-OUT =================
@app.post("/attendance/check-in/{employee_id}",
          response_model=schemas.AttendanceResponse, tags=["Attendance"])
def check_in(employee_id: int, db: Session = Depends(get_db)):
    get_employee_or_404(db, employee_id)
    today = dt.date.today()

    record = db.query(models.Attendance).filter(
        models.Attendance.employee_id == employee_id,
        models.Attendance.date == today).first()

    if record and record.check_in is not None:
        raise HTTPException(status_code=400, detail="Already checked in today")

    if record:   # was marked earlier without a time (or as Absent)
        record.status = AttendanceStatus.PRESENT
        record.check_in = current_time()
    else:
        record = models.Attendance(employee_id=employee_id, date=today,
                                   status=AttendanceStatus.PRESENT,
                                   check_in=current_time())
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


@app.post("/attendance/check-out/{employee_id}",
          response_model=schemas.AttendanceResponse, tags=["Attendance"])
def check_out(employee_id: int, db: Session = Depends(get_db)):
    get_employee_or_404(db, employee_id)
    today = dt.date.today()

    record = db.query(models.Attendance).filter(
        models.Attendance.employee_id == employee_id,
        models.Attendance.date == today).first()

    if not record or record.check_in is None:
        raise HTTPException(status_code=400, detail="Cannot check out before checking in")
    if record.check_out is not None:
        raise HTTPException(status_code=400, detail="Already checked out today")

    record.check_out = current_time()
    db.commit()
    db.refresh(record)
    return record


# ================= 4. DAILY ATTENDANCE =================
@app.get("/attendance/daily", response_model=List[schemas.DailyAttendanceItem],
         tags=["Attendance"])
def daily_attendance(date: Optional[dt.date] = Query(None, description="YYYY-MM-DD, default today"),
                     db: Session = Depends(get_db)):
    day = date or dt.date.today()

    rows = (db.query(models.Employee, models.Attendance)
              .outerjoin(models.Attendance,
                         and_(models.Attendance.employee_id == models.Employee.id,
                              models.Attendance.date == day))
              .order_by(models.Employee.id)
              .all())

    result = []
    for emp, att in rows:
        result.append(schemas.DailyAttendanceItem(
            employee_id=emp.id,
            name=emp.name,
            department=emp.department,
            status=att.status.value if att else "Not Marked",
            check_in=att.check_in if att else None,
            check_out=att.check_out if att else None,
            hours_worked=calc_hours(att),
        ))
    return result


# ================= 5. COUNT PRESENT / ABSENT DAYS =================
@app.get("/attendance/summary/{employee_id}",
         response_model=schemas.AttendanceSummary, tags=["Attendance"])
def attendance_summary(employee_id: int,
                       start_date: Optional[dt.date] = None,
                       end_date: Optional[dt.date] = None,
                       db: Session = Depends(get_db)):
    emp = get_employee_or_404(db, employee_id)

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

    filters = [models.Attendance.employee_id == employee_id]
    if start_date:
        filters.append(models.Attendance.date >= start_date)
    if end_date:
        filters.append(models.Attendance.date <= end_date)

    def count(state: AttendanceStatus) -> int:
        return db.query(func.count(models.Attendance.id)).filter(
            *filters, models.Attendance.status == state).scalar()

    present = count(AttendanceStatus.PRESENT)
    absent = count(AttendanceStatus.ABSENT)

    return schemas.AttendanceSummary(
        employee_id=emp.id, name=emp.name,
        start_date=start_date, end_date=end_date,
        present_days=present, absent_days=absent,
        total_marked_days=present + absent)


# ================= 6. REPORTS =================
@app.get("/reports/monthly", response_model=schemas.MonthlyReport, tags=["Reports"])
def monthly_report(month: int = Query(..., ge=1, le=12),
                   year: int = Query(..., ge=2000, le=2100),
                   db: Session = Depends(get_db)):
    first = dt.date(year, month, 1)
    last = dt.date(year, month, calendar.monthrange(year, month)[1])

    employees = db.query(models.Employee).order_by(models.Employee.id).all()
    records = db.query(models.Attendance).filter(
        models.Attendance.date >= first, models.Attendance.date <= last).all()

    # group records by employee
    grouped = {}
    for r in records:
        grouped.setdefault(r.employee_id, []).append(r)

    items = []
    for emp in employees:
        recs = grouped.get(emp.id, [])
        items.append(schemas.MonthlyReportItem(
            employee_id=emp.id, name=emp.name, department=emp.department,
            present_days=sum(1 for r in recs if r.status == AttendanceStatus.PRESENT),
            absent_days=sum(1 for r in recs if r.status == AttendanceStatus.ABSENT),
            total_hours=round(sum(calc_hours(r) or 0 for r in recs), 2)))

    return schemas.MonthlyReport(month=month, year=year, employees=items)


@app.get("/reports/employee/{employee_id}", response_model=schemas.EmployeeReport,
         tags=["Reports"])
def employee_report(employee_id: int,
                    start_date: dt.date = Query(...),
                    end_date: dt.date = Query(...),
                    db: Session = Depends(get_db)):
    emp = get_employee_or_404(db, employee_id)
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

    recs = (db.query(models.Attendance)
              .filter(models.Attendance.employee_id == employee_id,
                      models.Attendance.date >= start_date,
                      models.Attendance.date <= end_date)
              .order_by(models.Attendance.date).all())

    return schemas.EmployeeReport(
        employee_id=emp.id, name=emp.name, department=emp.department,
        start_date=start_date, end_date=end_date,
        present_days=sum(1 for r in recs if r.status == AttendanceStatus.PRESENT),
        absent_days=sum(1 for r in recs if r.status == AttendanceStatus.ABSENT),
        total_hours=round(sum(calc_hours(r) or 0 for r in recs), 2),
        records=[schemas.EmployeeReportRecord(
            date=r.date, status=r.status, check_in=r.check_in,
            check_out=r.check_out, hours_worked=calc_hours(r)) for r in recs])