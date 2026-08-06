import csv
import random

# Seed for reproducibility
random.seed(42)

# Templates for Safe Emails (Label = 0)
safe_templates = [
    # Corporate & Meetings
    ("Hi {name}, attached is the updated project roadmap for {quarter}. Please review before our sync meeting tomorrow at {time}.", "{quarter} Project Roadmap Review", "{name_lower}.{surname}@company.com"),
    ("Hey team, just a reminder that our weekly {dept} standup is scheduled for today at {time} on Zoom: https://zoom.us/j/{meeting_id}.", "Weekly {dept} Standup", "manager.{dept}@company.com"),
    ("Hi All, the quarterly town hall meeting recording and presentation slides have been uploaded to SharePoint.", "Town Hall Recording & Slides", "internal-comms@company.com"),
    ("Hi {name}, thanks for submitting the pull request for feature #{num}. I left a few minor comments on GitHub: https://github.com/company/repo/pull/{num}.", "Pull Request Review #{num}", "dev-lead@company.com"),
    ("Your Jira ticket {ticket_id} '{ticket_name}' has been marked as Resolved by QA.", "Jira Ticket Resolved: {ticket_id}", "jira@company.com"),
    ("Hi Team, please welcome our new {role}, {name} {surname}, who joins us today!", "Welcome New Team Member", "hr@company.com"),
    ("Hi team, please remember to submit your weekly timesheets before 5 PM today.", "Timesheet Reminder", "payroll@company.com"),
    ("Hi team, the office will be closed next Monday for the public holiday. Have a great long weekend!", "Office Closure Announcement", "ops@company.com"),
    ("Please join us for a lunch & learn presentation on {tech_topic} this Thursday at 12 PM in Conference Room B.", "Lunch & Learn: {tech_topic}", "events@company.com"),
    ("Hi {name}, your expense report for ${amount} has been approved by management and submitted to payroll.", "Expense Report Approved: ${amount}", "finance@company.com"),
    
    # Automated / Notifications
    ("Your monthly AWS cloud infrastructure billing invoice for {month} is now available in the AWS Management Console. Amount due: ${amount}.", "Amazon Web Services Billing Statement", "no-reply@amazon.com"),
    ("Your order #{order_id} has shipped via FedEx. Track your package status online at https://www.fedex.com/tracking?id={order_id}.", "Your Order Has Shipped", "shipping@amazon.com"),
    ("Your GitHub security advisory alert: A high severity vulnerability was found in repository dependency {dep_name}. View details at https://github.com/security.", "Security Advisory Alert", "notifications@github.com"),
    ("Your Slack verification code is {code}. Enter this code on the Slack login page to sign in.", "Slack Verification Code", "no-reply@slack.com"),
    ("Your Uber ride receipt for {day} evening is ready. Total: ${amount}. View trip details at https://www.uber.com/trips.", "Your {day} Evening Trip with Uber", "receipts@uber.com"),
    ("Your Spotify Premium receipt for this month (${amount}) has been processed. Thank you for listening!", "Your Spotify Receipt", "no-reply@spotify.com"),
    ("Security notice: Your Google Account was successfully accessed from a new device ({device}). If this was you, no action is needed.", "Security Alert: New Sign-in", "no-reply@accounts.google.com"),
    ("Your Apple Store order #{order_id} is ready for pickup at Apple Store {city}.", "Apple Store Pickup Ready #{order_id}", "no-reply@apple.com"),
    ("Your weekly digest from LinkedIn: {name} and {num} others viewed your profile this week.", "LinkedIn Weekly Digest", "newsletters@linkedin.com"),
    ("Thank you for your payment of ${amount} for your Microsoft 365 Subscription. Invoice #{order_id}.", "Microsoft 365 Payment Confirmation", "no-reply@microsoft.com"),
]

