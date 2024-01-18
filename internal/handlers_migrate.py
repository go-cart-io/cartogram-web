import json
import csv

from handlers import test
from handlers import argentina
from handlers import australia
from handlers import canada
from handlers import japan2
from handlers import france
from handlers import uae
from handlers import asean
from handlers import mexico
from handlers import singaporePA
from handlers import saudiArabia
from handlers import netherlands
from handlers import thailand
from handlers import phl
from handlers import israel3
from handlers import vietnam
from handlers import southAfrica
from handlers import italy2
from handlers import colombia
from handlers import southKorea2
from handlers import newZealand
from handlers import europe
from handlers import algeria
from handlers import libya
#from handlers import pakistan
from handlers import switzerland
from handlers import ireland
from handlers import poland
from handlers import sweden
from handlers import croatia
from handlers import czechrepublic3
from handlers import hungary
from handlers import unitedkingdom2
from handlers import finland
from handlers import austria
from handlers import denmark
from handlers import belgium
from handlers import russia
from handlers import nigeria
from handlers import luxembourg
from handlers import bangladesh
from handlers import sanMarino
from handlers import portugal
from handlers import greece
from handlers import malaysia
from handlers import qatar
from handlers import turkey
from handlers import cambodia
from handlers import andorra
from handlers import ethiopia
from handlers import myanmar
from handlers import chile
from handlers import kaz
from handlers import sudan
from handlers import mongolia
from handlers import peru
from handlers import pak
from handlers import bolivia
from handlers import iceland
from handlers import laos
from handlers import domrep
from handlers import laos
from handlers import paraguay
from handlers import nepal
from handlers import world
from handlers import angola
from handlers import romania
from handlers import ukraine
from handlers import jamaica
from handlers import yemen
from handlers import belarus
from handlers import bahamas
from handlers import guyana
from handlers import washington
from handlers import lebanon
from handlers import spain5
from handlers import arab_league
from handlers import estonia
from handlers import usa
from handlers import brazil
from handlers import china
from handlers import china2
from handlers import india
from handlers import srilanka
from handlers import germany
from handlers import indonesia
from handlers import singaporeRe
from handlers import singapore2

cartogram_handlers = {
#'test': test.CartogramHandler(),
'argentina': argentina.CartogramHandler(),
'australia': australia.CartogramHandler(),
'canada': canada.CartogramHandler(),
'japan2': japan2.CartogramHandler(),
'france': france.CartogramHandler(),
'uae': uae.CartogramHandler(),
'asean': asean.CartogramHandler(),
'mexico': mexico.CartogramHandler(),
'singaporePA': singaporePA.CartogramHandler(),
'saudiArabia': saudiArabia.CartogramHandler(),
'netherlands': netherlands.CartogramHandler(),
'thailand': thailand.CartogramHandler(),
'phl': phl.CartogramHandler(),
'israel3': israel3.CartogramHandler(),
'vietnam': vietnam.CartogramHandler(),
'southAfrica': southAfrica.CartogramHandler(),
'italy2': italy2.CartogramHandler(),
'colombia': colombia.CartogramHandler(),
'southKorea2': southKorea2.CartogramHandler(),
'newZealand': newZealand.CartogramHandler(),
'europe': europe.CartogramHandler(),
'algeria': algeria.CartogramHandler(),
'libya': libya.CartogramHandler(),
#'pakistan': pakistan.CartogramHandler(),
'switzerland': switzerland.CartogramHandler(),
'ireland': ireland.CartogramHandler(),
'poland': poland.CartogramHandler(),
'sweden': sweden.CartogramHandler(),
'croatia': croatia.CartogramHandler(),
'czechrepublic3': czechrepublic3.CartogramHandler(),
'hungary': hungary.CartogramHandler(),
'unitedkingdom2': unitedkingdom2.CartogramHandler(),
'finland': finland.CartogramHandler(),
'austria': austria.CartogramHandler(),
'denmark': denmark.CartogramHandler(),
'belgium': belgium.CartogramHandler(),
'nigeria': nigeria.CartogramHandler(),
'russia':russia.CartogramHandler(),
'luxembourg': luxembourg.CartogramHandler(),
'bangladesh': bangladesh.CartogramHandler(),
'sanMarino': sanMarino.CartogramHandler(),
'portugal': portugal.CartogramHandler(),
'greece': greece.CartogramHandler(),
'malaysia': malaysia.CartogramHandler(),
'qatar': qatar.CartogramHandler(),
'turkey': turkey.CartogramHandler(),
'cambodia': cambodia.CartogramHandler(),
'andorra': andorra.CartogramHandler(),
'ethiopia': ethiopia.CartogramHandler(),
'myanmar': myanmar.CartogramHandler(),
'chile': chile.CartogramHandler(),
'kaz': kaz.CartogramHandler(),
'sudan': sudan.CartogramHandler(),
'mongolia': mongolia.CartogramHandler(),
'peru': peru.CartogramHandler(),
'pak': pak.CartogramHandler(),
'bolivia': bolivia.CartogramHandler(),
'iceland': iceland.CartogramHandler(),
'domrep': domrep.CartogramHandler(),
'laos': laos.CartogramHandler(),
'paraguay': paraguay.CartogramHandler(),
'nepal': nepal.CartogramHandler(),
'world': world.CartogramHandler(),
'angola': angola.CartogramHandler(),
'romania': romania.CartogramHandler(),
'ukraine': ukraine.CartogramHandler(),
'jamaica': jamaica.CartogramHandler(),
'yemen': yemen.CartogramHandler(),
'belarus': belarus.CartogramHandler(),
'bahamas': bahamas.CartogramHandler(),
'guyana': guyana.CartogramHandler(),
'washington': washington.CartogramHandler(),
'lebanon': lebanon.CartogramHandler(),
'spain5': spain5.CartogramHandler(),
'arab_league': arab_league.CartogramHandler(),
'estonia': estonia.CartogramHandler(),
'usa': usa.CartogramHandler(),
'brazil': brazil.CartogramHandler(),
'china': china.CartogramHandler(),
'china2': china2.CartogramHandler(),
'india': india.CartogramHandler(),
'srilanka': srilanka.CartogramHandler(),
'germany': germany.CartogramHandler(),
'indonesia': indonesia.CartogramHandler(),
'singaporeRe': singaporeRe.CartogramHandler(),
'singapore2': singapore2.CartogramHandler(),
# ---addmap.py body marker---
# !!!END DO NOT MODFIY
}

def migrate():
    for key in cartogram_handlers:
        handler_name = cartogram_handlers[key].get_name()
        gen_file = cartogram_handlers[key].get_gen_file()
        id_data = cartogram_handlers[key].csv_to_area_string_and_colors('')
        print("'" + key + "': {'name':'" + handler_name + "', 'file':'" + gen_file + "'},")

        # Write regions data to geojson file
        with open(gen_file, 'r') as openfile: 
            json_obj = json.load(openfile)
        json_obj['regions'] = id_data
        with open(gen_file, "w") as outfile:
            outfile.write(json.dumps(json_obj))

        # Update template file
        template_file = "static/cartdata/{}/template.csv".format(key)
        with open(template_file, 'r') as csvfile:
            reader = csv.reader(csvfile)
            data = list(reader)
        # Move the 4th column to the 2nd column
        for row in data:
            row.insert(1, row.pop(3))
        # Write back to the CSV file
        with open(template_file, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)

migrate()