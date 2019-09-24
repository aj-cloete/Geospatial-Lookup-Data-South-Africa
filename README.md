# Geospatial Lookup Data - South Africa
Data and methodology to be used within a relational database with which to perform geospatial lookup and enrich location data for South Africa 

### Motivation
Interacting with geospatial or location information within a relational database is difficult - one usually has only a few options:
- perform a complex join involving sub-queries and "best guess approximations" based on proximity
- export the data to another tool in order to extract enrichment information
- perform an api call to obtain enrichment information - something that usually ends up costing money
- be lucky enough to have database extensions that allow for geospatial computations

This repository provides a neat alternative.

![South Africa Grid](images/South_Africa_grid_example_10000m.png)

### Methodology
1. Generate a grid over the country of interest (South Africa in this repository but feel free to fork!)
2. Grid can be as coarse or fine as is necessary (in the example image, dots are spaced 10km apart)
3. Translate the approximate accuracy into the required number of decimal points for the latitude and longitude values
Here is a very scientific guide to decide what is appropriate:
![coordinate precision](https://imgs.xkcd.com/comics/coordinate_precision.png)
4. Look up all the generated grid points against the source of your choice (see motivation) 
5. Store the results in your relational database, adding a composite text-based lookup key based on the desired accuracy level (point 3).  This is to ease database joins.  The alternative is to join to both latitude and longitude after truncation.
6. Transform the (latitude, longitude) pairs you wish to look up according to the accuracy level
7. Perform a simple database join to obtain the information you gathered in the steps above

### Coordinate transformation
The coordinate transformation required is as follows (you may need to adapt it slightly to your flavour of SQL):

```sql
SELECT 
    cast(cast(round(latitude,round_level)*100000 as int) as varchar)
  + ';'
  + cast(cast(round(longitude,round_level)*100000 as int) as varchar) as lookup_key
FROM input_data
```

> where `round_level` is given by `cast(5 - LOG(accuracy_m) as integer)`, i.e. accuracy_m=1000 -> round_level=2

### Installation
The [requirements.txt](requirements.txt) file contains the python dependencies.  Please note from the point above that there are other libraries required! Specifically, linux users should install `libspatialindex-dev` and MacOS users: `spatialindex`.
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

The [get_SA_data.sh](get_SA_data.sh) file can be run to download the data.  It will create a *data* folder in the working directory, containing the pivotal [South African Municipal Demarcation Board](http://www.demarcation.org.za) data from the [data portal](http://dataportal-mdb-sa.opendata.arcgis.com) as well as a dataset of postal codes and the South Africa dataset from [geonames](http://www.geonames.org).  The latter contains all kinds of points of interest including suburbs, towns, rivers, mountains, etc.

You can read more about the South African data in the [data_dictionary.md](data_dictionary.md)
