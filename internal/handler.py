import re
import json
import settings

cartogram_handlers = {
'argentina': {'name':'Argentina', 'region_identifier':'Region', 'file':'arg_processedmap.json'},
'australia': {'name':'Australia', 'region_identifier':'Region', 'file':'aus_processedmap.json'},
'canada': {'name':'Canada', 'region_identifier':'Region', 'file':'can_processedmap.json'},
'japan2': {'name':'Japan', 'region_identifier':'Prefectures', 'file':'jpn2_processedmap.json'},
'france': {'name':'France', 'region_identifier':'Region', 'file':'fra_processedmap.json'},
'uae': {'name':'United Arab Emirates', 'region_identifier':'Emirate', 'file':'are_processedmap.json'},
'asean': {'name':'ASEAN Countries', 'region_identifier':'Country', 'file':'asean_processedmap.json'},
'mexico': {'name':'Mexico', 'region_identifier':'State', 'file':'mex_processedmap.json'},
'singaporePA': {'name':'Singapore (by Planning Area)', 'region_identifier':'Planning Area', 'file':'singaporePA_processedmap.json'},
'saudiArabia': {'name':'Saudi Arabia', 'region_identifier':'Region', 'file':'saudiArabia_processedmap.json'},
'netherlands': {'name':'Netherlands', 'region_identifier':'Province', 'file':'netherlands_processedmap.json'},
'thailand': {'name':'Thailand', 'region_identifier':'Province', 'file':'thailand_processedmap.json'},
'phl': {'name':'Philippines', 'region_identifier':'Province/Region', 'file':'phl_processedmap.json'},
'israel3': {'name':'Israel', 'region_identifier':'District', 'file':'isr3_processedmap.json'},
'vietnam': {'name':'Vietnam', 'region_identifier':'Province/Municipality', 'file':'vietnam_processedmap.json'},
'southAfrica': {'name':'South Africa', 'region_identifier':'Province', 'file':'southAfrica_processedmap.json'},
'italy2': {'name':'Italy', 'region_identifier':'Region', 'file':'ita2_processedmap.json'},
'colombia': {'name':'Colombia', 'region_identifier':'Department', 'file':'colombia_processedmap.json'},
'southKorea2': {'name':'South Korea', 'region_identifier':'Province/City', 'file':'southKorea2_processedmap.json'},
'newZealand': {'name':'New Zealand', 'region_identifier':'Region', 'file':'newZealand_processedmap.json'},
'europe': {'name':'Europe (Eurostat members)', 'region_identifier':'Country', 'file':'europe_processedmap.json'},
'algeria': {'name':'Algeria', 'region_identifier':'Province', 'file':'dza_processedmap.json'},
'libya': {'name':'Libya', 'region_identifier':'District', 'file':'lby_processedmap.json'},
'switzerland': {'name':'Switzerland', 'region_identifier':'Region', 'file':'che_processedmap.json'},
'ireland': {'name':'Ireland', 'region_identifier':'Region', 'file':'irl_processedmap.json'},
'poland': {'name':'Poland', 'region_identifier':'Region', 'file':'pol_processedmap.json'},
'sweden': {'name':'Sweden', 'region_identifier':'Region', 'file':'swe_processedmap.json'},
'croatia': {'name':'Croatia', 'region_identifier':'Region', 'file':'hrv_processedmap.json'},
'czechrepublic3': {'name':'Czech Republic', 'region_identifier':'Region', 'file':'cze_processedmap_(1).json'},
'hungary': {'name':'Hungary', 'region_identifier':'Region', 'file':'hun_processedmap.json'},
'unitedkingdom2': {'name':'United Kingdom', 'region_identifier':'Region', 'file':'gbr_processedmap.json'},
'finland': {'name':'Finland', 'region_identifier':'Region', 'file':'fin_processedmap.json'},
'austria': {'name':'Austria', 'region_identifier':'Region', 'file':'aut_processedmap.json'},
'denmark': {'name':'Denmark', 'region_identifier':'Region', 'file':'dnk_processedmap.json'},
'belgium': {'name':'Belgium', 'region_identifier':'Region', 'file':'bel_processedmap.json'},
'nigeria': {'name':'Nigeria', 'region_identifier':'Region', 'file':'nga_processedmap.json'},
'russia': {'name':'Russia', 'region_identifier':'Region', 'file':'rus_processedmap.json'},
'luxembourg': {'name':'Luxembourg', 'region_identifier':'Canton', 'file':'lux_processedmap.json'},
'bangladesh': {'name':'Bangladesh', 'region_identifier':'Division', 'file':'bangladesh_processedmap.json'},
'sanMarino': {'name':'San Marino', 'region_identifier':'Municipality', 'file':'smr_processedmap.json'},
'portugal': {'name':'Portugal', 'region_identifier':'District', 'file':'prt_processedmap.json'},
'greece': {'name':'Greece', 'region_identifier':'Region/Autonomous Region', 'file':'grc_processedmap.json'},
'malaysia': {'name':'Malaysia', 'region_identifier':'State/Federal Territory', 'file':'mys_processedmap.json'},
'qatar': {'name':'Qatar', 'region_identifier':'Municipality', 'file':'qat_processedmap.json'},
'turkey': {'name':'Turkey', 'region_identifier':'Province', 'file':'tur_processedmap.json'},
'cambodia': {'name':'Cambodia', 'region_identifier':'Province', 'file':'cam_processedmap.json'},
'andorra': {'name':'Andorra', 'region_identifier':'Parish', 'file':'and_processedmap.json'},
'ethiopia': {'name':'Ethiopia', 'region_identifier':'Region', 'file':'eth_processedmap.json'},
'myanmar': {'name':'Myanmar', 'region_identifier':'State/Region', 'file':'mmr_processedmap.json'},
'chile': {'name':'Chile', 'region_identifier':'Region', 'file':'chl_processedmap.json'},
'kaz': {'name':'Kazakhstan', 'region_identifier':'Region', 'file':'kaz_processedmap.json'},
'sudan': {'name':'Sudan', 'region_identifier':'State', 'file':'sdn_processedmap.json'},
'mongolia': {'name':'Mongolia', 'region_identifier':'Province', 'file':'mng_processedmap.json'},
'peru': {'name':'Peru', 'region_identifier':'Region/Province', 'file':'per_processedmap.json'},
'pak': {'name':'Pakistan', 'region_identifier':'Division', 'file':'pak_processedmap.json'},
'bolivia': {'name':'Bolivia', 'region_identifier':'Department', 'file':'bol_processedmap.json'},
'iceland': {'name':'Iceland', 'region_identifier':'Region', 'file':'isl_processedmap.json'},
'domrep': {'name':'Dominican Republic', 'region_identifier':'Province', 'file':'dom_processedmap.json'},
'laos': {'name':'Laos', 'region_identifier':'Province', 'file':'lao_processedmap.json'},
'paraguay': {'name':'Paraguay', 'region_identifier':'Department', 'file':'pry_processedmap.json'},
'nepal': {'name':'Nepal', 'region_identifier':'Province', 'file':'nepal_processedmap.json'},
'world': {'name':'World', 'region_identifier':'Country', 'file':'world_enlarged.json'},
'angola': {'name':'Angola', 'region_identifier':'Province', 'file':'angola_processedmap.json'},
'romania': {'name':'Romania', 'region_identifier':'County', 'file':'romania_processedmap.json'},
'ukraine': {'name':'Ukraine', 'region_identifier':'Region', 'file':'ukraine_processedmap.json'},
'jamaica': {'name':'Jamaica', 'region_identifier':'Parish', 'file':'jamaica_processedmap.json'},
'yemen': {'name':'Yemen', 'region_identifier':'Governorate', 'file':'yem_processedmap.json'},
'belarus': {'name':'Belarus', 'region_identifier':'Region', 'file':'belarus_processedmap.json'},
'bahamas': {'name':'The Bahamas', 'region_identifier':'Island', 'file':'bahamas_processedmap.json'},
'guyana': {'name':'Guyana', 'region_identifier':'Region', 'file':'guyana_processedmap.json'},
'washington': {'name':'Washington (U.S. State)', 'region_identifier':'County', 'file':'washington_processedmap.json'},        
'lebanon': {'name':'Lebanon', 'region_identifier':'Governorate', 'file':'lbn_processedmap.json'},
'spain5': {'name':'Spain', 'region_identifier':'Autonomous Community/City', 'file':'spain5_processedmap.json'},
'arab_league': {'name':'Arab League', 'region_identifier':'Country', 'file':'arab_league_processedmap.json'},
'estonia': {'name':'Estonia', 'region_identifier':'County', 'file':'est_processedmap.json'},
'usa': {'name':'United States (Conterminous)', 'region_identifier':'State', 'file':'usa_processedmap.json'},
'brazil': {'name':'Brazil', 'region_identifier':'State', 'file':'brazil_processedmap.json'},
'china': {'name':'China (Mainland China and Taiwan)', 'region_identifier':'Province', 'file':'china_processedmap.json'},      
'china2': {'name':'Taiwan (Mainland China and Taiwan)', 'region_identifier':'Province', 'file':'china_processedmap.json'},
'india': {'name':'India', 'region_identifier':'State', 'file':'india_processedmap.json'},
'srilanka': {'name':'Sri Lanka', 'region_identifier':'District', 'file':'srilanka_processedmap.json'},
'germany': {'name':'Germany', 'region_identifier':'State', 'file':'germany_processedmap.json'},
'indonesia': {'name':'Indonesia', 'region_identifier':'Province', 'file':'idn_processedmap.json'},
'singaporeRe': {'name':'Singapore (by Region)', 'region_identifier':'Region', 'file':'singaporeRe_processedmap.json'},
'singapore2': {'name':'Singapore (2000 vs 2020)', 'region_identifier':'Planning Area', 'file':'singaporePA_processedmap.json'},
# DONOT remove or modify the below comment
# ---addmap.py header marker---
}

