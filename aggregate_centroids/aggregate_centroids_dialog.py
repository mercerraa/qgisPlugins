# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AggregateCentroidsDialog
                                 A QGIS plugin
 Creates centroids of attribute aggregates
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-05-31
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Andrew Mercer
        email                : https://github.com/mercerraa
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

from qgis.PyQt import uic # type: ignore
from qgis.PyQt import QtWidgets # type: ignore
from qgis.core import ( # type: ignore
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
    QgsVectorLayerSimpleLabeling,
    NULL,
    QgsExpression, 
    QgsExpressionContext, 
    QgsExpressionContextUtils
)
from qgis.PyQt.QtCore import QVariant # type: ignore
from qgis.utils import iface # type: ignore
from PyQt5.QtGui import QFont, QColor

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'aggregate_centroids_dialog_base.ui'))


class AggregateCentroidsDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AggregateCentroidsDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.mlcbLayerSelect.layerChanged.connect(self.layerSelectChange)
        self.layerSelectChange()

        self.bbOKCancel.accepted.connect(self.startMain)

    def layerSelectChange(self):
        """Set the layer to fetch field list from"""
        selectedLayer = self.mlcbLayerSelect.currentLayer()
        if selectedLayer:
            self.fewExpression1.setLayer(selectedLayer)
            self.fewExpression2.setLayer(selectedLayer)

    def startMain(self):
        print("Start")
        layer = self.mlcbLayerSelect.currentLayer()
        featureTotal = layer.featureCount()
        currentCrs = layer.crs()
        centroidLayerName = layer.name() + "_centroids"
        centroidLayer = QgsVectorLayer("Point", centroidLayerName, "memory")
        centroidLayer.setCrs(currentCrs)
        centroidLayerDP = centroidLayer.dataProvider()
        global firstFieldName
        firstFieldName = "Selection"
        global secondFieldName
        secondFieldName = "Of_"+str(featureTotal)+"_features"
        if self.fewExpression2.currentText() != '':
            global thirdFieldName
            thirdFieldName = 'Subsets' # Field only created if second expression used
            centroidLayerDP.addAttributes([QgsField(firstFieldName, QVariant.String), QgsField(secondFieldName, QVariant.Int), QgsField(thirdFieldName, QVariant.Int)])
        else:
            centroidLayerDP.addAttributes([QgsField(firstFieldName, QVariant.String), QgsField(secondFieldName, QVariant.Int)])
        centroidLayer.updateFields()

        # Expression 1
        if self.fewExpression1.isExpression()==True:
            expression1 = self.fewExpression1.expression()
            exp1Field1Value = re.search('\"[\w]*\"',expression1).group()
            selection1 = self.makeSelection(layer, expression1)
            self.makeCentroid(selection1, expression1, centroidLayerDP, firstFieldName, secondFieldName)
            self.expression2(centroidLayerDP, centroidLayer, layer, expression1, selection1, firstFieldName) 
        else:
            exp1Field1Value = self.fewExpression1.currentField()[0]
            exp1FieldIndex = layer.fields().indexOf(exp1Field1Value)
            exp1FieldValues = list(layer.uniqueValues(exp1FieldIndex))
            exp1FieldValues.sort()
            unique1Values = len(exp1FieldValues)
            for i in range(unique1Values):
                if exp1FieldValues[i] == NULL:
                    expression1 = "\"{0}\"  IS  {1} ".format(exp1Field1Value, exp1FieldValues[i])
                else:
                    expression1 = "\"{0}\"  IS  '{1}' ".format(exp1Field1Value, exp1FieldValues[i])
                selection1 = self.makeSelection(layer, expression1)
                self.makeCentroid(selection1, expression1, centroidLayerDP, firstFieldName, secondFieldName)
                self.expression2(centroidLayerDP, centroidLayer, layer, expression1, selection1, firstFieldName) 
                
    def expression2(self, centroidLayerDP, centroidLayer, layer, expression1, selection1, firstFieldName):
        # Expression 2
        if self.fewExpression2.currentText() != '':
            fieldName = "SubCount"
            centroidLayerDP.addAttributes([QgsField(fieldName, QVariant.Int)])
            centroidLayer.updateFields()

            if self.fewExpression2.isExpression()==True:
                expression2 = self.fewExpression2.expression()
                exp2Field1Value = re.search('\"[\w]*\"',expression2).group()
                selection2 = self.makeSelection(layer, expression2, selection1 )
                self.makeCentroid(selection2, expression2, centroidLayerDP, firstFieldName, thirdFieldName)
            else:
                exp2Field1Value = self.fewExpression2.currentField()[0]
                exp2FieldIndex = layer.fields().indexOf(exp2Field1Value)
                exp2FieldValues = list(layer.uniqueValues(exp2FieldIndex))
                exp2FieldValues.sort()
                unique2Values = len(exp2FieldValues)
                for i in range(unique2Values):
                    if exp2FieldValues[i] == NULL:
                        expression2 = "\"{0}\"  IS  {1} ".format(exp2Field1Value, exp2FieldValues[i])
                    else:
                        expression2 = "\"{0}\"  IS  '{1}' ".format(exp2Field1Value, exp2FieldValues[i])
                    selection2 = self.makeSelection(layer, expression2, selection1 )
                    self.makeCentroid(selection2, expression1+' AND '+expression2, centroidLayerDP, firstFieldName, thirdFieldName)
               
        #if makeCheck == 1:
        self.addLayerToMap("Selection", centroidLayer)

    
    def makeSelection(self, layer, expression_str, input_features=None):
        expression = QgsExpression(expression_str)
        context = QgsExpressionContext()
        context.appendScope(QgsExpressionContextUtils.globalScope())
        #fields = layer.fields()
        if input_features is None:
            selection = layer.getFeatures(QgsFeatureRequest().setFilterExpression(expression_str))
        else:
            selection = []
            for feature in input_features:
                context.setFeature(feature) 
                if expression.evaluate(context):
                    selection.append(feature)
        return list(selection)

    def makeCentroid(self, selection, expression, centroidLayerDP, firstFieldName, attributeFieldName):
        geometryList = []
        for member in selection:
            geometryList.append(member.geometry())
        valueCount = len(geometryList)
        attributeList = [expression, valueCount]
        centroidMade = self.addCentroid( geometryList, firstFieldName, attributeFieldName, attributeList, centroidLayerDP)
        return centroidMade

    def addCentroid(self, geometryList, firstFieldName, attributeFieldName, attributeList, centroidLayerDP):
        collected = QgsGeometry.collectGeometry(geometryList)
        if collected.isEmpty():
            iface.messageBar().pushMessage("Error", "No matches found. No centroid can be created.", level=1, duration=3)
            return 0
        centroid = collected.centroid()
        newFeature = QgsFeature()
        newFeature.setGeometry(QgsGeometry.fromPointXY(centroid.asPoint()))
        fields = centroidLayerDP.fields()
        attributes = [None] * len(fields)
        print("First field: {}\n Second field: {}".format(firstFieldName, attributeFieldName))
        attributes[fields.indexFromName(firstFieldName)] = attributeList[0]
        attributes[fields.indexFromName(attributeFieldName)] = attributeList[1]
        print("Attributes: {}".format(attributes))
        newFeature.setAttributes(attributes)
        centroidLayerDP.addFeatures([newFeature])
        centroidLayerDP.updateExtents()
        return 1

    def addLayerToMap(self, labelField, centroidLayer):
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
        layer_settings.fieldName = labelField
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
