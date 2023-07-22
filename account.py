from common import *
from loan import loan

class account:
    def __init__(self, contents):
        self.forgive_start = dt.strptime('7/1/1994', '%m/%d/%Y')
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
        # self.calculate_longest_payment_chain()
        self.create_unified_status_cal()
        self.favorable_cal = create_most_favorable_cal(self.status_cal)
        self.create_status_description_map()
        self.create_pd_cals()
        self.qualified_months = count_qualified_months(self.favorable_cal, self.dates_cal)
        # self.borrow_cal_favorable = self.get_most_favorable_cal(self.borrow_cal)

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


    ############################ READING AND PARSING FILE ##########################################
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
        self.student_log = [
            e for e in self.non_loan_file_data if 'Student' in next(iter(e.keys()))]
        for e in self.student_log:
            self.non_loan_file_data.remove(e)

    def parse_award_info(self):
        self.award_log = [
            e for e in self.non_loan_file_data if 'Award' in next(iter(e.keys()))
        ]
        for e in self.award_log:
            self.non_loan_file_data.remove(e)

    def parse_undergrad_info(self):
        self.undergrad_log = [
            e for e in self.non_loan_file_data if 'Undergraduate' in next(iter(e.keys()))
        ]
        for e in self.undergrad_log:
            self.non_loan_file_data.remove(e)

    def parse_grad_info(self):
        self.grad_log = [
            e for e in self.non_loan_file_data if 'Graduate' in next(iter(e.keys()))
        ]
        for e in self.grad_log:
            self.non_loan_file_data.remove(e)

    def parse_program_info(self):
        self.program_log = [
            e for e in self.non_loan_file_data if 'Program' in next(iter(e.keys()))
        ]
        for e in self.program_log:
            self.non_loan_file_data.remove(e)

    ############################ END READING AND PARSING FILE ##########################################

    def cal_relative_pos(self, loanObj: loan) -> tuple[int, int]:
        """Returns the start and end index where the loan's "calendar" fits in to the overall calendar.
        i.e. given a list of months  [i, ia, ... ix ... iy ... iz] where does it start in the list, ix, and end, iy.

        :param fdate: Date of the first loan (borrower first interaction)
        :param loanObj: loan that is to be examined
        :return: start and end index within the list
        """
        start_idx = diff_month(self.all_loans[0].loan_date_obj, loanObj.loan_date_obj)
        # The end of the loan's status might be today if it is not paid
        if isinstance(loanObj.paid_on, str):
            end_idx = diff_month(self.all_loans[0].loan_date_obj, loanObj.paid_on_obj)
        else:
            end_idx = diff_month(self.all_loans[0].loan_date_obj, dt.today())
        return start_idx, end_idx

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

    def merge_loan_cal_to_status_cal(self, loanObj: loan, acct_cal: list[set]):
        start_idx, end_idx = self.cal_relative_pos(loanObj)
        for loan_idx, bor_idx in enumerate(range(start_idx, end_idx)):
            [acct_cal[bor_idx].add(e) for e in loanObj.status_cal[loan_idx]]
        return acct_cal

    def create_unified_status_cal(self):
        first_date = self.all_loans[0].loan_date_obj
        first_date = dt(first_date.year, first_date.month, 1)
        borrower_months = diff_month(first_date, dt.today())
        account_cal = [set() for i in range(0, borrower_months)]
        for loanObj in [e for e in self.all_loans if not e.is_cancelled]:
            account_cal = self.merge_loan_cal_to_status_cal(loanObj, account_cal)
        self.status_cal = account_cal
        self.dates_cal = [first_date + relativedelta(months=+i) for i in range(0, borrower_months)]

    def create_pd_cals(self):
        self.status_pd_cal = cal_list_to_pd_cal(
            self.status_cal,
            self.dates_cal[0].month,
            self.dates_cal[0].year
        )
        self.favorable_pd_cal = cal_list_to_pd_cal(
            self.favorable_cal,
            self.dates_cal[0].month,
            self.dates_cal[0].year
        )

    def create_status_description_map(self):
        status_description_map = {}
        for e in self.all_loans:
            for e2 in e.status_changes:
                status_description_map[e2['Loan Status']] = e2['Loan Status Description']
        self.status_description_map = status_description_map

    # def calculate_longest_payment_chain(self):
    #     def get_loan_chain(l: loan) -> list:
    #         chain = [l]
    #         while chain[-1].__dict__.get('consolidated_by'):
    #             chain.append(chain[-1].consolidated_by)
    #         return chain

    #     # start with all original loans
    #     loan_trace = [
    #         {'obj': e, 'total_payments': e.payment_map['total_payments']} 
    #         for e in self.all_loans if not e.is_consolidated and e.__dict__.get('consolidated_by')
    #     ]
    #     # get chained loans, do payment aggregation
    #     for e in loan_trace:
    #         e['loan_chain'] = get_loan_chain(e['obj'])
    #         e['total_payments'] = sum(
    #             [e.payment_map['total_payments'] for e in e['loan_chain']]
    #         )
    #         # Make sure to only count payments since 7/1/1994 so subtract if any loans began payment before then
    #         for e2 in e['loan_chain']:
    #             if not e2.__dict__.get('first_repayment'):
    #                 origin_date = e2.loan_date_obj
    #             else:
    #                 origin_date = e2.first_repayment
    #             if origin_date < self.forgive_start:
    #                 e['total_payments'] = e['total_payments'] - diff_month(self.forgive_start, origin_date)

    #     # find the higest payment count
    #     self.longest_payment = 0
    #     for e in loan_trace:
    #         if e['total_payments'] > self.longest_payment:
    #             self.longest_payment = e['total_payments']

    #     self.possible_longest_chains = [
    #         e['loan_chain']
    #         for e in loan_trace
    #         if e['total_payments'] == self.longest_payment
    #     ]

    ############################ DISPLAYING RESULTS ##########################################

    def print_loans_summary(self) -> list:
        output = []
        output.append('-'*100)
        output.append('Account Summary')
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
        output.append(f'Estimated Months    : {self.qualified_months}')
        output.append('')
        output.append('Status Key:')
        [output.append(f'{k} = {v}') for k, v in self.status_description_map.items()]
        output.append('')
        output.append('MOST FAVORABLE CALENDAR')
        output.append(self.favorable_pd_cal.to_html().replace('\n', ''))
        output.append('AGGREGATE CALENDAR')
        output.append(self.status_pd_cal.to_html().replace('\n', ''))

        # Data weirdness needs works, serparate        
        # # Check for oddities and print warnings
        # warnings = []
        # if self.capitalized_interest + self.originally_loaned != self.current_principal:
        #     warnings.append('Original Principals + Capitalized Amount Does NOT add up.')
        # if len(warnings) > 0:
        #     output.append('WARNINGs:')
        # for i, e in enumerate(warnings):
        #     output.append(f'  {i+1} - {e}')

        output.append('-'*100)
        output.append('Current Active Loans')
        output.append('-'*100)
        for i, e in enumerate(self.current_loans):
            output.append(f'{i+1} - {e.loan_award_id} - {e.loan_type}')
            output.append(f'Loan Date: {e.loan_date} - ' \
                  f'Loan Amount: {e.net_loan_amount} - '\
                  f'Current Status: {e.current_loan_status_description}')
            output.append('')
        output.append('')
        return output

    def print_all_loan_details(self) -> list:
        output = []
        output.append('-'*100)
        output.append('All Loan Details')
        output.append('-'*100)
        for e in self.all_loans:
            output.append('\n'.join(e.print_details()))
            output.append('-'*100)
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

    ############################ END DISPLAYING RESULTS ##########################################