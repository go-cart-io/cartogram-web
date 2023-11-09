import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test147"

    def get_gen_file(self):
        return "{}/test147.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 49:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00021305,
2,{},E00021321,
3,{},E00021296,
4,{},E00167242,
5,{},E00021307,
6,{},E00021156,
7,{},E00021310,
8,{},E00021322,
9,{},E00021298,
10,{},E00021313,
11,{},E00021157,
12,{},E00021324,
13,{},E00021173,
14,{},E00021315,
15,{},E00021309,
16,{},E00021150,
17,{},E00021304,
18,{},E00021171,
19,{},E00021170,
20,{},E00021147,
21,{},E00021297,
22,{},E00021176,
23,{},E00021158,
24,{},E00021165,
25,{},E00021319,
26,{},E00167172,
27,{},E00021320,
28,{},E00021311,
29,{},E00021317,
30,{},E00021318,
31,{},E00021316,
32,{},E00021148,
33,{},E00021162,
34,{},E00021151,
35,{},E00021294,
36,{},E00021312,
37,{},E00021172,
38,{},E00021141,
39,{},E00021149,
40,{},E00021325,
41,{},E00021327,
42,{},E00021295,
43,{},E00021175,
44,{},E00021143,
45,{},E00021300,
46,{},E00167244,
47,{},E00021314,
48,{},E00021308,
49,{},E00021145,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00021305","E00021321","E00021296","E00167242","E00021307","E00021156","E00021310","E00021322","E00021298","E00021313","E00021157","E00021324","E00021173","E00021315","E00021309","E00021150","E00021304","E00021171","E00021170","E00021147","E00021297","E00021176","E00021158","E00021165","E00021319","E00167172","E00021320","E00021311","E00021317","E00021318","E00021316","E00021148","E00021162","E00021151","E00021294","E00021312","E00021172","E00021141","E00021149","E00021325","E00021327","E00021295","E00021175","E00021143","E00021300","E00167244","E00021314","E00021308","E00021145"], [0.0 for i in range(0,49)], {"E00021305":"1","E00021321":"2","E00021296":"3","E00167242":"4","E00021307":"5","E00021156":"6","E00021310":"7","E00021322":"8","E00021298":"9","E00021313":"10","E00021157":"11","E00021324":"12","E00021173":"13","E00021315":"14","E00021309":"15","E00021150":"16","E00021304":"17","E00021171":"18","E00021170":"19","E00021147":"20","E00021297":"21","E00021176":"22","E00021158":"23","E00021165":"24","E00021319":"25","E00167172":"26","E00021320":"27","E00021311":"28","E00021317":"29","E00021318":"30","E00021316":"31","E00021148":"32","E00021162":"33","E00021151":"34","E00021294":"35","E00021312":"36","E00021172":"37","E00021141":"38","E00021149":"39","E00021325":"40","E00021327":"41","E00021295":"42","E00021175":"43","E00021143":"44","E00021300":"45","E00167244":"46","E00021314":"47","E00021308":"48","E00021145":"49"})
