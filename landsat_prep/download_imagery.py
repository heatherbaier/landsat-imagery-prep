from datetime import date, timedelta
from joblib import Parallel, delayed
from functools import partial
import geopandas as gpd
import multiprocessing
import pandas as pd
import numpy as np
import argparse
import calendar
import datetime
import requests
import shapely
import pyproj
import shutil
import ee
import os

from .helpers import *


def download_imagery(geom, shapeID, ic, dates, imagery_dir, bands, scale = 30, cloud_free = False, im = False, v = True):
    
    ee.Initialize()

    cur_directory = os.path.join(imagery_dir, shapeID)
    
    if not os.path.isdir(cur_directory):
        os.makedirs(cur_directory)

    try:

        cur_shp = convert_to_ee_feature(geom)

        if im:
#             if bands == None:
            m = ee.Image(ic)
            if bands is not None:
                m = m.select(bands)
        elif not im:
            if dates is not None:
                imagery = ee.ImageCollection(ic).filterDate(dates[0], dates[1]).filterBounds(cur_shp)
            else:
                imagery = ee.ImageCollection(ic).filterBounds(cur_shp)
            if v:
                print(shapeID, " has ", imagery.size().getInfo(), " images available between ", " and ".join(dates))
            if cloud_free:
                m = ee.Algorithms.Landsat.simpleComposite(imagery).select(bands)
            elif not cloud_free:
                m = imagery.select(bands).median()               

        m = m.clip(cur_shp)

        region = ee.Geometry.Rectangle(list(geom.bounds))
        fname = cur_directory + "/" + shapeID + "_" + "_".join(dates) + ".zip"

        # Get the URL download link
        link = m.getDownloadURL({
                'name': shapeID + "_" + "_".join(dates),
                'crs': 'EPSG:4326',
                'fileFormat': 'GeoTIFF',
                'region': region,
                'scale': scale,
                'maxPixels': 1e9
        })

        r = requests.get(link, allow_redirects = True)
        open(fname, 'wb').write(r.content)

    except Exception as e:

        print(e)

