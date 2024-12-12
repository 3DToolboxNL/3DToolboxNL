import logging
import subprocess

from src import netcdf_to_tif
from src import tif_to_png
from src import create_layer_json
from config import Config as cfg

from output import Output

# configure a logger
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# create an output object
out = Output()

# Convert NetCDF file to set of GeoTIFF files
netcdf_to_tif.main(cfg, out)

# Convert GeoTIFF files to PNG files
tif_to_png.main(cfg, out)

# Create layer.json file
create_layer_json.main(cfg, out)
