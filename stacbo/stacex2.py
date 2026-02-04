import requests
import os
import json
from requests.auth import HTTPBasicAuth
from qgis.core import (# pyright: ignore[reportMissingImports]
    QgsProject
)

stacDict = [
{"STAC_URL": "https://api.lantmateriet.se/stac-hojd/v1", "COLLECTION": '', "USERNAME": "andrew.mercer@raa.se", "PASSWORD": "!WqhT8wkYM8AhAS"},
{"STAC_URL": "https://api.lantmateriet.se/stac-vektor/v1", "COLLECTION": 'kommun-lan-rike', "USERNAME": "andrew.mercer@raa.se", "PASSWORD": "!WqhT8wkYM8AhAS"},
{"STAC_URL": "https://landsatlook.usgs.gov/stac-server", "COLLECTION": 'landsat-c2ard-sr', "USERNAME": "", "PASSWORD": ""},
]

index = 1
STAC_URL = stacDict[index]['STAC_URL']
USERNAME = stacDict[index]['USERNAME']
PASSWORD = stacDict[index]['PASSWORD']
COLLECTION = stacDict[index]['COLLECTION']

bbox = [17.6, 60.05, 17.65, 60.10]

urladdress = STAC_URL
conformance_url = f"{urladdress}/conformance"
resp = requests.get(conformance_url)
resp.raise_for_status()
conformance = resp.json()
itemSearch = False
if "https://api.stacspec.org/v1.0.0/item-search" in conformance['conformsTo']:
    itemSearch = True

###
def stac_search(search_url, auth, bbox, collection=None):
    base_query = {
        "bbox": bbox,
        "limit": 5
    }

    # Attempt WITHOUT collections
    resp = requests.post(search_url, json=base_query, auth=auth)

    if resp.status_code < 400:
        return resp.json()

    # Retry WITH collections if provided
    if collection:
        base_query["collections"] = [collection]
        resp = requests.post(search_url, json=base_query, auth=auth)
        resp.raise_for_status()
        return resp.json()

    resp.raise_for_status()
###

collections_url = f"{urladdress}/collections"
print(collections_url)
resp = requests.get(collections_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
resp.raise_for_status()
collections = resp.json()
print(json.dumps(collections, indent=4))

search_url = f"{STAC_URL}/search"
search_results = stac_search(search_url, auth=HTTPBasicAuth(USERNAME, PASSWORD), bbox=bbox, collection=COLLECTION)
print(json.dumps(search_results, indent=4))

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
            if r.reason == 'Forbidden':
                print('Access forbidden')
            r.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
print(f'Files downloaded to {inPath}')
