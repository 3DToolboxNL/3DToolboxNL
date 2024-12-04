import logging
import os
from pandas import DataFrame
from tqdm import tqdm 
import xugrid as xu
import rasterio
from rasterio.transform import from_origin
import numpy as np


def export_df_to_raster(df: DataFrame, variable_name: str, postfix: str, dtype: str, cfg, crs='EPSG:28992') -> str:
    """
    Export a DataFrame to a GeoTIFF raster file.

    Parameters:
    df (DataFrame): The DataFrame containing the data to export.
    variable_name (str): The name of the variable to export.
    postfix (str): The postfix to add to the output filename.
    dtype (str): The data type of the output raster.
    cfg: The configuration object containing various settings.
    crs (str): The coordinate reference system of the output raster ('EPSG:XXXX').

    Returns:
    str: The filename of the created GeoTIFF file.
    """
    # Create a pivot table to convert the DataFrame to a 2D raster
    raster_data = df.pivot(index="Mesh2d_face_y", columns="Mesh2d_face_x", values=variable_name)
    # Flip the DataFrame vertically to match the rasterio coordinate system
    raster_data = raster_data.iloc[::-1]
    # Define a transformation matrix to place the raster at the correct location
    height, width = raster_data.shape
    west = raster_data.columns[0]
    north = raster_data.index[0]
    transform = from_origin(west - cfg.PIXEL_SIZE / 2, north + cfg.PIXEL_SIZE / 2, cfg.PIXEL_SIZE, cfg.PIXEL_SIZE)
    # write the raster to a file
    fname = f'{cfg.TMP_DIR}/{cfg.SCENARIO}_{postfix}.tif'

    # Replace invalid values with the nodata value
    raster_data = raster_data.fillna(cfg.NODATA_VALUE).astype(dtype)

    # write the raster to GeoTIFF
    with rasterio.open(fname, 'w', driver='GTiff', height=height, width=width, count=1, dtype=dtype, crs=crs, transform=transform, nodata=cfg.NODATA_VALUE) as dst:
        dst.write(raster_data, 1)
    return fname


def main(cfg, out):
    """
    Process a NetCDF file and export the data to GeoTIFF raster files.

    Parameters:
    cfg: The configuration object containing various settings.
    """

    if not os.path.exists(cfg.TMP_DIR):
        os.makedirs(cfg.TMP_DIR)

    # open NetCDF dataset with xugrid
    ds = xu.open_dataset(cfg.NC_PATH)

    # Log some stats
    logging.info(f"The earliest date in the data is: {ds[cfg.WATER_DEPTH_LAYER]["time"].values.min()}")
    logging.info(f"The latest date in the data is: {ds[cfg.WATER_DEPTH_LAYER]["time"].values.max()}")
    logging.info(f"The number of time steps is: {ds[cfg.WATER_DEPTH_LAYER]["time"].values.shape[0]} (source resolution: {cfg.SOURCE_TIME_RESOLUTION_MINUTES} minutes)")

    # Export the water depth layer to GeoTIFFs
    time_range = range(0, ds[cfg.WATER_DEPTH_LAYER]["time"].values.shape[0], int(cfg.TARGET_TIME_RESOLUTION_MINUTES / cfg.SOURCE_TIME_RESOLUTION_MINUTES))
    logging.info(f"Converting {len(time_range)} time steps to GeoTIFF (target resolution: {cfg.TARGET_TIME_RESOLUTION_MINUTES} minutes)...")
    for t in tqdm(time_range):
        df = ds[cfg.WATER_DEPTH_LAYER].isel(time=t).to_dataframe()
        fname = export_df_to_raster(df, variable_name=cfg.WATER_DEPTH_LAYER, postfix=t, dtype='uint8', cfg=cfg)

    # Export the ground layer to GeoTIFF
    df = ds[cfg.GROUND_LAYER].to_dataframe()
    fname = export_df_to_raster(df, variable_name=cfg.GROUND_LAYER, postfix='ground', dtype='float32', cfg=cfg)
    logging.info(f"GeoTIFF created for ground ({fname})")

    # Extract the class mapping from the waterdepth layer and write to the output object
    class_bounds = ds.class_bounds_hs.to_dict()['data']
    class_values = ds.class_bounds_hs.class_hs.to_dict()['data']
    if len(class_bounds) != len(class_values):
        raise ValueError("The number of class bounds does not match the number of class values.")
    
    out.class_mapping = {class_values[i]: class_bounds[i] for i in range(len(class_bounds))}
   
    # Take the max of the min-max bounds for each class and overwrite the class mapping
    out.class_mapping = {k: float(np.min(v)) for k, v in out.class_mapping.items()} 

    # Add a zero class if the first value is not zero
    if cfg.FIRST_VALUE_IS_ZERO and out.class_mapping[class_values[0]] != 0:
        out.class_mapping[class_values[0]] = 0
    
    print(out.class_mapping)
    # close the dataset
    ds.close()