#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-
# (c) Valik mailto:vasnake@gmail.com

'''
ArcGIS Toolbox tool script for Seismodensity project

Input: GPFeatureRecordSetLayer
	inputPolygon

Output: double default -1.0
	seismoDens km/km2
	profilesLength km
	shapeArea km2

Constants (string #95 and below)
	logFilename - file for log records
	toolDirPath - folder with gdb & other files
	oraSdeFName - oracle sde connection file
	oraFuncName - oracle stored function for seismodensity calc

Before invoking tool you must prepare valid polygon without holes.
That means no inner rings, no self intersections, clockwise draw direction.
For example, using simplify tool should be good (http://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/simplify).


Input examples (http://resources.arcgis.com/en/help/rest/apiref/gpsubmit.html)

wrong geometry - inner ring
inputPolygon={
"geometryType" : "esriGeometryPolygon",
"spatialReference" : {"wkid" : 4326},
"fields": [ {
	"name": "Name",
	"type": "esriFieldTypeString",
	"alias": "Name"
} ],
"features"  : [{
	"geometry" : {
		"rings" : [[ [-97.06326,32.759], [-97.06298,32.755], [-97.06153,32.749], [-97.06326,32.759] ]],
		"spatialReference" : {"wkid" : 4326}
	},
	"attributes" : {"Name" : "Feature 1"}
}]}

good geometry
inputPolygon={
"geometryType":"esriGeometryPolygon",
"spatialReference":{"wkid":102100},
"features":[{
	"geometry":{
		"spatialReference":{"wkid":102100},
		"rings":[[[7592337.47835702,9803507.48815798],[7924991.42545401,10312272.348424],[8277213.25179201,9979618.40132698],[7592337.47835702,9803507.48815798]]]
	},
	"attributes":{}
}]}

clockwise
http://cache.algis.com/ArcGIS/rest/services/five/seismodens/GPServer/seismoprofiles%20density/submitJob?inputPolygon=%7b%22geometryType%22%3a%22esriGeometryPolygon%22%2c%22spatialReference%22%3a%7b%22wkid%22%3a102100%7d%2c%22features%22%3a%5b%7b%22geometry%22%3a%7b%22spatialReference%22%3a%7b%22wkid%22%3a102100%7d%2c%22rings%22%3a%5b%5b%5b7064004.61385001%2c10781901.450208%5d%2c%5b7494497.95715201%2c11036283.880341%5d%2c%5b7533633.71563401%2c10625358.41628%5d%2c%5b7064004.61385001%2c10781901.450208%5d%5d%5d%7d%2c%22attributes%22%3a%7b%7d%7d%5d%7d

counterclockwise
http://cache.algis.com/ArcGIS/rest/services/five/seismodens/GPServer/seismoprofiles%20density/submitJob?inputPolygon=%7b%22geometryType%22%3a%22esriGeometryPolygon%22%2c%22spatialReference%22%3a%7b%22wkid%22%3a102100%7d%2c%22features%22%3a%5b%7b%22geometry%22%3a%7b%22spatialReference%22%3a%7b%22wkid%22%3a102100%7d%2c%22rings%22%3a%5b%5b%5b9216471.45536%2c11505912.982125%5d%2c%5b9040360.542191%2c11114555.397305%5d%2c%5b9392582.368529%2c11192826.914269%5d%2c%5b9216471.45536%2c11505912.982125%5d%5d%5d%7d%2c%22attributes%22%3a%7b%7d%7d%5d%7d


simplify example
http://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/simplify?sr=102100&geometries=%7B%0D%0A%09%22geometryType%22%3A%22esriGeometryPolygon%22%2C%0D%0A%09%22geometries%22%3A%5B%7B%0D%0A%09%09%22rings%22%3A%5B%5B%0D%0A%09%09%09%5B7827152.02924901%2C9666532.33347098%5D%2C%0D%0A%09%09%09%5B8316349.01027401%2C10057889.918291%5D%2C%0D%0A%09%09%09%5B7729312.63304402%2C10214432.952219%5D%2C%0D%0A%09%09%09%5B7827152.02924901%2C9666532.33347098%5D%5D%5D%0D%0A%09%7D%5D%0D%0A%7D&f=HTML
sr:102100
geometries:{
	"geometryType":"esriGeometryPolygon",
	"geometries":[{
		"rings":[[
			[7827152.02924901,9666532.33347098],
			[8316349.01027401,10057889.918291],
			[7729312.63304402,10214432.952219],
			[7827152.02924901,9666532.33347098]]]
	}]
}

If wkid is 102100 we should try 3857 instead

docs
http://help.arcgis.com/en/arcgisserver/10.0/help/arcgis_server_dotnet_help/index.html#/An_overview_of_geoprocessing_with_ArcGIS_Server/009300000028000000/
http://resources.arcgis.com/gallery/file/geoprocessing/details?entryID=E659B67B-1422-2418-A0FE-4F1642052299

Doctests
>>> testGlobal()
testGlobal [one]...:
testGlobal [two]...:

'''


