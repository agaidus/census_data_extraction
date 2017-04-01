import urllib2
import zipfile
import StringIO
import shapefile
import geopandas as gpd
from shapely.geometry import shape  
import osr
import pandas as pd
import requests

def zip_shp_to_gdf(zip_file_name):

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




def get_census_data(year, dataset, geography, area, variables, variable_labels = None):
    
    base_url = 'https://api.census.gov/data/{}/{}'.format(year, dataset)
    
    #define parameters
    get_parameter = ','.join(['NAME'] + variables)
    for_parameter = '{}:*'.format(geography)
    in_paramater = '+'.join([k+':'+v for (k,v) in area.items()])

    parameters = {'get' : get_parameter, 
                  'for' : for_parameter,
                  'in' : in_paramater}
    
    #make request specifiying url and parameters
    r = requests.get(base_url, params=parameters)
    
    #read json into pandas dataframe, specifying first row as column names
    data = r.json()
    df=pd.DataFrame(columns = data[0], data = data[1:])
    
    #identify geography fields - concatenate them into a fips code to be set as index and then delete them
    geo_fields = [x for x in df.columns if x not in ['NAME'] + variables]
    df.index = df[geo_fields].apply(lambda row: ''.join(map(str, row)), 1)
    df.index.name = 'FIPS'
    df = df.drop(geo_fields, 1)
    
    if variable_labels:
        df = df.rename(columns = dict(zip(variables, variable_labels)))
    
    #convert data numeric 
    df = df.applymap(lambda x:pd.to_numeric(x, errors='ignore'))
    return df




