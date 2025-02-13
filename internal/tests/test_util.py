import time
import util

testdata = {
    "handler": "singaporeRe",
    "values": {
        "fields": [
            {"key":"0","label":"Region"},
            {"key":"1","label":"RegionLabel"},
            {"key":"2","label":"Color"},
            {"key":"3","label":"Geographic Area (sq. km)"},
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
    "mapDBKey": time.time(),
    "persist": "true"
}

def test_sanitize_filename():
    filename = "invalid:/\\*?\"<>|name.txt"
    expected = "invalid_________name.txt"
    result = util.sanitize_filename(filename)
    assert result == expected

def test_get_csv():
    csvstring = util.get_csv(testdata)
    assert csvstring == '''Region,RegionLabel,Color,Geographic Area (sq. km),Population (people)
CENTRAL REGION,CR,#1b9e77,133.0,922580.0
EAST REGION,ER,#e7298a,93.0,685940.0
NORTH REGION,NR,#d95f02,135.0,582330.0
NORTH-EAST REGION,NER,#7570b3,104.0,930860.0
WEST REGION,WR,#66a61e,201.0,922540.0'''