import time, traceback
import sys, string, os
import logging

# global constants
logFilename = r'''\\cache\MXD\seismo\seismodensity.geoproc.log'''
toolDirPath = r'''\\cache\MXD\seismo'''
oraSdeFName = r'''oratoarc10.algis.sde'''
oraFuncName = r'''algis.calc_seismodensity'''

cp = 'utf-8'
log = logging.getLogger('seismodens') # http://docs.python.org/library/logging.html

def ts():
	return time.strftime('%Y-%m-%d %H:%M:%S')


def setLogger(log):
	''' http://docs.python.org/howto/logging-cookbook.html
	logrotate
	http://stackoverflow.com/questions/8467978/python-want-logging-with-log-rotation-and-compression
	http://docs.python.org/library/logging.handlers.html#rotatingfilehandler
	'''
	log.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	if not hasattr(log, 'vFHandle'):
		import logging.handlers as handlers
		# 5 files up to 1 megabyte each
		fh = handlers.RotatingFileHandler(logFilename, maxBytes=1000000, backupCount=5, encoding='utf-8')
		#~ fh = handlers.TimedRotatingFileHandler(logFilename, backupCount=3, when='M', interval=3, encoding='utf-8',)
		#~ fh = logging.FileHandler(logFilename)
		#~ fh = logging.NullHandler()
		fh.setLevel(logging.DEBUG)
		fh.setFormatter(formatter)
		log.addHandler(fh)
		log.vFHandle = fh
	print 'Log configured. Look file [%s] for messages' % logFilename
#def setLogger(log):


def arcpyStuff():
	''' Geoprocessor main program.
	In/out parameters
	fsetObj = arcpy.GetParameter(0) # featureset
	arcpy.SetParameterAsText(1, x) # Seismodensity double, km/km2
	arcpy.SetParameterAsText(2, y) # SeismorofilesLength double, km
	arcpy.SetParameterAsText(3, z) # ShapeArea double, km2

	Input polygon will be transformed into WGS84, coords will be extracted into WKT string.
	Oracle stored function will be invoked with WKT coords and WGS84 SR WKID as parameters.
	Function output will be parsed and returned from GP tool.

	We have problems with invalid geometry - interior rings (counterclockwise draw direction).
	If you draw polygon counterclockwise and send that to script, you get zeropart polygon.
	In that case you should use Geometry.Simplify geoservice http://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/simplify.
	Extra info:
	http://gis.stackexchange.com/questions/10201/arcpy-geometry-geo-interface-and-asshape-function-loss-of-precision-and-h/21627
	http://gis.stackexchange.com/questions/27255/how-to-identify-feature-vertices-that-are-part-of-a-donut-hole-in-arcgis-10
	http://gisintelligence.wordpress.com/2011/06/30/repair-geometry-is-critical/
	'''

	from arcpy import env
	arcpy.AddMessage("%s seismodensitysql processing started" % ts())

	# WGS84 spatialReference
	WKID = 4326 # WGS-1984 http://anothergisblog.blogspot.com/2011/05/spatial-reference-class.html
	sr = arcpy.SpatialReference()
	sr.factoryCode = WKID
	sr.create()
	env.outputCoordinateSystem = sr

