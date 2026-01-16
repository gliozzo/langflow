from pydantic import BaseModel, Field
from typing import List, Optional


class Employee(BaseModel):
    """
    Canonical representation of an employee record.

    This model is designed to be:
    - machine-readable (for LLM grounding and validation)
    - database-aligned (schema-first)
    - explainable (explicit semantics per field)
    """

    name: Optional[str] = Field(
        default=None,
        description="Full name of the employee."
    )

    email: Optional[str] = Field(
        default=None,
        description="email of the employee."
    )

    location: Optional[str] = Field(
        default=None,
        description="Primary work location of the employee (city, region, or country)."
    )

    base_salary: Optional[float] = Field(
        default=None,
        description="Annual base salary of the employee, expressed in US dollars (USD), excluding bonuses and equity."
    )

    role: Optional[str] = Field(
        default=None,
        description="Current job title or functional role of the employee within the organization."
    )

    reports: Optional[List[str]] = Field(
        default=None,
        description="List of names or identifiers of employees who directly report to this employee."
    )