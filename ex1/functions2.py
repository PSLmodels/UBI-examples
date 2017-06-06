
# coding: utf-8

# In[1]:

import copy
import pandas as pd
import numpy as np
from taxcalc import *

def add_income_bins(pdf, income_measure='expanded_income'):
    bins = [-1, 9999, 19999, 29999, 39999, 49999, 74999, 99999, 200000, 1000000,1e14]
    labels = [x for x in range(1, 11)]
    pdf['bins'] = pd.cut(pdf[income_measure], bins=bins, labels=labels)
    return pdf

# Function to find starting UBI amount
def ubi_amt(revenue, u18, abv18):
    ubi_18 = revenue / ((u18 * 0.5) + abv18)
    ubi_u18 = ubi_18 * 0.5
    total_ubi = (ubi_18 * abv18) + (ubi_u18 * u18)
    return ubi_18, ubi_u18


# In[4]:

# Function to find ending UBI amount
def ubi_finder(ubi_18, ubi_u18, tax_reform, revenue, calc_reform):
    # Build a calculator with the specified UBI levels
    recs_finder = Records('puf_benefits.csv', weights='puf_weights_new.csv', adjust_ratios='puf_ratios copy.csv')
    pol_finder = Policy()
    pol_finder.implement_reform(tax_reform)
    try:
        pol_finder.implement_reform(tax_reform)
    except NameError:
        pass
    ubi_finder_reform = {
        2014: {
            '_UBI1': [ubi_u18],
            '_UBI2': [ubi_18],
            '_UBI3': [ubi_18]
        }
    }
    pol_finder.implement_reform(ubi_finder_reform)
    calc_finder = Calculator(records=recs_finder, policy=pol_finder, verbose=False)
    calc_finder.records.e02400 = np.zeros(len(calc_finder.records.e02400))
    calc_finder.advance_to_year(2014)
    calc_finder.calc_all()
    # Check if UBI is greater or less than the additional revenue
    # Revenue from tax reform
    ubi_tax_rev = ((calc_finder.records.combined - calc_reform.records.combined) * calc_finder.records.s006).sum()
    total_rev = ubi_tax_rev + revenue
    ubi = (calc_finder.records.ubi * calc_finder.records.s006).sum()
    diff = ubi - total_rev
    return diff, ubi_tax_rev


# In[5]:

def table(table_data, avg_ben, avg_ben_mult):
    # Income floor per bin
    floors = []
    for x in range(1, 11):
        floors.append(min(table_data['e00200'][table_data['bins'] == x]))
    decile_floor = pd.Series(floors)
    
    # Average tax unit size
    avg_size = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'ppl')

    # Average UBI per person
    avg_ubi = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'ubi/person')

    # Average Primary Earner payroll MTR 
    avg_pmtr = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'pmtr')

    # Average primary earner income mtr
    avg_imtr = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'imtr')

    # Average combined MTR
    avg_cmtr = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'cmtr')

    # Average Tax Change
    avg_ctax = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'tax_change')

    # Average UBI per tax unit
    avg_ubitu = table_data.groupby('bins', as_index=False).apply(utils.weighted_mean, 'ubi')
    
    # taxunit in each bin
    tot_taxunit = table_data.groupby('bins', as_index=False).sum()['s006']
    
    # Create DataFrame with all relevant information
    info = pd.DataFrame()
    info['Wage and Salary Floor (Thousands)'] = (decile_floor / 1000).apply('{:,.0f}'.format)
    info['Tax Units (m)'] = tot_taxunit/1000000
    info['Avg Tax Unit Size'] = avg_size
    info['Avg UBI Per Person'] = avg_ubi.apply('{:,.0f}'.format)
    info['Avg MTR - Payroll'] = (avg_pmtr * 100).apply('{:.1f}%'.format)
    info['Avg MTR - Individual Income'] = (avg_imtr * 100).apply('{:.1f}%'.format)
    info['Avg MTR - Combined'] = (avg_cmtr * 100).apply('{:.1f}%'.format)
    info['Avg Tax Change'] = avg_ctax.apply('{:,.0f}'.format)
    info['Avg UBI Per Tax Unit'] = avg_ubitu.apply('{:,.0f}'.format)
    info['Avg Benefits Change'] = (-1.0 * avg_ben).apply('{:,.0f}'.format)
    info['Avg Benefits Change - Welfare Adj'] = (-1.0 * avg_ben_mult).apply('{:,.0f}'.format)
    info['Avg Combined Change'] = (avg_ubitu - avg_ctax - avg_ben).apply('{:,.0f}'.format)
    info['Avg Combined Change - Welfare Adj'] = (avg_ubitu - avg_ctax - avg_ben_mult).apply('{:,.0f}'.format)
    

    return info


