# Coding: utf-8

"""`main` is the top level module for your Flask application."""

# Import request and BS4

import requests
from bs4 import BeautifulSoup
import json
import pickle

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
    print( req.status_code)
    soup = BeautifulSoup(req.text,"html5lib")
    count = 0
    trs =  soup.find_all('table')[0].find_all('tr')
    for tr in trs:
        dm = {}
        cols = tr.find_all('td')
        if len(cols)==0:
            print("no cols returned:")
            continue
        dm['Approval Date'] = cols[0].contents[0]
        dm['ApplID'] = cols[1].find_all('a')[0].get('href').split('=')[2]
        dm['Submission'] = cols[2].contents[0]
        dm['ActiveIngredient']= cols[3].contents[0]
        dm['Company'] = cols[4].contents[0]
        if len(cols[5].contents) != 0:
            dm['Submission Classification'] = cols[5].contents[0]
        dm['Submission Status'] = cols[6].contents[0]
        dm['Details'] = get_drug_detail(dm['ApplID'])
        drugs.append(dm)
    return drugs

# 208535, 202674 Test cases
def get_drug_detail(applno=""):

    if applno == "":
        print("ERROR no applno")
        return []

    print("Fetching drug: ",applno)
    query_url=FDA_URL+"/scripts/cder/daf/index.cfm?event=overview.process&ApplNo="+applno
    req = requests.get(query_url)
    if req.status_code != 200:  # Failure
        print("Bad return code: ", req.status_code)
        return []
    soup = BeautifulSoup(req.text,"html5lib")
    drugfam=[]
    for row in soup.find_all('table')[0].find_all('tr', {'class': "prodBoldText"}):
        drug = {}
        cols = row.find_all('td')
        drug['Drug Name ']=cols[0].contents[0]
        drug['Active Ingredients'] = cols[1].contents[0]
        drug['Strength'] = cols[2].contents[0]
        drug['Dosage Fom/Route'] = cols[3].contents[0]
        drug['Marketing Status'] = cols[4].contents[0]
        drug['TE Code'] = cols[5].contents[0].strip()
        drug['RLD'] = cols[6].contents[0]
        drug['RS'] = cols[7].contents[0].strip()
        drugfam.append(drug)
    return drugfam


months=[1,2,3,4,5,6,7]
months_name=['January','February','March','April','May','June','July']
year = {}
for month in months:
    print("Processing: ",months_name[month-1])
    year[months_name[month-1]] = get_new_drugs(month,2017)

   with open(months_name[month-1]+"drug.dump","w") as text_file:
       print(year[months_name[month-1]], file=text_file)

   with open(months_name[month-1]+"drug.json","w") as json_file:
       print(json.dumps(year[months_name[month-1]]), file=json_file)
