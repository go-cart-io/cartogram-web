import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test29"

    def get_gen_file(self):
        return "{}/test29.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 49:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00022135,
2,{},E00021852,
3,{},E00021851,
4,{},E00021859,
5,{},E00022018,
6,{},E00022222,
7,{},E00021842,
8,{},E00022195,
9,{},E00022137,
10,{},E00022128,
11,{},E00022131,
12,{},E00022140,
13,{},E00022122,
14,{},E00022221,
15,{},E00022139,
16,{},E00022134,
17,{},E00022130,
18,{},E00022143,
19,{},E00022220,
20,{},E00022214,
21,{},E00022042,
22,{},E00022129,
23,{},E00022133,
24,{},E00022136,
25,{},E00022123,
26,{},E00021855,
27,{},E00021840,
28,{},E00022120,
29,{},E00022149,
30,{},E00022132,
31,{},E00021853,
32,{},E00022141,
33,{},E00022218,
34,{},E00021857,
35,{},E00022138,
36,{},E00022127,
37,{},E00021841,
38,{},E00022194,
39,{},E00022142,
40,{},E00022217,
41,{},E00022118,
42,{},E00022216,
43,{},E00022148,
44,{},E00022041,
45,{},E00022119,
46,{},E00022145,
47,{},E00021854,
48,{},E00022021,
49,{},E00022219,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00022135","E00021852","E00021851","E00021859","E00022018","E00022222","E00021842","E00022195","E00022137","E00022128","E00022131","E00022140","E00022122","E00022221","E00022139","E00022134","E00022130","E00022143","E00022220","E00022214","E00022042","E00022129","E00022133","E00022136","E00022123","E00021855","E00021840","E00022120","E00022149","E00022132","E00021853","E00022141","E00022218","E00021857","E00022138","E00022127","E00021841","E00022194","E00022142","E00022217","E00022118","E00022216","E00022148","E00022041","E00022119","E00022145","E00021854","E00022021","E00022219"], [0.0 for i in range(0,49)], {"E00022135":"1","E00021852":"2","E00021851":"3","E00021859":"4","E00022018":"5","E00022222":"6","E00021842":"7","E00022195":"8","E00022137":"9","E00022128":"10","E00022131":"11","E00022140":"12","E00022122":"13","E00022221":"14","E00022139":"15","E00022134":"16","E00022130":"17","E00022143":"18","E00022220":"19","E00022214":"20","E00022042":"21","E00022129":"22","E00022133":"23","E00022136":"24","E00022123":"25","E00021855":"26","E00021840":"27","E00022120":"28","E00022149":"29","E00022132":"30","E00021853":"31","E00022141":"32","E00022218":"33","E00021857":"34","E00022138":"35","E00022127":"36","E00021841":"37","E00022194":"38","E00022142":"39","E00022217":"40","E00022118":"41","E00022216":"42","E00022148":"43","E00022041":"44","E00022119":"45","E00022145":"46","E00021854":"47","E00022021":"48","E00022219":"49"})