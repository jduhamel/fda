# Coding: utf-8

"""`main` is the top level module for your Flask application."""

# Import request and BS4

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

### FDA URL
""" File Constants"""

FDA_URL="https://www.accessdata.fda.gov"
FDA_QRY_URL="/scripts/cder/daf/index.cfm?event=reportsSearch.process&rptName=1"
FDA_MONTH="&reportSelectMonth="
FDA_YEAR="&reportSelectYear="
FDA_DRUG_QRY_URL="/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=019661"



def get_new_drugs(month=7,year=2017):
    """Returns a list of all new drug ids or urls."""
    drugs = []
    query_url=FDA_URL+FDA_QRY_URL+FDA_MONTH+str(month)+FDA_YEAR+str(year)
    req = requests.get(query_url)
    print(query_url)
    soup = BeautifulSoup(req.text,"html5lib")
    count = 0
    trs =  soup.find_all('table')[0].find_all('tr')
    for tr in trs:
        if count > 10:
            exit(1)
        dm = {}
        cols = tr.find_all('td')
        if len(cols)==0:
            print("no cols returned:")
            continue
        dm['Approval Date'] = cols[0].contents[0]
        dm['ApplID'] = cols[1].find_all('a')[0].get('href').split('=')[2]
        for br in cols[1].find_all("br"):
            br.replace_with("\n")
        text = cols[1].find_all('a')[0].getText().split('\n')
        dm['Drug Name'] = text[0].strip()
        dm['ApplID2'] = text[1].strip().split('#')[1].strip()
        dm['Drug Type'] = text[1].strip().split('#')[0].strip()
        print("dm:",dm)
        dm['Submission'] = cols[2].contents[0].strip()
        dm['ActiveIngredient']= cols[3].contents[0]
        dm['Company'] = cols[4].contents[0]
        if len(cols[5].contents) != 0:
            dm['Submission Classification'] = cols[5].contents[0].strip()
        else:
            dm['Submission Classification'] = ''
        dm["Submission Status"] = cols[6].contents[0]
        # ok we need to check level 1 criteria
        drug_list = []
        if check_selection_criteria(dm):
            if dm['Drug Type'] != "ANDA":
                drug_list = get_drug_detail(dm)

        if drug_list:
            drugs = drugs+drug_list
            print(drug_list)

    return drugs

# 208535, 202674 Test cases

def check_selection_criteria(drug_item: dict,verbose: bool = False) -> bool:
    if 'Submission Classification' not in drug_item:
        print("Error no Submission Classification")
        return False

    if 'Submission' not in drug_item:
        print("Error no Submission")
        return False

    if 'Submission Status' not in drug_item:
        print('Error no "Submission Status"')
        return False

    sub_class = drug_item['Submission Classification']
    sub = drug_item['Submission']
    sub_status = drug_item['Submission Status']

    if sub_status.startswith('Tentative'):
        if verbose:
            print('rejected "Tentative Approval"')
        return False
    if sub.startswith('SUPPL'):
        if verbose:
            print('rejected "SUPPL"')
        return False
    if sub_class.startswith('Labeling'):
        if verbose:
            print('rejected "Labeling"')
        return False
    if sub_class.startswith('Manufacturing'):
        if verbose:
            print('rejected "Manufacturing"')
        return False
    if sub_class.startswith('Efficacy'):
        if verbose:
            print('rejected "Efficacy"')
        return False
    if sub_class.startswith('REMS'):
        if verbose:
            print('rejected "REMS"')
        return False
    # Write check function here
    return True

def get_drug_detail( drug_master_row: dict = {}) -> dict:
    """

    :rtype: object
    """
    if 'ApplID' not in drug_master_row:
        print("ERROR no ApplID passed in")
        return {}

#    print("Fetching drug: ",drug_master_row['ApplID'])
    query_url=FDA_URL+"/scripts/cder/daf/index.cfm?event=overview.process&ApplNo="+drug_master_row['ApplID']
    req = requests.get(query_url)
    if req.status_code != 200:  # Failure
        print("Bad return code: ", req.status_code)
        return []
    soup = BeautifulSoup(req.text,"html5lib")
    drugfam=[]
    for row in soup.find_all('table')[0].find_all('tr', {'class': "prodBoldText"}):
        drug = {}
        cols = row.find_all('td')
        drug['Drug Name2']=cols[0].contents[0]
        drug['Active Ingredients'] = cols[1].contents[0]
        drug['Strength'] = cols[2].contents[0]
        drug['Dosage Fom/Route'] = cols[3].contents[0]
        drug['Marketing Status'] = cols[4].contents[0]
        drug['TE Code'] = cols[5].contents[0].strip()
        drug['RLD'] = cols[6].contents[0]
        drug['RS'] = cols[7].contents[0].strip()
        drug.update(drug_master_row)
        drug['Drug Name'] = drug['Drug Name2']+' '+drug['Strength']
        #print(drug['Marketing Status'])
        if check_detail_criteria(drug):
            drugfam.append(drug)

    return drugfam

def check_detail_criteria(drug: dict,verbose: bool = True) -> bool:
    if "Marketing Status" not in drug:
        print("Error no Marketing Status")
        return False

    if drug["Marketing Status"].startswith("Prescription"):
        return True

    if verbose:
        print ("Rejected: ",drug["Drug Name"],drug["Marketing Status"])

    return False

if __name__ == "__main__":

    months=[7,8,9]
    months_name=['January','February','March','April','May','June','July','August','September','October','November','December']
    year = {}
    total = []
    for month in months:
        print("Processing: ",months_name[month-1])
        year[months_name[month-1]] = get_new_drugs(month,2017)
        total = total+year[months_name[month-1]]

    df = pd.DataFrame(total)
    df.to_csv("drug.csv")

