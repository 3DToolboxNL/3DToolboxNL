# 3D Buildings from footprints

In some cases, there is no detailed 3D data available for buildings, but footprints and height values (base height and roof height) can be obtained. This Python-based tool can read this data from a set of input files and create a single 3D Tiles dataset with the 3D buildings (extruded to the roof height). 

## Usage

### Dependencies
This project requires a Docker installation.

### Configuration
Configure the project by editing `main.py` under "0. CONFIGURATION". This configuration depends largely on the input data. In this implementation, the input data is a set of KML files that each represent a tile with many buildings. Make sure to add your input data to a `data` folder in the root. 

If your input data is not a set of KML files, you will have to adapt the script to fit your input format. This is (hopefully!) relatively easy because the script uses ogr2ogr. 

### Running
Run `python3 main.py` to start the conversion. The script will start a PostgreSQL docker container to do the dataprocessing in. The data also needs to be in a Postgres database for the creation of 3D Tiles using [pg2b3dm](https://github.com/Geodan/pg2b3dm).

After the run, you will find an output folder with the 3D Tiles contents. The script will automatically start a python server that serves `index.html`, which loads Cesium to display the 3D Tiles.