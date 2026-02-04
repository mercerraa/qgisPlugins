import requests
import os
import json
from requests.auth import HTTPBasicAuth
from datetime import  datetime 
from pathlib import Path
from osgeo import gdal # pyright: ignore[reportMissingImports]
from qgis.core import (# pyright: ignore[reportMissingImports]
    QgsLayerTreeLayer,
    Qgis,
    QgsProject,
    QgsDataSourceUri,
    QgsPointXY,
    QgsGeometry,
    QgsRectangle,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem
)
from qgis.utils import iface # pyright: ignore[reportMissingImports]
from qgis.gui import ( # pyright: ignore[reportMissingImports]
    QgsMapToolEmitPoint, 
    QgsRubberBand
)
from qgis.PyQt.QtCore import ( # pyright: ignore[reportMissingImports]
    Qt,
    pyqtSignal,
    QEventLoop
)
from qgis.PyQt.QtWidgets import ( # pyright: ignore[reportMissingImports]
    QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox, QFileDialog, QComboBox
)
#
##################
#
def setInitialPaths():
  '''Set paths for current project'''
  # Define and set names and paths
  #scriptsDir = os.path.dirname(os.path.abspath(__file__))
  projectInstance = QgsProject.instance()
  projectPath = projectInstance.absolutePath()
  # If QGIS not started from project the python path will be users root
  currentDir = os.getcwd()
  if projectPath != currentDir:
    os.chdir(os.path.normpath(projectPath))
    currentDir = os.getcwd()
  userDir = os.path.expanduser('~')
  return userDir, currentDir, projectInstance
#
def messageOut(title, messageText, level=Qgis.Info, duration=3):
    '''Sends message to user via QGIS message bar and to the built in QGIS Python console'''
    iface.messageBar().pushMessage(title, messageText, level, duration)
    print(f'{title}: {messageText}')
#
class LoginDialog(QDialog):
    """Class for creating gui. This uses addresses and login details from a json file, stored in the project folder, or default to empty. The details are then passed on to the main getStac function"""
    def __init__(self, parent=None, logindata=""):
        super().__init__(parent)

        self.setWindowTitle("Choose STAC")
        layout = QVBoxLayout()

        self.urlList = QComboBox()
        self.names = []
        self.urls = []
        self.collections = []
        self.users = []
        self.passwords = []
        for key, data in logindata.items():
            self.urlList.addItem(data['name'])
            self.names.append(data['name'])
            self.urls.append(data['stac_url'])
            self.collections.append(data['collection'])
            self.users.append(data['username'])
            self.passwords.append(data['password'])
        self.urlList.setEditable(True)
        self.urlList.setInsertPolicy(QComboBox.InsertAtBottom)
        self.urlList.currentTextChanged.connect(self.current_text_changed)

        self.stac_url_edit = QLineEdit()
        self.stac_url_edit.setPlaceholderText("STAC URL")
        self.stac_url_edit.setText(self.urls[0])

        self.collection_edit = QLineEdit()
        self.collection_edit.setPlaceholderText("STAC URL")
        self.collection_edit.setText(self.collections[0])

        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("Username")
        self.user_edit.setText(self.users[0])

        self.pass_edit = QLineEdit()
        self.pass_edit.setPlaceholderText("Password")
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setText(self.passwords[0])

        layout.addWidget(QLabel("STAC URL:"))
        layout.addWidget(self.urlList)
        layout.addWidget(self.stac_url_edit)
        layout.addWidget(self.collection_edit)
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.user_edit)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.pass_edit)

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def current_text_changed(self, s):
        """User can select a predefined STAC and login stored in a json file. This function updates the gui"""
        print("Current text: ", s)
        index = self.names.index(s)
        url = self.urls[index]
        collection = self.collections[index]
        user = self.users[index]
        password = self.passwords[index]
        print(f'{url}\n with {user}: {password}')
        self.stac_url_edit.setText(url)
        self.collection_edit.setText(collection)
        self.user_edit.setText(user)
        self.pass_edit.setText(password)

    def get_values(self):
        return self.stac_url_edit.text(), self.collection_edit.text(), self.user_edit.text(), self.pass_edit.text()
