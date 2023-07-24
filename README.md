## Student Loan Data Reader

### Purpose:

This project is meant to help in finding how many repayment counts have been made under the IDR adjustment. It uses data downloaded from studentaid.gov, parses it, and returns information that isn't so easily gleaned from their website.

My observations... the data is a mess and I'm sure I haven't see all the intricacies. Its also missing critical data like how to distinguish between in-school and other deferments vs. others.

### How it works:

A. If you trust me, I have an instance running here: https://mystudentdatatxt.com/.
 - Simply copy and paste the contents of the text. (no data is stored anywhere, make it anonymous by removing the student info but it will need the rest.)

A. If you want to run it natively (as in the source code you see) using python, do the following.

1. clone this repo to your machine.
    - git clone https://github.com/lanpartyline/fsa_student_loan_reader.git

B. Download your data.

1. Download your studnet aid file.
    1. You need to log in first.
        - https://studentaid.gov/fsa-id/sign-in/landing
    2. Click the link below.
        - https://studentaid.gov/aid-summary/loans
    3. Click "Download My Aid Data".
        - It should download to your downloads directory. If you download it elsewhere, put it in your downloads directory.  It looks for the file MyStudentData.txt

C. Run it.

1. Execute python3 loan_reader.py
2. Open results.txt in the same folder

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