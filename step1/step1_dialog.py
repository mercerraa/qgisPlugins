# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StepOneDialog
                                 A QGIS plugin
 Maybe this time Qt5 wont suddenly fail
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-05-24
        git sha              : $Format:%H$
        copyright            : (C) 2024 by me
        email                : mercerraa@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re
import sys

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import (
    QgsVectorLayer,
    QgsGeometry,
    QgsFeatureRequest,
    QgsField,
    QgsFeature,
    QgsPoint,
    QgsPolygon,
    QgsProject,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsFontUtils,
    QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling
)
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface
from PyQt5.QtGui import QFont, QColor

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'step1_dialog_base.ui'))


class StepOneDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(StepOneDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.cmbxSelectVector.layerChanged.connect(self.layerSelectChange)
        self.layerSelectChange()

        self.bbOKCancel.accepted.connect(self.checkQuery)

    def layerSelectChange(self):
        """Set the layer to fetch field list from"""
        selectedLayer = self.cmbxSelectVector.currentLayer()
        if selectedLayer:
            self.fewFilter.setLayer(selectedLayer)

    def checkQuery(self):
        layer = self.cmbxSelectVector.currentLayer()
        featureTotal = layer.featureCount()
        currentCrs = layer.crs()
        centroidLayerName = layer.name() + "_centroids"
        centroidLayer = QgsVectorLayer("Point", centroidLayerName, "memory")
        centroidLayer.setCrs(currentCrs)
        centroidLayerDP = centroidLayer.dataProvider()

        #print("Layer: {0} has {1} objects".format(layer.name(), featureTotal))
        if self.fewFilter.isExpression()==True:
            expression = self.fewFilter.expression()
            #print("Expression: {}".format(expression))
            fieldName = re.search('\"[\w]*\"',expression).group()
            #print("Field name from expression: {}".format(fieldName))
            centroidLayerDP.addAttributes([QgsField(fieldName, QVariant.String), QgsField("count", QVariant.Int), QgsField("percentage", QVariant.Double)])
            centroidLayer.updateFields()
            if self.centroidFromExpression(layer, expression, featureTotal, centroidLayerDP) == 1:
                self.addLayerToMap(fieldName, centroidLayer)
        else:
            fieldName = self.fewFilter.currentField()[0]
            #print("Field name: {}".format(fieldName))
            fieldIndex = layer.fields().indexOf(fieldName)
            fieldValues = list(layer.uniqueValues(fieldIndex))
            fieldValues.sort()
            uniqueValues = len(fieldValues)
            centroidLayerDP.addAttributes([QgsField(fieldName, QVariant.String), QgsField("count", QVariant.Int), QgsField("percentage", QVariant.Double)])
            centroidLayer.updateFields()
            if self.centroidFromUnique(layer, uniqueValues, fieldName, fieldValues, featureTotal, centroidLayerDP) == 1:
                self.addLayerToMap(fieldName, centroidLayer)
 

    def centroidFromUnique(self, layer, uniqueValues, fieldName, fieldValues, featureTotal, centroidLayerDP):
        for i in range(uniqueValues):
            searchTerm = "\"{0}\"  IS  '{1}' ".format(fieldName, fieldValues[i])
            selection = layer.getFeatures(QgsFeatureRequest().setFilterExpression(searchTerm))
            selectionList = []
            geometryList = []
            for member in selection:
                selectionList.append(member)
                geometryList.append(member.geometry())
            valueCount = len(selectionList)
            attributeName = fieldValues[i]
            if self.addCentroid(geometryList, valueCount, featureTotal, attributeName, centroidLayerDP) == 0:
                return 0
        return 1
    
    def centroidFromExpression(self, layer, expression, featureTotal, centroidLayerDP):
        selection = layer.getFeatures(QgsFeatureRequest().setFilterExpression(expression))
        selectionList = []
        geometryList = []
        for member in selection:
            selectionList.append(member)
            geometryList.append(member.geometry())
        valueCount = len(selectionList)
        attributeName = expression
        if self.addCentroid(geometryList, valueCount, featureTotal, attributeName, centroidLayerDP) == 0:
            return 0
        else:
            return 1

    def addCentroid(self, geometryList, valueCount, featureTotal, attributeName, centroidLayerDP):
        collected = QgsGeometry.collectGeometry(geometryList)
        if collected.isEmpty():
            iface.messageBar().pushMessage("Error", "No matches found. No centroid can be created.", level=1, duration=3)
            return 0
        #print("collected: {}\n Truth of isEmpty: {}".format(collected, collected.isEmpty()))
        centroid = collected.centroid()
        newFeature = QgsFeature()
        newFeature.setGeometry(QgsGeometry.fromPointXY(centroid.asPoint()))
        percent = valueCount/featureTotal
        newFeature.setAttributes([attributeName, valueCount, percent])
        centroidLayerDP.addFeatures([newFeature])
        centroidLayerDP.updateExtents()
        return 1
        
    def addLayerToMap(self, fieldName, centroidLayer):
        layer_settings  = QgsPalLayerSettings()
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 10))
        text_format.setSize(10)

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(True)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor("white"))

        text_format.setBuffer(buffer_settings)
        layer_settings.setFormat(text_format)
        layer_settings.fieldName = fieldName
        #layer_settings.placement = 2
        layer_settings.enabled = True
        layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
        centroidLayer.setLabelsEnabled(True)
        centroidLayer.setLabeling(layer_settings)
        centroidLayer.triggerRepaint()
        QgsProject.instance().addMapLayer(centroidLayer)
        iface.setActiveLayer(centroidLayer)
        iface.zoomToActiveLayer()
        iface.messageBar().pushMessage("Done", "Centroid layer created", level=3, duration=3)

