import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "test52"

    def get_gen_file(self):
        return "{}/test52.geojson".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 51:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},E00011679,
2,{},E00011683,
3,{},E00011623,
4,{},E00011665,
5,{},E00011641,
6,{},E00011653,
7,{},E00011635,
8,{},E00011620,
9,{},E00011652,
10,{},E00011675,
11,{},E00011640,
12,{},E00011691,
13,{},E00011631,
14,{},E00011667,
15,{},E00011614,
16,{},E00011684,
17,{},E00011654,
18,{},E00011666,
19,{},E00011639,
20,{},E00011674,
21,{},E00011681,
22,{},E00011688,
23,{},E00011662,
24,{},E00011670,
25,{},E00011669,
26,{},E00011663,
27,{},E00011673,
28,{},E00011618,
29,{},E00011629,
30,{},E00011676,
31,{},E00011633,
32,{},E00011682,
33,{},E00011638,
34,{},E00011628,
35,{},E00011672,
36,{},E00011689,
37,{},E00011655,
38,{},E00011624,
39,{},E00011612,
40,{},E00011678,
41,{},E00011685,
42,{},E00011680,
43,{},E00011687,
44,{},E00011661,
45,{},E00011658,
46,{},E00011657,
47,{},E00011686,
48,{},E00011671,
49,{},E00011660,
50,{},E00011677,
51,{},E00011690,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Region", 0, 1, 2, 3, ["E00011679","E00011683","E00011623","E00011665","E00011641","E00011653","E00011635","E00011620","E00011652","E00011675","E00011640","E00011691","E00011631","E00011667","E00011614","E00011684","E00011654","E00011666","E00011639","E00011674","E00011681","E00011688","E00011662","E00011670","E00011669","E00011663","E00011673","E00011618","E00011629","E00011676","E00011633","E00011682","E00011638","E00011628","E00011672","E00011689","E00011655","E00011624","E00011612","E00011678","E00011685","E00011680","E00011687","E00011661","E00011658","E00011657","E00011686","E00011671","E00011660","E00011677","E00011690"], [0.0 for i in range(0,51)], {"E00011679":"1","E00011683":"2","E00011623":"3","E00011665":"4","E00011641":"5","E00011653":"6","E00011635":"7","E00011620":"8","E00011652":"9","E00011675":"10","E00011640":"11","E00011691":"12","E00011631":"13","E00011667":"14","E00011614":"15","E00011684":"16","E00011654":"17","E00011666":"18","E00011639":"19","E00011674":"20","E00011681":"21","E00011688":"22","E00011662":"23","E00011670":"24","E00011669":"25","E00011663":"26","E00011673":"27","E00011618":"28","E00011629":"29","E00011676":"30","E00011633":"31","E00011682":"32","E00011638":"33","E00011628":"34","E00011672":"35","E00011689":"36","E00011655":"37","E00011624":"38","E00011612":"39","E00011678":"40","E00011685":"41","E00011680":"42","E00011687":"43","E00011661":"44","E00011658":"45","E00011657":"46","E00011686":"47","E00011671":"48","E00011660":"49","E00011677":"50","E00011690":"51"})