# Templates for Phishing Emails (Label = 1)
phishing_templates = [
    # Credential Harvesting
    ("Dear customer, your {brand} account has been temporarily restricted due to unauthorized login attempts from IP {ip}. Please verify your identity immediately at http://{brand_domain}-security-check.com/login to prevent permanent account termination.", "Action Required: Account Suspended", "security@{brand_domain}-security-check.com"),
    ("URGENT: Your Microsoft 365 password expires in {num} hours. Keep your current password by verifying your credentials at http://micros0ft-office365-verify.com/login", "Security Alert: Password Expiring", "admin@micros0ft-office365-verify.com"),
    ("FINAL NOTICE: Your {brand} subscription payment of ${amount} was declined. Update your credit card details immediately at http://{brand_domain}-billing-update.com to avoid service interruption.", "Payment Failure - Action Required", "support@{brand_domain}-billing-update.com"),
    ("Warning: Unusual sign-in activity detected on your Google Account from {city}, Russia. If this wasn't you, secure your account now at http://g00gle-accounts-security.com", "Critical Security Alert", "no-reply@g00gle-accounts-security.com"),
    ("Your DocuSign document 'Executive Signature Required - Wire Transfer Agreement' is ready for review. Click here to sign: http://docus1gn-signature-verify.com/doc", "DocuSign: Please Sign Document", "docusign@docus1gn-signature-verify.com"),
    ("ATTENTION: Your Chase Online Banking access has been locked due to suspicious activity. Verify your debit card number and PIN immediately at http://chase-bank-verify.com/auth", "Important Security Notice", "security@chase-bank-verify.com"),
    ("Your Apple ID has been suspended due to billing information mismatch. Click here to reactivate your account: http://appleid-apple-verify.com", "Apple ID Suspended", "support@appleid-apple-verify.com"),
    ("ALERT: Unauthorized device logged into your Bank of America account. Lock your account immediately at http://bankofamer1ca-security.com", "Bank of America Alert", "alert@bankofamer1ca-security.com"),
    ("ACCOUNT SECURITY NOTICE: Someone tried to change your Instagram password. If this was not you, confirm your account details at http://instagram-verify-center.com", "Password Reset Request", "no-reply@instagram-verify-center.com"),
    ("IMPORTANT: Your Dropbox storage is full and your files will be deleted in 24 hours. Upgrade or verify your account at http://dropb0x-storage-upgrade.com", "Dropbox Account Alert", "support@dropb0x-storage-upgrade.com"),
    
    # BEC & Invoice Fraud
    ("URGENT WIRE TRANSFER: I am in a board meeting right now and need you to process an urgent wire payment of ${amount} to our new supplier. Reply with confirmation once sent.", "Confidential Request", "ceo@company-exec-mail.com"),
    ("Urgent invoice payment overdue! Invoice #INV-{num} for ${amount} is overdue by 14 days. Pay online now at http://quickbooks-online-pay.com to avoid legal penalties.", "Overdue Invoice #INV-{num}", "billing@quickbooks-online-pay.com"),
    ("Hello {name}, I need you to purchase {num} Apple Gift Cards (${amount} each) for our client appreciation event today. Send the claim codes directly to this email.", "Urgent Task for Client Event", "executive-board-office@mail-secure-corp.com"),
    ("Payroll Direct Deposit Change: Please update my bank account routing details for this week's paycheck immediately. Click here: http://payroll-portal-hr-update.com", "Urgent Direct Deposit Update", "employee-payroll-change@company-portal-hr.com"),
    
    # Prize & Tax Refund Fraud
    ("Congratulations! Your email address was selected as the winner of the 2026 International Apple iPhone Giveaway. Claim your prize now at http://apple-winner-claim2026.com", "You Won an iPhone 15 Pro!", "prize@apple-winner-claim2026.com"),
    ("IRS TAX REFUND ALERT: You are eligible to receive a tax refund of ${amount}. Submit your SSN and bank account details at http://irs-tax-refund-portal.com", "IRS Tax Refund Notification", "refund@irs-tax-refund-portal.com"),
    ("Notification of Unclaimed Inheritance: You have been listed as a beneficiary for an unclaimed estate of ${amount}. Contact agent at http://unclaimed-estate-claim.com", "Beneficiary Notification", "attorney@unclaimed-estate-claim.com"),
]

