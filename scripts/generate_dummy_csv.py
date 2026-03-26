"""Generate a dummy CSV file with all employee fields for bulk import testing."""
import csv
import random
import string
from datetime import date, timedelta

OUTPUT = "dummy_employees.csv"
NUM_ROWS = 50

FIRST_NAMES_M = ["Rahul", "Amit", "Vikram", "Suresh", "Rajesh", "Arun", "Deepak", "Manoj", "Sanjay", "Kiran",
                  "Ravi", "Nikhil", "Anand", "Pranav", "Rohit", "Gaurav", "Vivek", "Ajay", "Naveen", "Harish"]
FIRST_NAMES_F = ["Priya", "Sneha", "Anjali", "Divya", "Pooja", "Neha", "Swati", "Kavita", "Meena", "Lakshmi",
                 "Sunita", "Rekha", "Asha", "Geeta", "Nandini", "Pallavi", "Shruti", "Ananya", "Rani", "Shalini"]
LAST_NAMES = ["Sharma", "Verma", "Patel", "Kumar", "Singh", "Reddy", "Nair", "Gupta", "Joshi", "Rao",
              "Iyer", "Das", "Mehta", "Mishra", "Chopra", "Bhat", "Pillai", "Chauhan", "Tiwari", "Saxena"]

DESIGNATIONS = ["Software Engineer", "Senior Developer", "QA Analyst", "Project Manager",
                "Business Analyst", "DevOps Engineer", "UI/UX Designer", "Data Analyst",
                "HR Executive", "Team Lead", "Technical Architect", "Product Manager"]

QUALIFICATIONS = ["B.Tech", "M.Tech", "BCA", "MCA", "B.Sc", "M.Sc", "MBA", "B.Com", "M.Com", "BBA"]
INSTITUTES = ["IIT Delhi", "NIT Trichy", "BITS Pilani", "Anna University", "VIT Vellore",
              "SRM University", "Amity University", "Delhi University", "Mumbai University", "Pune University"]

BANKS = ["State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank", "Punjab National Bank",
         "Bank of Baroda", "Canara Bank", "Union Bank", "Kotak Mahindra Bank", "IndusInd Bank"]
BRANCHES = ["MG Road", "Connaught Place", "Banjara Hills", "Koramangala", "Andheri West",
            "Salt Lake", "Viman Nagar", "Jubilee Hills", "Whitefield", "Hinjewadi"]

STREETS = ["MG Road", "Park Street", "Brigade Road", "FC Road", "Church Street",
           "Ring Road", "NH 44", "Old Airport Road", "Residency Road", "Tank Bund"]
TOWNS = ["Bangalore", "Hyderabad", "Chennai", "Mumbai", "Pune", "Delhi", "Kolkata",
         "Ahmedabad", "Jaipur", "Lucknow"]

PROJECTS = ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta", "Project Omega",
            "Internal Tools", "Client Portal", "Mobile App", "Data Platform", "Cloud Migration"]

RELATIONS = ["Father", "Mother", "Spouse", "Brother", "Sister"]
HEALTH_ISSUES = [None, None, None, None, "Asthma", "Diabetes", "Hypertension", None, None, None]
ALLERGIES = [None, None, None, "Dust", "Pollen", None, None, "Penicillin", None, None]


def rand_phone():
    return f"9{random.randint(100000000, 999999999)}"


def rand_aadhaar():
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def rand_pan():
    letters = string.ascii_uppercase
    return (
        "".join(random.choices(letters, k=5))
        + "".join(random.choices(string.digits, k=4))
        + random.choice(letters)
    )


def rand_uan():
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def rand_esi():
    return "".join([str(random.randint(0, 9)) for _ in range(17)])


def rand_dl():
    state = random.choice(["KA", "TN", "MH", "DL", "AP", "TS", "KL"])
    return f"{state}{random.randint(10, 99)}{random.randint(10000000000, 99999999999)}"


