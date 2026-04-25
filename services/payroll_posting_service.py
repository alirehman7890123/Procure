"""
payroll_posting_service.py — Pure computation functions for payroll.
No DB access, no UI imports. All functions take plain Python values and return dicts.
"""

import calendar


def get_working_days(year: int, month: int) -> int:
    """
    Return the number of working days (Mon–Sat) in a given year/month.
    Saturday is counted as a working day; Sunday is off.
    """
    _, total_days = calendar.monthrange(year, month)
    working = 0
    for day in range(1, total_days + 1):
        weekday = calendar.weekday(year, month, day)  # 0=Mon … 6=Sun
        if weekday != 6:  # exclude Sunday only
            working += 1
    return working


def compute_deduction(basic_salary: float, absent_days: int, half_days: int,
                      working_days: int) -> float:
    """
    Compute salary deduction from absences.
    absent_days count as full deduction; half_days count as 0.5.
    """
    if working_days <= 0:
        return 0.0
    effective_absent = absent_days + (half_days * 0.5)
    return round((effective_absent / working_days) * basic_salary, 2)


def compute_net_salary(basic_salary: float, allowances: float,
                       deductions: float, advance_deduct: float) -> float:
    """Return net salary, floored at 0."""
    net = basic_salary + allowances - deductions - advance_deduct
    return round(max(net, 0.0), 2)


def build_payroll_payload(employee_id: int, year_month: str,
                          basic_salary: float, allowances: float,
                          attendance_summary: dict, advance_deduct: float,
                          working_days: int) -> dict:
    """
    Build the complete payroll computation result dict.

    attendance_summary must have keys: present, absent, half_day, leave
    Returns dict ready to be passed to payroll_service.insert_payroll.
    """
    absent   = attendance_summary.get("absent", 0)
    half_day = attendance_summary.get("half_day", 0)

    deductions = compute_deduction(basic_salary, absent, half_day, working_days)
    net_salary = compute_net_salary(basic_salary, allowances, deductions, advance_deduct)

    return {
        "employee_id":    employee_id,
        "month":          year_month,
        "basic_salary":   round(basic_salary, 2),
        "allowances":     round(allowances, 2),
        "deductions":     deductions,
        "advance_deduct": round(advance_deduct, 2),
        "net_salary":     net_salary,
        "present_days":   attendance_summary.get("present", 0),
        "absent_days":    absent,
        "half_days":      half_day,
        "leave_days":     attendance_summary.get("leave", 0),
        "working_days":   working_days,
    }
