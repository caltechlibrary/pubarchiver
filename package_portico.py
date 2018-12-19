import requests, sys, base64, glob, subprocess, datetime, os, shutil
import xmltodict

def validate_response(response):
    if (response.status_code != 200):
        print(str(response.status_code) + " " + response.text)
        exit()
    else:
        return response.json()

def trace_url(url):
    get = requests.get(url)
    return get.url

endpoint = 'https://api.datacite.org/dois/'

files = glob.glob('*.pdf')
if os.path.isdir('data') == True:
    print("Please remvove the old data directory")
    exit()        
os.mkdir('data')
os.chdir('data')

issn = '2578-9430'

for f in files:
    doi_parts = f[0:-4].split('-')
    prefix = doi_parts[0]
    identifier = doi_parts[1]
    doi = prefix +'/'+ identifier
    query = endpoint + doi
    response = requests.get(query)
    response = validate_response(response)
    date = response['data']['attributes']['registered']
    xml = base64.b64decode(response['data']['attributes']['xml'])
    mfile = xmltodict.parse(xml)

    os.mkdir(identifier)    
    os.chdir(identifier)
    os.rename('../../'+f,identifier+'.pdf')
    
    volume = int(mfile['resource']['publicationYear'])-2014
    mfile['resource']['dates']['date']['#text'] = date
    mfile['resource']['volume'] = volume
    mfile['resource']['journal'] = mfile['resource'].pop('publisher')
    mfile['resource']['e-issn'] = issn
    mfile['resource']['file'] = identifier+'.pdf'
    mfile['resource']["rightsList"] = [{
            "rights": "Creative Commons Attribution 4.0",
            "rightsURI": "https://creativecommons.org/licenses/by/4.0/legalcode"}] 
    mfile['resource'].pop('@xmlns')
    mfile['resource'].pop('@xsi:schemaLocation')
    outname = identifier+'.xml'
    outstring = xmltodict.unparse(mfile)
    with open(outname,'w',encoding='utf8') as outfile:
        outfile.write(outstring)
    
    os.chdir('..')

    
datestamp = datetime.date.today().isoformat()

os.chdir('..')

shutil.make_archive(issn+'_'+datestamp, 'zip','data')
