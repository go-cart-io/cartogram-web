import pytest
import json
import time
from tests.conftest import client

testdata = {
    "handler": "singaporeRe",
    "values": {
        "fields": [
            {"key":"0","label":"Region"},
            {"key":"1","label":"Abbreviation"},
            {"key":"2","label":"Color"},
            {"key":"3","label":"Land Area (km sq.)"},
            {"key":"4","label":"Population (people)"}            
        ],
        "items": {
            "1":["CENTRAL REGION","CR","#1b9e77",133.0,922580.0],
            "2":["EAST REGION","ER","#e7298a",93.0,685940.0],
            "3":["NORTH REGION","NR","#d95f02",135.0,582330.0],
            "4":["NORTH-EAST REGION","NER","#7570b3",104.0,930860.0],
            "5":["WEST REGION","WR","#66a61e",201.0,922540.0]
        }
    },
    "stringKey": time.time(),
    "persist": "true"
}

def test_cartogram_post(client):
    response = client.post("/api/v1/cartogram", data={"data": json.dumps(testdata)})
    print(response.data)
    assert response.status_code == 200