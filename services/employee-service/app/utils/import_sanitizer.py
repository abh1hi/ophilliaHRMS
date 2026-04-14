"""
Import Sanitizer — 3-layer validation + auto-clean + security for bulk employee imports.

Layer 1: Schema validation (Pydantic, no DB) — field formats, required fields, enums
Layer 2: Cross-row validation (in-memory, no DB) — duplicate emails within the file
Layer 3: (Runs inside Celery task) — business validation against DB

Also handles:
- CSV injection prevention (cells starting with = + - @ are prefixed with single-quote)
- Auto-clean rules (trim, title-case names, normalize enums, phone cleaning, date normalisation)
- File magic-byte validation
- UTF-8 BOM stripping (open CSV with utf-8-sig)
"""
import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from typing import Any

# XLSX magic bytes: PK\x03\x04 (ZIP archive)
XLSX_MAGIC = b"PK\x03\x04"
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

# Characters that trigger spreadsheet formula injection
_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# Enum normalization maps
_GENDER_MAP = {
    "male": "male", "m": "male",
    "female": "female", "f": "female",
    "other": "other", "o": "other",
}
_STATUS_MAP = {
    "active": "active", "a": "active",
    "inactive": "inactive", "i": "inactive",
    "terminated": "terminated", "t": "terminated",
    "on_leave": "on_leave",
}
_SALARY_MODE_MAP = {
    "bank": "bank", "b": "bank",
    "cheque": "cheque", "check": "cheque", "c": "cheque",
    "cash": "cash",
}

# Date normalization patterns (all → YYYY-MM-DD)
_DATE_SLASH = re.compile(r"^(\d{4})/(\d{2})/(\d{2})$")     # YYYY/MM/DD
_DATE_DMY_DASH = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")  # DD-MM-YYYY
_DATE_DMY_DOT = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$") # DD.MM.YYYY (European)

# Phone cleaning: strip +91 prefix and non-digit separators
_PHONE_PREFIX = re.compile(r"^\+91[-\s]?")
_PHONE_CLEAN = re.compile(r"[-\s()]")


@dataclass
class AutoCorrection:
    row: int
    field: str
    original: str
    fixed: str


@dataclass
class RowIssue:
    row: int
    field: str
    error: str
    suggested_fix: str = ""
    original_value: str = ""
    is_warning: bool = False   # True = soft warning, doesn't block upload
    is_cross_row: bool = False  # True = duplicate within the file itself


@dataclass
class SanitizeResult:
    rows: list[dict]
    auto_corrections: list[AutoCorrection] = field(default_factory=list)
    issues: list[RowIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if not i.is_warning)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.is_warning)


# ── File-level validation ───────────────────────────────────────────────────

def validate_file(filename: str, content: bytes) -> str:
    """
    Validate file size, extension, and magic bytes.
    Returns 'csv' or 'xlsx'. Raises ValueError on rejection.
    """
    if len(content) > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds maximum size of 10 MB ({len(content):,} bytes received)")

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("csv", "xlsx"):
        raise ValueError(f"Unsupported file type '.{ext}'. Only .csv and .xlsx are accepted.")

    is_xlsx_bytes = content[:4] == XLSX_MAGIC
    if ext == "xlsx" and not is_xlsx_bytes:
        raise ValueError("File has .xlsx extension but does not appear to be a valid Excel file.")
    if ext == "csv" and is_xlsx_bytes:
        raise ValueError("File has .csv extension but appears to be an Excel (.xlsx) file. Please rename it.")

    return ext


# ── File parsing ────────────────────────────────────────────────────────────

def _normalize_header(key: str) -> str:
    """Normalize a column header to a canonical field name."""
    k = key.strip().lower().replace(" ", "_").replace("-", "_")
    # Fix known typos/variants in user-supplied headers
    _HEADER_ALIASES = {
        "aaadhaar_number": "aadhaar_number",  # triple-a typo
        "aadhar_number": "aadhaar_number",     # common misspelling
        "adhar_number": "aadhaar_number",
        "pan": "pan_number",
        "uan": "uan_number",
        "esi": "esi_number",
        "dob": "date_of_birth",
        "joining_date": "date_joined",
        "date_of_joining": "date_joined",
        "mobile": "phone",
        "mobile_number": "phone",
        "phone_number": "phone",
        "salary": "joining_salary",
        "ctc": "joining_salary",
        "pincode": "pin_code",
        "pin": "pin_code",
        "village_town": "village_town",
    }
    return _HEADER_ALIASES.get(k, k)


