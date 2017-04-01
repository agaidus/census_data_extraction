
import urllib2
import zipfile
import StringIO
import shapefile
from json import dumps
from shapely.geometry import *
import geopandas as gpd
from shapely.geometry import shape  
import osr
import sys

#useful links
#https://github.com/mlaloux/PyShp-as-Fiona--with-geo_interface-
#http://geospatialpython.com/2011/09/reading-shapefiles-from-cloud.html

#census api
#http://api.census.gov/data/2013/acs5/examples.html




fname='http://www2.census.gov/geo/tiger/TIGER2010/BG/2010/tl_2010_06075_bg10.zip'
cloudfile = urllib2.urlopen(fname)
memoryfile = StringIO.StringIO(cloudfile.read())
zipshape = zipfile.ZipFile(memoryfile)

filenames = [y for y in sorted(zipshape.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)] 
dbf, prj, shp, shx = [StringIO.StringIO(zipshape.read(filename)) for filename in filenames]



def get_shp(zip_file_name):

    cloudfile = urllib2.urlopen(zip_file_name)
    memoryfile = StringIO.StringIO(cloudfile.read())
    zipshape = zipfile.ZipFile(memoryfile)
    
    filenames = [y for y in sorted(zipshape.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)] 
    dbf, prj, shp, shx = [StringIO.StringIO(zipshape.read(filename)) for filename in filenames]
    
    reader = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)
    
    proj4 = osr.SpatialReference(prj.read()).ExportToProj4()
    
    
    
    atts, shapes = [], []
    field_names = [field[0] for field in reader.fields[1:]]  
    for sr in reader.shapeRecords():  
        shapely_geo = shape(sr.shape.__geo_interface__)  
        att = dict(zip(field_names, sr.record))  
        atts.append(att)
        shapes.append(shapely_geo)
    
    gdf = gpd.GeoDataFrame(data = atts, geometry = shapes, crs = proj4)
    return gdf



bgs = get_shp(fname).to_crs(epsg=3310)

bgs=bgs[bgs.ALAND10>0]
water = get_shp('http://www2.census.gov/geo/tiger/TIGER2010/AREAWATER/tl_2010_06075_areawater.zip').to_crs(epsg=3310).unary_union

print 'calc diff'
geo2 = bgs.geometry.difference(water)

bgs2=gpd.GeoDataFrame(bgs, geometry=geo2, crs=bgs.crs)

bgs2[['GEOID10','geometry']].to_file('C:/Temp/a.shp')

#result.to_file("C:/Temp/aaplease3.shp")









#http://www2.census.gov/geo/tiger/TIGER2010/AREAWATER/tl_2010_06075_areawater.zip