class CartogramHandler:
    def has_handler(self, handler):
        return handler in cartogram_handlers
    
    def get_sorted_handler_names(self):
        return dict(sorted(cartogram_handlers.items(), key=lambda item: item[1]['name']))

    def get_name(self, handler):
        return cartogram_handlers[handler]['name']

    def get_gen_file(self, handler):
        return '{}/{}'.format(settings.CARTOGRAM_DATA_DIR, cartogram_handlers[handler]['file'])  
    
    def remove_holes(self):
        return False
    
    def expect_geojson_output(self):
        return True
        
    # This function takes a CSVReader and returns a tuple containing:
    #   
    #   1. The areas string
    #   2. Color values for each region
    #   3. Tooltip data for each region
    def get_area_string_and_colors(self, handler, data):
        if handler not in cartogram_handlers:
            raise KeyError('The handler was invaild.')

        with open(self.get_gen_file(handler), 'r') as openfile: 
            handler_data = json.load(openfile)    

        colName = 0
        colColor = 1
        colValue = 2 # Starting column of data

        datastring = 'cartogram_id,Region Data,Region Name,Inset\n'
        colorJson = {}
        tooltip = {'data':{}}

        for rowId, region in data['values']['items'].items():
            # Validate values
            region[colName] = region[colName].replace(',', '')
            if region[colValue] is not None:
                float(region[colValue])
            else:
                region[colValue] = 'NA',
            if not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', region[colColor]):
                raise ValueError('The color data was invaild.')
                   
            regionId = handler_data['regions'][region[colName]]
            datastring = datastring + '{0},{1},{2},\n'.format(regionId, region[colValue], region[colName])
            colorJson['id_' + regionId] = region[colColor]
            tooltip['data']['id_' + regionId] = {'name': region[colName], 'value': region[colValue]}

        m = re.match(r'(.+)\s?\((.+)\)$', data['values']['fields'][colValue]['label'])
        if m:
            tooltip['label'] = m.group(1)
            tooltip['unit'] = m.group(2)
        else:
            tooltip['label'] = data['values']['fields'][colValue]['label']
        
        return datastring, colorJson, tooltip
    