#
def getUsePass(STAC_URL="", USERNAME="first.last@mail.org", PASSWORD="password"):
    projectInstance = QgsProject.instance()
    projectPath = projectInstance.absolutePath()
    stacsfile = 'stacs.json'
    stacspath = os.path.join(projectPath, stacsfile)
    try:
        with open(stacspath, encoding='utf-8') as f:
            jsondata = json.load(f)
    except:
        jsondata = {"empty":{
        "name": "",
        "stac_url": "",
        "collection": "",
        "username": "",
        "password": ""
        }}

    dlg = LoginDialog(
    parent=iface.mainWindow(),
    logindata=jsondata
    )
    if dlg.exec():
        stac_url, collection, username, password = dlg.get_values()
        #QMessageBox.information(iface.mainWindow(), "Feedback", "Username/password entered")
    else:
        print("User cancelled")
        stac_url = collection = username = password = None
    return stac_url, collection, username, password
#
class DragRectangle(QgsMapToolEmitPoint):
    rectangleDrawn = pyqtSignal(QgsRectangle)
    #
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.start_point = None
        self.end_point = None
        self.rubber_band = QgsRubberBand(self.canvas, Qgis.GeometryType.Polygon)
        self.rubber_band.setStrokeColor(Qt.red)
        self.rubber_band.setWidth(1)
    #
    def canvasPressEvent(self, e):
        self.start_point = self.toMapCoordinates(e.pos())
    #
    def canvasMoveEvent(self, e):
        if self.start_point:
            end_point = self.toMapCoordinates(e.pos())
            self.rubber_band.reset(Qgis.GeometryType.Polygon)
            p = self.get_rect_points(self.start_point, end_point)
            self.rubber_band.setToGeometry(QgsGeometry.fromPolygonXY(p), None)
    ""
    def canvasReleaseEvent(self, e):
        self.end_point = self.toMapCoordinates(e.pos())
        rect = QgsRectangle(self.start_point, self.end_point)

        # Transform to WGS84
        crs_src = self.canvas.mapSettings().destinationCrs()
        crs_wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
        transform = QgsCoordinateTransform(crs_src, crs_wgs84, QgsProject.instance())
        rect_wgs84 = transform.transformBoundingBox(rect)

        # Emit signal
        self.rectangleDrawn.emit(rect_wgs84)

        # Reset and deactivate
        self.rubber_band.reset(Qgis.GeometryType.Polygon)
        iface.mapCanvas().unsetMapTool(self)

    def get_rect_points(self, startPoint, endPoint):
        return [[
            QgsPointXY(startPoint.x(), startPoint.y()),
            QgsPointXY(endPoint.x(), startPoint.y()),
            QgsPointXY(endPoint.x(), endPoint.y()),
            QgsPointXY(startPoint.x(), endPoint.y())
        ]]
#
def draw_rectangle():
    """
    Lets the user draw a rectangle on the QGIS canvas.
    Waits until drawing is complete, then returns the rectangle in WGS84 (EPSG:4326).
    """
    canvas = iface.mapCanvas()
    tool = DragRectangle(canvas)
    loop = QEventLoop()
    result = {}
    #
    def handle_rectangle(rect):
        result['rect'] = rect
        loop.quit()  # stop waiting
    #
    tool.rectangleDrawn.connect(handle_rectangle)
    canvas.setMapTool(tool)
    messageOut('Get STAC data:', "Draw a rectangle on the map")
    # Wait for the user to finish drawing
    loop.exec_()
    # Return WGS84 rectangle
    return result['rect']
