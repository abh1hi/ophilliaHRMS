# Phase 7: PDF Payslip Generation (Async) Guide

## Overview

Phase 7 provides asynchronous PDF payslip generation with:
1. **Jinja2 HTML Templates** — Professional payslip layout
2. **WeasyPrint PDF Conversion** — High-quality PDF generation
3. **Background Worker** — Async processing after payroll completion
4. **PDF Storage** — Base64 encoding in database
5. **Download Endpoint** — Employees retrieve their payslips

---

## Architecture

### Event Flow

```
Payroll Processing Complete (COMPLETED state)
         ↓
Publishes: payroll.payslips_ready event
         ↓
PDF Worker subscribes to event
         ↓
Worker: For each payslip in run
  ├─ Build context (employee, company, YTD data)
  ├─ Render Jinja2 template → HTML
  ├─ WeasyPrint: HTML → PDF bytes
  ├─ Base64 encode → Store in payslips.pdf_data
  └─ Repeat for next payslip
         ↓
Publishes: salary.processed event per employee
         ↓
Notification Service subscribes
         ↓
Email PDF to employee
```

### Database Integration

**Phase 1A Model Addition**:
```sql
ALTER TABLE payslips ADD COLUMN pdf_data BYTEA;
-- or for JSON storage:
ALTER TABLE payslips ADD COLUMN pdf_data TEXT; -- base64 encoded
```

**Query**:
```sql
SELECT pdf_data FROM payslips WHERE id = ?; -- base64 string
DECODE(pdf_data, 'base64') → PDF bytes → Download
```

---

## Components

### 1. Jinja2 HTML Template (`payslip.html`)

**Features**:
- Company header with logo placeholder
- Employee information block
- Earnings and deductions table (dual-column for balance)
- Net pay highlighted in green box
- Year-to-date (YTD) summary table
- Pro-ration and LOP notes
- Footer with signature lines
- Professional styling with print-optimized CSS
- Watermark: "CONFIDENTIAL"

**Template Variables**:
```jinja2
Company Info:
- company_name
- company_address, company_phone, company_email

Payslip Period:
- period_start, period_end
- issued_date
- current_month

Employee Info:
- employee_id, employee_name
- designation, department, joining_date
- uan, bank_account_masked

Salary Components:
- earnings: [{ name, amount }, ...]
- deductions: [{ name, amount }, ...]
- gross_salary, total_deductions, net_pay, net_pay_words

YTD:
- ytd_gross, ytd_basic, ytd_pf_employee, ytd_esi_employee
- ytd_professional_tax, ytd_tds

Pro-ration:
- pro_rata_factor (e.g., 0.3667 for 36.67%)
- effective_from (joining/revision date)
- lop_days, lop_amount
```

### 2. PDF Service (`pdf_service.py`)

**Class: PDFService**

```python
generate_payslip_pdf(payslip_data, company_data, employee_data, ytd_data)
  → bytes (PDF file)

_build_payslip_context(...)
  → Dict[str, Any] (Jinja2 context)

_html_to_pdf(html_content: str)
  → bytes (PDF)

_format_currency(value: Decimal)
  → str (e.g., "1,00,000.00")

_rupees_to_words(amount: float)
  → str (e.g., "One Lakh Twenty Thousand Rupees Only")
```

**Features**:
- Jinja2 environment setup with custom filters
- WeasyPrint HTML→PDF conversion
- Currency formatting (Indian comma style)
- Amount-to-words conversion
- Error handling and logging

### 3. PDF Worker (`pdf_worker.py`)

**Class: PDFWorker**

```python
generate_payslips_for_run(payroll_run_id, company_id)
  → Dict[success, failed, errors]
  (Generates PDF for all payslips in run)

_generate_single_payslip_pdf(payslip, payroll_run, company_id, db)
  → bytes (PDF for one payslip)

run_pdf_worker()
  (Main async loop: listens for events)
```

**Workflow**:
1. Receives `payroll.payslips_ready` event
2. For each payslip:
   - Fetch YTD data for FY
   - Build context dict
   - Call PDFService.generate_payslip_pdf()
   - Encode result to base64
   - Store in payslips.pdf_data column
3. Commit all PDFs to database
4. Publish `salary.processed` event per employee
5. Log results: success/failed counts

---

## Usage Examples

### Example 1: Generate PDF for One Payslip

