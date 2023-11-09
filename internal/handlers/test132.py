import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test132"

    def get_gen_file(self):
        return "{}/test132.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 48:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00015131,
2,{},E00015008,
3,{},E00014686,
4,{},E00015009,
5,{},E00015127,
6,{},E00015119,
7,{},E00015118,
8,{},E00014987,
9,{},E00015004,
10,{},E00014983,
11,{},E00014988,
12,{},E00014687,
13,{},E00014688,
14,{},E00015120,
15,{},E00015128,
16,{},E00015117,
17,{},E00015000,
18,{},E00014981,
19,{},E00014685,
20,{},E00015007,
21,{},E00015018,
22,{},E00014690,
23,{},E00015006,
24,{},E00014684,
25,{},E00014986,
26,{},E00015121,
27,{},E00015126,
28,{},E00014691,
29,{},E00014998,
30,{},E00014994,
31,{},E00015012,
32,{},E00015015,
33,{},E00014689,
34,{},E00015005,
35,{},E00015116,
36,{},E00015123,
37,{},E00015032,
38,{},E00014985,
39,{},E00014984,
40,{},E00015001,
41,{},E00015125,
42,{},E00015134,
43,{},E00015034,
44,{},E00014683,
45,{},E00015135,
46,{},E00015017,
47,{},E00014676,
48,{},E00015014,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00015131","E00015008","E00014686","E00015009","E00015127","E00015119","E00015118","E00014987","E00015004","E00014983","E00014988","E00014687","E00014688","E00015120","E00015128","E00015117","E00015000","E00014981","E00014685","E00015007","E00015018","E00014690","E00015006","E00014684","E00014986","E00015121","E00015126","E00014691","E00014998","E00014994","E00015012","E00015015","E00014689","E00015005","E00015116","E00015123","E00015032","E00014985","E00014984","E00015001","E00015125","E00015134","E00015034","E00014683","E00015135","E00015017","E00014676","E00015014"], [0.0 for i in range(0,48)], {"E00015131":"1","E00015008":"2","E00014686":"3","E00015009":"4","E00015127":"5","E00015119":"6","E00015118":"7","E00014987":"8","E00015004":"9","E00014983":"10","E00014988":"11","E00014687":"12","E00014688":"13","E00015120":"14","E00015128":"15","E00015117":"16","E00015000":"17","E00014981":"18","E00014685":"19","E00015007":"20","E00015018":"21","E00014690":"22","E00015006":"23","E00014684":"24","E00014986":"25","E00015121":"26","E00015126":"27","E00014691":"28","E00014998":"29","E00014994":"30","E00015012":"31","E00015015":"32","E00014689":"33","E00015005":"34","E00015116":"35","E00015123":"36","E00015032":"37","E00014985":"38","E00014984":"39","E00015001":"40","E00015125":"41","E00015134":"42","E00015034":"43","E00014683":"44","E00015135":"45","E00015017":"46","E00014676":"47","E00015014":"48"})
