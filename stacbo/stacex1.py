import requests
import os
import json
from requests.auth import HTTPBasicAuth
from qgis.core import (# pyright: ignore[reportMissingImports]
    QgsProject
)

def pretty_print_POST(req):
    """
    At this point it is completely built and ready
    to be fired; it is "prepared".

    However pay attention at the formatting used in 
    this function because it is programmed to be pretty 
    printed and may differ from the actual request.
    """
    print('{}\n{}\r\n{}\r\n\r\n{}'.format(
        '-----------START-----------',
        req.method + ' ' + req.url,
        '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body,
    ))


stacDict = [
{"STAC_URL": "https://api.lantmateriet.se/stac-hojd/v1", "COLLECTION": '', "USERNAME": "HIDDEN", "PASSWORD": "HIDDEN"},
{"STAC_URL": "https://api.lantmateriet.se/stac-vektor/v1", "COLLECTION": 'kommun-lan-rike', "USERNAME": "HIDDEN", "PASSWORD": "HIDDEN"},
{"STAC_URL": "https://landsatlook.usgs.gov/stac-server", "COLLECTION": 'landsat-c2ard-sr', "USERNAME": "", "PASSWORD": ""},
]

index = 2
STAC_URL = stacDict[index]['STAC_URL']
USERNAME = stacDict[index]['USERNAME']
PASSWORD = stacDict[index]['PASSWORD']
COLLECTION = stacDict[index]['COLLECTION']

bbox = [17.6, 60.05, 17.65, 60.10]

urladdress = STAC_URL.split('/collections')[0]
if len(STAC_URL.split('/collections')) > 1:
    urlcollection = STAC_URL.split('/collections')[1]
else:
    urlcollection = ""
collections_url = f"{urladdress}/collections"

print(collections_url)
try:
    resp = requests.get(collections_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    resp.raise_for_status()
    collections = resp.json()

    search_url = f"{STAC_URL}/search"
    query = {
        "bbox": bbox,
        "limit": 5,
        "collections": [COLLECTION]
    }

    req = requests.Request('POST',search_url, json=query, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    prepared = req.prepare()
    pretty_print_POST(prepared)
    s = requests.Session()
    resp = s.send(prepared)

    # resp = requests.post(search_url, json=query, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    # resp.raise_for_status()

    search_results = resp.json()
    #print(f'search url =\n {search_url}')
    #json_formatted_str2 = json.dumps(search_results, indent=4)
    #print(json_formatted_str2)

    projectInstance = QgsProject.instance()
    projectPath = projectInstance.absolutePath()
    os.chdir(os.path.normpath(projectPath))
    inPath = projectPath
    for item in search_results.get("features", []):
        item_id = item["id"]
        print(f"\nItem: {item_id}")
        for asset_key, asset in item["assets"].items():
            url = asset["href"]
            print(f"  - {asset_key}: {url}")
            local_path = os.path.join(inPath, os.path.basename(url))
            print(f"    Downloading to {local_path}...")
            with requests.get(url, stream=True, auth=HTTPBasicAuth(USERNAME, PASSWORD)) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            print(f'Files downloaded to {inPath}')
except:
    print(f'{collections_url} failed')