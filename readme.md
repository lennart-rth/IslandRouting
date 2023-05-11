# IslandRouting

A routing and map-tiles generation script to find possible routes for swimpacking.

The aim is to find a graph of connected islands that are reachable within a certain distance you are capable to swim. This script builds a nxGraph from the islands where you can find shortest path from island A to island B.

Additionaly it marks islands that:
1. finds all neigbouring islands and draws a line between the shortest distances 
2. are not reachable from the mainland
3. finds islands that are inhabited 
    1. e.g there is a house on the island
    2. not appropiate to camp on
4. finds islands that are not inhabited and have a squarearea larger than X
5. finds strongly connected Components in the graph, isnide of you can reach any islands.


# Map legend
1. red boarder: islands that are not suitable to camp on (to small, houses, not reachable from mainland)
2. green boarder: islands that are suitable to camp on (no houses,reachable from mainland)
2. crossed grey: island that are not reachable from mainland
5. blue line: shortest path between neighbouring island (distance in Meters)
6. crossed green: Strong connected Swim areas where you can do "island hopping"

# Usage
## Input 
1. A file with the coatsline including the mainland
2. A file conatining all Houses in the area
## Output
1. All files labeld explained in the "Map legend" as `.geojson` or `.shp` file 

# Overpass Querys

## Get all Houses in a BBox:
```
[out:json];
(
  way["building"]
  ({{bbox}});
);
(._;>;);
out;
```

# Links 
1. Shape Data for coastlines: https://osmdata.openstreetmap.de/data/land-polygons.html
2. Get OSM features into GeoJSON: https://overpass-turbo.eu/

