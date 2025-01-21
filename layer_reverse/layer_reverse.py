from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis
from qgis.core import QgsProject
from qgis.utils import iface

class LayerReverse:
    def __init__(self, iface):
        self.iface = iface  # Reference to QGIS interface
        self.action = None  # Placeholder for the action (button)
        self.toolbar = None  # Placeholder for the custom toolbar

    def initGui(self):
        # Create a toolbar for the plugin if needed
        self.toolbar = self.iface.addToolBar("Mercer Toolbar")
        self.toolbar.setObjectName("MercerToolbar")
        # Create an action (button)
        self.action = QAction(QIcon(":/plugins/layer_reverse/icon.png"), "Run Script", self.iface.mainWindow())
        self.action.triggered.connect(self.run_script)

        # Add the action (button) to the toolbar
        self.toolbar.addAction(self.action)
        
        # Add the action to the toolbar
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Layer Reverse", self.action)

    def unload(self):
        # Remove the button and menu item when plugin is unloaded
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("&Layer Reverse", self.action)

    def run_script(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        selected = iface.layerTreeView().selectedLayers()
        if len(selected)>0:
            for layer in selected:
                node = root.findLayer(layer.id())
                if node:
                    parent = node.parent()
                    clone = node.clone()
                    parent.insertChildNode(0, clone)
                    parent.removeChildNode(node)
            iface.messageBar().pushMessage("Success", "Layer order reversed", level=Qgis.Success, duration=3)
        else:
            iface.messageBar().pushMessage("Warning", "No layers were highlighted", level=Qgis.Warning, duration=3)