# input
	fsetTxt = arcpy.GetParameterAsText(0) # Feature Set
	log.info("arcpyStuff, input polygons text '%s'" % fsetTxt)
	fsetObj = arcpy.GetParameter(0)
	log.info("arcpyStuff, input polygons obj '%s'" % (fsetObj)) # geoprocessing record set object (FeatureSet)

# parse input
	# don't work anyway, may be cutted off freely
	fsetDesc = arcpy.Describe(fsetObj)
	if hasattr(fsetDesc, 'ShapeFieldName'): log.info("arcpyStuff, input fset ShapeFieldName '%s'" % fsetDesc.ShapeFieldName)  # haven't
	else: log.info("arcpyStuff, input fset ShapeFieldName are not accessible")
	if hasattr(fsetDesc, 'spatialReference'): log.info("arcpyStuff, input fset spatialReference '%s'" % fsetDesc.spatialReference) # haven't
	else: log.info("arcpyStuff, input fset spatialReference are not accessible")

	# search cursor
	geomWkt = '' # (70 70, 71 72, 85 65, 70 70), (...)
	workSR = sr # decimal degree good for Oracle
	rows = arcpy.SearchCursor(fsetObj, '', workSR)

	for row in rows: # for each polygon
		geom = row.shape
		# debug output
		arcpy.AddMessage("%s arcpyStuff, input geom '%s'" % (ts(), geom.__geo_interface__))
		log.info("arcpyStuff searchcursor, geometry type '%s', area '%s', parts '%s'" % (geom.type, geom.area, geom.partCount)) # geometry type 'polygon', area '-218254081896.0', parts '0'
		log.info("arcpyStuff searchcursor, geometry geojson '%s'" % (geom.__geo_interface__)) # {'type': 'Polygon', 'coordinates': []}
		if hasattr(geom, 'spatialReference'): log.info("arcpyStuff searchcursor, geometry spatialReference '%s'" % (geom.spatialReference)) # haven't
		else: log.info("arcpyStuff searchcursor, geometry spatialReference are not accessible")

		# todo: gemetry.simplify on server
		# http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Repair_Geometry/00170000003v000000/
		# http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//007000000011000000
		if geom.partCount <= 0 or geom.area <=0:
			raise NameError("Wrong input polygon, you should send no selfintersected clockwise drawed single ring")

		for part in geom:
			log.info("arcpyStuff searchcursor, geometry part, len '%s'" % (len(part)))
			partWkt = ''
			for pnt in part:
				pntWkt = '%.15f %.15f' % (pnt.X, pnt.Y) # decimal degree precision
				if partWkt == '':
					partWkt = pntWkt
				else:
					partWkt = '%s, %s' % (partWkt, pntWkt)
			partWkt = '(%s)' % partWkt

			if geomWkt == '':
				geomWkt = '%s' % partWkt
			else:
				geomWkt = '%s, %s' % (geomWkt, partWkt)

		break # only one polygon we need
	# end for each polygon

	log.info("arcpyStuff, input SR WKID '%s', geom WKT '%s'" % (workSR.factoryCode, geomWkt))
	arcpy.AddMessage("%s input parsed" % ts())

# send query to Oracle http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/ArcSDESQLExecute/000v00000057000000/
	sql = r'''select %s('%s', %s) as calcres from DUAL''' % (oraFuncName, geomWkt, workSR.factoryCode)
	#~ sql = r'''select sr_name, srid, cs_id from sde.st_spatial_references where cs_id in (3857, 102100, 4326)'''

	sdeConn = arcpy.ArcSDESQLExecute(os.path.join(toolDirPath, oraSdeFName)) # \\cache\MXD\seismo\oratoarc10.algis.sde
	log.info("arcpyStuff, sql [%s]" % (sql))
	sdeReturn = sdeConn.execute(sql)
	log.info("arcpyStuff, ora result '%s', resType '%s'" % (sdeReturn, type(sdeReturn).__name__)) # ora result '    .068,       7154.117,     104761.243', resType 'unicode'
	arcpy.AddMessage("%s ora query executed" % ts())

	# check the result, expecting string
	if isinstance(sdeReturn, str) or type(sdeReturn) == unicode:
		log.info("arcpyStuff, ora return string '%s'" % (sdeReturn.strip()))
	elif isinstance(sdeReturn, list):
		log.info("arcpyStuff, ora return %s rows" % (len(sdeReturn)))
		for row in sdeReturn:
			log.info("arcpyStuff, row '%s'" % (row))
		raise NameError("Oracle return array instead of string")
	else:
		if sdeReturn == True: # DDL?
			log.info("arcpyStuff, sql statement ran successfully")
		else:
			log.info("arcpyStuff, error, sql statement FAILED")
		raise NameError("Oracle return nor array nor string")

