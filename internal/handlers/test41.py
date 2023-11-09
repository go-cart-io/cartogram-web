import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test41"

    def get_gen_file(self):
        return "{}/test41.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 57:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00008329,
2,{},E00008134,
3,{},E00008104,
4,{},E00008333,
5,{},E00008337,
6,{},E00008343,
7,{},E00008135,
8,{},E00176577,
9,{},E00008140,
10,{},E00008101,
11,{},E00008335,
12,{},E00008354,
13,{},E00008349,
14,{},E00008123,
15,{},E00176546,
16,{},E00008132,
17,{},E00008344,
18,{},E00008119,
19,{},E00008336,
20,{},E00008122,
21,{},E00008347,
22,{},E00008318,
23,{},E00008128,
24,{},E00008139,
25,{},E00176533,
26,{},E00008352,
27,{},E00008118,
28,{},E00008136,
29,{},E00008330,
30,{},E00008342,
31,{},E00008340,
32,{},E00008115,
33,{},E00008351,
34,{},E00008332,
35,{},E00008108,
36,{},E00008346,
37,{},E00008114,
38,{},E00176584,
39,{},E00008331,
40,{},E00008107,
41,{},E00008116,
42,{},E00176549,
43,{},E00008341,
44,{},E00176564,
45,{},E00008117,
46,{},E00008345,
47,{},E00176541,
48,{},E00008339,
49,{},E00008102,
50,{},E00008144,
51,{},E00008143,
52,{},E00176581,
53,{},E00008328,
54,{},E00176569,
55,{},E00008334,
56,{},E00008133,
57,{},E00176548,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00008329","E00008134","E00008104","E00008333","E00008337","E00008343","E00008135","E00176577","E00008140","E00008101","E00008335","E00008354","E00008349","E00008123","E00176546","E00008132","E00008344","E00008119","E00008336","E00008122","E00008347","E00008318","E00008128","E00008139","E00176533","E00008352","E00008118","E00008136","E00008330","E00008342","E00008340","E00008115","E00008351","E00008332","E00008108","E00008346","E00008114","E00176584","E00008331","E00008107","E00008116","E00176549","E00008341","E00176564","E00008117","E00008345","E00176541","E00008339","E00008102","E00008144","E00008143","E00176581","E00008328","E00176569","E00008334","E00008133","E00176548"], [0.0 for i in range(0,57)], {"E00008329":"1","E00008134":"2","E00008104":"3","E00008333":"4","E00008337":"5","E00008343":"6","E00008135":"7","E00176577":"8","E00008140":"9","E00008101":"10","E00008335":"11","E00008354":"12","E00008349":"13","E00008123":"14","E00176546":"15","E00008132":"16","E00008344":"17","E00008119":"18","E00008336":"19","E00008122":"20","E00008347":"21","E00008318":"22","E00008128":"23","E00008139":"24","E00176533":"25","E00008352":"26","E00008118":"27","E00008136":"28","E00008330":"29","E00008342":"30","E00008340":"31","E00008115":"32","E00008351":"33","E00008332":"34","E00008108":"35","E00008346":"36","E00008114":"37","E00176584":"38","E00008331":"39","E00008107":"40","E00008116":"41","E00176549":"42","E00008341":"43","E00176564":"44","E00008117":"45","E00008345":"46","E00176541":"47","E00008339":"48","E00008102":"49","E00008144":"50","E00008143":"51","E00176581":"52","E00008328":"53","E00176569":"54","E00008334":"55","E00008133":"56","E00176548":"57"})
