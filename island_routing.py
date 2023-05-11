import geopandas as gpd

from methods import *
from settings import *

coast = gpd.read_file('data/raw/land1.geojson')
houses = gpd.read_file('data/raw/houses1.geojson')
houses = houses.to_crs('EPSG:3857')

# Create a spatial index for the polygons
sindex = coast.sindex

# Create a buffer around each polygon with MAXDISTANCE radius
coast["buffer"] = coast.geometry.buffer(MAXDISTANCE)
coast["sea_locked"] = False

lines = build_routes(coast)
graph = build_graph(lines)

# find mainland and remove it from coast df
main_land_id =  coast.iloc[coast.area.idxmax()]["FID"]
main_land = coast[coast["FID"] == main_land_id]     # a df with the mainland as a single row
coast = coast[coast["FID"] != main_land_id]        # all islands except the mainland

sea_locked = get_sealocked_islands(coast, main_land, graph) # all islands that are not reachable by the mainland
# remove all routes that arent reachable from mainland
lines = lines[~lines['start_fid'].isin(sea_locked['FID']) & ~lines['end_fid'].isin(sea_locked['FID'])]
graph = build_graph(lines)  #update the graph accordingly

swim_areas = get_swim_areas(coast, graph, main_land_id)

swim_areas = gpd.overlay(swim_areas, coast, how='symmetric_difference')

land_bound = coast[~coast["FID"].isin(sea_locked["FID"])]   # all islands that are reachable by the mainland

candidates, no_candidates = filter_islands(land_bound,houses)   #candidates = all islands that are reachable by the mainland and are above MINISLANDSIZE and dont have a house/ no_candidates = every other except mainland

plot(candidates, no_candidates, main_land, sea_locked, swim_areas, lines)

def save(gdf,fname):
    gdf_c = gdf.copy()
    gdf_c = gdf_c.drop(columns=["buffer"])
    gdf_c = gdf_c.to_crs(epsg=3857)
    gdf_c.to_file(fname, driver='GeoJSON')

save(candidates,"data/raw/400/candidates1.geojson")
save(coast,"data/raw/400/coast4.geojson")
save(no_candidates,"data/raw/400/no_candidates4.geojson")
save(main_land,"data/raw/400/main_land4.geojson")
save(sea_locked,"data/raw/400/sea_locked4.geojson")

gdf_c = swim_areas.copy()
gdf_c = gdf_c.drop(columns=["buffer","sea_locked","FID","id"])
gdf_c = gdf_c.to_crs(epsg=3857)
gdf_c.to_file("data/raw/400/swim_area4.geojson", driver='GeoJSON')

gdf = gpd.GeoDataFrame(lines, geometry='line')
gdf.to_file("data/raw/400/lines4.shp", driver='ESRI Shapefile')