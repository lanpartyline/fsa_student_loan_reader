from common import *

class loan:
    def __init__(self, data: list[dict]):
        self.file_data = data
        for e in data:
            for k, v in e.items():
                self.__dict__[k.replace(' ', '_').lower()] = v
        
        self.loan_type = self.loan_type_description
        self.data_weird = []
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
        
        self.create_status_log(self.file_data)
        self.sort_status()
        self.create_paid_on_data()
        self.create_status_durations()
        self.create_loan_cal()
        self.create_cal_of_status()
        self.create_pd_cal_of_status()
        self.favorable_cal = create_most_favorable_cal(self.status_cal)
        
        self.create_payment_data()
        self.create_disbursment_data()
        self.create_consolidation_data()
        self.qualified_months = count_qualified_months(
            self.favorable_cal, self.dates_cal, self.is_paid
        )
        
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
        self.status_changes = status_changes
       
    def create_payment_data(self):
        if self.is_cancelled:
            self.payment_map = {}
        else:
            self.payment_map = self.create_payment_status(self.status_changes)
            #self.payment_map['total_payments'] = 0
            # for k, v in self.payment_map.items():
                # if k == 'FORBEARANCE' or k == 'IN REPAYMENT':
                    # self.payment_map['total_payments'] = self.payment_map['total_payments'] + v
            for e in self.status_changes:
                if 'REPAYMENT' in e['Loan Status Description']:
                    self.first_repayment = e['Loan Status Effective Date Obj']
                    
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
                    diff_month(e[date_key], dt.today())
            else:
                payment_map[e[status_key]] = \
                    payment_map[e[status_key]] + \
                    diff_month(e[date_key], status_changes[i+1][date_key])
        return payment_map
                    
    def create_consolidation_data(self):
        self.consolidated_on = None
        self.consolidated_on_mo_yr = None
        for e in self.status_changes:
            if "CONSOLIDATION" in e['Loan Status Description']:
                self.consolidated_on_obj = e['Loan Status Effective Date Obj']
                self.consolidated_on = dateobj_to_str(self.consolidated_on_obj)
                self.consolidated_on_mo_yr = dateobj_to_str_mo_yr(self.consolidated_on_obj)
                self.consolidated_by = ''
                
    def create_paid_on_data(self):
        self.paid_on = None
        self.paid_on_yr = None
        if "PAID IN FULL" in self.status_changes[-1]['Loan Status Description']:
                self.paid_on_obj = self.status_changes[-1]['Loan Status Effective Date Obj']
                self.paid_on = dateobj_to_str(self.paid_on_obj)
                self.paid_on_mo_yr = dateobj_to_str_mo_yr(self.paid_on_obj)
                self.is_paid = True
        else:
            self.is_paid = False

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
                    
    def create_disbursment_data(self):
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
    
    def check_consolidation_amounts(self):
        if self.is_consolidated:
            self.consolidated_amounts = []
            for e in self.consolidates:
                self.consolidated_amounts.append(
                    currency_to_decimal(e.loan_amount) + currency_to_decimal(e.capitalized_interest)
                )
            self.consolidated_amount = sum(self.consolidated_amounts)
            
    def sort_status(self) -> list[dict]:
        """Sorts the loan status changes

        :param loanObj: loan obj with status changes
        :return: the sorted status changes
        """
        self.status_changes = sorted(self.status_changes, key=lambda x: x["Loan Status Effective Date Obj"])
    
    def create_status_durations(self) -> list[tuple]:
        """Returns a status and duration of status changes for a given loan

        :param loanA: loanObj
        """  
        status_updates = []
        for i in range(0, len(self.status_changes) - 1):
            status = self.status_changes[i]['Loan Status']
            start_date = self.status_changes[i]['Loan Status Effective Date Obj']
            end_date = self.status_changes[i+1]['Loan Status Effective Date Obj']
            status_updates.append((diff_month(start_date, end_date), status))
        if not self.is_paid:
            status_updates.append((
                diff_month(
                    self.status_changes[-1]['Loan Status Effective Date Obj'],
                    dt.today()
                ),
                self.status_changes[-1]['Loan Status']
            ))
        else:
            status_updates.append((1, self.status_changes[-1]['Loan Status']))
        self.status_durations = status_updates
        
    def create_loan_cal(self):
        end_loan_date = self.paid_on_obj if self.is_paid else dt.today()
        # The data sucks... here is an example.
        # Loan Date:12/06/2011
        # Loan Status Description:FORBEARANCE
        # Loan Status Effective Date:06/09/2011
        # How can you have a status update before the loan was even created?
        # so, you need to pick the date that is the earlier of the two, because which is right?
        start_loan_date = self.loan_date_obj
        if start_loan_date > self.status_changes[0]['Loan Status Effective Date Obj']:
            start_loan_date = self.status_changes[0]['Loan Status Effective Date Obj']
            self.data_weird.append(
                f'Loan date is later than status updates, loan_date={self.loan_date}, ' + \
                f'first_status_update={dateobj_to_str(start_loan_date)}'
            )
        self.loan_months = diff_month(start_loan_date, end_loan_date)
        self.dates_cal = [
            start_loan_date + relativedelta(months=+i)
            for i in range(0, self.loan_months)
        ]
        self.status_cal = [set() for i in range(0, self.loan_months)]
        if self.is_paid:
            self.status_cal.append(set())
        
    def create_cal_of_status(self):
        i = 0
        for e in self.status_durations:
            for x in range(i, i + e[0]):
                self.status_cal[x].add(e[1])
            i = i + e[0]
        if self.is_paid:
            self.status_cal.pop(-1)
        
    def create_pd_cal_of_status(self):
        status_pd_cal = cal_list_to_pd_cal(
            self.status_cal,
            self.status_changes[0]['Loan Status Effective Date Obj'].month,
            self.status_changes[0]['Loan Status Effective Date Obj'].year
        )
        self.status_pd_cal = status_pd_cal

    ############################ DISPLAYING RESULTS ##########################################
                
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
            'is_paid',
            'qualified_months',
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
                elif f == 'qualified_months':
                    output.append(f'estimated_months = {self.qualified_months}')
                elif f == 'status_changes':
                    output.append('STATUS CHANGES')
                    output.append(
                        "\n".join([
                            f'- {e["Loan Status Description"].lower()}: {e["Loan Status Effective Date"]}'
                            for e in self.status_changes]))
                else:
                    output.append(f'{f} = {self.__dict__[f]}')
        output.append('')            
        output.append(self.status_pd_cal.to_html().replace('\n', ''))
        return output
    
    ############################ END DISPLAYING RESULTS ##########################################