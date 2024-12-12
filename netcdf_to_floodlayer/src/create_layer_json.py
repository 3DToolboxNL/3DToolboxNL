import json
import os


def main(cfg, out):
    '''
    Create a JSON file that describes the scenario for the web application.
    :param cfg: Configuration object
    :param out: Output object
    '''

    # Read contents of output directory
    outputFiles = os.listdir(cfg.OUTPUT_DIR)

    doc = {
        "name": cfg.SCENARIO,
        "sw": out.sw,
        "ne": out.ne,
        "terrain": {
            "scaling": {
                "min": float(out.terrain_scaling_min),
                "max": float(out.terrain_scaling_max)
            },
            "path": cfg.OUTPUT_TERRAIN_FILE
        },
        "flood_planes": {
            "class_mapping": out.class_mapping,
            "paths": sorted([path for path in outputFiles if path.endswith('png') and not path == cfg.OUTPUT_TERRAIN_FILE])
        }
    }

    with open(os.path.join(cfg.OUTPUT_DIR, 'layer.json'), 'w') as f:
        json.dump(doc, f, indent=4)