'''
Configuration object used throughout the application.
'''


class Config:

    # directories
    OUTPUT_DIR = "output"
    TMP_DIR = "tmp"

    # input
    SCENARIO = '[SCENARIO_NAME]'
    SUB_PATH = '[RELATIVE_PATH_TO_NC_FILE_FROM_SCENARIO_FOLDER]'
    NC_PATH = f'[PATH_TO_SCENARIO_FOLDER]/{SCENARIO}/{SUB_PATH}'
    WATER_DEPTH_LAYER = "Mesh2d_waterdepth"
    GROUND_LAYER = "Mesh2d_flowelem_bl"
    PIXEL_SIZE = 50
    SOURCE_TIME_RESOLUTION_MINUTES = 10
    TARGET_TIME_RESOLUTION_MINUTES = 60
    NODATA_VALUE = 0
    FIRST_VALUE_IS_ZERO = True

    # output
    OUTPUT_TERRAIN_FILE = "terrain.png"
    N_CHARS_OUTPUT_TIF_FILE = 5