from datetime import datetime
from decimal import Decimal
import re
import os
import sys

def main():  
    loans_obj = loans(read_file(find_file()))
    print('\n'.join(loans_obj.print_loans_summary()))
    print('\n'.join(loans_obj.print_all_loan_details()))
    print('\n'.join(loans_obj.print_longest_payment_chains()))
    
def find_file():
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

def read_file(filepath):
    with open(filepath) as f:
        fc = f.read()
    return fc

def mon_between(d1: datetime, d2: datetime) -> int:
    return round(abs((d2 - d1).days/30))

def currency_to_decimal(money: str) -> Decimal:
    return Decimal(re.sub(r'[^\d.]', '', money))

def format_to_currency(num: int | float) -> str:
    return '${:0,.0f}'.format(num)

def datestr_to_obj(datestring: str) -> datetime:
    return datetime.strptime(datestring.strip(), '%m/%d/%Y')
   
def dateobj_to_str(date: datetime) -> str:
    return datetime.strftime(date, '%m/%d/%Y')

def dateobj_to_str_mo_yr(date: datetime) -> str:
    return datetime.strftime(date, '%m/%Y')

class loans:
    def __init__(self, contents):
        self.forgive_start = datetime.strptime('7/1/1994', '%m/%d/%Y')
        self.contents = contents
        self.file_lines, self.file_data = self.read_contents(contents)
        self.data_source = next(iter(self.file_data[0].values()))
        self.data_pulled = next(iter(self.file_data[1].values()))
        self.parse_loan_details()
        self.parse_enrollment_info()
        self.parse_award_info()
        self.parse_studnet_info()
        self.parse_program_info()
        self.parse_undergrad_info()
        self.parse_grad_info()
        self.sort_loans()
        self.create_consolidations()
        self.calculate_longest_payment_chain()
        
        self.original_loans = [e for e in 
            self.all_loans if not e.is_consolidated and not e.is_cancelled
        ]
        self.consolidated_loans = [e for e in 
            self.all_loans if e.is_consolidated and not e.is_cancelled
        ]
        self.cancelled_loans = [e for e in self.all_loans if e.is_cancelled]
        self.current_loans = [e for e in 
            self.all_loans if not isinstance(e.paid_on, str) and not e.is_cancelled
        ]
        self.originally_loaned = sum([
            currency_to_decimal(e.loan_disbursed_amount) for e in self.original_loans
        ])
        self.current_principal = sum([
            currency_to_decimal(e.loan_outstanding_principal_balance) for e in self.current_loans
        ])
        self.current_interest = sum([
            currency_to_decimal(e.loan_outstanding_interest_balance) for e in self.current_loans
        ])
        self.capitalized_interest = sum([
            currency_to_decimal(e.capitalized_interest) for e in self.all_loans
        ])
        self.current_total = self.current_interest + self.current_principal
        self.pct_remaining = round(self.current_total/self.originally_loaned*100, 2)
        
        self.n_all_loans = len(self.all_loans)
        self.n_orig_loans = len(self.original_loans)
        self.n_cons_loans = len(self.consolidated_loans)
        self.n_canc_loans = len(self.cancelled_loans)
        
    def read_contents(self, contents) -> tuple[list, list[dict]]:
        file_lines = [e.replace('\r', '') for e in contents.split('\n')]
        file_data = [{e.split(':')[0]: e.split(':')[1]} for e in file_lines]
        return file_lines, file_data
        
    def parse_loan_details(self):
        loan_starts = [
            i for i, e in enumerate(self.file_data)
            if 'Loan Type Code' == next(iter(e.keys()))
        ]        
        
        loan_ends = [e for e in loan_starts[1:]]
        # get the last line for the final loan
        ii = loan_ends[-1]
        loan_ends = loan_ends + [
            i+ii for i, e in enumerate(self.file_data[ii:])
            if 'Loan Special Contact' == next(iter(e.keys()))]        
        
        loan_start_ends = [
            (loan_starts[i], loan_ends[i])
            for i in range(0, len(loan_ends))
        ]
        
        # init loans
        self.all_loans = [
            loan(self.file_data[e[0]: e[1]])
            for e in loan_start_ends
        ]
        self.non_loan_file_data = \
            self.file_data[0: loan_start_ends[0][0]] + \
            self.file_data[loan_start_ends[-1][1]: -1]
    
    def parse_enrollment_info(self):
        self.enrollment_log = [
            e for e in self.non_loan_file_data 
            if 'Enrolled' in next(iter(e.keys()))
            ]
        for e in self.enrollment_log:
            self.non_loan_file_data.remove(e)
        self.enrollment_info = []
        for i in range(0, len(self.enrollment_log), 5):
            x = i
            change = {}
            for e in self.enrollment_log[x:x+5]:
                change.update(e)
            self.enrollment_info.append(change)
        
    def parse_studnet_info(self):
        self.student_log = [e for e in self.non_loan_file_data if 'Student' in next(iter(e.keys()))]
        for e in self.student_log:
            self.non_loan_file_data.remove(e)
            
    def parse_award_info(self):
        self.award_log = [e for e in self.non_loan_file_data if 'Award' in next(iter(e.keys()))]
        for e in self.award_log:
            self.non_loan_file_data.remove(e)
            
    def parse_undergrad_info(self):
        self.undergrad_log = [e for e in self.non_loan_file_data if 'Undergraduate' in next(iter(e.keys()))]
        for e in self.undergrad_log:
            self.non_loan_file_data.remove(e)
            
    def parse_grad_info(self):
        self.grad_log = [e for e in self.non_loan_file_data if 'Graduate' in next(iter(e.keys()))]
        for e in self.grad_log:
            self.non_loan_file_data.remove(e)
    
    def parse_program_info(self):
        self.program_log = [e for e in self.non_loan_file_data if 'Program' in next(iter(e.keys()))]
        for e in self.program_log:
            self.non_loan_file_data.remove(e)
                
    def sort_loans(self):
        order = []
        for i, e in enumerate(self.all_loans):
            order.append((e.loan_date, e))
        ordered_loans = sorted(order, key=lambda x: datestr_to_obj(x[0]))
        self.all_loans = [e[1] for e in ordered_loans]
    
    def get_loan_by_id(self, id: str):
        fetch_loans = [e for e in self.all_loans if e.loan_award_id == id]
        if len(fetch_loans) == 1:
            return fetch_loans[0]
        elif len(fetch_loans) == 0:
            raise Exception(f'Cannot find loan {id}')
        else:
            raise Exception(f'More than 1 loan found! {fetch_loans}')
        
    def create_consolidations(self):
        self.consolidation_log = []
        for o in [e for e in self.all_loans if isinstance(e.paid_on, str)]:
            for c in [e for e in self.all_loans]:
                if \
                ((c.is_subsidized == o.is_subsidized) or ("FFEL" in c.loan_type_description)) and \
                (o.paid_on_obj.month, o.paid_on_obj.year) in [(e.month, e.year) for e in c.disbursements]:
                    c.consolidates.append(o)
                    o.consolidated_by = c
                    self.consolidation_log.append(f'{o.loan_award_id} consolidated by {c.loan_award_id}')
                    break # loan can only consolidated by 1 other loan... which isn't technically true but lets assume
        for e in self.all_loans:
            e.check_consolidation_amounts()
    
    def calculate_longest_payment_chain(self):
        def get_loan_chain(l: loan) -> list:
            chain = [l]
            while chain[-1].__dict__.get('consolidated_by'):
                chain.append(chain[-1].consolidated_by)
            return chain

        # start with all original loans
        loan_trace = [
            {'obj': e, 'total_payments': e.payment_map['total_payments']} 
            for e in self.all_loans if not e.is_consolidated and e.__dict__.get('consolidated_by')
        ]
        # get chained loans, do payment aggregation
        for e in loan_trace:
            e['loan_chain'] = get_loan_chain(e['obj'])
            e['total_payments'] = sum(
                [e.payment_map['total_payments'] for e in e['loan_chain']]
            )
            # Make sure to only count payments since 7/1/1994 so subtract if any loans began payment before then
            for e2 in e['loan_chain']:
                if not e2.__dict__.get('first_repayment'):
                    origin_date = e2.loan_date_obj
                else:
                    origin_date = e2.first_repayment
                if origin_date < self.forgive_start:
                    e['total_payments'] = e['total_payments'] - mon_between(self.forgive_start, origin_date)

        # find the higest payment count
        self.longest_payment = 0
        for e in loan_trace:
            if e['total_payments'] > self.longest_payment:
                self.longest_payment = e['total_payments']
                
        self.possible_longest_chains = [
            e['loan_chain']
            for e in loan_trace 
            if e['total_payments'] == self.longest_payment
        ]
                
    def print_loans_summary(self) -> list:
        output = []
        output.append('-'*100)
        output.append('Loans Summary')
        output.append('-'*100)
        output.append(f'Num of Loans        : {self.n_all_loans}')
        output.append(f'Num of Orig. Loans  : {self.n_orig_loans}')
        output.append(f'Num of Cons. Loans  : {self.n_cons_loans}')
        output.append(f'Num of Canc. Loans  : {self.n_canc_loans}')
        output.append(f'Orig. Loaned Amt    : {format_to_currency(self.originally_loaned)}')
        output.append(f'Capitalized Interest: {format_to_currency(self.capitalized_interest)}')
        output.append(f'Current Principal   : {format_to_currency(self.current_principal)}')
        output.append(f'Current Interest    : {format_to_currency(self.current_interest)}')
        output.append(f'Current Total       : {format_to_currency(self.current_total)}')
        output.append(f'Pct Remaining       : '+ '{:0,.0f} %'.format(self.pct_remaining))
        
        # Check for oddities and print warnings
        warnings = []
        if self.capitalized_interest + self.originally_loaned != self.current_principal:
            warnings.append('Original Principals + Capitalized Amount Does NOT add up.')
        if len(warnings) > 0:
            output.append('WARNINGs:')
        for i, e in enumerate(warnings):
            output.append(f'  {i+1} - {e}')
        
        output.append('-'*100)
        output.append('Unpaid Loans')
        output.append('-'*100)
        for i, e in enumerate(self.current_loans):
            output.append(f'{i+1} - {e.loan_award_id} - {e.loan_type}')
            output.append(f'Loan Date: {e.loan_date} - ' \
                  f'Loan Amount: {e.net_loan_amount} - '\
                  f'Current Status: {e.current_loan_status_description}')
            output.append('')
        return output
        
    def print_all_loan_details(self) -> list:
        output = []
        output.append('-'*100)
        output.append('Loan Details')
        output.append('-'*100)
        for e in self.all_loans:
            output.append('\n'.join(e.print_details()))
            output.append('')
        output.append('-'*100)
        output.append('Consolidation Log')
        output.append('-'*100)
        output.append('\n'.join(self.consolidation_log)+'\n')
        return output
        
    def print_longest_payment_chains(self) -> list:
        output = []
        output.append('-'*100)
        output.append('Longest Payment Chain Details')
        output.append('-'*100)
        output.append(f'longest_payment = {self.longest_payment}')
        output.append('')
        for i, e in enumerate(self.possible_longest_chains):
            output.append(f'CHAIN {i+1} {"-"*50}')
            for e2 in e:
                output.append('\n'.join(e2.print_details()))
                output.append('')
        return output

