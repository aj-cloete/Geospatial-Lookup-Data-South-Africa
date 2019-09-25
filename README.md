# Geospatial Lookup Data - South Africa
Data and methodology to be used within a relational database with which to perform geospatial lookup and enrich location data for South Africa (or whichever country/place - feel free to fork!) 

### Motivation
Interacting with geospatial or location information within a relational database is difficult - one usually has only a few options:
- perform a complex join involving sub-queries and "best guess approximations" based on proximity
- export the data to another tool in order to extract enrichment information
- perform an api call to obtain enrichment information - something that usually ends up costing money
- be lucky enough to have database extensions that allow for geospatial computations

This repository provides a neat alternative:

![South Africa Grid](images/South_Africa_grid_example_10000m.png)
> A map of South Africa with a grid overlay made up of points spaced 10000m apart.  Making the grid finer increases accuracy but also increases the number of data points required.

### The idea
Generate a grid over the country/area of interest.  Make the grid as coarse or fine as is needed for the application.  Enrich the grid points once (outside of the database, using this repository as an example), finding useful information about nearby places, suburb, town, city, province, etc.  

With the information now available at the grid points, construct a key from the (latitude; longitude) information, taking into account the spacing of the points.  Store the resulting dataset in the same database into which new, unenriched location data flows.

New location data, (latitude; longitude) pairs, can then be transformed, using the same methodology as for the grid, into a key that can be used to find the nearest grid point, along with all the previously extracted enrichment information.  The enrichment problem is thus reduced to a one-to-one join to the generated grid table.

