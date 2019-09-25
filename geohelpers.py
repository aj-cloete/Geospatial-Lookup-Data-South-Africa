import numpy as np
import pandas as pd
import geopandas as gpd
import os

def _check_chunksize(chunksize, df_size):
    '''Check that the chunksize is reasonable given the size of the data'''
    try:
        chunksize = int(chunksize)
    except TypeError:
        chunksize = min(max(df_size//50,5000), 60000)
    return chunksize

def cartesian_product(*arrays):
    '''
    Perform a cartesian product on the provided arrays
    arrays: numpy arrays or lists
    '''
    ndim = len(arrays)
    return np.stack(np.meshgrid(*arrays), axis=-1).reshape(-1, ndim)

def generate_key(df, accuracy_m=1000, lats='latitude',longs='longitude'):
    '''
    Generate the key based on the selected level of accuracy
    df(dataframe): pandas-like dataframe containing the latitudes and longitudes to be converted to key
    accuracy_m(int): desired accuracy (in meters) - should be consistent with rest of the data
    lats(str): (optional) specify the name of the column containing the latitudes
    longs(str): (optional) specify the name of the column containing the longitudes
    Returns: dataframe with generated key columns attached (will replace existing 'key' column if present)
    '''
    print('Generating the geokey')
    # ensure that the lats and longs correspond with the selected accuracy
    round_level = int(5 - np.log10(accuracy_m))
    df = df.copy()
    df[lats] = df[lats].round(round_level)
    df[longs] = df[longs].round(round_level)
    df['geokey'] = (df[lats]*100000).astype(int).astype(str) \
            +';'+ (df[longs]*100000).astype(int).astype(str)
    return df

def generate_points_from_coordinates(df, chunksize=None, lats='latitude',longs='longitude'):
    '''
    Generate a Point geometries column from the latitudes and longitudes
    df(dataframe): pandas-like dataframe containing the latitudes and longitudes to be converted to Points
    '''
    print('Generating the geometry points from the coordinates')
    chunksize = _check_chunksize(chunksize, df.shape[0])
    print(f'selected chunksize {chunksize}', flush=True, end='')
    dfs = []
    for df_chunk in _chunker(df, chunksize):
        df_ret = gpd.GeoDataFrame(df_chunk, geometry=gpd.points_from_xy(df_chunk[longs],df_chunk[lats]))
        df_ret.crs = {'init': 'epsg:4326'}
        dfs.append(df_ret)
        print('.', flush=True, end='')
    print('Done!')
    return pd.concat(dfs)

def _generate_smaller_grid(lats, longs, accuracy_m, verbose):
    '''For use with generate grid'''
    mlat, mlong = len(lats), len(longs)
    if max(mlat,mlong) >= 1500:
        # potentially too large to handle in one go...dividing and conquering
        dfs = []
        if mlat>mlong: 
            for lat in np.array_split(lats,mlat//100):
                dfs += [_generate_smaller_grid(lat,longs,accuracy_m,verbose)]
        else:
            for lon in np.array_split(longs,mlong//100):
                dfs += [_generate_smaller_grid(lats,lon,accuracy_m,verbose)]
        grid = pd.concat(dfs)
        if verbose: print('collecting results')

    else:
        if verbose: print('.',end='',flush=True)
        cols=['latitude','longitude']
        grid = pd.DataFrame(cartesian_product(lats,longs), columns=cols)
    return grid

def generate_grid(lats, longs, accuracy_m=1000, verbose=False):
    '''Create accuracy_m spaced grid using (min,max) pairs provided in lats, longs
    longs(array-like): min,max values for longitude range
    lats(array-like): min,max values for latitude range
    accuracy_m(int): desired approximate accuracy in meters from (1,10,100,1000,10000,100000)
    verbose(bool): set verbosity level
    Returns: GeoDataFrame with latitudes, longitudes, coordinates and constructed key
    '''
    try:
        accuracy_m = int(accuracy_m)
        if not accuracy_m in (10**x for x in range(6)):
            raise ValueError('accuracy_m not in (1,10,100,1000,10000,100000)')
    except Exception:
        raise ValueError('accuracy_m must be one of these values: (1,10,100,1000,10000,100000)')
    
    steps = accuracy_m/100000
    lats = np.arange(np.min(lats), np.max(lats), steps)
    longs = np.arange(np.min(longs), np.max(longs), steps)
    print('Generating point grid')
    ret = _generate_smaller_grid(lats,longs,accuracy_m,verbose).reset_index(drop=True)
    print(f'\nGrid of size {ret.shape} generated!')
    return ret

def _chunker(df, chunksize=None):
    '''
    df(dataframe): Pandas-like df to be split into chunks
    chunksize(int): desired size of smaller dfs
    returns: generator of dfs with at most chunksize rows or at most chunks entries
    '''
    if not chunksize:
        return [df]
    df_in = df.copy()
    dfs = []
    for (g,df) in df_in.groupby(np.arange(df_in.shape[0]) // chunksize):
        dfs+=[df]
    return dfs

def do_join(points, geometries):
    '''
    Helper to do the geometry join
    '''
    joined = gpd.sjoin(points, geometries, how='inner', op='within', rsuffix='geometries')
    return joined

def locate_points(points, geometries, chunksize=None, verbose=False):
    '''
    Locate the points within the provided geometries
    points(geopandasdf): GeoPandasDF containing a single column of Points to locate in geometries
    geometries(geopandasdf): GeoPandasDF conatining a single column of Geometries
    chunksize(int): (optional) specify the size of the chunks in which to process the points
    verbose(bool): Do you want all the information? (Default False)
    '''
    print('Locating the points')
    results = []
    chunksize = _check_chunksize(chunksize, points.shape[0])
    if points.shape[0] > 500000:
        print('There are many points to locate - this is going to take a while!')
    n,steps = 0,0
    for small_points in _chunker(points, chunksize):
        if verbose: print('.',flush=True,end='')
        small_join = do_join(small_points, geometries)
        results += [small_join]
        steps += 1
        n += small_points.shape[0]
        if steps%10==0:
            print(f' ({n} of {points.shape[0]} [{n*100//points.shape[0]}%] processed)')
    print('Combining results')
    ret = pd.concat(results)
    print(f'Done!')
    if verbose: 
        print(f'{ret.shape[0]} of {points.shape[0]} located within geometries')
        print(f'{points.shape[0] - ret.shape[0]} points were not found within provided geometries!')
    return ret.reset_index(drop=True)

def save_data(df, filename='filename.json.gz', directory='processed_data', columns=None):
    '''
    Save the data in json records format, optionally only keeping certain columns
    df(dataframe): dataframe to save
    filename(str): the name of the destination filename, including extension and compression
    directory(str): the directory in which to save the files
    columns(list/dict): list of columns to keep in the saved file.  
    If dictionary is passed in columns, the keys will be used to filter the df 
    while the (key:value) pairs will be used to rename the columns
    '''
    if columns:
        if not isinstance(columns, dict):
            if not isinstance(columns, list):
                df = df[list(columns)]
        else:
            df = df[columns.keys()]
            df = df.rename(columns=columns)
    df = pd.DataFrame(df)
    try:
        # Create target Directory
        os.mkdir(directory)
        print(f"Directory {directory} created")
    except FileExistsError:
        print(f"Directory {directory} already exists")
    full_pathname = os.path.join(directory,filename)
    print(f'Writing file at {full_pathname}')
    df.to_json(full_pathname,orient='records')
    return df

def process_dataframe(df, geometries, accuracy_m=1000, chunksize=None, verbose=False):
    chunksize = _check_chunksize(chunksize, df.shape[0])
    df = generate_key(df, accuracy_m)
    df = generate_points_from_coordinates(df, chunksize)
    df = locate_points(df, geometries, chunksize, verbose)
    return df