# In[7]:

def cps_avg_ben(cps_storage, other_programs, group='all', bins='decile'):
    
    head = (cps_storage.age_head>=65)
    spouse = (cps_storage.age_spouse>=65)
    d1 = (cps_storage.age_dep1>=65)
    d2 = (cps_storage.age_dep2>=65)
    d3 = (cps_storage.age_dep3>=65)
    d4 = (cps_storage.age_dep4>=65)
    d5 = (cps_storage.age_dep5>=65)
    over_65 = (head|spouse|d1|d2|d3|d4|d5)
    under_65 = np.invert(over_65)
    
    if group == 'all':
        cps = cps_storage
    elif group == 'under 65':
        cps = copy.deepcopy(cps_storage[under_65])
    elif group == '65 or over':
        cps = copy.deepcopy(cps_storage[over_65])
        
    # Welfare multipliers
    # Welfare multiples
    welfare_mult ={
        'mcare': 0.75,
        'mcaid': 0.30,
        'snap': 0.95,
        'ss': 1.0,
        'ssi': 1.0,
        'vb': 0.95
    }
    # Find distribution of benefits
    cps['tot_ben'] = (cps['MedicareX'] + cps['MEDICAID'] + cps['SS'] + cps['SSI'] + cps['SNAP'] + cps['VB'] + cps['other'])

    cps['tot_ben_mult'] = ((cps['MedicareX'] * welfare_mult['mcare']) +
                           (cps['MEDICAID'] * welfare_mult['mcaid']) +
                           (cps['SS'] * welfare_mult['ss']) +
                           (cps['SSI'] * welfare_mult['ssi']) +
                           (cps['SNAP'] * welfare_mult['snap']) +
                           (cps['VB'] * welfare_mult['vb']) +
                           cps['other']) 
    
    if bins=='decile':
        cps = utils.add_weighted_income_bins(cps, income_measure='WAS')
    elif bins=='income':
        cps = add_income_bins(cps, income_measure='WAS')
        
    # Total number in each bin
    nums = []
    for x in range(1, 11):
        nums.append(cps.s006[cps.bins == x].sum())
    nums = pd.Series(nums)
    nums.index = [x for x in range(1, 11)]
    
    tot_ben = pd.Series(cps.groupby('bins').apply(utils.weighted_sum, 'tot_ben'))
    avg_ben = tot_ben / nums
    avg_ben.index = [x for x in range(0, 10)]
    
    tot_ben_mult = pd.Series(cps.groupby('bins').apply(utils.weighted_sum, 'tot_ben_mult'))
    avg_ben_mult = tot_ben_mult / nums
    avg_ben_mult.index = [x for x in range(0, 10)]
    
    return avg_ben, avg_ben_mult
# In[8]:

def prep_table_data(calc, calc_base, mtrs, group='all', bins='decile'):
    p = (calc.records.age_head>=65)
    s = (calc.records.age_spouse>=65)
    old = (calc.records.elderly_dependent==1)
    over_65_puf = (p|s|old)
    
    if group == 'all':
        f = (calc_base.records.e02400>=0)
    elif group == 'under 65':
        f = np.invert(over_65_puf)
    elif group == '65 or over':
        f = over_65_puf
        
    table_data = pd.DataFrame()

    table_data['s006'] = copy.deepcopy(calc.records.s006[f])
    table_data['c00100'] = copy.deepcopy(calc.records.c00100[f])
    table_data['e00200'] = copy.deepcopy(calc.records.e00200[f])
    table_data['ubi'] = copy.deepcopy(calc.records.ubi[f])
    table_data['ppl'] = calc.records.nu18[f] + calc.records.n1821[f] + calc.records.n21[f]

    #* table_data1.ppl
    table_data['ubi/person'] = table_data['ubi'] / table_data['ppl']
    table_data['tax_change'] = calc.records.combined[f] - calc_base.records.combined[f]
    # Payroll, income, and combined mtr
    table_data['pmtr'] = copy.deepcopy(mtrs[0][f])
    table_data['imtr'] = copy.deepcopy(mtrs[1][f])
    table_data['cmtr'] = copy.deepcopy(mtrs[2][f])
    
    if bins=='decile':
        table_data = utils.add_weighted_income_bins(table_data, income_measure='e00200')
    elif bins=='income':
        table_data = add_income_bins(table_data, income_measure='e00200')
    
    return table_data


# In[ ]:



