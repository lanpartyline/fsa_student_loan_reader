## Student Loan Data Reader

### Purpose:

This project is meant to help in finding how many repayment counts have been made under the IDR adjustment. It uses data downloaded from studentaid.gov, parses it, and returns information that isn't so easily gleaned from their website. This simply writes to results.txt in the local directory for you to examine. It does not communicate with anything, its completely local, take a look at the source code.

My observations... the data is a mess and I'm sure I haven't see all the intricacies.

### How it works:

A. If you trust me, you can download a binary for Windows.

1. Download zip. Here: https://drive.google.com/drive/folders/1RkbjrH5pOpBANMTMi-V8uzmc2qFXUGlD
2. Unzip it.

A. If you want to run it natively (as in the source code you see) using python, do the following.
- (You can skip these steps if you have the binary)

1. clone this repo to your machine. 
    - git clone https://github.com/lanpartyline/fsa_student_loan_reader.git
2. Download and install Python on your machine.
    - https://www.python.org/downloads/

B. Download your data.

1. Download your studnet aid file.
    1. You need to log in first.
        - https://studentaid.gov/fsa-id/sign-in/landing
    2. Click the link below.
        - https://studentaid.gov/aid-summary/loans
    3. Click "Download My Aid Data".
        - It should download to your downloads directory. If you download it elsewhere, put it in your downloads directory.  It looks for the file MyStudentData.txt

C. Run it.

1. Execute loan_reader.exe
    - Or (if running it native python) python3 loan_reader.py
    - it might say it will scan for viruses, I'm not doing anything funny, it's Microsoft being careful.
2. Open results.txt in the same folder

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

### Bugs and Issues

Feel free to submit an issue but I don't have much time to dedicate to this and its a bit difficult to troubleshoot without having your specific data. PLEASE DO NOT post private info.