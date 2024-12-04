# create output dir if not exists
import logging
import math
import os
import subprocess
from osgeo import gdal
from tqdm import tqdm


def get_number(file, chars=None):
    '''
    Get the number from the filename. It is located after the last underscore and before the .tif extension.

    :param file: The filename to get the number from.
    :param chars: The number of 0's to fill the number with. If None, the number will not be filled.
    '''
    n = int(file.split("_")[-1].replace(".tif", ""))
    if chars is not None:
        return str(n).zfill(chars)
    return n

def get_min_max(input):
    '''
    Get the minimum and maximum value of a raster file.

    :param input: The input raster file.
    '''
    ds = gdal.Open(input)
    band = ds.GetRasterBand(1)
    min, max, _, _ = band.ComputeStatistics(False)
    return math.floor(min), math.ceil(max)


def main(cfg, out):

    if not os.path.exists(cfg.OUTPUT_DIR):
        os.makedirs(cfg.OUTPUT_DIR)

    input = f"{cfg.TMP_DIR}/{cfg.SCENARIO}_ground.tif"
    input_4326 = input.replace(".tif", "_4326.tif")

    logging.info("Converting terrain to PNG file...")

    # transform terrain to 4326+4979 (Cesium ellipsoid)
    subprocess.run(["gdalwarp", "-dstnodata", "nan", "-s_srs", "EPSG:28992", "-t_srs", "EPSG:4326+4979", input, input_4326])

    min, max = get_min_max(input_4326)
    if min == 0:
        # set all values of 0 to nan
        subprocess.run(["gdal_calc", "-A", input_4326, f"--outfile={input_4326}", "--calc=numpy.where(A==0, numpy.nan, A)", "--NoDataValue=nan"])
        min, _ = get_min_max(input_4326)
    
    # write min and max to output object
    out.terrain_scaling_min = min
    out.terrain_scaling_max = max

    # get the extent of the terrain file in EPSG:4326 and write to out.ne and out.sw
    ds = gdal.Open(input_4326)
    gt = ds.GetGeoTransform()
    x_min, y_max = gt[0], gt[3]
    x_max = x_min + ds.RasterXSize * gt[1]
    y_min = y_max + ds.RasterYSize * gt[5]
    out.sw = [x_min, y_min]
    out.ne = [x_max, y_max]

    # scale values to 0 - 65535 (full UInt16 range) and export to png
    subprocess.run(["gdal_translate", "-of", "PNG", "-ot", "UInt16", "-scale", f"{min}", f"{max}", "0", "65535", input_4326, f"{cfg.OUTPUT_DIR}/{cfg.OUTPUT_TERRAIN_FILE}"])

    logging.info("Converting water heights to PNG files...")
    tif_files = sorted([file for file in os.listdir(cfg.TMP_DIR) if file.endswith(".tif") and "ground" not in file], key=lambda x: get_number(x))
    for file in tqdm(tif_files):
        # transform to 4326
        subprocess.run(["gdalwarp", "-q", "-s_srs", "EPSG:28992", "-t_srs", "EPSG:4326", f"{cfg.TMP_DIR}/{file}", f"{cfg.TMP_DIR}/{file.replace(".tif", "")}_4326.tif"])
        
        # export to png
        subprocess.run(["gdal_translate", "-q", "-of", "PNG", "-ot", "Byte", f"{cfg.TMP_DIR}/{file.replace(".tif", "")}_4326.tif", f"{cfg.OUTPUT_DIR}/{get_number(file, chars=cfg.N_CHARS_OUTPUT_TIF_FILE)}.png"])

    # remove temporary files
    # subprocess.run(["rm", "-rf", cfg.TMP_DIR])

    # remove .aux.xml files in output directory
    subprocess.run(f"rm -rf {cfg.OUTPUT_DIR}/*.png.aux.xml", shell=True)