class loan:
    def __init__(self, data: list[dict]):
        self.file_data = data
        for e in data:
            for k, v in e.items():
                self.__dict__[k.replace(' ', '_').lower()] = v
        
        self.loan_type = self.loan_type_description
        self.loan_date_obj = datestr_to_obj(self.loan_date)
        self.loan_date_mo_yr = dateobj_to_str_mo_yr(datestr_to_obj(self.loan_date))
        self.is_ffel = True if 'FFEL' in self.loan_type else False
        self.is_direct = True if 'DIRECT' in self.loan_type else False
        self.is_cancelled = True if 'CANCELLED' in self.current_loan_status_description else False
        self.is_consolidated = True if 'CONSOLIDATED' in self.loan_type_description else False
        if self.is_consolidated:
            self.consolidates = []
        self.is_subsidized = False if 'UNSUBSIDIZED' in self.loan_type_description else True
        self.loan_award_id = self.loan_award_id.replace('*', '')
        self.status_changes = self.create_status_log(self.file_data)
        if self.is_cancelled:
            self.payment_map = {}
        else:
            self.payment_map = self.create_payment_status(self.status_changes)
            self.payment_map['total_payments'] = 0
            for k, v in self.payment_map.items():
                if k == 'FORBEARANCE' or k == 'IN REPAYMENT':
                    self.payment_map['total_payments'] = self.payment_map['total_payments'] + v
            for e in self.status_changes:
                if 'REPAYMENT' in e['Loan Status Description']:
                    self.first_repayment = e['Loan Status Effective Date Obj']
        if not self.is_cancelled:
            self.disbursment_map = self.create_disbursement_log(self.file_data)
            self.disbursements = [
                e['Loan Disbursement Date Obj']
                for e in self.disbursment_map
            ]
            self.total_disbursed = sum([
                currency_to_decimal(e['Loan Disbursement Amount'])
                for e in self.disbursment_map
            ])
        else:
            self.disbursment_map = {}
            self.disbursements = []
        self.consolidated_on = None
        self.consolidated_on_mo_yr = None
        self.paid_on = None
        self.paid_on_yr = None
        for e in self.status_changes:
            if "CONSOLIDATION" in e['Loan Status Description']:
                self.consolidated_on_obj = e['Loan Status Effective Date Obj']
                self.consolidated_on = dateobj_to_str(self.consolidated_on_obj)
                self.consolidated_on_mo_yr = dateobj_to_str_mo_yr(self.consolidated_on_obj)
                self.consolidated_by = ''
            if "PAID IN FULL" in e['Loan Status Description']:
                self.paid_on_obj = e['Loan Status Effective Date Obj']
                self.paid_on = dateobj_to_str(self.paid_on_obj)
                self.paid_on_mo_yr = dateobj_to_str_mo_yr(self.paid_on_obj)
        
    def create_status_log(self, file_data: list[dict]) -> list:
        data = [e for e in file_data if 
            'Loan Status' in next(iter(e.keys())) and 
            'Current' not in next(iter(e.keys()))]
        status_changes = []
        for i in range(0, len(data), 3):
            x = i
            change = {}
            for e in data[x:x+3]:
                change.update(e)
            status_changes.append(change)
        status_changes = sorted(
            status_changes, key=lambda x: datestr_to_obj(x['Loan Status Effective Date']))
        for e in status_changes:
            e['Loan Status Effective Date Obj'] = datestr_to_obj(e['Loan Status Effective Date'])
        return status_changes
    
    def create_disbursement_log(self, file_data: list[dict]) -> list:
        data = [e for e in file_data if 'Loan Disbursement' in next(iter(e.keys()))]
        disbursements = []
        for i in range(0, len(data), 2):
            x = i
            disbursement = {}
            for e in data[x:x+2]:
                disbursement.update(e)
            disbursements.append(disbursement)
        disbursements = sorted(
            disbursements, key=lambda x: datestr_to_obj(x['Loan Disbursement Date']))
        for e in disbursements:
            e['Loan Disbursement Date Obj'] = datestr_to_obj(e['Loan Disbursement Date'])
        return disbursements

    def create_payment_status(self, status_changes: list[dict]) -> dict:
        payment_map = {}
        last_key = len(status_changes) -1
        date_key = 'Loan Status Effective Date Obj'
        status_key = 'Loan Status Description'
        for i, e in enumerate(status_changes):
            if 'PAID IN FULL' in e[status_key]:
                break
            if not payment_map.get(e[status_key]):
                payment_map[e[status_key]] = 0
            if i == last_key:
                payment_map[e[status_key]] = \
                    payment_map[e[status_key]] + \
                    mon_between(e[date_key], datetime.today())
            else:
                payment_map[e[status_key]] = \
                    payment_map[e[status_key]] + \
                    mon_between(e[date_key], status_changes[i+1][date_key])
        return payment_map
    
    def check_consolidation_amounts(self):
        if self.is_consolidated:
            self.consolidated_amounts = []
            for e in self.consolidates:
                self.consolidated_amounts.append(
                    currency_to_decimal(e.loan_amount) + currency_to_decimal(e.capitalized_interest)
                )
            self.consolidated_amount = sum(self.consolidated_amounts)
                
    def print_details(self) -> list:
        output = []
        attribs = [
            'loan_type_description',
            'current_loan_status_description',
            'loan_award_id',
            'is_consolidated',
            'loan_date',
            'loan_amount',
            'total_disbursed',
            'paid_on',
            'is_subsidized',
            'first_repayment',
            'consolidated_by',
            'consolidates',
            'consolidated_amount',
            'payment_map',
            'status_changes'
        ]
        for f in attribs:
            if self.__dict__.get(f):
                if f == 'consolidates':
                    output.append(f'{f} = {[e.loan_award_id for e in self.__dict__[f]]}')
                elif f == 'consolidated_by':
                    output.append(f'{f} = {self.__dict__[f].loan_award_id}')
                elif f == 'first_repayment':
                    output.append(f'{f} = {dateobj_to_str(self.first_repayment)}')
                elif f == 'total_disbursed':
                    output.append(f'{f} = {format_to_currency(self.total_disbursed)}')
                elif f == 'consolidated_amount':
                    output.append(f'{f} = {format_to_currency(self.consolidated_amount)}')
                elif f == 'status_changes':
                    output.append(
                        "\n".join([f'{e["Loan Status Description"]}: {e["Loan Status Effective Date"]}' for e in self.status_changes])
                    )
                else:
                    output.append(f'{f} = {self.__dict__[f]}')
        return output

if __name__ == '__main__':
    with open('results.txt','wt') as f:
        sys.stdout = f
        main()