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
	gdbFName - gdb which contains seismoprofiles
	seisFCName - seismoprofiles FeatureClass

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
gdbFName = r'''Seis_button.gdb'''
seisFCName = r'''APP_GP_SEISM2D_L'''

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

	Get spatialReference from seismoprofiles GDB FeatureClass;
	GP.Clip seismoprofiles by input polygon into temp FeatureClass;
	Sum length of clipped seismoprofiles;
	Get input polygon area;
	Calc seismodensity.

	We have problems with invalid geometry - interior rings (counterclockwise draw direction).
	If you draw polygon counterclockwise and send that to script, you get zeropart polygon.
	In that case you should use Geometry.Simplify geoservice http://tasks.arcgisonline.com/ArcGIS/rest/services/Geometry/GeometryServer/simplify.
	Extra info:
	http://gis.stackexchange.com/questions/10201/arcpy-geometry-geo-interface-and-asshape-function-loss-of-precision-and-h/21627
	http://gis.stackexchange.com/questions/27255/how-to-identify-feature-vertices-that-are-part-of-a-donut-hole-in-arcgis-10
	http://gisintelligence.wordpress.com/2011/06/30/repair-geometry-is-critical/
	'''

	from arcpy import env
	arcpy.AddMessage("%s seismodensitynosql processing started" % ts())

# spatialReference
	seisDesc = arcpy.Describe(os.path.join(toolDirPath, gdbFName, seisFCName))
	log.info("arcpyStuff, seismoprofiles WKID '%s'" % (seisDesc.spatialReference.factoryCode))
	workSR = seisDesc.spatialReference # seismoprofiles meters good for clip
	env.outputCoordinateSystem = workSR

# input
	fsetTxt = arcpy.GetParameterAsText(0) # Feature Set
	log.info("arcpyStuff, input polygons text '%s'" % fsetTxt)
	fsetObj = arcpy.GetParameter(0)
	log.info("arcpyStuff, input polygons obj '%s'" % (fsetObj)) # geoprocessing record set object (FeatureSet)

	# unique FC name
	# FAQ: What characters should not be used in ArcGIS for field names and table names?
	# http://support.esri.com/index.cfm?fa=knowledgebase.techarticles.articleShow&d=23087
	# "Eliminate anything that is not an alphanumeric character or an underscore. Do not start field or table names with an underscore or a number. Also, it is necessary to edit the field names in delimited text files to remove unsupported characters before using them."
	#~ import uuid
	#~ gid = ('%r' % uuid.uuid4().hex)[1:-1]
	#~ tabname = arcpy.ValidateTableName(gid, "in_memory")
	#~ clippedFCN = "in_memory/a%s" % tabname
	# KISS principle
	clippedFCN = arcpy.CreateScratchName ('seismo', 'profiles', 'FeatureClass', 'in_memory')

# seismoprofiles length
	log.info("Clip_analysis into FC '%s'..." % (clippedFCN))
	arcpy.Clip_analysis(os.path.join(toolDirPath, gdbFName, seisFCName), fsetObj, clippedFCN)
	log.info("Clip_analysis done, create geometryList...")
	g = arcpy.Geometry()
	geometryList = arcpy.CopyFeatures_management(clippedFCN, g)
	log.info("create geometryList done, calc length...")

	length = 0
	for geometry in geometryList:
		length += geometry.length
	length = length / 1000.0 # kilometers from meters
	log.info("clipped seismoprofiles length '%s' km." % (length))
	#~ arcpy.Delete_management(clippedFCN) # no need for in_memory

# polygon area
	area = 0
	rows = arcpy.SearchCursor(fsetObj, '', workSR)
	for row in rows: # for each polygon
		geom = row.shape
		log.info("arcpyStuff searchcursor, geometry type '%s', area '%s', parts '%s'" % (geom.type, geom.area, geom.partCount)) # geometry type 'polygon', area '-218254081896.0', parts '0'
		log.info("arcpyStuff searchcursor, geometry geojson '%s'" % (geom.__geo_interface__)) # {'type': 'Polygon', 'coordinates': []}
		area = geom.area
		break # only one polygon
	area = area / 1000000.0 # kilometers from meters
	log.info("polygon area '%s' km2" % (area))

# density
	density = length / area
	log.info("seismodens '%s' km/km2" % (density))

	arcpy.SetParameterAsText(1, '%.3f' % density) # Seismodensity double
	arcpy.SetParameterAsText(2, '%.3f' % length) # SeismorofilesLength double
	arcpy.SetParameterAsText(3, '%.3f' % area) # ShapeArea double

# todo
# gemetry.simplify on server
# http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#/Repair_Geometry/00170000003v000000/
# http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//007000000011000000

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
	repfile = r'''c:\d\code\git\oracle\seismodens\python.oracle\seismodensitynosql.py'''
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