# Random sample data fillers
names = ["Alex", "Sarah", "David", "Emma", "Michael", "Jessica", "James", "Emily", "Daniel", "Olivia", "Robert", "Sophia"]
surnames = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson"]
depts = ["Engineering", "Product", "Marketing", "Sales", "HR", "Finance", "DevOps", "Cybersecurity"]
quarters = ["Q1", "Q2", "Q3", "Q4"]
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
cities = ["Moscow", "Beijing", "Lagos", "Bucharest", "Shenzhen", "St. Petersburg"]
brands = ["PayPal", "Amazon", "Netflix", "Google", "Microsoft", "Apple", "Facebook", "LinkedIn"]
brand_domains = ["paypa1", "amaz0n", "netfl1x", "g00gle", "micros0ft", "app1e", "faceb00k", "linkd1n"]
devices = ["iPhone 14 Pro", "Windows PC", "MacBook Air", "Android Phone", "Linux Server"]
tech_topics = ["Docker & Kubernetes", "Zero Trust Architecture", "GraphQL APIs", "CI/CD Pipeline Security", "React Server Components"]

rows = []

# Generate 600 Safe Emails
for i in range(600):
    template, subj_t, sender_t = random.choice(safe_templates)
    name = random.choice(names)
    surname = random.choice(surnames)
    dept = random.choice(depts)
    quarter = random.choice(quarters)
    month = random.choice(months)
    day = random.choice(days)
    city = random.choice(cities)
    amount = f"{random.randint(15, 850)}.{random.randint(10, 99):02d}"
    num = random.randint(10, 999)
    order_id = f"{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(10, 99)}"
    meeting_id = f"{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"
    code = f"{random.randint(100, 999)}-{random.randint(100, 999)}"
    ticket_id = f"{dept[:3].upper()}-{random.randint(100, 999)}"
    
    text = template.format(
        name=name, surname=surname, name_lower=name.lower(), dept=dept, quarter=quarter,
        time=f"{random.randint(1, 12)} PM", num=num, ticket_id=ticket_id, ticket_name="Update authentication flow",
        role="Senior Developer", amount=amount, month=month, order_id=order_id, meeting_id=meeting_id,
        dep_name="lodash", code=code, day=day, device=random.choice(devices), city=random.choice(cities),
        tech_topic=random.choice(tech_topics)
    )
    subject = subj_t.format(quarter=quarter, dept=dept, num=num, ticket_id=ticket_id, amount=amount, day=day, order_id=order_id, tech_topic=random.choice(tech_topics))
    sender = sender_t.format(name_lower=name.lower(), surname=surname.lower(), dept=dept.lower())
    
    rows.append({"text": text, "subject": subject, "sender": sender, "label": 0})

# Generate 600 Phishing Emails
for i in range(600):
    template, subj_t, sender_t = random.choice(phishing_templates)
    name = random.choice(names)
    brand_idx = random.randint(0, len(brands)-1)
    brand = brands[brand_idx]
    brand_domain = brand_domains[brand_idx]
    amount = f"{random.randint(150, 4500):,}.00"
    num = random.randint(1, 48)
    ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    city = random.choice(cities)
    
    text = template.format(
        brand=brand, brand_domain=brand_domain, ip=ip, num=num, amount=amount,
        city=city, name=name
    )
    subject = subj_t.format(brand=brand, num=num, amount=amount)
    sender = sender_t.format(brand_domain=brand_domain)
    
    rows.append({"text": text, "subject": subject, "sender": sender, "label": 1})

# Shuffle dataset
random.shuffle(rows)

# Write to CSV
with open("data/emails.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["text", "subject", "sender", "label"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Successfully generated {len(rows)} records in data/emails.csv!")
