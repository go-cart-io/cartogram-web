import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test47"

    def get_gen_file(self):
        return "{}/test47.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 45:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00022564,
2,{},E00022569,
3,{},E00022884,
4,{},E00022535,
5,{},E00022542,
6,{},E00022533,
7,{},E00022572,
8,{},E00022895,
9,{},E00022546,
10,{},E00170957,
11,{},E00022886,
12,{},E00171065,
13,{},E00022574,
14,{},E00022567,
15,{},E00022894,
16,{},E00170967,
17,{},E00022548,
18,{},E00022877,
19,{},E00022547,
20,{},E00022882,
21,{},E00022897,
22,{},E00022891,
23,{},E00022571,
24,{},E00022559,
25,{},E00022570,
26,{},E00171038,
27,{},E00022544,
28,{},E00022540,
29,{},E00022565,
30,{},E00022534,
31,{},E00022566,
32,{},E00022541,
33,{},E00022563,
34,{},E00022560,
35,{},E00022554,
36,{},E00022575,
37,{},E00022552,
38,{},E00022576,
39,{},E00022555,
40,{},E00022557,
41,{},E00022532,
42,{},E00022558,
43,{},E00022568,
44,{},E00170959,
45,{},E00022573,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00022564","E00022569","E00022884","E00022535","E00022542","E00022533","E00022572","E00022895","E00022546","E00170957","E00022886","E00171065","E00022574","E00022567","E00022894","E00170967","E00022548","E00022877","E00022547","E00022882","E00022897","E00022891","E00022571","E00022559","E00022570","E00171038","E00022544","E00022540","E00022565","E00022534","E00022566","E00022541","E00022563","E00022560","E00022554","E00022575","E00022552","E00022576","E00022555","E00022557","E00022532","E00022558","E00022568","E00170959","E00022573"], [0.0 for i in range(0,45)], {"E00022564":"1","E00022569":"2","E00022884":"3","E00022535":"4","E00022542":"5","E00022533":"6","E00022572":"7","E00022895":"8","E00022546":"9","E00170957":"10","E00022886":"11","E00171065":"12","E00022574":"13","E00022567":"14","E00022894":"15","E00170967":"16","E00022548":"17","E00022877":"18","E00022547":"19","E00022882":"20","E00022897":"21","E00022891":"22","E00022571":"23","E00022559":"24","E00022570":"25","E00171038":"26","E00022544":"27","E00022540":"28","E00022565":"29","E00022534":"30","E00022566":"31","E00022541":"32","E00022563":"33","E00022560":"34","E00022554":"35","E00022575":"36","E00022552":"37","E00022576":"38","E00022555":"39","E00022557":"40","E00022532":"41","E00022558":"42","E00022568":"43","E00170959":"44","E00022573":"45"})
