import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test15"

    def get_gen_file(self):
        return "{}/test15.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 42:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00006508,
2,{},E00006512,
3,{},E00006516,
4,{},E00006494,
5,{},E00006510,
6,{},E00006480,
7,{},E00006485,
8,{},E00006501,
9,{},E00006506,
10,{},E00006487,
11,{},E00006514,
12,{},E00006515,
13,{},E00006498,
14,{},E00006497,
15,{},E00006504,
16,{},E00166869,
17,{},E00006502,
18,{},E00006264,
19,{},E00006491,
20,{},E00006505,
21,{},E00006265,
22,{},E00006267,
23,{},E00006477,
24,{},E00006507,
25,{},E00006488,
26,{},E00006481,
27,{},E00006486,
28,{},E00006496,
29,{},E00006492,
30,{},E00006493,
31,{},E00006489,
32,{},E00006483,
33,{},E00006475,
34,{},E00006474,
35,{},E00006511,
36,{},E00006266,
37,{},E00006503,
38,{},E00006509,
39,{},E00006476,
40,{},E00006499,
41,{},E00006268,
42,{},E00006500,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00006508","E00006512","E00006516","E00006494","E00006510","E00006480","E00006485","E00006501","E00006506","E00006487","E00006514","E00006515","E00006498","E00006497","E00006504","E00166869","E00006502","E00006264","E00006491","E00006505","E00006265","E00006267","E00006477","E00006507","E00006488","E00006481","E00006486","E00006496","E00006492","E00006493","E00006489","E00006483","E00006475","E00006474","E00006511","E00006266","E00006503","E00006509","E00006476","E00006499","E00006268","E00006500"], [0.0 for i in range(0,42)], {"E00006508":"1","E00006512":"2","E00006516":"3","E00006494":"4","E00006510":"5","E00006480":"6","E00006485":"7","E00006501":"8","E00006506":"9","E00006487":"10","E00006514":"11","E00006515":"12","E00006498":"13","E00006497":"14","E00006504":"15","E00166869":"16","E00006502":"17","E00006264":"18","E00006491":"19","E00006505":"20","E00006265":"21","E00006267":"22","E00006477":"23","E00006507":"24","E00006488":"25","E00006481":"26","E00006486":"27","E00006496":"28","E00006492":"29","E00006493":"30","E00006489":"31","E00006483":"32","E00006475":"33","E00006474":"34","E00006511":"35","E00006266":"36","E00006503":"37","E00006509":"38","E00006476":"39","E00006499":"40","E00006268":"41","E00006500":"42"})
