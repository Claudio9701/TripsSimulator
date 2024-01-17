# Simple Trips Simulation using OSMnx

To build a a simple Trips simulation we need to set a few initial parameters:

- Number of people in the simulation, we will use the population density to calculate this.
- Number of trips per person, we will take the asumption that each person makes 2 trips per day (to and from work)
- Where people live and where they work, we will use the zonification layer to define this:
    - Residential zones -> people's homes
    - Commercial zones -> people's work
- Schedule of the trips, we will use normal probability distributions to define this. We will use the following parameters:
    - Departure time: 6am to 8am
    - Return time: 5pm to 7pm

## What data will be used ?

The data used is a grid of a portion of the city of Lima, Peru. The grid is composed of ~1km x 1km cells and each cell has the following information:

- Population density (people per km2) from Meta's High Resolution Population Density Maps
- Zonification (residential, commercial, etc.) from the Metropolitan Planning Institute of Lima (IMP)

<img src="images/dense_zone_layers.png" height="391">

## How the simulation works ?

The simulation will be based on the following steps:

1. Assign each person a home and a work location based on the density and zonification layers
2. Assign each person a departure and return time based on a normal distribution
3. Calculate the fastest route between the home and work locations and viceversa using the OSMnx library as routing engine

## What is the output of the simulation ?

The output of the simulation will be a list of trips with the following information:

- Person ID: integer
- Start time: unix timestamp
- Type: string ("to_home" or "to_work")
- Path: list of coordinates (lat, lon)
- Timestamps: list of unix timestamps (one for each coordinate)

Visualization of trips in Kepler.gl:

![Simulation](images/viz.gif)