def parse_csv_bytes(content: bytes) -> list[dict]:
    """Parse CSV bytes (handles UTF-8 BOM and auto-detects delimiter)."""
    text = content.decode("utf-8-sig", errors="replace")
    # Auto-detect delimiter: try comma, semicolon, tab
    sample = text[:2048]
    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample.strip() else None
    delimiter = dialect.delimiter if dialect else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for row in reader:
        rows.append({_normalize_header(k): v for k, v in row.items()})
    return rows


def parse_xlsx_bytes(content: bytes) -> list[dict]:
    """Parse XLSX bytes using openpyxl. Strips formulas (cells starting with =)."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)

    headers_raw = next(rows_iter, None)
    if not headers_raw:
        return []
    headers = [
        _normalize_header(str(h)) if h else f"col_{i}"
        for i, h in enumerate(headers_raw)
    ]

    result = []
    for row_vals in rows_iter:
        if all(v is None for v in row_vals):
            continue  # skip blank rows
        result.append({
            headers[i]: (str(v) if v is not None else "")
            for i, v in enumerate(row_vals)
            if i < len(headers)
        })
    wb.close()
    return result


# ── Cell-level sanitization ─────────────────────────────────────────────────

def _sanitize_injection(value: str, row_idx: int, field_name: str, corrections: list) -> str:
    """Prefix cells starting with formula-injection characters."""
    if value and value[0] in _INJECTION_PREFIXES:
        original = value
        value = "'" + value
        corrections.append(AutoCorrection(row=row_idx, field=field_name, original=original, fixed=value))
    return value


def _clean_field(field_name: str, value: str, row_idx: int, corrections: list) -> str:
    """Apply field-specific auto-clean rules. Returns cleaned value."""
    if not isinstance(value, str):
        value = str(value) if value is not None else ""

    original = value
    value = value.strip()

    # Injection prevention first (before other transforms that might introduce leading chars)
    value = _sanitize_injection(value, row_idx, field_name, corrections)
    if value.startswith("'"):
        return value  # already flagged and prefixed; skip further transforms

    # Treat lone dash/hyphen as empty (common placeholder in spreadsheets)
    if value == "-":
        value = ""

    if field_name == "email":
        value = value.lower()
    elif field_name in ("first_name", "last_name"):
        value = value.title()
    elif field_name == "pan_number":
        value = value.upper()
    elif field_name in ("aadhaar_number", "uan_number"):
        # Strip spaces inside Aadhaar / UAN (e.g. "9669 4146 6813" → "966941466813")
        value = value.replace(" ", "")
    elif field_name == "gender":
        norm = _GENDER_MAP.get(value.lower())
        if norm:
            value = norm
    elif field_name == "employment_status":
        norm = _STATUS_MAP.get(value.lower())
        if norm:
            value = norm
    elif field_name == "salary_mode":
        norm = _SALARY_MODE_MAP.get(value.lower())
        if norm:
            value = norm
    elif field_name in ("date_of_birth", "date_joined"):
        m = _DATE_SLASH.match(value)
        if m:
            value = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        else:
            m2 = _DATE_DMY_DASH.match(value)
            if m2:
                value = f"{m2.group(3)}-{m2.group(2)}-{m2.group(1)}"
            else:
                m3 = _DATE_DMY_DOT.match(value)
                if m3:
                    value = f"{m3.group(3)}-{m3.group(2)}-{m3.group(1)}"
    elif field_name in ("phone", "phone_2"):
        value = _PHONE_PREFIX.sub("", value)
        value = _PHONE_CLEAN.sub("", value)
    elif field_name in _NUMERIC_FIELDS:
        # Strip thousands-separators (commas) — e.g. "9,00" → "900", "50,000" → "50000"
        value = value.replace(",", "")

    if value != original and not original.startswith("'"):
        corrections.append(AutoCorrection(row=row_idx, field=field_name, original=original, fixed=value))

    return value


# ── Layer 1: Schema validation (Pydantic, no DB) ────────────────────────────

_REQUIRED_FIELDS = ("first_name", "last_name", "email")
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_AADHAAR_RE = re.compile(r"^\d{12}$")
_DATE_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUMERIC_FIELDS = ("joining_salary", "last_drawn_salary", "years_of_experience", "percentage")


def _schema_validate_row(row: dict, row_idx: int) -> list[RowIssue]:
    issues = []

    for f in _REQUIRED_FIELDS:
        if not row.get(f, "").strip():
            issues.append(RowIssue(
                row=row_idx, field=f,
                error=f"'{f}' is required and cannot be empty.",
                suggested_fix=f"Provide a valid {f.replace('_', ' ')}.",
            ))

    email = row.get("email", "").strip()
    if email and not _EMAIL_RE.match(email):
        issues.append(RowIssue(
            row=row_idx, field="email",
            error=f"Invalid email format: '{email}'",
            suggested_fix="Use format like name@company.com",
            original_value=email,
        ))

    pan = row.get("pan_number", "").strip()
    if pan and not _PAN_RE.match(pan):
        issues.append(RowIssue(
            row=row_idx, field="pan_number",
            error=f"Invalid PAN format: '{pan}'",
            suggested_fix="PAN must be 5 letters + 4 digits + 1 letter, e.g. ABCDE1234F",
            original_value=pan,
        ))

    aadhaar = row.get("aadhaar_number", "").strip()
    if aadhaar and not _AADHAAR_RE.match(aadhaar):
        issues.append(RowIssue(
            row=row_idx, field="aadhaar_number",
            error=f"Aadhaar must be exactly 12 digits: '{aadhaar}'",
            original_value=aadhaar,
        ))

    for date_field in ("date_of_birth", "date_joined"):
        val = row.get(date_field, "").strip()
        if val and not _DATE_ISO_RE.match(val):
            issues.append(RowIssue(
                row=row_idx, field=date_field,
                error=f"Date must be in YYYY-MM-DD format: '{val}'",
                suggested_fix="Format: YYYY-MM-DD, e.g. 1990-06-15",
                original_value=val,
            ))

    for num_field in _NUMERIC_FIELDS:
        val = row.get(num_field, "").strip()
        if val:
            try:
                float(val)
            except ValueError:
                issues.append(RowIssue(
                    row=row_idx, field=num_field,
                    error=f"'{num_field}' must be a number: '{val}'",
                    suggested_fix="Enter a numeric value, e.g. 50000",
                    original_value=val,
                ))

    # year_of_passing: must be a 4-digit year, not a range like "2019-2022"
    yop = row.get("year_of_passing", "").strip()
    if yop and not re.match(r"^\d{4}$", yop):
        issues.append(RowIssue(
            row=row_idx, field="year_of_passing",
            error=f"'year_of_passing' must be a 4-digit year: '{yop}'",
            suggested_fix="Use a single year like 2022, not a range.",
            original_value=yop,
            is_warning=True,
        ))

    # Soft warnings for missing recommended fields
    for warn_field in ("phone", "date_of_birth", "employee_code"):
        if not row.get(warn_field, "").strip():
            issues.append(RowIssue(
                row=row_idx, field=warn_field,
                error=f"'{warn_field}' is missing (recommended).",
                is_warning=True,
            ))

    return issues


# ── Layer 2: Cross-row validation ───────────────────────────────────────────

def _cross_row_validate(rows: list[dict]) -> list[RowIssue]:
    """Detect duplicate emails within the uploaded file itself."""
    issues = []
    seen: dict[str, int] = {}  # email → first row index
    for idx, row in enumerate(rows):
        email = row.get("email", "").strip().lower()
        if not email:
            continue
        if email in seen:
            issues.append(RowIssue(
                row=idx,
                field="email",
                error=f"Duplicate email '{email}' — also appears at row {seen[email]}.",
                suggested_fix="Remove the duplicate row or use a different email.",
                original_value=email,
                is_cross_row=True,
            ))
        else:
            seen[email] = idx
    return issues


# ── Main entry point ─────────────────────────────────────────────────────────

def sanitize_rows(raw_rows: list[dict]) -> SanitizeResult:
    """
    Apply auto-clean (Layer 0) + schema validation (Layer 1) + cross-row validation (Layer 2).
    Returns cleaned rows, corrections, and issues.
    Layer 3 (DB business validation) runs inside the Celery task.
    """
    corrections: list[AutoCorrection] = []
    all_issues: list[RowIssue] = []
    cleaned_rows = []

    for idx, row in enumerate(raw_rows):
        cleaned = {}
        for k, v in row.items():
            cleaned[k] = _clean_field(k, v if v is not None else "", idx, corrections)
        cleaned_rows.append(cleaned)
        all_issues.extend(_schema_validate_row(cleaned, idx))

    all_issues.extend(_cross_row_validate(cleaned_rows))

    return SanitizeResult(rows=cleaned_rows, auto_corrections=corrections, issues=all_issues)


def compute_idempotency_key(file_bytes: bytes, company_id: str) -> str:
    """SHA-256 of (file content + company_id). Used for dedup of re-uploads."""
    h = hashlib.sha256()
    h.update(file_bytes)
    h.update(company_id.encode())
    return h.hexdigest()
