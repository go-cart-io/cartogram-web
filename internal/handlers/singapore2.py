import settings
import handlers.base_handler
import csv

class CartogramHandler(handlers.base_handler.BaseCartogramHandler):

    def get_name(self):
        return "Singapore (2000 vs 2020)"

    def get_gen_file(self):
        return "{}/singaporePA_processedmap.json".format(settings.CARTOGRAM_DATA_DIR)
    
    def validate_values(self, values):

        if len(values) != 55:
            return False
        
        for v in values:
            if type(v) != float:
                return False

        return True
    
    def gen_area_data(self, values):
        return """cartogram_id,Region Data,Region Name,Inset
1,{},Ang Mo Kio,
2,{},Bedok,
3,{},Bishan,
4,{},Boon Lay,
5,{},Bukit Batok,
6,{},Bukit Merah,
7,{},Bukit Panjang,
8,{},Bukit Timah,
9,{},Central Water Catchment,
10,{},Changi,
11,{},Changi Bay,
12,{},Choa Chu Kang,
13,{},Clementi,
14,{},Downtown Core,
15,{},Geylang,
16,{},Hougang,
17,{},Jurong East,
18,{},Jurong West,
19,{},Kallang,
20,{},Lim Chu Kang,
21,{},Mandai,
22,{},Marina East,
23,{},Marina South,
24,{},Marine Parade,
25,{},Museum,
26,{},Newton,
27,{},North-eastern Islands,
28,{},Novena,
29,{},Orchard,
30,{},Outram,
31,{},Pasir Ris,
32,{},Paya Lebar,
33,{},Pioneer,
34,{},Punggol,
35,{},Queenstown,
36,{},River Valley,
37,{},Rochor,
38,{},Seletar,
39,{},Sembawang,
40,{},Sengkang,
41,{},Serangoon,
42,{},Simpang,
43,{},Singapore River,
44,{},Southern Islands,
45,{},Straits View,
46,{},Sungei Kadut,
47,{},Tampines,
48,{},Tanglin,
49,{},Tengah,
50,{},Toa Payoh,
51,{},Tuas,
52,{},Western Islands,
53,{},Western Water Catchment,
54,{},Woodlands,
55,{},Yishun,""".format(*values)
    
    def expect_geojson_output(self):
        return True

    def csv_to_area_string_and_colors(self, csvfile):

        return self.order_by_example(csv.reader(csvfile), "Planning Area", 0, 1, 2, 3, ["Ang Mo Kio","Bedok","Bishan","Boon Lay","Bukit Batok","Bukit Merah","Bukit Panjang","Bukit Timah","Central Water Catchment","Changi","Changi Bay","Choa Chu Kang","Clementi","Downtown Core","Geylang","Hougang","Jurong East","Jurong West","Kallang","Lim Chu Kang","Mandai","Marina East","Marina South","Marine Parade","Museum","Newton","North-eastern Islands","Novena","Orchard","Outram","Pasir Ris","Paya Lebar","Pioneer","Punggol","Queenstown","River Valley","Rochor","Seletar","Sembawang","Sengkang","Serangoon","Simpang","Singapore River","Southern Islands","Straits View","Sungei Kadut","Tampines","Tanglin","Tengah","Toa Payoh","Tuas","Western Islands","Western Water Catchment","Woodlands","Yishun"], [0.0 for i in range(0,55)], {"Ang Mo Kio":"1","Bedok":"2","Bishan":"3","Boon Lay":"4","Bukit Batok":"5","Bukit Merah":"6","Bukit Panjang":"7","Bukit Timah":"8","Central Water Catchment":"9","Changi":"10","Changi Bay":"11","Choa Chu Kang":"12","Clementi":"13","Downtown Core":"14","Geylang":"15","Hougang":"16","Jurong East":"17","Jurong West":"18","Kallang":"19","Lim Chu Kang":"20","Mandai":"21","Marina East":"22","Marina South":"23","Marine Parade":"24","Museum":"25","Newton":"26","North-eastern Islands":"27","Novena":"28","Orchard":"29","Outram":"30","Pasir Ris":"31","Paya Lebar":"32","Pioneer":"33","Punggol":"34","Queenstown":"35","River Valley":"36","Rochor":"37","Seletar":"38","Sembawang":"39","Sengkang":"40","Serangoon":"41","Simpang":"42","Singapore River":"43","Southern Islands":"44","Straits View":"45","Sungei Kadut":"46","Tampines":"47","Tanglin":"48","Tengah":"49","Toa Payoh":"50","Tuas":"51","Western Islands":"52","Western Water Catchment":"53","Woodlands":"54","Yishun":"55"})
