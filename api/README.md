# FastAPI GeoJSON Trips Application

This is a FastAPI application that generates trips based on the provided GeoJSON data.

## Installation

To install the dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Running the Application

To run the application, use the following command:

```bash
uvicorn app.main:app --reload
```

This will start the FastAPI application on your localhost.

## Usage

To use the trips functionality, send a POST request to the `/trips` endpoint with a GeoJSON object in the request body. The GeoJSON object should contain grid data with population density and zonification values.

The application will return a list of trips generated based on the provided GeoJSON data.

## Testing

To run the tests, use the following command:

```bash
pytest
```

This will run all the tests in the `tests` directory and display the results.