from decimal import Decimal as dec
from datetime import datetime as dt
from dateutil.relativedelta import *
import re
import os
import pandas as pd

def diff_month(d1: dt, d2: dt) -> int:
    """Returns the number of months between two dates

    :param d1: the latest date (the greater than)
    :param d2: the first date
    :return: months
    """
    return (d2.year - d1.year) * 12 + d2.month - d1.month

def currency_to_decimal(money: str) -> dec:
    """Formats currency to a decimal

    :param money: currency to be converted
    :return: currency as decimal
    """
    return dec(re.sub(r'[^\d.]', '', money))

def format_to_currency(num) -> str:
    """Formats number to currency

    :param num: number to be formatted
    :return: string rep of the number as currency
    """
    return '${:0,.0f}'.format(num)

def datestr_to_obj(datestring: str) -> dt:
    """Takes a date string of format '%m/%d/%Y' and convers to datetime obj

    :param datestring: string to be formatted
    :return: datetime obj
    """
    return dt.strptime(datestring.strip(), '%m/%d/%Y')

def dateobj_to_str(date: dt) -> str:
    """Takes a datetime obj and formats into a string '%m/%d/%Y'

    :param date: date to be formatted
    :return: string representation
    """
    return dt.strftime(date, '%m/%d/%Y')

def dateobj_to_str_mo_yr(date: dt) -> str:
    """Takes a datetime obj and formats into a string '%m/%Y'

    :param date: date to be formatted
    :return: string representation
    """
    return dt.strftime(date, '%m/%Y')

def cal_list_to_pd_cal(cal_list: list, f_mo: int, f_yr: int):
    """Take a list of statuses and formats into a pandas df
     that is a calendar representation of the statuses

    :param cal_list: list of statuses
    :param f_mo: The month that is the first entry in cal_list
    :param f_yr: The year that is the first entry in cal_list
    :return: pd df that is a calendar
    """
    # add offset to start in Jan
    lcal = ['' for i in range(0, f_mo - 1)] + cal_list

    # add offset to end in Dec
    ct_cal = len(lcal)
    remining_mon = ct_cal % 12
    if remining_mon > 0:
        lcal = lcal + ['' for e in range(0, 12 - remining_mon)]

    # divide up the entire cal into parts of 12
    cals = [lcal[x:x+12] for x in range(0, ct_cal, 12)]

    # create the labels for each month
    cal_records = []
    for e in cals:
        year_dict = {}
        for i, e2 in enumerate(e, start=1):
            year_dict.update({dt(1900, i, 1).strftime('%B'): e2})
        cal_records.append(year_dict)

    # create a list of pd frames of cals
    yr_idx = [f_yr + i for i in range(0, len(cal_records))]
    pd_cals = [
        pd.DataFrame([e], index=[yr_idx[i]])
        for i, e in enumerate(cal_records)
    ]
    return pd.concat(pd_cals)

def create_most_favorable_cal(cal_list: list[set]) -> list[str]:
    """Takes a list that is a calendar of statuses and chooses the
     most favorable status else chooses the first one

    :param cal_list: _description_
    :return: _description_
    """
    favorable_cal = []
    order_of_pref = ('RP', 'FB', 'DA')
    for e in cal_list:
        chosen = False
        for e2 in order_of_pref:
            if e2 in e:
                favorable_cal.append(e2)
                chosen = True
                break
        if not chosen:
            favorable_cal.append(list(e)[0])
    return favorable_cal

def count_qualified_months(cal_list: list, dates_list: list[dt], isPaid: bool=False) -> int:
    """Returns a count of qualified months under the IDR adjustment

    :param cal_list: list that is a calendar of statuses
    :return: the number of months that are qualified
    """
    # any months in a repayment status, regardless of the payments made, loan type, or repayment plan;
    # 12 or more months of consecutive forbearance or 36 or more months of cumulative forbearance;
    # any months spent in economic hardship or military deferments in 2013 or later;
    # any months spent in any deferment (with the exception of in-school deferment) prior to 2013; and
    # any time in repayment (or deferment or forbearance, if applicable)
    #   on earlier loans before consolidation of those loans into a consolidation loan.

    # because it is impossible to tell the diff. between economic vs other deferments,
    #   we must assume all deferment is not applicable.
    #  therefore, we on have to deal with RP and FB.

    list_len = len(cal_list) - 1
    covid_fb_start = dt(2020, 3, 1)
    rp, cum_fb, accumulated_con_fb, cont_fb, prev_stat = 0, 0, 0, 0, ''
    for i, e in enumerate(cal_list):
        # Months in covid count for all! So, no need to count, will add later
        if dates_list[i] < covid_fb_start:
            if 'RP' == e:
                rp += 1
            if 'FB' == e:
                cont_fb += 1
                cum_fb += 1
            # we have to be careful how we count.
            # it is possible to have 2 consecutives but the third steak might not be ok (e.g. 12, 12, 11)
            # count the consecutive at status change or end of list
            if ((prev_stat == 'FB' and e != 'FB') or (i == list_len)) and cum_fb < 36:
                if cont_fb >= 12:
                    accumulated_con_fb = accumulated_con_fb + cont_fb
            i += 1
    counted_fb = cum_fb if cum_fb >= 36 else accumulated_con_fb
    # add the covid months back into the count, ignore paid loans
    if not isPaid:
        counted_fb = counted_fb + diff_month(covid_fb_start, dt(2023, 9, 1))
    return rp  + counted_fb