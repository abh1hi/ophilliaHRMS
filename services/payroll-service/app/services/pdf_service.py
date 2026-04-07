"""PDF generation service for payslips using WeasyPrint.

Converts Jinja2 HTML templates to PDF documents.
Supports base64 encoding for database storage.
"""
import logging
import base64
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, Dict, Any
from uuid import UUID
from io import BytesIO

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

# Number to words mapping for rupees
ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen"
]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
SCALES = ["", "Thousand", "Lakh", "Crore"]


class PDFService:
    """Service for generating PDF payslips."""

    def __init__(self, template_dir: str = "app/templates"):
        """Initialize PDF service with template directory.

        Args:
            template_dir: Path to Jinja2 templates directory
        """
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Add custom filters
        self.env.filters["format_number"] = self._format_currency
        self.env.filters["rupees_words"] = self._rupees_to_words

    async def generate_payslip_pdf(
        self,
        payslip_data: Dict[str, Any],
        company_data: Dict[str, Any],
        employee_data: Dict[str, Any],
        ytd_data: Dict[str, Any],
    ) -> bytes:
        """Generate PDF payslip from payslip and employee data.

        Args:
            payslip_data: Payslip model fields
            company_data: Company/employer details
            employee_data: Employee details
            ytd_data: Year-to-date accumulated data

        Returns:
            PDF file as bytes
        """
        # Build template context
        context = self._build_payslip_context(
            payslip_data, company_data, employee_data, ytd_data
        )

        # Render Jinja2 template
        template = self.env.get_template("payslip.html")
        html_content = template.render(**context)

        # Convert to PDF using WeasyPrint
        pdf_bytes = self._html_to_pdf(html_content)

        logger.info(
            f"Payslip PDF generated for employee {employee_data.get('id')}",
            extra={"employee_id": str(employee_data.get("id"))},
        )

        return pdf_bytes

    def _build_payslip_context(
        self,
        payslip_data: Dict[str, Any],
        company_data: Dict[str, Any],
        employee_data: Dict[str, Any],
        ytd_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build Jinja2 template context from payslip data.

        Args:
            payslip_data: Payslip model fields
            company_data: Company details
            employee_data: Employee details
            ytd_data: YTD accumulated data

        Returns:
            Context dict for template rendering
        """
        # Parse amounts
        gross = Decimal(str(payslip_data.get("gross", 0)))
        net = Decimal(str(payslip_data.get("net", 0)))
        ctc = Decimal(str(payslip_data.get("ctc", 0)))

        # Build earnings list
        earnings = [
            {"name": "Basic", "amount": Decimal(str(payslip_data.get("basic", 0)))},
            {"name": "HRA", "amount": Decimal(str(payslip_data.get("hra", 0)))},
            {"name": "Allowances", "amount": Decimal(str(payslip_data.get("allowances", 0)))},
        ]

        # Add adjustments if present
        if payslip_data.get("adjustments"):
            for adj in payslip_data["adjustments"]:
                if adj.get("direction") == "CREDIT":
                    earnings.append({
                        "name": adj.get("type", "Adjustment"),
                        "amount": Decimal(str(adj.get("amount", 0))),
                    })

        # Build deductions list
        deductions = [
            {"name": "PF (Employee)", "amount": Decimal(str(payslip_data.get("pf_deduction", 0)))},
            {"name": "ESI (Employee)", "amount": Decimal(str(payslip_data.get("esi_deduction", 0)))},
            {"name": "Professional Tax", "amount": Decimal(str(payslip_data.get("professional_tax", 0)))},
            {"name": "TDS", "amount": Decimal(str(payslip_data.get("tds_deduction", 0)))},
            {"name": "LWF", "amount": Decimal(str(payslip_data.get("lwf_employee", 0)))},
        ]

        # Add loan EMI if present
        if payslip_data.get("adjustments"):
            for adj in payslip_data["adjustments"]:
                if adj.get("direction") == "DEBIT":
                    deductions.append({
                        "name": adj.get("type", "Deduction"),
                        "amount": Decimal(str(adj.get("amount", 0))),
                    })

        # Max rows for balanced table
        max_rows = max(len(earnings), len(deductions))

        return {
            # Company info
            "company_name": company_data.get("name", "Company Name"),
            "company_address": company_data.get("address", ""),
            "company_phone": company_data.get("phone", ""),
            "company_email": company_data.get("email", ""),

            # Payslip period
            "period_start": payslip_data.get("period_start", "").strftime("%d-%b-%Y") if payslip_data.get("period_start") else "",
            "period_end": payslip_data.get("period_end", "").strftime("%d-%b-%Y") if payslip_data.get("period_end") else "",
            "issued_date": datetime.now().strftime("%d-%b-%Y"),
            "current_month": datetime.now().strftime("%B"),

            # Employee info
            "employee_id": str(employee_data.get("id", "")),
            "employee_name": employee_data.get("name", ""),
            "designation": employee_data.get("designation", ""),
            "department": employee_data.get("department", ""),
            "joining_date": employee_data.get("joining_date", "").strftime("%d-%b-%Y") if employee_data.get("joining_date") else "",
            "uan": employee_data.get("uan", ""),
            "bank_account_masked": employee_data.get("bank_account_masked", "XXXX****XXXX"),

            # Salary info
            "ctc": ctc,
            "salary_structure": employee_data.get("salary_structure", ""),
            "cost_center": employee_data.get("cost_center", ""),

            # Earnings & deductions
            "earnings": earnings,
            "deductions": deductions,
            "max_rows": max_rows,
            "gross_salary": gross,
            "total_deductions": Decimal(str(payslip_data.get("total_deductions", 0))),
            "net_pay": net,
            "net_pay_words": self._rupees_to_words(float(net)),

            # YTD
            "ytd_gross": Decimal(str(ytd_data.get("ytd_gross", 0))),
            "ytd_basic": Decimal(str(ytd_data.get("ytd_basic", 0))),
            "ytd_pf_employee": Decimal(str(ytd_data.get("ytd_pf_employee", 0))),
            "ytd_esi_employee": Decimal(str(ytd_data.get("ytd_esi_employee", 0))),
            "ytd_professional_tax": Decimal(str(ytd_data.get("ytd_professional_tax", 0))),
            "ytd_tds": Decimal(str(ytd_data.get("ytd_tds", 0))),

            # Pro-ration & LOP
            "pro_rata_factor": Decimal(str(payslip_data.get("pro_rata_factor", 1.0))),
            "effective_from": payslip_data.get("effective_from", "").strftime("%d-%b-%Y") if payslip_data.get("effective_from") else "",
            "lop_days": payslip_data.get("lop_days", 0),
            "lop_amount": Decimal(str(payslip_data.get("lop_amount", 0))),
        }

    @staticmethod
    def _html_to_pdf(html_content: str) -> bytes:
        """Convert HTML string to PDF bytes using WeasyPrint.

        Args:
            html_content: HTML content as string

        Returns:
            PDF file as bytes
        """
        try:
            # Create HTML document from string
            html = HTML(string=html_content)

            # Generate PDF to BytesIO buffer
            pdf_buffer = BytesIO()
            html.write_pdf(pdf_buffer)

            # Get PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise

    @staticmethod
    def _format_currency(value: Decimal) -> str:
        """Format decimal number as Indian currency (with commas).

        Args:
            value: Decimal value

        Returns:
            Formatted string (e.g., "1,00,000.00")
        """
        if not value:
            return "0.00"

        # Convert to string with 2 decimal places
        amount_str = f"{float(value):.2f}"
        parts = amount_str.split(".")
        integer_part = parts[0]
        decimal_part = parts[1] if len(parts) > 1 else "00"

        # Add Indian commas (every 2 digits from right, except first 3)
        if len(integer_part) <= 3:
            return f"{integer_part}.{decimal_part}"

        # Reverse, add commas every 2 digits
        reversed_int = integer_part[::-1]
        chunks = [reversed_int[0:3]]
        for i in range(3, len(reversed_int), 2):
            chunks.append(reversed_int[i:i+2])

        formatted = ",".join(chunks)
        return f"{formatted[::-1]}.{decimal_part}"

    @staticmethod
    def _rupees_to_words(amount: float) -> str:
        """Convert numeric rupees amount to words.

        Args:
            amount: Numeric amount

        Returns:
            Amount in words (e.g., "One Lakh Twenty Thousand Five Hundred")
        """
        if amount == 0:
            return "Zero Rupees Only"

        amount = int(amount)
        words = []

        # Split into crore, lakh, thousand, ones
        crores = amount // 10_000_000
        amount %= 10_000_000

        lakhs = amount // 100_000
        amount %= 100_000

        thousands = amount // 1000
        amount %= 1000

        hundreds = amount

        # Build words
        if crores > 0:
            words.append(PDFService._convert_below_1000(crores))
            words.append("Crore")

        if lakhs > 0:
            words.append(PDFService._convert_below_1000(lakhs))
            words.append("Lakh")

        if thousands > 0:
            words.append(PDFService._convert_below_1000(thousands))
            words.append("Thousand")

        if hundreds > 0:
            words.append(PDFService._convert_below_1000(hundreds))

        return " ".join(words) + " Rupees Only"

    @staticmethod
    def _convert_below_1000(num: int) -> str:
        """Convert number below 1000 to words.

        Args:
            num: Number (0-999)

        Returns:
            Words representation
        """
        if num == 0:
            return ""

        hundreds = num // 100
        remainder = num % 100

        words = []

        if hundreds > 0:
            words.append(ONES[hundreds])
            words.append("Hundred")

        if remainder >= 20:
            tens = remainder // 10
            ones = remainder % 10
            words.append(TENS[tens])
            if ones > 0:
                words.append(ONES[ones])
        elif remainder > 0:
            words.append(ONES[remainder])

        return " ".join(words)