```python
from app.services.pdf_service import PDFService

service = PDFService(template_dir="app/templates")

payslip_data = {
    "gross": Decimal("100000"),
    "net": Decimal("85000"),
    "ctc": Decimal("1200000"),
    "basic": Decimal("50000"),
    "hra": Decimal("20000"),
    "allowances": Decimal("15000"),
    "pf_deduction": Decimal("6000"),
    "esi_deduction": Decimal("750"),
    "professional_tax": Decimal("200"),
    "tds_deduction": Decimal("1100"),
    "period_start": date(2025, 4, 1),
    "period_end": date(2025, 4, 30),
    "pro_rata_factor": Decimal("1.0"),
    "lop_days": 0,
    "lop_amount": Decimal("0"),
}

company_data = {
    "name": "OphilliaHRMS",
    "address": "123 Business Park, Bangalore",
    "phone": "+91-9876543210",
    "email": "hr@company.com",
}

employee_data = {
    "id": UUID("..."),
    "name": "Ramesh Kumar",
    "designation": "Senior Engineer",
    "department": "Engineering",
    "joining_date": date(2020, 1, 15),
    "uan": "UAN123456789012",
    "bank_account_masked": "XXXX****1234",
}

ytd_data = {
    "ytd_gross": Decimal("400000"),
    "ytd_basic": Decimal("200000"),
    "ytd_pf_employee": Decimal("24000"),
    "ytd_esi_employee": Decimal("3000"),
    "ytd_professional_tax": Decimal("800"),
    "ytd_tds": Decimal("4400"),
}

pdf_bytes = await service.generate_payslip_pdf(
    payslip_data, company_data, employee_data, ytd_data
)

# Save to file
with open("payslip.pdf", "wb") as f:
    f.write(pdf_bytes)

# Or encode to base64 for database
pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
```

### Example 2: Async Worker Processing

```python
from app.workers.pdf_worker import PDFWorker

worker = PDFWorker(database_url="postgresql+asyncpg://...")

result = await worker.generate_payslips_for_run(
    payroll_run_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
    company_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
)

print(f"Success: {result['success']}")
print(f"Failed: {result['failed']}")
print(f"Errors: {result['errors']}")
```

### Example 3: Download Payslip Endpoint (TBD in routes)

```python
@router.get("/payroll/payslips/{id}/pdf")
async def download_payslip_pdf(
    id: UUID,
    current_user: User = Depends(get_current_user),
):
    """Download payslip PDF."""
    payslip = await repo.get_payslip(id)
    if not payslip or payslip.pdf_data is None:
        raise HTTPException(404, "PDF not available yet")

    # Decode from base64
    pdf_bytes = base64.b64decode(payslip.pdf_data)

    # Return as attachment
    return FileResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        filename=f"payslip_{payslip.employee_id}_{payslip.period_start.strftime('%Y%m%d')}.pdf",
    )
```

---

## Payslip Layout

### Page Structure

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║  Company Logo        PAYSLIP             Period: Apr 2025  ║
║  Company Name        Issued: 07-Apr-2025                  ║
║  Address, Phone                                            ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Employee Information          Salary Information         ║
║  ─────────────────────        ─────────────────────       ║
║  Name: Ramesh Kumar            CTC: ₹12,00,000          ║
║  ID: EMP-001                   Structure: Senior Eng     ║
║  Designation: Senior Eng       Bank: XXXX****1234       ║
║  Department: Engineering       UAN: UAN12345678         ║
║  Joining: 15-Jan-2020                                     ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  EARNINGS & DEDUCTIONS                                     ║
║  ─────────────────────────────────────────────────────     ║
║  Earnings            Amount     Deductions         Amount   ║
║  Basic               ₹50,000    PF (Employee)      ₹6,000  ║
║  HRA                 ₹20,000    ESI (Employee)      ₹750   ║
║  Allowances          ₹15,000    Professional Tax     ₹200  ║
║  Performance Bonus   ₹25,000    TDS                 ₹1,100 ║
║                      ───────                        ─────── ║
║  Gross Salary       ₹1,10,000   Total Deductions   ₹8,050  ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║    NET PAY CREDITED TO YOUR ACCOUNT                       ║
║    ₹1,01,950                                              ║
║    One Lakh One Thousand Nine Hundred Fifty Rupees Only   ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  YEAR-TO-DATE SUMMARY (April - April)                     ║
║  ─────────────────────────────────────────────            ║
║  YTD Gross Salary             ₹4,40,000                   ║
║  YTD PF (Employee)               ₹24,000                   ║
║  YTD ESI (Employee)               ₹3,000                   ║
║  YTD Professional Tax             ₹800                     ║
║  YTD TDS Deducted                 ₹4,400                   ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Pro-ration & Attendance Notes:                            ║
║  Salary pro-rated at 100% (joined on 01-Apr-2025)         ║
║  0 day(s) Leave of Pay (LOP) deducted: ₹0                 ║
║                                                            ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Signature            HR Authorized      Finance Approved  ║
║  ──────────           ──────────────      ─────────────   ║
║                                                            ║
║  Confidential: This payslip is intended for the named     ║
║  employee only. Verify details and report discrepancies   ║
║  to HR within 7 days.                                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## Integration Points

