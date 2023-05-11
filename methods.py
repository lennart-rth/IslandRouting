import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points, unary_union
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from settings import *

def shorten_line(line):
    # Convert the LineString to a Shapely object
    shapely_line = LineString(line)

    # Get the unit vector from the start to end point
    start_point = np.array(shapely_line.coords[0])
    end_point = np.array(shapely_line.coords[-1])

    vector = end_point - start_point

    if vector[0] != 0 and vector[1] != 0: 
        unit_vector = vector / np.linalg.norm(vector)
    
        # Get the displacement vector
        displacement = unit_vector * (line.length*0.01)

        # Add the displacement vector to the start and end points
        new_start_point = Point(start_point + displacement)
        new_end_point = Point(end_point - displacement)

        # Create a new LineString with the new points
        new_line = LineString([new_start_point.coords[0], new_end_point.coords[0]])
        return new_line
    else:
        return None

def build_routes(coast):
    lines_list = []
    # Iterate over each polygon and find its neighbors
    for index, polygon in coast.iterrows():

        # Get the neighbors that intersect the buffer
        neighbors = coast[coast.intersects(polygon.buffer)].drop(index)

        # Iterate over the neighbors and find the shortest distance
        for _, neighbor in neighbors.iterrows():
            point_1, point_2 = nearest_points(polygon.geometry, neighbor.geometry)

            line = LineString([point_1, point_2])
            # print(line, line.length)

            shorter_line = shorten_line(line)

            if not shorter_line is None:
                intersects = coast.intersects(shorter_line)

                if not intersects.any():
                    _line = line
                    start= polygon["FID"]
                    end=neighbor["FID"]
                    weight=int(line.length/2)
                    lines_list.append([_line, start, end, weight])

    lines = pd.DataFrame(lines_list,columns=["line","start_fid","end_fid","weight"])

    # now remove any duplicate lines. (e.g. line from id 2 to 4 -> remove line from 4 to 2)
    lines['start_end'] = lines.apply(lambda x: '-'.join(sorted([str(x['start_fid']), str(x['end_fid'])])), axis=1)
    df_unique = lines.drop_duplicates(subset='start_end')
    lines = df_unique.drop(columns='start_end')

    return lines

def filter_islands(coast,houses):
    # only islands that dont have houses on them
    df_joined = gpd.sjoin(coast, houses, predicate='contains')
    candidates = coast[~coast["FID"].isin(df_joined["FID"])]

    # only islands with area greater than ...
    candidates = candidates[candidates.area >= MINISLANDSIZE]

    # all islands you cant sleep on
    no_candidates = coast[~coast['FID'].isin(candidates["FID"])]

    return candidates, no_candidates

def build_graph(lines):
    G = nx.from_pandas_edgelist(lines, source='start_fid', target='end_fid', edge_attr='weight')
    return G

def get_sealocked_islands(coast,main_land, graph):
    mainland_id = main_land["FID"].values[0]

    def check_sea_lock(row):
        end = row["FID"]
        if graph.has_node(mainland_id) and graph.has_node(end):
            return not nx.has_path(graph, mainland_id, end)     #True if an island is not reachable from the mainland
        else:
            return True
    
    coast["sea_locked"] = coast.apply(check_sea_lock, axis=1)
    sea_locked = coast[coast["sea_locked"] == True]

    return sea_locked

def get_swim_areas(coast, graph, main_land_id):
    # add all nodes except the one to be removed
    graph_without_mainland = nx.Graph()
    graph_without_mainland.add_nodes_from([node for node in graph.nodes() if node != main_land_id])

    # add all edges except those involving the node to be removed
    graph_without_mainland.add_edges_from([(u, v) for u, v in graph.edges() if u != main_land_id and v != main_land_id])
    swim_areas = list(nx.connected_components(graph_without_mainland))

    swim_area_df = []
    for area in swim_areas:
        area = list(area)
        area_df = coast[coast["FID"].isin(area)]
        swim_area_df.append(area_df)

    hulls = []
    for df in swim_area_df:
        convex_hull = unary_union(df.geometry).convex_hull
        hulls.append(convex_hull)

    # create a new GeoDataFrame from the merged convex hulls
    df = gpd.GeoDataFrame(geometry=hulls,crs="EPSG:3857")
    return df

def plot(candidates, no_candidates, main_land, sea_locked, swim_area, lines):
    fig, ax = plt.subplots(figsize=(10,10))
    no_candidates.plot(ax=ax, facecolor="red")
    candidates.plot(ax=ax,facecolor="green")
    main_land.plot(ax=ax, facecolor="#987654")
    sea_locked.plot(ax=ax, facecolor="grey")

    swim_area = swim_area.reset_index()
    swim_area.plot(column="index", cmap="Set3", ax=ax, alpha=0.5, edgecolor="green")
    
    for line in lines["line"]:
        x,y = line.xy
        ax.plot(x,y, color='blue')

    plt.show()