# qgisPlugins
 QGIS plugin development

## For Riksantikvarieämbetet - Swedish National Heritage Board

I am developing at least one and possible more plugins for QGIS as part of my work for RAÄ.

## 03.06.2024
As of the 3<sup>rd</sup> of June 2024 the "Aggregate Centroids" is a functional plugin.

This plugin has three components (widgets): a layer selector and two expression builders.
Select a vector layer and one of the following:

- In the first expression builder select a field. This will return all unique values as centroids with a count of objects as an attribute.
- In the first expression builder set a selection query. This will return a single centroid with an object count as attribute.
- One of the above and then select a field in the second expression builder. This will return centroids for the first selection subsetted by the second selection.

For example, selecting "BuildingType" and then "County" will return a layer of centroids (with object counts) for each building type and each building type in each county.

## 14.06.2024

Aggregate Centroids is now a finished product.
Select field names using dropdowns in either the first or both of the expression fields and/or write expressions.
An expression can be written using the built in QGIS Expression Builder, for example ```"FieldName" ilike '%searchTerm%'```will search for all text strings in the field named FieldName that contain (case insensitive) searchterm.