def rand_ifsc():
    bank_codes = ["SBIN", "HDFC", "ICIC", "UTIB", "PUNB", "BARB", "CNRB", "UBIN", "KKBK", "INDB"]
    return f"{random.choice(bank_codes)}0{random.randint(100000, 999999)}"


def rand_account():
    return "".join([str(random.randint(0, 9)) for _ in range(random.randint(11, 16))])


def rand_date(start_year=1985, end_year=2000):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def rand_join_date():
    start = date(2020, 1, 1)
    end = date(2025, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_row(idx):
    gender = random.choice(["Male", "Female"])
    if gender == "Male":
        first = random.choice(FIRST_NAMES_M)
    else:
        first = random.choice(FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    email = f"{first.lower()}.{last.lower()}{idx}@example.com"
    personal_email = f"{first.lower()}{random.randint(10, 99)}@gmail.com"
    dob = rand_date()
    join_date = rand_join_date()

    return {
        "first_name": first,
        "last_name": last,
        "gender": gender,
        "date_of_birth": dob.isoformat(),
        "email": email,
        "personal_email": personal_email,
        "phone": rand_phone(),
        "phone_2": rand_phone() if random.random() > 0.6 else "",
        "door_no": str(random.randint(1, 500)),
        "street": random.choice(STREETS),
        "village_town": random.choice(TOWNS),
        "pin_code": str(random.randint(100000, 999999)),
        "aadhaar_number": rand_aadhaar(),
        "pan_number": rand_pan(),
        "uan_number": rand_uan() if random.random() > 0.3 else "",
        "esi_number": rand_esi() if random.random() > 0.5 else "",
        "driving_license_number": rand_dl() if random.random() > 0.4 else "",
        "bank_name": random.choice(BANKS),
        "bank_branch": random.choice(BRANCHES),
        "bank_account_number": rand_account(),
        "ifsc_code": rand_ifsc(),
        "emergency_contact_name": f"{random.choice(FIRST_NAMES_M + FIRST_NAMES_F)} {random.choice(LAST_NAMES)}",
        "emergency_contact_number": rand_phone(),
        "emergency_contact_relation": random.choice(RELATIONS),
        "highest_qualification": random.choice(QUALIFICATIONS),
        "year_of_passing": str(random.randint(2005, 2023)),
        "percentage": f"{random.uniform(55, 95):.1f}",
        "institute_name": random.choice(INSTITUTES),
        "last_firm_name": random.choice(["TCS", "Infosys", "Wipro", "HCL", "Accenture", "Cognizant", "Tech Mahindra", ""]),
        "years_of_experience": str(random.randint(0, 15)),
        "last_designation": random.choice(DESIGNATIONS) if random.random() > 0.3 else "",
        "last_drawn_salary": str(random.randint(15000, 150000)) if random.random() > 0.3 else "",
        "reason_to_quit": random.choice(["Better opportunity", "Relocation", "Higher studies", "Personal reasons", ""]),
        "referred_by": f"{random.choice(FIRST_NAMES_M + FIRST_NAMES_F)} {random.choice(LAST_NAMES)}" if random.random() > 0.5 else "",
        "health_issues": random.choice(HEALTH_ISSUES) or "",
        "allergies": random.choice(ALLERGIES) or "",
        "designation": random.choice(DESIGNATIONS),
        "date_joined": join_date.isoformat(),
        "joining_salary": str(random.randint(20000, 200000)),
        "project": random.choice(PROJECTS),
        "role": random.choice(["employee", "manager", "hr"]),
        "initial_password": f"Welcome@{random.randint(100, 999)}",
    }


def main():
    rows = [generate_row(i) for i in range(1, NUM_ROWS + 1)]
    fieldnames = list(rows[0].keys())

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {OUTPUT} with {NUM_ROWS} rows and {len(fieldnames)} columns.")
    print(f"Columns: {', '.join(fieldnames)}")


if __name__ == "__main__":
    main()