#
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
#
def getFolder(startpath=""):
    folder = QFileDialog.getExistingDirectory(
    None,
    "Select a folder",
    startpath,
    QFileDialog.ShowDirsOnly
    )

    if folder:
        print("Selected folder:", folder)
        return folder
    else:
        return None
#
def getSTAC():
    """"""
    userDir, currentDir, projectInstance = setInitialPaths()
    STAC_URL, COLLECTION, USERNAME, PASSWORD = getUsePass()
    if STAC_URL == None:
        return

    rect = draw_rectangle()
    bbox = [rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()]  # min lon, min lat, max lon, max lat
    print(f'{bbox}')

    urladdress = STAC_URL
    conformance_url = f"{urladdress}/conformance"
    resp = requests.get(conformance_url)
    resp.raise_for_status()
    conformance = resp.json()
    itemSearch = False
    if "https://api.stacspec.org/v1.0.0/item-search" in conformance['conformsTo']:
        itemSearch = True
        print('Item search found')

    collections_url = f"{urladdress}/collections"
    print(collections_url)
    resp = requests.get(collections_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    resp.raise_for_status()
    collections = resp.json()
    print(json.dumps(collections, indent=4))

    search_url = f"{STAC_URL}/search"
    search_results = stac_search(search_url, auth=HTTPBasicAuth(USERNAME, PASSWORD), bbox=bbox, collection=COLLECTION)
    print(json.dumps(search_results, indent=4))

    projectPath = projectInstance.absolutePath()
    os.chdir(os.path.normpath(projectPath))
    inPath = getFolder(projectPath)
    if inPath == None:
        todaydt = datetime.now()
        dateStr = todaydt.strftime("%Y%m%d_%H%M%S")
        initPath = os.path.join(projectPath, 'STAC', dateStr)
        inPath = os.path.normpath(initPath)
        os.mkdir(inPath)
        if not os.path.isdir(inPath):
            os.mkdir(inPath)
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
    
def downloadFiles():
    """"""
    userDir, currentDir, projectInstance = setInitialPaths()
    todaydt = datetime.now()
    dateStr = todaydt.strftime("%Y%m%d_%H%M%S")

    rect = draw_rectangle()
    bbox = [rect.xMinimum(), rect.yMinimum(), rect.xMaximum(), rect.yMaximum()]  # min lon, min lat, max lon, max lat
    print(f'{bbox}')
    # Lantmäteriet credentials
    #thisdir = os.path.dirname(os.path.abspath(__file__))
    STAC_URL, USERNAME, PASSWORD = getUsePass()
    print(f'Obtain from {STAC_URL} using credentials for {USERNAME}')
    if STAC_URL == None:
        return
    todaydt = datetime.now()
    dateStr = todaydt.strftime("%Y%m%d_%H%M%S")

    collections_url = f"{STAC_URL}/collections"
    try:
        resp = requests.get(collections_url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    except:
        return
    resp.raise_for_status()
    collections = resp.json()

    search_url = f"{STAC_URL}/search"
    query = {
        "bbox": bbox,
        "limit": 5,
        # optionally add: "collections": ["nh_dtm_1"]
    }

    resp = requests.post(search_url, json=query, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    resp.raise_for_status()
    search_results = resp.json()

    projectPath = projectInstance.absolutePath()
    # currentDir = os.getcwd()
    # if projectPath != currentDir:
    #     os.chdir(os.path.normpath(projectPath))
    
    # Download directory
    homeDir = Path.home()
    todaydt = datetime.now()
    dateStr = todaydt.strftime("%Y%m%d")
    #dateStr = todaydt.strftime("%Y%m%d_%H%M%S")
    # initPath = os.path.join(homeDir, 'InData', 'DEM', dateStr)
    # inPath = os.path.normpath(initPath)
    # if not os.path.isdir(inPath):
    #     os.mkdir(inPath)

    inPath = getFolder(projectPath)

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
        messageOut('Update',f'DEMs downloaded to {inPath}')

    return #inPath

getSTAC()