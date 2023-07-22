from common import *
from account import account
import sys

def main():  
    loans_obj = account(read_file(find_file()))
    print('\n'.join(loans_obj.print_loans_summary()))
    print('\n'.join(loans_obj.print_all_loan_details()))
    
if __name__ == '__main__':
    with open('results.txt','wt') as f:
        sys.stdout = f
        main()