from typing import List
from fastapi.testclient import TestClient
from app.main import app
from app.models.geojson import GeoJSON, Trips

client = TestClient(app)


def test_generate_trips():
    # Read test data
    with open("./tests/data/grid_data.geojson") as f:
        geojson = GeoJSON.parse_raw(f.read())

    # Send a POST request to the generate_trips endpoint
    simulation_params = {
        "population_size": None,
        "trips_per_person": 2,
    }
    response = client.post("/trips/", json=geojson.dict(), params=simulation_params)

    # Check that the status code is 200
    assert response.status_code == 200

    response_json = response.json()
    response_element = response_json[0]

    # Check that the response is a JSON object
    assert isinstance(response_json, list)

    # Check that the response contains the expected number of elements
    if simulation_params["population_size"]:
        assert (
            len(response_json)
            == simulation_params["population_size"]
            * simulation_params["trips_per_person"]
        )

    # Check that the response contains a 'path' key
    assert "path" in response_element and isinstance(response_element["path"], list)

    # Check that the response contains a 'timestamps' key
    assert "timestamps" in response_element and isinstance(
        response_element["timestamps"], list
    )

    # Check that the response contains a 'start_time' key
    assert "start_time" in response_element and isinstance(
        response_element["start_time"], int
    )

    # Check that the response contains a 'type' key
    assert "type" in response_element and isinstance(response_element["type"], str)
