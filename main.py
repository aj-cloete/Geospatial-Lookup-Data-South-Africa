## ensure that the data folder is colocated with this file
## if you don't have the data folder, run the get_data.sh script first
import numpy as np
import pandas as pd
import geopandas as gpd
import geohelpers as gh
import os, sys

def load_raw_data():
    print('Reading geonames dataset')
    geo_cols = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude',
                'feature_class', 'feature_code', 'country_code', 'cc2',
                'admin1_code', 'admin2_code', 'admin3_code', 'admin4_code',
                'population', 'elevation', 'dem', 'timezone', 'modification_date',]
    geonames = pd.read_csv('data/geonames.tsv', sep='\t', names=geo_cols, dtype=object)
    geonames['f_code'] = geonames.feature_class.astype(str)+'.'+(geonames.feature_code).astype(str)
    geofeats_cols = ['f_code','desc_short','desc_long']
    geofeats = pd.read_csv('data/geonames_features.tsv', sep='\t', names=geofeats_cols)
    geonames = geonames.merge(geofeats, how='left',on='f_code')
    geonames[['latitude','longitude']] = geonames[['latitude','longitude']].astype(float)
    geonames[['geonameid','population']] = geonames[['geonameid','population']].astype(int)

    print('Reading postal codes')
    pc_cols = ['country_code', 'postal_code', 'place_name', 
               'admin_name1', 'admin_code1', 'admin_name2', 'admin_code2', 
               'admin_name3', 'admin_code3', 'latitude', 'longitude', 'accuracy',]
    postal_codes = pd.read_csv('data/postal_codes.tsv', sep='\t', names=pc_cols, dtype={1:object})
    postal_codes[['latitude','longitude']] = postal_codes[['latitude','longitude']].astype(float)

    print('Reading wards')
    geometries = gpd.read_file('data/MDBWard2016.gdb/').set_geometry('geometry')
    geometries = geometries.drop(columns=[])
    
    print('All files read!')
    
    return geometries, geonames, postal_codes

def extract_names_datasets(located_geonames):
    ## Descoped nearest points for now
    ## see here on how to do it: https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
    ## or here: https://stackoverflow.com/questions/56520780/how-to-use-geopanda-or-shapely-to-find-nearest-point-in-same-geodataframe
    lg = located_geonames
    provinces = pd.DataFrame(lg[lg.feature_code=='ADM1']).reset_index(drop=True)
    districts = pd.DataFrame(lg[lg.feature_code=='ADM2']).reset_index(drop=True)
    towns = pd.DataFrame(lg[lg.feature_code=='ADM3']).reset_index(drop=True)
    suburbs = pd.DataFrame(lg[lg.feature_class=='P']).reset_index(drop=True)
    return provinces, districts, towns, suburbs

def process_data(accuracy_m=1000, verbose=False):
    geometries, geonames, postal_codes = load_raw_data()
    points_grid = gh.generate_grid(lats=[-35,-22], longs=[16,33], accuracy_m=accuracy_m, verbose=verbose)
    gh.check_grid(points_grid)
    
    print('\nProcessing the generated grid dataset')
    located_grid = gh.process_dataframe(points_grid, geometries, accuracy_m, verbose=verbose)
    gh.check_grid(located_grid)
    del points_grid # free up RAM
    grid_cols = {
        'geokey':'geokey',
        'latitude':'latitude',
        'longitude':'longitude',
        'WardID':'ward_id',
        'WardNumber':'ward_number',
        'Shape_Length':'ward_length',
        'Shape_Area':'ward_area',
        'LocalMunicipalityName':'local_municipality',
        'DistrictMunicipalityCode':'district_minicipal_code',
        'DistrictMunicipalityName':'district_municipality',
        'ProvinceName':'province_code',
        'ProvinceCode':'province_name',}
    grid = gh.save_data(located_grid, 'located_grid.json.gz','processed_data',columns=grid_cols)
    wards = grid.drop(columns=['geokey','latitude','longitude']).drop_duplicates()
    grid = grid[['geokey','ward_id','latitude','longitude']].drop_duplicates()
    
    print('\nProcessing the geonames dataset')
    located_geonames = gh.process_dataframe(geonames, geometries, accuracy_m, verbose=verbose)
    geonames_cols = {
        'geonameid':'geoname_id',
        'WardID':'ward_id',
        'geokey':'geokey',
        'latitude':'latitude',
        'longitude':'longitude',
        'name':'name',
        'feature_class':'feature_class',
        'feature_code':'feature_code',
        'population':'population',
        'desc_short':'desc_short',
        'desc_long':'desc_long',
        }
    located_geonames = located_geonames[list(geonames_cols)]
    located_geonames['desc_long'] = located_geonames['desc_long'].fillna(located_geonames['desc_short'])
    located_geonames = located_geonames.dropna()
    loc_geo = gh.save_data(located_geonames, 'located_geonames.json.gz','processed_data',columns=geonames_cols)
    provinces, districts, towns, suburbs = extract_names_datasets(loc_geo)
    
    print('\nProcessing the postal_codes dataset')
    located_postal_codes = gh.process_dataframe(postal_codes, geometries, accuracy_m, verbose=verbose)
    postal_code_cols = {
        'geokey':'geokey',
        'WardID':'ward_id',
        'postal_code':'postal_code',
        'place_name':'place_name',
        'latitude':'latitude',
        'longitude':'longitude',
        }
    postal_codes_dataset = gh.save_data(located_postal_codes,
                                        'located_postal_codes.json.gz',
                                        'processed_data',columns=postal_code_cols, 
                                        skip_checks=True)

    print('\nSaving datasets')
    gh.save_data(df=postal_codes_dataset, filename='postal_codes.json.gz', directory='datasets')
    gh.save_data(df=provinces, filename='provinces.json.gz', directory ='datasets')
    gh.save_data(df=districts, filename='districts.json.gz', directory ='datasets')
    gh.save_data(df=towns, filename='towns.json.gz', directory ='datasets')
    gh.save_data(df=suburbs, filename='suburbs.json.gz', directory ='datasets')
    gh.save_data(df=wards, filename='wards.json.gz', directory ='datasets')
    gh.save_data(df=grid, filename='grid.json.gz', directory ='datasets')
    
    print('Done!')
    return (located_grid, located_geonames, located_postal_codes)
    
if __name__=='__main__':
    (located_grid, located_geonames, located_postal_codes) = process_data(accuracy_m=1000, verbose=True)
    print([x.shape for x in (located_grid, located_geonames, located_postal_codes)])
    provinces, districts, towns, suburbs = extract_names_datasets(located_geonames)
    print([x.shape for x in (provinces, districts, towns, suburbs)])
