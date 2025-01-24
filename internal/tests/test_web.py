import json
import time
import csv
from tests.conftest import client

def test_cartogram_post(client):
    testdata = {
        "title": '',
        "handler": "singaporeRe",
        "scheme": "pastel1",
        "values": {
            "fields": [
                {"key":"0","label":"Region"},
                {"key":"1","label":"RegionLabel"},
                {"key":"2","label":"Color"},
                {"key":"3","label":"Geographic Area (sq. km)"},
                {"key":"4","label":"Population (people)"},
                {"key":"5","label":"Number of Landed Properties (Landed Properties)"}
            ],
            "items": {
                "1":["CENTRAL REGION","CR","#1b9e77",133.0,922580.0,84950],
                "2":["EAST REGION","ER","#e7298a",93.0,685940.0,58390],
                "3":["NORTH REGION","NR","#d95f02",135.0,582330.0,10990],
                "4":["NORTH-EAST REGION","NER","#7570b3",104.0,930860.0,76100],
                "5":["WEST REGION","WR","#66a61e",201.0,922540.0,20960]
            }
        },
        "mapDBKey": time.time(),
        "persist": "true"
    }

    response = client.post("/api/v1/cartogram", data={"data": json.dumps(testdata)})
    print(response.data)
    assert response.status_code == 200

def test_cartogram_post_world(client):
    with open('static/cartdata/world/data.csv', 'r') as file:
        csv_string = file.read()

    testdata = {
        "title": '',
        "handler": "world",
        "scheme": "pastel1",
        "csv": csv_string,
        "mapDBKey": time.time(),
        "persist": "true"
    }

    response = client.post("/api/v1/cartogram", data={"data": json.dumps(testdata)})
    print(response.data)
    assert response.status_code == 200

def test_cartogram_post_inset(client):
    key = time.time()

    with open("tests/data/usa_by_state_since_1959.csv", 'r') as file:
        csv_string = file.read()
    with open("tests/data/usa_by_state_since_1959.geojson", 'rb') as file:
        data = {'file': (file, 'filename')}        
        response = client.post(f"/api/v1/cartogram/preprocess/{key}", data=data, content_type='multipart/form-data')

    testdata = {
        "title": "",
        "handler": "custom",
        "scheme": "pastel1",
        "csv": csv_string,
        "mapDBKey": key,
        "persist": "true"
    }

    response = client.post("/api/v1/cartogram", data={"data": json.dumps(testdata)})
    print(response.data)
    assert response.status_code == 200

def test_cleanup(client):
    response = client.get("/cleanup")
    print(response)