import re
import json
import settings

cartogram_handlers = {
'argentina': {'name':'Argentina', 'file':'arg_processedmap.json'},
'australia': {'name':'Australia', 'file':'aus_processedmap.json'},
'canada': {'name':'Canada', 'file':'can_processedmap.json'},
'japan2': {'name':'Japan', 'file':'jpn2_processedmap.json'},
'france': {'name':'France', 'file':'fra_processedmap.json'},
'uae': {'name':'United Arab Emirates', 'file':'are_processedmap.json'},
'asean': {'name':'ASEAN Countries', 'file':'asean_processedmap.json'},
'mexico': {'name':'Mexico', 'file':'mex_processedmap.json'},
'singaporePA': {'name':'Singapore (by Planning Area)', 'file':'singaporePA_processedmap.json'},
'saudiArabia': {'name':'Saudi Arabia', 'file':'saudiArabia_processedmap.json'},
'netherlands': {'name':'Netherlands', 'file':'netherlands_processedmap.json'},
'thailand': {'name':'Thailand', 'file':'thailand_processedmap.json'},
'phl': {'name':'Philippines', 'file':'phl_processedmap.json'},
'israel3': {'name':'Israel', 'file':'isr3_processedmap.json'},
'vietnam': {'name':'Vietnam', 'file':'vietnam_processedmap.json'},
'southAfrica': {'name':'South Africa', 'file':'southAfrica_processedmap.json'},
'italy2': {'name':'Italy', 'file':'ita2_processedmap.json'},
'colombia': {'name':'Colombia', 'file':'colombia_processedmap.json'},
'southKorea2': {'name':'South Korea', 'file':'southKorea2_processedmap.json'},
'newZealand': {'name':'New Zealand', 'file':'newZealand_processedmap.json'},
'europe': {'name':'Europe (Eurostat members)', 'file':'europe_processedmap.json'},
'algeria': {'name':'Algeria', 'file':'dza_processedmap.json'},
'libya': {'name':'Libya', 'file':'lby_processedmap.json'},
'switzerland': {'name':'Switzerland', 'file':'che_processedmap.json'},
'ireland': {'name':'Ireland', 'file':'irl_processedmap.json'},
'poland': {'name':'Poland', 'file':'pol_processedmap.json'},
'sweden': {'name':'Sweden', 'file':'swe_processedmap.json'},
'croatia': {'name':'Croatia', 'file':'hrv_processedmap.json'},
'czechrepublic3': {'name':'Czech Republic', 'file':'cze_processedmap_(1).json'},
'hungary': {'name':'Hungary', 'file':'hun_processedmap.json'},
'unitedkingdom2': {'name':'United Kingdom', 'file':'gbr_processedmap.json'},
'finland': {'name':'Finland', 'file':'fin_processedmap.json'},
'austria': {'name':'Austria', 'file':'aut_processedmap.json'},
'denmark': {'name':'Denmark', 'file':'dnk_processedmap.json'},
'belgium': {'name':'Belgium', 'file':'bel_processedmap.json'},
'nigeria': {'name':'Nigeria', 'file':'nga_processedmap.json'},
'russia': {'name':'Russia', 'file':'rus_processedmap.json'},
'luxembourg': {'name':'Luxembourg', 'file':'lux_processedmap.json'},
'bangladesh': {'name':'Bangladesh', 'file':'bangladesh_processedmap.json'},
'sanMarino': {'name':'San Marino', 'file':'smr_processedmap.json'},
'portugal': {'name':'Portugal', 'file':'prt_processedmap.json'},
'greece': {'name':'Greece', 'file':'grc_processedmap.json'},
'malaysia': {'name':'Malaysia', 'file':'mys_processedmap.json'},
'qatar': {'name':'Qatar', 'file':'qat_processedmap.json'},
'turkey': {'name':'Turkey', 'file':'tur_processedmap.json'},
'cambodia': {'name':'Cambodia', 'file':'cam_processedmap.json'},
'andorra': {'name':'Andorra', 'file':'and_processedmap.json'},
'ethiopia': {'name':'Ethiopia', 'file':'eth_processedmap.json'},
'myanmar': {'name':'Myanmar', 'file':'mmr_processedmap.json'},
'chile': {'name':'Chile', 'file':'chl_processedmap.json'},
'kaz': {'name':'Kazakhstan', 'file':'kaz_processedmap.json'},
'sudan': {'name':'Sudan', 'file':'sdn_processedmap.json'},
'mongolia': {'name':'Mongolia', 'file':'mng_processedmap.json'},
'peru': {'name':'Peru', 'file':'per_processedmap.json'},
'pak': {'name':'Pakistan', 'file':'pak_processedmap.json'},
'bolivia': {'name':'Bolivia', 'file':'bol_processedmap.json'},
'iceland': {'name':'Iceland', 'file':'isl_processedmap.json'},
'domrep': {'name':'Dominican Republic', 'file':'dom_processedmap.json'},
'laos': {'name':'Laos', 'file':'lao_processedmap.json'},
'paraguay': {'name':'Paraguay', 'file':'pry_processedmap.json'},
'nepal': {'name':'Nepal', 'file':'nepal_processedmap.json'},
'world': {'name':'World', 'file':'world_enlarged.json'},
'angola': {'name':'Angola', 'file':'angola_processedmap.json'},
'romania': {'name':'Romania', 'file':'romania_processedmap.json'},
'ukraine': {'name':'Ukraine', 'file':'ukraine_processedmap.json'},
'jamaica': {'name':'Jamaica', 'file':'jamaica_processedmap.json'},
'yemen': {'name':'Yemen', 'file':'yem_processedmap.json'},
'belarus': {'name':'Belarus', 'file':'belarus_processedmap.json'},
'bahamas': {'name':'The Bahamas', 'file':'bahamas_processedmap.json'},
'guyana': {'name':'Guyana', 'file':'guyana_processedmap.json'},
'washington': {'name':'Washington (U.S. State)', 'file':'washington_processedmap.json'},
'lebanon': {'name':'Lebanon', 'file':'lbn_processedmap.json'},
'spain5': {'name':'Spain', 'file':'spain5_processedmap.json'},
'arab_league': {'name':'Arab League', 'file':'arab_league_processedmap.json'},
'estonia': {'name':'Estonia', 'file':'est_processedmap.json'},
'usa': {'name':'United States (Conterminous)', 'file':'usa_processedmap.json'},
'brazil': {'name':'Brazil', 'file':'brazil_processedmap.json'},
'china': {'name':'China (Mainland China and Taiwan)', 'file':'china_processedmap.json'},
'china2': {'name':'Taiwan (Mainland China and Taiwan)', 'file':'china_processedmap.json'},
'india': {'name':'India', 'file':'india_processedmap.json'},
'srilanka': {'name':'Sri Lanka', 'file':'srilanka_processedmap.json'},
'germany': {'name':'Germany', 'file':'germany_processedmap.json'},
'indonesia': {'name':'Indonesia', 'file':'idn_processedmap.json'},
'singaporeRe': {'name':'Singapore (by Region)', 'file':'singaporeRe_processedmap.json'},
'singapore2': {'name':'Singapore (2000 vs 2020)', 'file':'singaporePA_processedmap.json'},
}

class CartogramHandler:
    def has_handler(self, handler):
        return handler in cartogram_handlers
    
    def get_sorted_handler_names(self):
        cartogram_handlers_select = {}
        for key, handler in cartogram_handlers.items():
            cartogram_handlers_select[key] = handler['name']

        return dict(sorted(cartogram_handlers_select.items()))

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
    
