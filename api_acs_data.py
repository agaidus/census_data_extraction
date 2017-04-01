import requests
import pandas as pd

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


 get_census_data(2015, 'ac5', 'tract', {'county':'001', 'state':'06'}, ['B19013_001E'], ['income'])



varlist = ['B02001_001E', 'B03002_003E', 'B03002_012E', 'B02001_002E', 'B02001_003E', 'B02001_005E', 'B02001_004E', 'B02001_006E', 'B02001_007E', 'B02001_008E']
names = ['total', 'white_nhs', 'hispanic', 'white','black', 'asian', 'ai_an', 'nh_pi', 'other', 'two_plus']

df = get_census_data(2015, 'acs5', 'county', {'state':'*'}, varlist, names)