### With Payroll Service (Phase 4)

**Trigger**: After `process_payroll()` completes (APPROVED → COMPLETED)
```python
run.status = PayrollStatus.COMPLETED.value
await repo.update_payroll_run(run)

# Publish event
await event_publisher.publish("payroll.payslips_ready", {
    "run_id": str(run.id),
    "company_id": company_id,
})
```

### With Notification Service (TBD)

**Event**: `salary.processed` (published per employee)
```python
await event_publisher.publish("salary.processed", {
    "employee_id": str(payslip.employee_id),
    "run_id": str(payroll_run_id),
    "pdf_ready": True,
})

# Notification service:
# Email payslip to employee with PDF attachment
```

### With Employee Service (TBD)

- Fetch employee name, designation, department
- Fetch bank account (masked)
- Fetch UAN
- Fetch joining date

### With YTD Service (Phase 4)

- Fetch YTD accumulated data per financial year
- Used in payslip summary section

---

## Performance Considerations

### Async Processing

- PDF generation is **non-blocking**
- Worker runs independently of HTTP requests
- Multiple payslips can be processed in parallel

### Resource Usage

**Memory**:
- Each PDF ≈ 50-100 KB depending on content
- HTML rendering ≈ 1-2 MB per payslip (temporary)
- Base64 encoding: ~33% size increase (for storage)

**Time**:
- Single payslip PDF generation: ~500ms-1s
- For 500 employees: ~5-10 minutes background processing
- Does not block payroll UI/API

### Storage

**Database** (base64 in payslips.pdf_data):
- 100 employees × 12 months = 1,200 payslips
- ~60-120 MB for full year (assuming ~50-100 KB per PDF)
- Or: Use MinIO/S3 + store path in column

**Alternative: Cloud Storage**
```python
# Instead of base64 in DB:
pdf_bytes = await service.generate_payslip_pdf(...)
s3_path = f"payslips/{company_id}/{payslip.id}.pdf"
await s3_client.put_object(s3_path, pdf_bytes)
payslip.pdf_path = s3_path  # Store path, not bytes
```

---

## Verification Checklist

✅ Jinja2 template renders correctly with all variables  
✅ WeasyPrint converts HTML to valid PDF  
✅ Currency formatted as Indian (₹1,00,000.00)  
✅ Amount-to-words conversion correct (e.g., "One Lakh")  
✅ YTD summary table populated from database  
✅ Pro-ration factor applied (if < 1.0, shows note)  
✅ LOP days and amount included  
✅ PDF base64 stored successfully in database  
✅ Base64 decoded correctly for download  
✅ PDF downloaded with correct filename  
✅ Worker handles failures gracefully (logs errors)  
✅ Worker processes all payslips even if one fails  
✅ Event published after all PDFs generated  

---

## Testing

### Unit Test Example

```python
async def test_pdf_generation():
    """Test payslip PDF generation."""
    service = PDFService()

    payslip_data = {
        "gross": Decimal("100000"),
        "net": Decimal("85000"),
        # ... other fields
    }

    pdf_bytes = await service.generate_payslip_pdf(
        payslip_data, company_data, employee_data, ytd_data
    )

    assert pdf_bytes is not None
    assert pdf_bytes.startswith(b"%PDF")  # PDF magic bytes
    assert len(pdf_bytes) > 10000  # Reasonable size

def test_currency_formatting():
    """Test Indian currency format."""
    service = PDFService()

    assert service._format_currency(Decimal("100000")) == "1,00,000.00"
    assert service._format_currency(Decimal("1200000")) == "12,00,000.00"
    assert service._format_currency(Decimal("500")) == "500.00"

def test_rupees_to_words():
    """Test amount-to-words conversion."""
    service = PDFService()

    assert "One Lakh" in service._rupees_to_words(100000)
    assert "Twelve Lakh" in service._rupees_to_words(1200000)
    assert "Five Hundred" in service._rupees_to_words(500)
```

---

## Deployment

### Docker Service

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    libcairo2

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run PDF worker as background service
CMD ["python", "-m", "app.workers.pdf_worker"]
```

### Systemd Service

```ini
[Unit]
Description=OphilliaHRMS PDF Worker
After=network.target

[Service]
Type=simple
User=payroll
WorkingDirectory=/opt/payroll
ExecStart=/opt/payroll/venv/bin/python -m app.workers.pdf_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Future Enhancements

- [ ] Email PDF as attachment immediately after generation
- [ ] Store PDFs on MinIO/S3 instead of database
- [ ] Generate payslip in multiple languages
- [ ] Custom watermarks per company
- [ ] Digital signature on PDFs
- [ ] Payslip template versioning
- [ ] Bulk export (all employees, all months as ZIP)

