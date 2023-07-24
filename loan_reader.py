from common import *
from account import account
import sys

def main():
    loans_obj = account(read_file(find_file()))
    print('\n'.join(loans_obj.print_loans_summary()))
    print('\n'.join(loans_obj.print_all_loan_details()))

def find_file() -> str:
    """Search for a specific file in a specific location

    :return: file path
    """
    # Download File Here: https://studentaid.gov/aid-summary/loans, click "Download My Aid Data"
    look_for_files = ['mystudentdata.txt']
    look_in = [f'{os.getenv("HOMEPATH")}\\Downloads\\']
    file = None
    for folder in look_in:
        for file in look_for_files:
            if file in [e.lower() for e in os.listdir(folder)]:
                return f'{folder}\\{file}'
    print('Student File Not Found')
    print(f'Looked for {look_for_files} in {look_in}')
    exit()

def read_file(filepath: str) -> str:
    """Reads file and returns contents

    :param filepath: file oath to read
    :return: contents
    """
    with open(filepath) as f:
        fc = f.read()
    return fc

if __name__ == '__main__':
    with open('results.txt','wt') as f:
        sys.stdout = f
        main()