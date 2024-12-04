import fnmatch
import subprocess
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# ======== 0. CONFIGURATION ========
# Add password to environment
os.environ['PGPASSWORD'] = 'postgres'
# File pattern to match for kml files
KML_FILE_PATTERN = 'GRBGebL1D2_*.kml'
# Postgres table to write data to
TABLE = 'public.buildings'
# Batch size for merging kml input files
BATCH_SIZE = 3000
# Column to use for the base height
BASE_HEIGHT_COLUMN = 'h_dtm_min'
# Column to use for extrusion
EXTRUSION_COLUMN = 'hn_p99'
# Columns to drop
COLUMNS_TO_DROP = ['description', 'timestamp', 'begin', 'end', 'tessellate', 'extrude', 'visibility', 'draworder', 'icon', 'geometry']
# Attributes to include in the 3D Tiles
ATTRIBUTES = ['name', 'altitudemode', 'grb_oidn', 'grb_uidn', 'entiteit', 'type', 'lbltype', 'datum_grb', 'datum_lid', 'straatnmid', 'straatnm', 'niscode', 'gemeente', 'postcode', 'hnrlabel']

# ======== 1. DATABASE SETUP ========
try:
    # Run postgis container (silent)
    subprocess.run('docker run -d -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e PROJ_NETWORK=ON -p 5439:5432 postgis/postgis:16-master', 
                            shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print('Started postgis container')
    # Wait for postgis container to start
    subprocess.run('sleep 5', shell=True)
except subprocess.CalledProcessError as e:
    print('Postgis container already running')



Drop TABLE if exists
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"DROP TABLE IF EXISTS {TABLE}"])


# ======== 2. DATA PREPARATION ========

# List all kml files in ./data
kml_files = [fn for fn in os.listdir('./data') if fnmatch.fnmatch(fn, KML_FILE_PATTERN)]

# Workaround to make GDAL read the kml files well
# Inspect if first kml file contains 'kml:' and if so, remove it
with open(f'./data/{kml_files[0]}', 'r') as file:
    filedata = file.read()
    if 'kml:' in filedata:
        print('kml: found in first kml file')
        # open each kml file in ./data and replace 'kml:' with ''
        for kml in tqdm(kml_files):
            with open(f'./data/{kml}', 'r') as file:
                filedata = file.read()
                filedata = filedata.replace('kml:', '')
            with open(f'./data/{kml}', 'w') as file:
                file.write(filedata)
    else:
        print('kml: not found in first kml file')


# ======== 3. UPLOAD TO DATABASE ========
# create batches and merge them into an sqlite database with ogrmerge
kml_batches = [['data/' + kml_file for kml_file in kml_files[i:i+BATCH_SIZE]] for i in range(0, len(kml_files), BATCH_SIZE)]
# remove tmp folder if it exists
subprocess.run(["rm", "-rf", "./tmp"])
# create a tmp folder to store the merged kml files
subprocess.run(["mkdir", "./tmp"])
for i, kml_batch in tqdm(enumerate(kml_batches)):
    subprocess.run(["ogrmerge", "-single", "-o", f"./tmp/{i}.sqlite", *kml_batch])
    print("Merged ", len(kml_batch), " files into ", f"./tmp/{i}.sqlite")

    # import file into postgres database with ogr2ogr
    subprocess.run(["ogr2ogr", 
                    "-f", "PostgreSQL", 
                    "PG:host=localhost port=5439 user=postgres dbname=postgres password=postgres", 
                    f"./tmp/{i}.sqlite",
                    "-nln", TABLE])
    print("Uploaded ", len(kml_batch), f" files to database ({TABLE})")


# ======== 4. BUILDING EXTRUSION ========
# Create extension postgis_sfcgal
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", "CREATE EXTENSION postgis_sfcgal"])

# Evaluate validity of the geometries and fix if invalid
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"UPDATE {TABLE} SET geometry = ST_MakeValid(geometry) WHERE NOT ST_IsValid(geometry)"])

# Set column type to 'geometry'
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"ALTER TABLE {TABLE} ALTER COLUMN geometry TYPE geometry"])

# Transform coordinates from EPSG:4326 to EPSG:31370
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"UPDATE {TABLE} SET geometry = ST_Transform(geometry, 31370)"])

# Add a geom column with extruded geometry
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"ALTER TABLE {TABLE} ADD COLUMN geom geometry"])

# Convert the geometry to a 3D geometry
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"UPDATE {TABLE} SET geom = ST_Force3D(geometry, {BASE_HEIGHT_COLUMN})"])

# Update the geom column with extruded geometry
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"UPDATE {TABLE} SET geom = CG_Extrude(geom, 0, 0, {EXTRUSION_COLUMN})"])

# Transform the geometry from 6190 to 4979
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"UPDATE {TABLE} SET geom = ST_Transform(ST_SetSRID(geom, 6190), 4979)"])

# Create index on geometry
subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"CREATE INDEX ON {TABLE} USING gist(st_centroid(st_envelope(geom)))"])

# Drop columns
for column in COLUMNS_TO_DROP:
    subprocess.run(["psql", "-h", "localhost", "-p", "5439", "-U", "postgres", "-d", "postgres", "-c", f"ALTER TABLE {TABLE} DROP COLUMN \"{column}\""])

# Run pg2b3dm to make 3D Tiles
subprocess.run(f'docker run -v $(pwd)/output:/app/output -it --network="host" geodan/pg2b3dm -h localhost -p 5439 -U postgres -d postgres -t {TABLE} -a {','.join(ATTRIBUTES)} --use_implicit_tiling false -o ./output -c geom --create_gltf false', shell=True)

# Run python server
subprocess.run('python -m http.server 8000', shell=True)