### Methodology
1. Generate a grid over the country of interest (South Africa in this repository but feel free to fork!)
2. Grid can be as coarse or fine as is necessary (in the example image, dots are spaced 10km apart)
3. Translate the approximate accuracy into the required number of decimal points for the latitude and longitude values
Here is a very scientific guide to decide what is appropriate:
![coordinate precision](https://imgs.xkcd.com/comics/coordinate_precision.png)
4. Look up all the generated grid points against the source of your choice (see resources below) 
5. Store the results in your relational database, adding a composite text-based lookup key based on the desired accuracy level (point 3).  This is to ease database joins.  The alternative is to join to both latitude and longitude after truncation.
6. Transform the (latitude, longitude) pairs you wish to look up according to the accuracy level
7. Perform a simple database join to obtain the information you gathered in the steps above

### Coordinate transformation
The coordinate transformation required is as follows (you may need to adapt it slightly to your flavour of SQL):

```sql
SELECT 
    cast(cast(round(latitude,round_level)*100000 as int) as varchar)
  + ';'
  + cast(cast(round(longitude,round_level)*100000 as int) as varchar) as geokey
FROM input_data
```

> where `round_level` is given by `cast(5 - LOG(accuracy_m) as integer)`, i.e. accuracy_m=1000 -> round_level=2

### Installation
The [requirements.txt](requirements.txt) file contains the python dependencies.  Please note from the point above that there are other libraries required! Specifically, linux users should install `libspatialindex-dev` and MacOS users: `spatialindex`.  The `wget`, `zip`, and `unzip` libraries are also required in order to run the [get_SA_data.sh](get_SA_data.sh) script.
> Install these packages _before_ you install the pip packages or you may run into trouble.

The [setup.sh](setup.sh) script can be run to install the dependencies.  
Alternatively, a [Dockerfile](Dockerfile) is provided for convenience. 
> _You can also use either of these as a reference when troubleshooting your own installation._


### Resources
This methodology requires access to shapefile data about your continent/country/city of interest.  Specifically, the data needs to contain a shapefile - a set of coordinates which define the boundaries of an area - which will be used to classify the generated grid of points.

#### Tools
- [Geopandas](http://geopandas.org) (carefully read through the [installation instructions](http://geopandas.org/install.html) and pay attention to its dependencies)
- [Matplotlib](https://matplotlib.org) for plotting. [installation instructions](https://matplotlib.org/users/installing.html)

#### Data sources
Feel free to add more _open_ data sources to this list!
- [geonames](http://www.geonames.org) (an excellent open resource for worldwide geospatial datasets)
- [top open geospatial data](https://gisgeography.com/best-free-gis-data-sources-raster-vector/) (provides links to other sources)

#### Helper functions
A set of helper functions has been included in [geohelpers.py](geohelpers.py).  Make sure the file is in your working directory and then simply import it: 
```python
import geohelpers as gh
```


## South Africa
With our bases covered about the general repository, let's dig in to how it is applied to the South African data.

The [get_SA_data.sh](get_SA_data.sh) file can be run to download the data.  It creates a *data* folder in the working directory, containing the pivotal [South African Municipal Demarcation Board](http://www.demarcation.org.za) data from the [data portal](http://dataportal-mdb-sa.opendata.arcgis.com) as well as a dataset of postal codes and the South Africa dataset from [geonames](http://www.geonames.org).  The latter contains all kinds of points of interest including suburbs, towns, rivers, mountains, etc.

You can read more about the South African data in the [data_dictionary.md](data_dictionary.md)

### The ETL process
#### You can follow along here or have a look at the [Example notebook South Africa](Example%20notebook%20South%20Africa.ipynb) to see how the process works.

#### Shell script
First thing you'll want to do is set up and enter your environment (see [setup.sh](setup.sh)) or docker image (see [Dockerfile](Dockerfile)).
The next step is running the [get_SA_data.sh](get_SA_data.sh) to download the raw data into the **data** folder.  Do this before you continue to the python section.
``` ./get_SA_data.sh```

#### Python script generating lookup datasets
While you can simply run `python main.py` at this point, I'd like to walk you through the main steps.  You can replace the provided [main.py](main.py) sript with your own after understanding the steps.

Go ahead and launch `python` and do one simple import: (make sure your working directory is the root of the repository)
```python
from main import *
```

We then load the source enrichment data by running 
```python
geometries, geonames, postal_codes = load_raw_data()
```
Our methodology involves generating a grid that covers the area of interest.  To that end, South Africa is bounded by latitudes in the range [-35,-22] and longitudes in the range [16,33].  We therefore generate the grid using those to sets with the command 
```python
points_grid = gh.generate_grid(lats=[-35,-22], longs=[16,33], accuracy_m=1000, verbose=True)
gh.check_grid(points_grid)
```

> whenever you see the `gh.`, note that those are functions from the [geohelpers.py](geohelpers.py) file.

Next, we look up the grid against the geometries - this is the crux of this repository.
```python 
located_grid = gh.process_dataframe(points_grid, geometries, accuracy_m=1000, verbose=True)
gh.check_grid(located_grid)
```

> Note that the **geometries** dataframe contains a column named _geometry_ that is a [shapely](https://shapely.readthedocs.io/en/stable/manual.html) geometry Polygon and the grid contains a [shapely](https://shapely.readthedocs.io/en/stable/manual.html) geometry Point.  This allows us to find the geometry containing the point.

With the lookup done, all that remains is decomposing the parts for use in a database.  You want to store an identifier to the geometries file (in our case **ward_id**) in the generated grid file, along with the lookup key.  This becomes the **grid** dataset.  In our case we have this **grid** table with four columns (`ward_id`,`geokey`,`latitude`,`longitude`) and N rows, where N depends on the chosen accuracy_m level.

Next, we save the data by using the `gh.save_data` helper function.  It accepts a dictionary which will be used to filter and rename the columns to keep only the relevant ones.  We also decompose the table into two parts: the **grid** and the **wards** datasets and save each.

```python
grid_cols = {
    'WardID':'ward_id',
    'WardNumber':'ward_number',
    'Shape_Length':'ward_length',
    'Shape_Area':'ward_area',
    'LocalMunicipalityName':'local_municipality',
    'DistrictMunicipalityCode':'district_minicipal_code',
    'DistrictMunicipalityName':'district_municipality',
    'ProvinceName':'province_code',
    'ProvinceCode':'province_name',
    'geokey':'geokey',
    'latitude':'latitude',
    'longitude':'longitude'}
grid = gh.save_data(located_grid, 'located_grid.json.gz','processed_data',columns=grid_cols)
wards = grid.drop(columns=['geokey','latitude','longitude']).drop_duplicates()
grid = grid[['geokey','ward_id','latitude','longitude']].drop_duplicates()
gh.save_data(df=wards, filename='wards.json.gz', directory ='datasets')
gh.save_data(df=grid, filename='grid.json.gz', directory ='datasets')
```

That concludes the processing and therefore the ETL.  

#### Python script for looking up new location data

Any new incoming data can be classified within a database using a combination of the **grid** and the **wards** data, as simulated below and generating sample data from Cape Town area:

```python
from main import *
# generate the input data (on a higher level of accuracy - not unlike real-world location data coming in)
incoming_data = gh.generate_grid(lats=[-34.5,-33.5], longs=[18,19], accuracy_m=10).sample(500)

# generate the geokey on the new incoming data
geokey = gh.generate_key(incoming_data, accuracy_m=1000)['geokey']
incoming_data['geokey'] = geokey

# read the grid and wards datasets (which could be stored in your database/warehouse)
grid = pd.read_json('datasets/grid.json.gz')
wards = pd.read_json('datasets/wards.json.gz')

## the lookup steps
# Step1 of the lookup process
located = incoming_data.merge(grid, how='left', on='geokey')
# Step2 of the lookup process
final = located.merge(wards, how='left', on='ward_id')

```
And with that, we have successfully done a lookup of new incoming data and asserted in which wards the points lie - all without having to leave the comfort of our data warehouse.

## Addressing scheduling and scaling

### Scheduling
If the data will be accessed frequently, or if the lookup data changes from time to time, it may be necessary to schedule the creation of the lookup datasets or the lookup process of new incoming data.

One could, for example, schedule a job using Apache Airflow that runs once a day at 7:00, that looks up all the new location data against the generated lookup tables **grid** and **ward** and stores the results in a table called **locations_enriched**.  Each new day, the job would run, enrich the new location data from the day before and store the results in **location_enriched** where the data users can easily obtain the additional information without having to join to **grid** and **wards** again.

### Scaling
#### Scaling the users (concurrent access to the data)
The above examples show just how powerful this methodology can be.  

To make this scalable, the data should be housed in a database (like AWS RDS postgres) or warehouse (like AWS Redshift), where it can be accessible from anywhere in the world.  It could then easily be accessed by 100s of users simultaneously, each one looking up their own set of incoming data points.

#### Scaling the data
What happens if the data sizes are increased 10x?  Since this is a two-pronged approach, let's consider both cases:
##### The classification (source) data increases 100x:
Since this entire process can be dockerised (see [Dockerfile](Dockerfile)), the approach can be scaled by:
1. Partitioning the data into logical subsets (e.g. country, province, city, etc) and use a separate docker container for each partition.  The generated grids can be appropriately adjusted to fit the partition.
2. If only a single docker/machine can be used, the codebase includes the option to specify a *chunksize* which splits the generation and classification of data into smaller subsets.  If memory becomes an issue, these intermediate steps can be written to disk.  At this point, utilising Spark to interact with the data makes the most sense.
##### The generation of new unenriched data increases 100x:
1. Using an analytical (column-based) warehouse like AWS Redshift means that your cluster can simply be resized to cater for the increase in requirements.  
2. Making use of AWS S3 and Spark can be a good alternative to AWS Redshift.  The classification data (grid, wards) data can be stored on S3 and Spark can be used to look up new data against these disk-based datasets.
3. Making use of scheduling (as noted above) can reduce the load on the warehouse by scheduling the heavy lifting (joins) and store the results.  The frequency can be increased from daily to twice, three, four times a day as the data needs change.

## End notes
This repository was created as my **Capstone Project** for the [Udacity](https://www.udacity.com) [**Data Engineering Nanodegree Programme (DEND)**](https://www.udacity.com/course/data-engineer-nanodegree--nd027).
