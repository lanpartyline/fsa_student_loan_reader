## Student Loan Data Reader

### Purpose:

This project is meant to assist people in finding out about their repayment counts.

### How it works:

1. Download this repo to a local folder on your computer.
2. Download your studnet aid file. Here: https://studentaid.gov/aid-summary/loans, click "Download My Aid Data". (You may need to log in first, then click the link) It should download to your downloads directory. If you download elsewhere, put in in your downloads directory.
3. Execute run.bat
4. Open results.txt

### Results Layout:

The file should be divided into sections like these:

- Loans Summary
  - This section contain a general summary of the entire loan history, loan counts and financials
  - The depressing part is usually pct remaining... over 100% in many cases.
  - It tries to account for all original loan amount, capitalization, etc, and if the numbers don't match up it will give a "warning."
- Unpaid Loans
  - This section contains the listing of current unpaid (not consolidated, not paid, not cancelled loans). Not too much more in here other than a current overview.
- Loan Details
  - This section is the meat and potatoes.  It will list all of the loans in the history 
  and details about those loans, including an estimated payment history.
  - Two notable sections, payment_map and consolidated_by.
    - payment_map looks like the result below. 
      - {'LOAN ORIGINATED': 12, 'IN GRACE PERIOD': 9, 'IN REPAYMENT': 21, 'total_payments': 21}
      - It does not take in account grace periods > 6 as in repayment
      - It rounds. Meaning if in repayment happened on 7/1/2000 but deferred on 7/12/2000, it will count as 0. If deferred on 7/16/2000, it will count as 1.
    - consolidated by give you the loan that consolidated this loan. Its useful to track for payment history. =
- Consolidation Log
  - This is the log of what the program decided is consoldated by what loan.
  - The logic for consolidation is tough because its not as clear cut.  Below is the logic as it stands.
    - It goes through all the loan and finds out what has been consolidated.
    - For each consolidated loan it will look at the date (month/year) when it was paid off and looks for a corresponding (month/year) disbursement in a consolidated loan.
    - It attempts to take into account subsidized and unsubsidized loans but its a mess because FFEL consolidated loans don't show those properties.
- Longest Payment Chain Details
  - This is probably the most interesting to most. 
  - The program attempts to determine the highest payment count towards loan discharged for IDR. The counts are in months.  
    - It will also show the "path" from origin to consolidated loans to current loan.
    - It should also take into account the 7/1/1994 date.  Meaning, payment from before this date won't count to the total_payments.
    - longest_payment means, basically, what chain of loans give the longest payments in number of months.

### Disclaimer

- To call this release alpha code would be generous. Errors in runtime are guaranteed.
  - Because there is is much activity and questions about these numbers, I wanted to quickly get something out.
- There are NO WARRANTIES.
  - No really, no guarantees of any kind. This is best guess from the data.
- DOUBLE CHECK the results!
  - I tried my best but this thing makes a lot of assumptions.
- This is NOT financial advice.
- USE AT YOUR OWN RISK!