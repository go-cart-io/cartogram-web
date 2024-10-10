import pytest
import json
import time
import cartogram

def test_process_data():
    testdata = '''Region,Abbreviation,Color,Land Area (km sq.),Population (people)
CENTRAL REGION,CR,,133.0,922580.0
EAST REGION,ER,,93.0,685940.0
NORTH REGION,NR,,135.0,582330.0
NORTH-EAST REGION,NER,,104.0,930860.0
WEST REGION,WR,,201.0,922540.0'''
    datacsv, datasets, is_area_as_base = cartogram.process_data(testdata, "static/cartdata/singaporeRe/original.json")
    print(datacsv)
    assert datasets == [{'label': 'Population', 'datastring': 'name,Data,Color\nCENTRAL REGION,922580.0,\nEAST REGION,685940.0,\nNORTH REGION,582330.0,\nNORTH-EAST REGION,930860.0,\nWEST REGION,922540.0,\n'}]
    assert is_area_as_base == True