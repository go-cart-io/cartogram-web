import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test117"

    def get_gen_file(self):
        return "{}/test117.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 48:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00009644,
2,{},E00009665,
3,{},E00009658,
4,{},E00009498,
5,{},E00009661,
6,{},E00009485,
7,{},E00009487,
8,{},E00009673,
9,{},E00009671,
10,{},E00009646,
11,{},E00009647,
12,{},E00009482,
13,{},E00009679,
14,{},E00009496,
15,{},E00009493,
16,{},E00009653,
17,{},E00009486,
18,{},E00009461,
19,{},E00009499,
20,{},E00009463,
21,{},E00009652,
22,{},E00009464,
23,{},E00009483,
24,{},E00009494,
25,{},E00009466,
26,{},E00009495,
27,{},E00009462,
28,{},E00009659,
29,{},E00009465,
30,{},E00009667,
31,{},E00009668,
32,{},E00009491,
33,{},E00009670,
34,{},E00009654,
35,{},E00009488,
36,{},E00009489,
37,{},E00009467,
38,{},E00009497,
39,{},E00009490,
40,{},E00009501,
41,{},E00009648,
42,{},E00009651,
43,{},E00009672,
44,{},E00009492,
45,{},E00009662,
46,{},E00009666,
47,{},E00009669,
48,{},E00009500,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00009644","E00009665","E00009658","E00009498","E00009661","E00009485","E00009487","E00009673","E00009671","E00009646","E00009647","E00009482","E00009679","E00009496","E00009493","E00009653","E00009486","E00009461","E00009499","E00009463","E00009652","E00009464","E00009483","E00009494","E00009466","E00009495","E00009462","E00009659","E00009465","E00009667","E00009668","E00009491","E00009670","E00009654","E00009488","E00009489","E00009467","E00009497","E00009490","E00009501","E00009648","E00009651","E00009672","E00009492","E00009662","E00009666","E00009669","E00009500"], [0.0 for i in range(0,48)], {"E00009644":"1","E00009665":"2","E00009658":"3","E00009498":"4","E00009661":"5","E00009485":"6","E00009487":"7","E00009673":"8","E00009671":"9","E00009646":"10","E00009647":"11","E00009482":"12","E00009679":"13","E00009496":"14","E00009493":"15","E00009653":"16","E00009486":"17","E00009461":"18","E00009499":"19","E00009463":"20","E00009652":"21","E00009464":"22","E00009483":"23","E00009494":"24","E00009466":"25","E00009495":"26","E00009462":"27","E00009659":"28","E00009465":"29","E00009667":"30","E00009668":"31","E00009491":"32","E00009670":"33","E00009654":"34","E00009488":"35","E00009489":"36","E00009467":"37","E00009497":"38","E00009490":"39","E00009501":"40","E00009648":"41","E00009651":"42","E00009672":"43","E00009492":"44","E00009662":"45","E00009666":"46","E00009669":"47","E00009500":"48"})