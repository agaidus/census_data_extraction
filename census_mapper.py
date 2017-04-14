from urllib2 import urlopen
from zipfile import ZipFile
from StringIO import StringIO
import shapefile
import geopandas as gpd
from shapely.geometry import shape  
import osr
import pandas as pd
import requests
from shapely.geometry import Point
from numpy.random import RandomState, uniform


def gen_random_points_poly(poly, num_points, seed = None):
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    i=0
    while len(points) < num_points:
        s=RandomState(seed+i) if seed else RandomState(seed)
        random_point = Point([s.uniform(min_x, max_x), s.uniform(min_y, max_y)])
        if random_point.within(poly):
            points.append(random_point)
        i+=1
    return points


def num_points_in_gdf(geometry, values, points_per_value = None, seed = None):
    
    if points_per_value:
        new_values = (values/points_per_value).astype(int)
    else:
        new_values = values
    new_values = new_values[new_values>0]
    g = gpd.GeoDataFrame(data = {'vals':new_values}, geometry = geometry)
    
    a = g.apply(lambda row: tuple(gen_random_points_poly(row['geometry'], row['vals'], seed)),1)
    b = gpd.GeoSeries(a.apply(pd.Series).stack(), crs = geometry.crs)
    return b


def zip_shp_to_gdf(zip_file_name):

    zipfile = ZipFile(StringIO(urlopen(zip_file_name).read()))
    filenames = [y for y in sorted(zipfile.namelist()) for ending in ['dbf', 'prj', 'shp', 'shx']\
                 if y.endswith(ending)] 
    dbf, prj, shp, shx = [StringIO(zipfile.read(filename)) for filename in filenames]
    r = shapefile.Reader(shp=shp, shx=shx, dbf=dbf)
    
    attributes, geometry = [], []
    field_names = [field[0] for field in r.fields[1:]]  
    for row in r.shapeRecords():  
        geometry.append(shape(row.shape.__geo_interface__))  
        attributes.append(dict(zip(field_names, row.record)))  
        
    proj4_string = osr.SpatialReference(prj.read()).ExportToProj4()
    gdf = gpd.GeoDataFrame(data = attributes, geometry = geometry, crs = proj4_string)
    return gdf



def get_census_variables(year, dataset, geography, area, variables, variable_labels = None):
    
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




