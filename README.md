density
=======

Calculate polylines density inside a polygon. ArcGIS toolbox.

This project shows how to make ArcGIS toolbox for specific geoprocessing task, using Python script with Arcpy extensions.
Besides, we can see here how Oracle DB + SDE can be used for geoprocessing calculations.

* seismodensity.sql -- Oracle + SDE SQL function for density calculation.
* seismodensity.py -- arcpy script for toolbox.
This version perform calculations using SQL function from Oracle DB.
* seismodensitynosql.py -- arcpy script for toolbox.
This version calculates density w/o using SQL by using ArcGIS spatial functions on data stored in file GDB.
* seismo.tbx -- ArcGIS toolbox for density calculation.
* tbx.hhp -- project file for compiling CHM help file from HTM file.
* tbxhelp.htm -- HTM help file for toolbox.

Links

* [Configuring+Oracle+Net+Services+to+use+ST_Geometry+SQL+functions](https://www.google.com/search?
q=Configuring+Oracle+Net+Services+to+use+ST_Geometry+SQL+functions)
