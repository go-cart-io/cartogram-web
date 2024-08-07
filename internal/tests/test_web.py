import pytest
import json
import time
from tests.conftest import client

testdata = {
    "handler": "singaporeRe",
    "values": {
        "fields": [
            {"key":"area","label":"Region"},
            {"key":"color","label":"Color"},
            {"key":"1","label":"Population (people)"},
            {"key":"2","label":"Test (unit)"}
        ],
        "items": {
            "1":["CENTRAL REGION","#1b9e77",922580,10],
            "2":["EAST REGION","#e7298a",685940,20],
            "3":["NORTH REGION","#d95f02",582330,30],
            "4":["NORTH-EAST REGION","#7570b3",930860,40],
            "5":["WEST REGION","#66a61e",922540,50]
        }
    },
    "stringKey": time.time(),
    "persist":"true"
}

def test_cartogram_post(client):
    response = client.post("/api/v1/cartogram", data={"data": json.dumps(testdata)})
    print(response.data)
    assert response.status_code == 200