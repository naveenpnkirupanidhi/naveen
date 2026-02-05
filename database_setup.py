"""
Database Setup Module
Creates and populates the SQLite databases for the AI Assistant
"""

import sqlite3
from datetime import datetime, timedelta


def setup_company_database():
    """
    Creates the company database with employees and departments tables.
    Used by the SQL Agent for natural language database queries.
    """
    conn = sqlite3.connect('company.db')
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute('DROP TABLE IF EXISTS employees')
    cursor.execute('DROP TABLE IF EXISTS departments')
    cursor.execute('DROP TABLE IF EXISTS projects')

    # Create departments table
    cursor.execute('''
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            budget REAL,
            manager_id INTEGER
        )
    ''')

    # Create employees table
    cursor.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            salary REAL,
            hire_date TEXT,
            email TEXT
        )
    ''')

    # Create projects table
    cursor.execute('''
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            department TEXT,
            budget REAL,
            start_date TEXT,
            status TEXT
        )
    ''')

    # Insert sample departments
    departments = [
        (1, 'Engineering', 500000.00, 1),
        (2, 'Marketing', 200000.00, 4),
        (3, 'Sales', 300000.00, 6),
        (4, 'Human Resources', 150000.00, 8),
        (5, 'Finance', 250000.00, 10)
    ]
    cursor.executemany('INSERT INTO departments VALUES (?, ?, ?, ?)', departments)

    # Insert sample employees
    employees = [
        (1, 'Alice Johnson', 'Engineering', 95000.00, '2020-01-15', 'alice@techvision.com'),
        (2, 'Bob Smith', 'Engineering', 85000.00, '2021-03-20', 'bob@techvision.com'),
        (3, 'Carol Williams', 'Engineering', 75000.00, '2022-06-10', 'carol@techvision.com'),
        (4, 'David Brown', 'Marketing', 70000.00, '2019-08-01', 'david@techvision.com'),
        (5, 'Eve Davis', 'Marketing', 65000.00, '2023-01-05', 'eve@techvision.com'),
        (6, 'Frank Miller', 'Sales', 80000.00, '2018-11-20', 'frank@techvision.com'),
        (7, 'Grace Lee', 'Sales', 72000.00, '2021-07-15', 'grace@techvision.com'),
        (8, 'Henry Wilson', 'Human Resources', 68000.00, '2020-04-10', 'henry@techvision.com'),
        (9, 'Ivy Chen', 'Human Resources', 62000.00, '2022-09-01', 'ivy@techvision.com'),
        (10, 'Jack Taylor', 'Finance', 88000.00, '2019-02-28', 'jack@techvision.com'),
        (11, 'Karen White', 'Finance', 78000.00, '2021-05-15', 'karen@techvision.com'),
        (12, 'Leo Martinez', 'Engineering', 90000.00, '2020-10-01', 'leo@techvision.com')
    ]
    cursor.executemany('INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)', employees)

    # Insert sample projects
    projects = [
        (1, 'Website Redesign', 'Engineering', 50000.00, '2024-01-01', 'In Progress'),
        (2, 'Mobile App v2', 'Engineering', 75000.00, '2024-02-15', 'In Progress'),
        (3, 'Q1 Marketing Campaign', 'Marketing', 30000.00, '2024-01-10', 'Completed'),
        (4, 'Sales Training Program', 'Sales', 15000.00, '2024-03-01', 'Planning'),
        (5, 'HR System Upgrade', 'Human Resources', 25000.00, '2024-02-01', 'In Progress'),
        (6, 'Annual Budget Review', 'Finance', 10000.00, '2024-01-01', 'Completed')
    ]
    cursor.executemany('INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)', projects)

    conn.commit()
    conn.close()
    print("Company database created with employees, departments, and projects tables.")


def setup_events_database():
    """
    Creates the events database for the Recommendation Agent.
    Contains events that can be recommended based on weather conditions.
    """
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Drop existing table if it exists
    cursor.execute('DROP TABLE IF EXISTS events')

    # Create events table
    cursor.execute('''
        CREATE TABLE events (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            location TEXT,
            date TEXT,
            time TEXT
        )
    ''')

    # Generate dates for the next 7 days
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]

    # Insert sample events
    events = [
        # Today's events
        (1, 'Morning Yoga in the Park', 'outdoor', 'Start your day with outdoor yoga', 'Central Park', dates[0], '07:00'),
        (2, 'Tech Meetup', 'indoor', 'Monthly tech community gathering', 'Innovation Hub', dates[0], '18:00'),
        (3, 'Food Festival', 'outdoor', 'Local food vendors and live music', 'Downtown Square', dates[0], '11:00'),

        # Tomorrow's events
        (4, 'Art Exhibition', 'indoor', 'Contemporary art showcase', 'City Art Museum', dates[1], '10:00'),
        (5, 'Beach Volleyball Tournament', 'outdoor', 'Amateur volleyball competition', 'Sunny Beach', dates[1], '09:00'),
        (6, 'Cooking Workshop', 'indoor', 'Learn to cook Italian cuisine', 'Culinary School', dates[1], '14:00'),

        # Day 3 events
        (7, 'Hiking Trail Adventure', 'outdoor', 'Guided nature hike', 'Mountain Trail', dates[2], '08:00'),
        (8, 'Movie Night', 'indoor', 'Classic film screening', 'Grand Cinema', dates[2], '19:00'),
        (9, 'Farmers Market', 'outdoor', 'Fresh produce and crafts', 'Town Square', dates[2], '07:00'),

        # Day 4 events
        (10, 'Photography Workshop', 'indoor', 'Learn landscape photography', 'Photo Studio', dates[3], '10:00'),
        (11, 'Outdoor Concert', 'outdoor', 'Live jazz performance', 'Amphitheater', dates[3], '18:00'),
        (12, 'Book Club Meeting', 'indoor', 'Monthly book discussion', 'City Library', dates[3], '15:00'),

        # Day 5 events
        (13, 'Cycling Tour', 'outdoor', 'City bike tour', 'Bike Station', dates[4], '09:00'),
        (14, 'Board Game Night', 'indoor', 'Strategy games and snacks', 'Game Cafe', dates[4], '17:00'),

        # Day 6 events
        (15, 'Sunrise Meditation', 'outdoor', 'Guided meditation session', 'Hilltop Park', dates[5], '06:00'),
        (16, 'Wine Tasting', 'indoor', 'Sample local wines', 'Vineyard Estate', dates[5], '16:00'),

        # Day 7 events
        (17, 'Marathon', 'outdoor', 'Annual city marathon', 'City Center', dates[6], '07:00'),
        (18, 'Science Fair', 'indoor', 'Student science projects', 'Convention Center', dates[6], '10:00')
    ]
    cursor.executemany('INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)', events)

    conn.commit()
    conn.close()
    print(f"Events database created with {len(events)} events for the next 7 days.")


def create_sample_document():
    """
    Creates a sample employee handbook document for RAG.
    """
    handbook_content = """EMPLOYEE HANDBOOK
TechVision Solutions Inc.
Effective Date: January 1, 2026

========================================
WELCOME TO TECHVISION SOLUTIONS
========================================

Welcome to TechVision Solutions! We are thrilled to have you as part of our team. This employee handbook has been prepared to inform you about our company policies, procedures, benefits, and expectations.

TechVision Solutions is a leading software development and IT consulting firm dedicated to delivering innovative technology solutions to businesses worldwide. Founded in 2010, we have grown from a small startup to a company of over 500 employees.

========================================
SECTION 1: EMPLOYMENT POLICIES
========================================

1.1 Equal Employment Opportunity

TechVision Solutions is committed to providing equal employment opportunities to all employees and applicants without regard to race, color, religion, sex, national origin, age, disability, or genetic information.

1.2 At-Will Employment

Employment with TechVision Solutions is on an "at-will" basis. This means that either you or the company may terminate the employment relationship at any time, with or without cause, and with or without notice.

1.3 Work Schedule

Standard business hours are Monday through Friday, 9:00 AM to 5:00 PM. Flexible scheduling options may be available depending on job requirements and manager approval. Remote work policies allow employees to work from home up to 3 days per week with manager approval.

========================================
SECTION 2: COMPENSATION AND BENEFITS
========================================

2.1 Pay Schedule

Employees are paid bi-weekly on every other Friday. Direct deposit is available and encouraged.

2.2 Health Insurance

TechVision Solutions offers comprehensive health insurance coverage including:
- Medical insurance (PPO and HMO options)
- Dental insurance
- Vision insurance
- Health Savings Account (HSA) options

Coverage begins on the first day of the month following 30 days of employment. The company pays 80% of employee premiums and 50% of dependent premiums.

2.3 401(k) Retirement Plan

All employees are eligible to participate in our 401(k) retirement plan after 90 days of employment. The company matches 100% of employee contributions up to 4% of salary. Vesting is immediate for employee contributions and follows a 3-year graded vesting schedule for employer contributions.

2.4 Paid Time Off (PTO)

Employees accrue PTO based on years of service:
- 0-2 years: 15 days per year
- 3-5 years: 20 days per year
- 6+ years: 25 days per year

PTO may be rolled over up to a maximum of 5 days to the following year. Unused PTO above 5 days will be forfeited. Upon separation from the company, accrued but unused PTO will be paid out at the employee's current rate.

2.5 Sick Leave

Employees receive 10 paid sick days per year. Sick leave may be used for personal illness, medical appointments, or to care for an immediate family member.

2.6 Holidays

TechVision Solutions observes the following paid holidays:
- New Year's Day
- Martin Luther King Jr. Day
- Presidents' Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving Day
- Day after Thanksgiving
- Christmas Eve
- Christmas Day

========================================
SECTION 3: WORKPLACE CONDUCT
========================================

3.1 Professional Conduct

All employees are expected to conduct themselves in a professional manner. This includes treating colleagues, clients, and vendors with respect and courtesy.

3.2 Anti-Harassment Policy

TechVision Solutions is committed to providing a work environment free from harassment. Harassment based on race, color, religion, sex, national origin, age, disability, or any other protected characteristic is strictly prohibited.

To report harassment, employees should:
1. Contact their direct supervisor or manager
2. Contact the Human Resources department
3. Use the anonymous ethics hotline: 1-800-ETHICS-1
4. Submit a written complaint to hr@techvision.com

All reports will be investigated promptly and confidentially.

3.3 Dress Code

Business casual attire is the standard dress code. On Fridays, casual attire is permitted. When meeting with clients, business professional attire is expected.

========================================
SECTION 4: LEAVE POLICIES
========================================

4.1 Family and Medical Leave (FMLA)

Eligible employees may take up to 12 weeks of unpaid, job-protected leave per year for:
- Birth and care of a newborn child
- Placement of a child for adoption or foster care
- Care for an immediate family member with a serious health condition
- Medical leave when unable to work due to a serious health condition

4.2 Parental Leave

In addition to FMLA, TechVision Solutions provides:
- 12 weeks of paid parental leave for birth parents
- 6 weeks of paid parental leave for non-birth parents
- Can be taken within 12 months of birth or adoption

4.3 Bereavement Leave

Employees may take up to 5 days of paid bereavement leave for the death of an immediate family member (spouse, child, parent, sibling) and up to 3 days for extended family members.

========================================
SECTION 5: TECHNOLOGY AND SECURITY
========================================

5.1 Acceptable Use Policy

Company technology resources should be used primarily for business purposes. Limited personal use is permitted as long as it does not interfere with work responsibilities.

5.2 Data Security

All employees are responsible for protecting company and client data. This includes:
- Using strong passwords and changing them every 90 days
- Not sharing login credentials
- Reporting suspicious emails or security incidents immediately
- Following data handling procedures for sensitive information

5.3 Remote Work Security

When working remotely, employees must:
- Use company-provided VPN for all work-related activities
- Ensure home WiFi networks are password-protected
- Keep work devices secure and not accessible to others
- Report any lost or stolen devices immediately

========================================
ACKNOWLEDGMENT
========================================

By accepting employment with TechVision Solutions, you acknowledge that you have received, read, and understood this Employee Handbook. You agree to comply with all policies and procedures outlined herein.

This handbook is subject to change at the company's discretion. Employees will be notified of any significant policy changes.

For questions about this handbook or company policies, please contact the Human Resources department at hr@techvision.com.

Last Updated: January 2026
"""

    with open('employee_handbook.txt', 'w', encoding='utf-8') as f:
        f.write(handbook_content)

    print("Employee handbook document created.")


def initialize_all_databases():
    """
    Initialize all databases and sample documents.
    """
    print("=" * 50)
    print("Initializing AI Assistant Databases")
    print("=" * 50)

    setup_company_database()
    setup_events_database()
    create_sample_document()

    print("=" * 50)
    print("All databases initialized successfully!")
    print("=" * 50)


if __name__ == "__main__":
    initialize_all_databases()
