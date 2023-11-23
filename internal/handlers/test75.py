import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test75"

    def get_gen_file(self):
        return "{}/test75.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 37:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00018958,
2,{},E00018953,
3,{},E00018933,
4,{},E00018952,
5,{},E00018928,
6,{},E00018948,
7,{},E00018959,
8,{},E00018939,
9,{},E00018932,
10,{},E00018961,
11,{},E00018943,
12,{},E00175129,
13,{},E00018936,
14,{},E00018931,
15,{},E00018945,
16,{},E00018955,
17,{},E00018934,
18,{},E00018930,
19,{},E00175166,
20,{},E00018937,
21,{},E00018947,
22,{},E00018929,
23,{},E00018951,
24,{},E00018960,
25,{},E00175143,
26,{},E00018956,
27,{},E00175130,
28,{},E00018950,
29,{},E00018938,
30,{},E00018954,
31,{},E00018957,
32,{},E00018935,
33,{},E00175169,
34,{},E00018946,
35,{},E00018949,
36,{},E00175168,
37,{},E00018944,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00018958","E00018953","E00018933","E00018952","E00018928","E00018948","E00018959","E00018939","E00018932","E00018961","E00018943","E00175129","E00018936","E00018931","E00018945","E00018955","E00018934","E00018930","E00175166","E00018937","E00018947","E00018929","E00018951","E00018960","E00175143","E00018956","E00175130","E00018950","E00018938","E00018954","E00018957","E00018935","E00175169","E00018946","E00018949","E00175168","E00018944"], [0.0 for i in range(0,37)], {"E00018958":"1","E00018953":"2","E00018933":"3","E00018952":"4","E00018928":"5","E00018948":"6","E00018959":"7","E00018939":"8","E00018932":"9","E00018961":"10","E00018943":"11","E00175129":"12","E00018936":"13","E00018931":"14","E00018945":"15","E00018955":"16","E00018934":"17","E00018930":"18","E00175166":"19","E00018937":"20","E00018947":"21","E00018929":"22","E00018951":"23","E00018960":"24","E00175143":"25","E00018956":"26","E00175130":"27","E00018950":"28","E00018938":"29","E00018954":"30","E00018957":"31","E00018935":"32","E00175169":"33","E00018946":"34","E00018949":"35","E00175168":"36","E00018944":"37"})