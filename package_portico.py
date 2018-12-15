import requests, sys, base64, glob,subprocess
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

endpoint = 'https://api.datacite.org/works/'

files = glob.glob('*.pdf')

for f in files:
    doi_parts = f[0:-4].split('-')
    doi = doi_parts[0] +'/'+doi_parts[1]
    query = endpoint + doi
    response = requests.get(query)
    response = validate_response(response)
    xml = base64.b64decode(response['data']['attributes']['xml'])
    metadata = xmltodict.parse(xml)

    print(metadata)