# output
	resData = sdeReturn.split(',')
	resArr = []
	for item in resData:
		resArr.append('%.3f' % float(item))

	arcpy.SetParameterAsText(1, resArr[0]) # Seismodensity double
	arcpy.SetParameterAsText(2, resArr[1]) # SeismorofilesLength double
	arcpy.SetParameterAsText(3, resArr[2]) # ShapeArea double

	arcpy.AddMessage("%s processing done" % ts()) # http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Writing_messages_in_script_tools/00150000000p000000/
#def arcpyStuff():


def main(note=''):
	argc = len(sys.argv)
	argv = sys.argv
	print >> sys.stderr, 'argc: [%s], argv: [%s]' % (argc, argv)

	# log setup
	setLogger(log)
	log.info('start, argv: %s, note "%s"' % (argv, note))

	import arcpy
	try:
		# geoprocessor tool script
		arcpyStuff()
	except Exception, e:
		arcpy.AddError('Toolbox had failed try')
		arcpy.AddError(e)
		if type(e).__name__ == 'COMError':
			log.error('main, COM error, msg [%s]' % e)
		else:
			log.exception('main, error, program failed')
			raise
	finally:
		log.info('End Of Program, logging shutdown')
		logging.shutdown()
#def main():


def doDocTest():
	''' http://docs.python.org/library/doctest.html
	'''
	import doctest
	doctest.testmod(verbose=True)
#def doDocTest():


def deploy():
	repfile = r'''c:\d\code\git\oracle\seismodens\python.oracle\seismodensity.py'''
	target = r'''\\cache\MXD\seismo\seismodensity.py'''
	locfile = sys.argv[0]
	if locfile == repfile and os.path.exists(target):
		print 'copy'
		import shutil
		shutil.copyfile(repfile, target)
	else: print 'no deploy today'
#def deploy():


if __name__ == "__main__":
	# function tests
	# doDocTest()

	# development environment only, copy source code to ArcGIS server
	deploy()

	import time, traceback
	print time.strftime('%Y-%m-%d %H:%M:%S')

	try:
		# run program
		main()
		print u'Если это видно, сбоев нет'.encode(cp)
	except Exception, e:
		if type(e).__name__ == 'COMError':
			print 'COM error, msg [%s]' % e
		else:
			print 'Error, program failed:'
			traceback.print_exc(file=sys.stderr)

	print time.strftime('%Y-%m-%d %H:%M:%S')
# end main

################################################################################

# bag, attic, dumpster

aLittleGlobVar = "one"
def testGlobal():
	global aLittleGlobVar
	print 'testGlobal [%s]...:' % aLittleGlobVar
	if aLittleGlobVar == 'one':
		aLittleGlobVar = 'two'
	print 'testGlobal [%s]...:' % aLittleGlobVar
#def testGlobal():


def listcopy(fsetObj):
	''' list coords example: featureset.save to featureclass
	'''
	fc = arcpy.CreateFeatureclass_management("in_memory", "temppolygon") #, "POLYGON")
	fsetObj.save(fc)
	g = arcpy.Geometry()
	geometryList = arcpy.CopyFeatures_management(fc, g)
	for geom in geometryList:
		log.info("arcpyStuff fccopy, geometry type '%s', area '%s', parts '%s'" % (
			geom.type, geom.area, geom.partCount)) # geometry type 'polygon', area '198726085061.0', parts '1'
		for points in geom:
			for pnt in points:
				log.info("arcpyStuff fccopy, point x '%s', y '%s'" % (pnt.X, pnt.Y))
		#~ log.info("arcpyStuff fccopy, geometry spatialReference '%s'" % (geom.spatialReference)) # haven't
#def listcopy()
