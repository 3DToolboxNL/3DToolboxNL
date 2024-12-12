# NetCDF To FloodLayer

The Leia viewer has the ability to visualize flooding scenario's, based on a specific layer type, the FloodLayer. 
This tool creates a FloodLayer from a NetCDF file, which some hydrological models output. The core of the FloodLayer is a set of PNG images that describe the flood depth at each time point and a single PNG image that describes the terrain in the same area. The relevant metadata is stored in `layer.json`. 

## FloodLayer contents

The FloodLayer `layer.json` file has the following structure:

```json
{
    "name": "name",
    "sw": [
        3.6784870348225507,
        51.61105200421035
    ],
    "ne": [
        4.105647104708608,
        51.74730720991563
    ],
    "terrain": {
        "scaling": {
            "min": 41.0,
            "max": 64.0
        },
        "path": "terrain.png"
    },
    "flood_planes": {
        "class_mapping": {
            "0": 0.0,
            "1": 0.02,
            "2": 0.1,
            "3": 0.2,
            "4": 0.3,
            "5": 0.4,
            ...
        },
        "paths": [
            "00000.png",
            "00001.png",
            ...
        ]
    }
}
```

The `sw` and `ne` properties describe the south-west and north-east corners of the layer, which is needed to georeference the data (sent to the viewer as PNG-images). 

The `terrain` property describes the terrain data, where the scaling describes how to scale the integer color values (0-65535, UInt16) in the PNG to height values, using a linear min-max scaling. 

The `flood_planes` property describes a `class_mapping`, which maps integer PNG values (0-255, UInt8) to flood depth values (float). The `paths` describe the locations of the PNGs with flood depth information. 

## Usage

### Dependencies
This project requires a Docker installation.

### Configuration
Configure the project by editing `config.py`. Make sure to at least fill in SCENARIO, SUB_PATH and NC_PATH.

### Running
Run `python3 main.py` to start the conversion. After the run (which should take about 2 minutes for each NetCDF file), you will find an output folder with the FloodLayer contents.
