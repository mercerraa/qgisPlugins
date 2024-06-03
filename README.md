# qgisPlugins
 QGIS plugin development

## For Riksantikvarieämbetet - Swedish National Heritage Board

I am developing at least one and possible more plugins for QGIS as part of my work for RAÄ.

As of the 3^rd^ of June 2024 the "Aggregate Centroids" is a functional plugin.

This plugin has three components (widgets): a layer selector and two expression builders.
Select a vector layer and one of the following:

- In the first expression builder select a field. This will return all unique values as centroids with a count of objects as an attribute.
- In the first expression builder set a selection query. This will return a single centroid with an object count as attribute.
- One of the above and then select a field in the second expression builder. This will return centroids for the first selection subsetted by the second selection.

For example, selecting "BuildingType" and then "County" will return a layer of centroids (with object counts) for each building type and each building type in each county.

