import pandas as pd
import pdfplumber
import re
from dateutil import parser
import ace_tools as tools

# Function to extract transactions from PDFs with strict date validation
def extract_transactions_with_date_filter(pdf_path):
    transactions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for line in lines:
                    parts = re.split(r'\s{2,}', line)  # Splitting by multiple spaces to detect columns
                    if len(parts) >= 3:
                        date_candidate = parts[0].strip()

                        # Validate date range
                        try:
                            parsed_date = parser.parse(date_candidate, dayfirst=True, fuzzy=False)
                            if parsed_date.year < 2000 or parsed_date.year > 2050:
                                continue
                        except (ValueError, TypeError, OverflowError):
                            continue  # Skip invalid dates

                        description = parts[1].strip()
                        debit, credit = None, None

                        # Extract numeric values
                        for part in parts[2:]:
                            clean_part = re.sub(r"[^\d.]", "", part)
                            if clean_part.replace(".", "").isdigit():
                                try:
                                    amount = float(clean_part)
                                    if debit is None:
                                        debit = amount
                                    else:
                                        credit = amount
                                except ValueError:
                                    continue

                        transactions.append((parsed_date.strftime('%Y-%m-%d'), description, debit, credit))
    return transactions

# Function to process transactions into monthly summaries
def process_transactions(transactions):
    monthly_summary = {}
    for transaction in transactions:
        date, description, debit, credit = transaction
        month = date[:7]  # Extract YYYY-MM format

        if month not in monthly_summary:
            monthly_summary[month] = {
                'total_deposits': 0, 'total_withdrawals': 0, 'net_balance': 0,
                'Loans': 0, 'Salaries': 0, 'Rent': 0, 'Utilities': 0, 'Other Expenses': 0
            }

        if debit:
            monthly_summary[month]['total_withdrawals'] += debit
            # Categorize expenses
            if 'loan' in description.lower():
                monthly_summary[month]['Loans'] += debit
            elif 'salary' in description.lower():
                monthly_summary[month]['Salaries'] += debit
            elif 'rent' in description.lower():
                monthly_summary[month]['Rent'] += debit
            elif 'utility' in description.lower() or 'electricity' in description.lower():
                monthly_summary[month]['Utilities'] += debit
            else:
                monthly_summary[month]['Other Expenses'] += debit

        if credit:
            monthly_summary[month]['total_deposits'] += credit

        monthly_summary[month]['net_balance'] = (
            monthly_summary[month]['total_deposits'] - monthly_summary[month]['total_withdrawals']
        )
    
    return monthly_summary

# Load bank statements
pdf_files = ["/mnt/data/Untitled.pdf", "/mnt/data/Untitled-2.pdf", "/mnt/data/Untitled-3.pdf", "/mnt/data/Untitled-4.pdf"]
all_transactions = []
for pdf in pdf_files:
    all_transactions.extend(extract_transactions_with_date_filter(pdf))

# Process extracted transactions
processed_summary = process_transactions(all_transactions)

# Convert to DataFrame for visualization
summary_data = []
for month, data in processed_summary.items():
    row = {"Month": month, **data}
    summary_data.append(row)

summary_df = pd.DataFrame(summary_data)
tools.display_dataframe_to_user(name="Final Processed Financial Summary", dataframe=summary_df)
