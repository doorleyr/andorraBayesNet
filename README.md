# Andorra PGM transport model
Estimates travel demand and traffic in Andorra based on combination of telecom data and limited traffic counts using a Gaussian Bayesian Network model. A JS front end maps the results over time.

## Overview

This repo contains 3 main components:

### 1. Model Calibration
The andorraPGMnet.py script reads the pre-prepared hourly "naive" O-D matrices (estimated from RNC telecom data) and some hourly 
traffic count data for a number of junctions in Andorra. It uses the combination of these data sources to produce calibrated 
O-D matrices and traffic volume estimates for every road and each hour. There is no need to run this script as the results are 
already in the data/results folder. This process in described in more detail in the Methodology section.

### 2. Flask Server
The appSocket.py script reads the results of the model calibration, produces geojson files and serves them to the javascript 
front end.

### 3. Projection Mapping
The javascript front end maps the results of the analysis using a keystonable [Mapbox](https://www.mapbox.com/) map. This projection mapping uses the excellent [MapTasticJS lib](https://github.com/glowbox/maptasticjs).

## Running

In order to run the visualisation:

1. Clone the repository
2. Run the appSocket.py script in a terminal
3. Open a web browser and navigate to http://localhost:5000/

## Methodology
This framework deals with the problem of estimating travel patterns in a road network based on data whch is incomplete and/or biased. 
An initial O-D matrix is estimated based on the available telecoms data. This O-D matrix is based on incomplete observations and has inherent biases.
However, traffic volume counts provide a reliable source of information in relation to the traffic on a subset of roads. 
A Bayesian network model is therefore constructed to represent the relationships betwen the O-D flows and the traffic volumes. 
The Bayesian network model allows the available evidence on traffic volumes to update our estimates about the O-D flows through probabilistic relationships.

By combining the Bayesian network approach with a network equilibrium model (stochastic user equilibrium), the effects of traffic congestion are also taken into account.

This approach is inspired by Castillo's work on [predicting traffic flows using Bayesian networks](https://www.sciencedirect.com/science/article/pii/S0191261507001300). 
