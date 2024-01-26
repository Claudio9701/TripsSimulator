from typing import Optional
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import osmnx as ox
import time
import json
from datetime import datetime
from fastapi.encoders import jsonable_encoder

# from pandarallel import pandarallel
from models.geojson import GeoJSON

# Get number of available cores
cores = os.cpu_count()
# pandarallel.initialize(progress_bar=True, nb_workers=cores)

from tqdm import tqdm

tqdm.pandas()


def generate_single_trip(
    G: ox.graph, nodes: gpd.GeoDataFrame, route: list, start_time: datetime
):
    """
    Generate a trip with OSMnx using the route and the start time.

    Parameters
    ----------
    G : ox.graph
        Graph to use for routing.
    nodes : gpd.GeoDataFrame
        GeoDataFrame with the nodes of the graph.
    route : list
        List of nodes that represent the route.
    start_time : datetime
        Start time of the trip.

    """
    if (route_len := len(route)) <= 1:
        return {}

    # Get route information
    route_gdf = ox.utils_graph.route_to_gdf(G, route, "travel_time")
    # Build the timestamp for each route step
    time_deltas = pd.to_timedelta(route_gdf["travel_time"].cumsum(), unit="s")
    timestamps_series = (time_deltas + start_time).astype("int64") // 10**9
    timestamps = timestamps_series.values.tolist()
    timestamps.insert(
        0, int(datetime.timestamp(start_time))
    )  # Add origin to match route length

    assert route_len == len(
        timestamps
    ), "Route and timestamps must have the same length"

    # Get the coordinates of the nodes in the route
    route_nodes = nodes.loc[route]

    return {
        "start_time": timestamps[0],
        "path": route_nodes[["x", "y"]].values.tolist(),
        "timestamps": timestamps,
    }


def generate_trips(
    data: GeoJSON,
    population_size: Optional[int] = None,
    trips_per_person: int = 2,
    departure_hours: tuple = (6, 9),
    return_hours: tuple = (17, 20),
):
    print("Reading GeoJSON data into GeoDataFrame")
    json_compatible_data = jsonable_encoder(data)
    data = gpd.read_file(json.dumps(json_compatible_data))
    print("GeoDataFrame created")

    # Set simulation parameters
    if population_size is None:
        population_size = data["denspob"].sum().round().astype(int)

    origins = data[data["desc_zoni"] == "RESIDENCIAL"].geometry.centroid  # Home
    destinations = data[data["desc_zoni"] == "COMERCIAL"].geometry.centroid  # Work

    total_trips = population_size * trips_per_person
    departure_hour = np.random.normal(
        sum(departure_hours) / 2,
        1,
        population_size,
    ).round(2)
    return_hour = np.random.normal(
        sum(return_hours) / 2,
        1,
        population_size,
    ).round(2)

    # Log simulation parameters
    print(
        f"""
    Simulation Parameters:
    ---------------------      
    Population size: {population_size}
    Origins: {origins.shape[0]}
    Destinations: {destinations.shape[0]}
    Total trips: {total_trips}
    Departure hour range: [{departure_hour.min()} - {departure_hour.max()}]
    Return hour range: [{return_hour.min()} - {return_hour.max()}]
    """
    )

    # Download the Graph for the data area + 1km buffer using OSMnx
    buffer_diameter = 0.01
    area_of_interest = data.geometry.unary_union.buffer(buffer_diameter / 2)

    start = time.time()
    G = ox.graph_from_polygon(area_of_interest, network_type="all")
    print(f"Downloaded graph in {time.time() - start} seconds")

    # Prepare the graph for routing

    # impute speed on all edges missing data
    hwy_speeds = {"residential": 35, "secondary": 50, "tertiary": 60}
    G = ox.add_edge_speeds(G, hwy_speeds)

    # calculate travel time (seconds) for all edges
    G = ox.add_edge_travel_times(G)

    # Calculate the nearest nodes to the origins and destinations
    start = time.time()
    origins_nearest_nodes = pd.Series(ox.nearest_nodes(G, origins.x, origins.y))
    destinations_nearest_nodes = pd.Series(
        ox.nearest_nodes(G, destinations.x, destinations.y)
    )
    print(f"Found nearest nodes in {time.time() - start} seconds")

    # Stratified sampling origins using the population density
    start = time.time()
    sampled_origins = origins_nearest_nodes.sample(
        weights=data[data["desc_zoni"] == "RESIDENCIAL"]["denspob"],
        n=population_size,
        replace=True,
    )
    # Random sampling destinations
    sampled_destinations = destinations_nearest_nodes.sample(
        n=population_size, replace=True
    )
    print(f"Origins and destinations sampled in {time.time() - start} seconds")

    # Get the graph node to query coordinates after routing
    nodes = G.nodes()
    nodes = pd.DataFrame.from_dict(nodes, orient="index")
    nodes = nodes.rename(columns={0: "x", 1: "y"})
    nodes.index.name = "osmid"
    # Create a GeoDataFrame from the nodes
    nodes = gpd.GeoDataFrame(nodes, geometry=gpd.points_from_xy(nodes.x, nodes.y))
    nodes.head()

    # Create a dummy pd.Series to use pandarallel
    indexs_series = pd.Series(range(population_size))
    # Convert the departure and return times to datetime
    today = datetime.today()
    start_date = datetime(today.year, today.month, today.day)
    work_start_dts = pd.to_timedelta(departure_hour, unit="h") + start_date
    home_start_dts = pd.to_timedelta(return_hour, unit="h") + start_date

    # Generate the trips to work and to home
    batch_size = 500
    num_batches = (population_size + batch_size - 1) // batch_size

    for batch_num in tqdm(range(num_batches)):
        start_index = batch_num * batch_size
        end_index = min((batch_num + 1) * batch_size, total_trips)

        batch_data = indexs_series.iloc[start_index:end_index]

        # Get the fastest route using OSMnx
        start = time.time()
        route_to_work = ox.shortest_path(
            G,
            sampled_origins[start_index:end_index],
            sampled_destinations[start_index:end_index],
            weight="travel_time",
            cpus=cores,
        )
        route_to_home = ox.shortest_path(
            G,
            sampled_destinations[start_index:end_index],
            sampled_origins[start_index:end_index],
            weight="travel_time",
            cpus=cores,
        )
        print(f"Found fastest routes in {time.time() - start} seconds")

        # Generate the trips to work and to home
        work_trips = [
            generate_single_trip(
                G, nodes, route=route_to_work[i], start_time=work_start_dts[batch_index]
            )
            for i, batch_index in enumerate(batch_data.index)
        ]
        work_trips_df = pd.DataFrame.from_records(work_trips, index=batch_data.index)
        work_trips_df.index.name = "person_id"
        work_trips_df["type"] = "to_work"

        home_trips = [
            generate_single_trip(
                G, nodes, route=route_to_home[i], start_time=home_start_dts[batch_index]
            )
            for i, batch_index in enumerate(batch_data.index)
        ]
        home_trips_df = pd.DataFrame.from_records(home_trips, index=batch_data.index)
        home_trips_df.index.name = "person_id"
        home_trips_df["type"] = "to_home"

        all_trips_df = pd.concat([work_trips_df, home_trips_df])
        print(all_trips_df.shape)
        print(all_trips_df.columns)
        all_trips_df.sort_values(by=["person_id", "start_time"], inplace=True)

        # Remove trips with no path
        clean_trips_df = all_trips_df.dropna()

        print(clean_trips_df.columns)

        yield clean_trips_df.to_json(orient="records") + "\n"
