"""Initial reference data for ALERTIFY (Batangas City only).

Evacuation centers: extracted from EVACUATION-CENTER-2-1.pdf, LGU = "Batangas City"
(5th District) only — names/locations from the detailed listing, capacities and
X/Y coordinates from the matching coordinate table. Every other municipality is
excluded. All records are seeded as *pending verification*; hazard suitability
and operational status are left blank/unknown until an administrator verifies them.
"""

SOURCE_PDF = "EVACUATION-CENTER-2-1.pdf (Batangas Province evacuation center list)"

CATEGORIES = [
    # code, name, icon, description
    ("flood", "Flood", "🌊", "Rising water from heavy rain, overflowing rivers or storm surge."),
    ("typhoon", "Typhoon", "🌀", "Tropical cyclone with strong winds and heavy rain."),
    ("earthquake", "Earthquake", "🏚️", "Ground shaking, possible aftershocks and tsunami along the coast."),
    ("fire", "Fire", "🔥", "Structural, grass or electrical fire."),
    ("volcanic", "Volcanic Activity", "🌋", "Ashfall, volcanic gas or eruption (e.g. Taal Volcano)."),
    ("landslide", "Landslide", "⛰️", "Slope failure, rockfall or mudflow."),
    ("other", "Other Emergency", "⚠️", "Any other emergency not listed above."),
]

# (name, location as written in source, barangay, families, persons, lng(X), lat(Y), note)
EVACUATION_CENTERS = [
    ("Alangilan Central Elementary School", "Alangilan, Batangas City", "Alangilan", 18, 90, 121.06937, 13.78775, None),
    ("Alangilan Senior High School", "Alangilan, Batangas City", "Alangilan", 28, 140, 121.06836, 13.78767, None),
    ("Balagtas Elementary School", "Balagtas, Batangas City", "Balagtas", 26, 130, 121.07066, 13.80149, None),
    ("Balete Elementary School", "Balete, Batangas City", "Balete", 20, 100, 121.06663, 13.83101, None),
    ("Balete National High School", "Balete, Batangas City", "Balete", 10, 50, 121.06561, 13.83573, None),
    ("Balete Relocation Elementary School", "Balete Relocation, Batangas City", "Balete", 20, 100, 121.06071, 13.82077, None),
    ("Banaba East Elementary School", "Banaba East, Batangas City", "Banaba East", 14, 70, 121.05931, 13.81413, None),
    ("Banaba West Elementary School", "Banaba West, Batangas City", "Banaba West", 12, 60, 121.05401, 13.80518, None),
    ("Banaba Center Elementary School", "Banaba Center, Batangas City", "Banaba Center", 16, 80, 121.0623, 13.80804, None),
    ("Banaba South Elementary School", "Banaba South, Batangas City", "Banaba South", 20, 100, 121.05394, 13.78725, None),
    ("Batangas City East Elementary School", "Brgy. 06, P. Herrera St., Batangas City", "Barangay 6 (Poblacion)", 70, 350, 121.06424, 13.76008, None),
    ("Batangas City South Central ES", "Brgy. 11, Batangas City", "Barangay 11 (Poblacion)", 30, 150, 121.06097, 13.76101, None),
    ("South SHS-included in BCSCES list", "Brgy. 11, Batangas City", "Barangay 11 (Poblacion)", 30, 150, 121.06097, 13.76101,
     "Source lists this SHS as included in the Batangas City South Central ES record (same site/coordinates)."),
    ("Batangas National High School", "Brgy. 20, Batangas City", "Barangay 20 (Poblacion)", 30, 150, 121.05489, 13.75485, None),
    ("Batangas Province High School for Culture and Arts", "Brgy. 20, Batangas City", "Barangay 20 (Poblacion)", 30, 150, 121.04554, 13.77619, None),
    ("Bilogo Elementary School", "Bilogo, Batangas City", "Bilogo", 4, 20, 121.16159, 13.7437, None),
    ("Bolbok Elementary School", "Bolbok, Batangas City", "Bolbok", 10, 50, 121.04595, 13.77397, None),
    ("Bucal Elementary School", "Bucal, Batangas City", "Bucal", 8, 40, 121.09575, 13.83995, None),
    ("Calicanto Elementary School", "Caliicanto, Batangas City", "Calicanto", 23, 115, 121.05327, 13.76695, None),
    ("Katandala Elementary School", "Katandala, Batangas City", "Katandala", 14, 70, 121.13854, 13.77358, None),
    ("Concepcion Elementary School", "Concepcion, Batangas City", "Concepcion", 36, 180, 121.0807, 13.8291, None),
    ("Ramos Memorial National High School", "Concepcion, Batangas City", "Concepcion", 22, 110, 121.0837, 13.83133, None),
    ("Conde Itaas Elementary School", "Conde Itaas, Batangas City", "Conde Itaas", 8, 40, 121.12543, 13.7239, None),
    ("Conde Labac Elementary School", "Conde Labac, Batangas City", "Conde Labac", 8, 40, 121.11073, 13.73437, None),
    ("Julian A. Pastor Memorial Elementary School", "Cuta, Batangas City", "Cuta", 42, 210, 121.05495, 13.75113, None),
    ("Cumba Elementary School", "Curnba, Batangas City", "Cumba", 12, 60, 121.13827, 13.68218, None),
    ("Melecio Arceo Memorial Elementary School", "Dalig, Batangas City", "Dalig", 12, 60, 121.08514, 13.77296, None),
    ("Dumantay Elementary School", "Dumantay, Batangas City", "Dumantay", 10, 50, 121.10344, 13.76566, None),
    ("Dumuclay Elementary School", "Dumuclay, Batangas City", "Dumuclay", 14, 72, 121.08928, 13.74598, None),
    ("Gulod Elementary School", "Gulod Itaas, Batangas City", "Gulod Itaas", 4, 20, 121.08252, 13.76193, None),
    ("Gulod Senior High School", "Gulod Itaas, Batangas City", "Gulod Itaas", 4, 20, 121.08224, 13.76203, None),
    ("Haligue Kanluran Elementary School", "Haligue Kanluran, Batangas City", "Haligue Kanluran", 6, 30, 121.09913, 13.68316, None),
    ("Haligue Silangan Elementary School", "Haligue Silangan, Batangas City", "Haligue Silangan", 4, 20, 121.10542, 13.66362, None),
    ("Haligue SHS- included in HSES list", "Haligue Silangan, Batangas City", "Haligue Silangan", 4, 20, 121.10542, 13.66362,
     "Source lists this SHS as included in the Haligue Silangan ES record (same site/coordinates)."),
    ("Kumintang Elementary School", "Kumintang Ilaya, Batangas City", "Kumintang Ilaya", 34, 170, 121.06527, 13.77431, None),
    ("Libjo Elementary School", "Libjo, Batangas City", "Libjo", 24, 120, 121.07163, 13.74409, None),
    ("Libjo National High School", "Libjo, Batangas City", "Libjo", 24, 120, 121.07199, 13.74008, None),
    ("Mahabang Dahilig Elementary School", "Mahabang Dahilig, Batangas City", "Mahabang Dahilig", 10, 50, 121.0929, 13.71026, None),
    ("Mahabang Dahilig Senior High School", "Mahabang Dahilig, Batangas City", "Mahabang Dahilig", 10, 50, 121.0929, 13.71026,
     "Same coordinates as Mahabang Dahilig ES in source."),
    ("Mahacot Elementary School", "Mahacot West, Batangas City", "Mahacot West", 14, 70, 121.1221, 13.77281, None),
    ("Eulalia Talban Ebora Memorial Elementary School", "Malalim, Batangas City", "Malalim", 10, 50, 121.09043, 13.72445, None),
    ("Malibayo Elementary School", "Malibayo, Batangas City", "Malibayo", 10, 50, 121.08431, 13.67192, None),
    ("Malitam Elementary School", "Malitam, Batangas City", "Malitam", 14, 70, 121.05859, 13.74432, None),
    ("Malitam National High School", "Malitam, Batangas City", "Malitam", 14, 70, 121.05475, 13.75527, None),
    ("Maruclap Elementary School", "Maruclap, Batangas City", "Maruclap", 20, 100, 121.11026, 13.68366, None),
    ("Paharang Elementary School", "Paharang West, Batangas City", "Paharang West", 10, 50, 121.13934, 13.75243, None),
    ("Paharang National High School", "Paharang West, Batangas City", "Paharang West", 10, 50, 121.13963, 13.75387, None),
    ("Pallocan East Elementary School", "Pallocan East, Batangas City", "Pallocan East", 10, 50, 121.08055, 13.75367, None),
    ("Jose C. Pastor Elementary School", "Pallocan West, Batangas City", "Pallocan West", 20, 100, 121.06626, 13.75442, None),
    ("Piit Elementary School", "Piit, Pinamucan East, Batangas City", "Pinamucan East", 20, 100, 121.08225, 13.6916, None),
    ("Pinamukan Elementary School", "Pinamukan Proper, Batangas City", "Pinamucan Proper", 10, 50, 121.05414, 13.69777, None),
    ("Pinamucan National High School", "Pinamukan Proper, Batangas City", "Pinamucan Proper", 10, 50, 121.0551, 13.69736, None),
    ("Pinamucan Ibaba Elementary School", "Pinamucan Ibaba, Batangas City", "Pinamucan Ibaba", 14, 70, 121.06227, 13.68733, None),
    ("Sampaga Elementary School", "Sampaga, Batangas City", "Sampaga", 20, 100, 121.1038, 13.75472, None),
    ("San Isidro Elementary School", "San Isidro, Batangas City", "San Isidro", 18, 90, 121.07798, 13.73296, None),
    ("Bagong Silang Elementary School", "Bagong Silang, San Jose Sico, Batangas City", "San Jose Sico", 20, 100, 121.17676, 13.73612, None),
    ("San Jose Sico Elementary School", "San Jose Sico, Batangas City", "San Jose Sico", 16, 80, 121.17173, 13.73908, None),
    ("San Miguel Elementary School", "San Miguel, Batangas City", "San Miguel", 22, 110, 121.11242, 13.71794, None),
    ("San Pedro Elementary School", "San Pedro, Batangas City", "San Pedro", 14, 70, 121.10206, 13.77785, None),
    ("Sta. Clara Elementary School", "Sta Clara, Batangas City", "Sta. Clara", 50, 250, 121.04472, 13.75316, None),
    ("Sta. Rita Elementary School", "Sta Rita Karsada, Batangas City", "Sta. Rita Karsada", 40, 200, 121.04129, 13.77894, None),
    ("Sto. Domingo Elementary School", "Sto. Domingo, Batangas City", "Sto. Domingo", 16, 80, 121.1385, 13.71089, None),
    ("Sto. Nino Elementary School", "Sto Nino, Batangas City", "Sto. Niño", 20, 100, 121.09643, 13.69833, None),
    ("Sto. Nino National High School", "Sto Nino, Batangas City", "Sto. Niño", 20, 100, 121.09589, 13.69781, None),
    ("Sirang Lupa Elementary School", "Sirang Lupa, Batangas City", "Sirang Lupa", 20, 100, 121.09246, 13.7356, None),
    ("Sorosoro Elementary School", "Sorosoro, Batangas City", "Sorosoro", 12, 60, 121.08903, 13.81552, None),
    ("Tinga Sorosoro Integrated School", "Sorosoro, Batangas City", "Sorosoro", 28, 140, 121.09033, 13.80784, None),
    ("Ambulong Elementary School", "Ambulong, Tabangao, Batangas City", "Tabangao Ambulong", 20, 100, 121.07446, 13.71845, None),
    ("Tabangao Elementary School", "Tabangao Aplaya, Batangas City", "Tabangao Aplaya", 20, 100, 121.06226, 13.71487, None),
    ("Tabangao Integrated School", "Tabangao Aplaya, Batangas City", "Tabangao Aplaya", 16, 80, 121.06226, 13.71487,
     "Same coordinates as Tabangao ES in source."),
    ("Dao Elementary School", "Tabangao Dao, Batangas City", "Tabangao Dao", 20, 100, 121.08332, 13.69832, None),
    ("Talahib Payapa Elementary School", "Talahib Payapa, Batangas City", "Talahib Payapa", 20, 100, 121.12282, 13.66471, None),
    ("Talumpok Proper Elementary School", "Talumpok West, Batangas City", "Talumpok West", 10, 50, 121.15389, 13.73267, None),
    ("Talumpok Integrated School", "Talumpok West, Batangas City", "Talumpok West", 10, 50, 121.1548, 13.7328, None),
    ("Talumpok Silangan Elementary School", "Talumpok Silangan, Batangas City", "Talumpok Silangan", 20, 100, 121.16295, 13.72536, None),
    ("Guinto Elementary School", "Talumpok West, Batangas City", "Talumpok West", 20, 100, 121.13635, 13.73362, None),
    ("Tinga Itaas Elementary School", "Tinga Itaas, Batangas City", "Tinga Itaas", 12, 60, 121.08831, 13.79787, None),
    ("Tinga Labac Elementary School", "Tinga Labac, Batangas City", "Tinga Labac", 12, 60, 121.07827, 13.78555, None),
    ("Tulo II Elementary School", "Tulo, Batangas City", "Tulo", 20, 100, 121.12298, 13.7541, None),
    ("Tulo I Elementary School", "Tulo, Batangas City", "Tulo", 12, 60, 121.12312, 13.74509, None),
]

# The 105 barangays of Batangas City (for manual location selection).
BARANGAYS = [f"Barangay {i} (Poblacion)" for i in range(1, 25)] + [
    "Alangilan", "Balagtas", "Balete", "Banaba Center", "Banaba East", "Banaba South", "Banaba West",
    "Bilogo", "Bolbok", "Bucal", "Calicanto", "Katandala", "Concepcion", "Conde Itaas",
    "Conde Labac", "Cumba", "Cuta", "Dalig", "Dela Paz", "Dela Paz Pulot Aplaya", "Dela Paz Pulot Itaas",
    "Dumantay", "Dumuclay", "Gulod Itaas", "Gulod Labac", "Haligue Kanluran", "Haligue Silangan", "Ilihan",
    "Kumintang Ibaba", "Kumintang Ilaya", "Libjo", "Liponpon, Isla Verde", "Maapas", "Mabacong",
    "Mahabang Dahilig", "Mahabang Parang", "Mahacot East", "Mahacot West", "Malalim", "Malibayo",
    "Malitam", "Maruclap", "Pagkilatan", "Paharang East", "Paharang West", "Pallocan East",
    "Pallocan West", "Pinamucan East", "Pinamucan Ibaba", "Pinamucan Proper", "Sampaga",
    "San Agapito, Isla Verde", "San Agustin East, Isla Verde", "San Agustin West, Isla Verde",
    "San Andres, Isla Verde", "San Antonio, Isla Verde", "San Isidro", "San Jose Sico", "San Miguel",
    "San Pedro", "Simlong", "Sirang Lupa", "Sorosoro Ibaba", "Sorosoro Ilaya",
    "Sorosoro Karsada", "Sta. Clara", "Sta. Rita Aplaya", "Sta. Rita Karsada", "Sto. Domingo",
    "Sto. Niño", "Tabangao Ambulong", "Tabangao Aplaya", "Tabangao Dao", "Talahib Pandayan",
    "Talahib Payapa", "Talumpok Silangan", "Talumpok West", "Tinga Itaas",
    "Tinga Labac", "Tulo", "Wawa",
]
BARANGAYS = sorted(set(BARANGAYS), key=lambda b: (not b.startswith("Barangay "), b))

# Approximate bounding box of Batangas City (incl. Isla Verde) for sanity checks.
CITY_BOUNDS = {"min_lat": 13.55, "max_lat": 13.90, "min_lng": 120.95, "max_lng": 121.22}
CITY_CENTER = (13.7565, 121.0583)

CONTACT_SOURCE_NOTE = "Initial reference list — pending administrator verification."

# (organization, category, numbers, description, is_primary)
CONTACTS = [
    ("Philippine National Emergency Hotline", "General Emergency Services", "911",
     "Nationwide 24/7 emergency hotline for police, fire, and medical emergencies.", True),
    ("Mayor's Action Center", "General Emergency Services", "(043) 723-1511",
     "Batangas City government action center for public assistance.", False),
    ("EBD Emergency Health Hotline (24/7)", "General Emergency Services", "0999-222-6626",
     "24/7 emergency health hotline.", False),
    ("BFP Batangas City", "Fire and Police", "(043) 425-7163 / 301-7996 / 0915-602-1984",
     "Bureau of Fire Protection — fire suppression, rescue and fire emergencies.", True),
    ("BFP Alangilan Substation", "Fire and Police", "(043) 702-1973",
     "Bureau of Fire Protection substation serving the Alangilan area.", False),
    ("PNP Batangas City", "Fire and Police", "(043) 408-8023 / 0917-847-5757 / 0916-429-1515",
     "Philippine National Police — crime, public safety and security.", True),
    ("Batangas Medical Center", "Hospitals", "(043) 723-0911 / 740-8307",
     "Government tertiary hospital in Batangas City.", False),
    ("St. Patrick's Hospital & Medical Center", "Hospitals", "(043) 723-1605 / 723-7089 / 723-7090 / 723-7091 / 723-7092",
     "Private hospital and medical center (trunk lines 723-7089 to 723-7092).", False),
    ("Jesus of Nazareth Hospital", "Hospitals", "(043) 723-4144", "Private hospital.", False),
    ("Golden Gate General Hospital", "Hospitals", "(043) 723-2508 / 341-3112", "Private general hospital.", False),
    ("Batangas Healthcare Specialists Medical Center", "Hospitals", "(043) 403-8642 / 741-2088",
     "Private medical center.", False),
    ("United Doctors of St. Camillus de Lellis Hospital and Medical Center", "Hospitals", "0918-994-2074",
     "Private hospital and medical center.", False),
    ("City Disaster Risk Reduction and Management Office (CDRRMO)", "Utilities and Disaster Management",
     "(043) 702-3902", "Coordinates local disaster response, rescue and evacuation in Batangas City.", True),
    ("Meralco", "Utilities and Disaster Management", "16211 / 1622-2847",
     "Power outages, fallen or sparking electric lines.", False),
    ("National Power Corporation – National Highway", "Utilities and Disaster Management", "300-3592",
     "National Power Corporation office.", False),
    ("PrimeWater Batangas City", "Utilities and Disaster Management", "0949-414-2633 / 980-6928",
     "Water supply concerns and pipe leaks.", False),
    ("VAWC Batangas City", "VAWC", "0956-826-7017",
     "Violence Against Women and their Children desk — protection and assistance.", False),
    ("Philippine Red Cross – General Hotline", "Philippine Red Cross – Batangas Chapter", "143",
     "Philippine Red Cross nationwide hotline.", True),
    ("Philippine Red Cross – Batangas City Branch Office", "Philippine Red Cross – Batangas Chapter",
     "0917-135-6219", "Batangas City branch office.", False),
    ("Philippine Red Cross – Emergency Medical Services / ERU", "Philippine Red Cross – Batangas Chapter",
     "0951-282-0000", "Ambulance, emergency medical and emergency response unit.", False),
    ("Philippine Red Cross – Blood Center", "Philippine Red Cross – Batangas Chapter",
     "0917-773-4912 / 0998-851-1107", "Blood requests and blood donation.", False),
]

GUIDANCE_SRC = "Based on NDRRMC/OCD, PAGASA, PHIVOLCS, BFP and Philippine Red Cross public safety guidance"

# --------------------------------------------------------------------------
# Response instructions used by the assessment engine.
# (disaster, section, condition, text, priority)
# section: immediate | avoid | bring | evacuate | contact
# disaster 'general' lines apply to every report.
# --------------------------------------------------------------------------
RESPONSE_INSTRUCTIONS = [
    # ---------------- general
    ("general", "immediate", "trapped", "Call 911 now. Give your exact location (barangay, street, landmark), how many people are with you, and any injuries.", 1),
    ("general", "immediate", "trapped", "Stay where rescuers can find you. Signal with a flashlight, whistle, bright cloth, or by tapping on pipes or walls.", 2),
    ("general", "immediate", "trapped", "Save phone battery: lower screen brightness and send text messages if calls do not go through.", 3),
    ("general", "immediate", "injured", "Give first aid only if you are trained: apply firm, direct pressure on bleeding wounds. Do not move a person with a suspected head, neck, or back injury unless they are in immediate danger.", 5),
    ("general", "immediate", "vulnerable", "Prioritize children, older adults, pregnant individuals, persons with disabilities, and anyone with medical conditions. Keep their medicines and assistive devices with them.", 20),
    ("general", "avoid", "trapped", "Do not attempt risky self-rescue through floodwater, fire, smoke, or collapsed structures.", 1),
    ("general", "avoid", "base", "Do not spread or act on unverified information. Rely on official advisories from the Batangas City government, CDRRMO, PAGASA, and PHIVOLCS.", 90),
    ("general", "bring", "base", "Drinking water and ready-to-eat food for at least 3 days.", 10),
    ("general", "bring", "base", "Maintenance medicines, prescriptions, and a first aid kit.", 11),
    ("general", "bring", "base", "Flashlight, whistle, charged phone and power bank, battery-powered radio.", 12),
    ("general", "bring", "base", "Important documents (IDs, certificates, insurance) in a waterproof bag, and some cash.", 13),
    ("general", "bring", "base", "Extra clothing, blanket, face masks, and hygiene items.", 14),
    ("general", "bring", "vulnerable", "Baby supplies, mobility aids, hearing aids, eyeglasses, and any special medical equipment.", 15),
    ("general", "evacuate", "base", "Follow evacuation orders from the Batangas City government, CDRRMO, and your barangay officials. ALERTIFY's automated assessment does not replace official orders.", 90),
    ("general", "evacuate", "vulnerable", "Evacuate early. People who need assistance should leave before conditions worsen — tell responders about special needs when you call.", 20),
    ("general", "contact", "base", "If anyone is in immediate danger, call 911 (national emergency hotline).", 10),
    ("general", "contact", "base", "Batangas City CDRRMO coordinates local rescue and evacuation — see the Emergency Contacts page.", 20),
    ("general", "contact", "injured", "For medical emergencies call 911 or the Philippine Red Cross (143 / Emergency Medical Services).", 5),

    # ---------------- flood
    ("flood", "immediate", "flood.rising", "Water is rising — move to higher ground now if it is safe to do so. Do not wait for the water to reach your knees.", 3),
    ("flood", "immediate", "flood.deep", "Water at waist level or higher is very dangerous. Move to the highest safe floor of a sturdy building and call for rescue instead of wading out. Avoid enclosed attics where rising water could trap you.", 2),
    ("flood", "immediate", "flood.indoors", "Turn off electricity at the main breaker and close the LPG tank only if you are standing on dry ground and it is safe to do so.", 10),
    ("flood", "immediate", "base", "Move important documents, valuables, and emergency supplies to an upper floor or a higher place.", 30),
    ("flood", "immediate", "base", "Monitor PAGASA rainfall/flood advisories and announcements from the CDRRMO and your barangay.", 40),
    ("flood", "avoid", "base", "Do not walk, swim, or drive through floodwater. About 15 cm (6 in) of moving water can knock you down and 60 cm (2 ft) can sweep away a vehicle.", 2),
    ("flood", "avoid", "base", "Stay away from electric posts, fallen wires, drainage canals, open manholes, and riverbanks.", 3),
    ("flood", "avoid", "base", "Avoid contact with floodwater — it may be contaminated. If you waded in floodwater, especially with wounds, consult a health center about leptospirosis prevention.", 4),
    ("flood", "bring", "base", "Rubber boots, raincoat, and plastic bags to keep items dry.", 20),
    ("flood", "evacuate", "base", "Evacuate to a designated evacuation center when advised by authorities, or right away if you live in a low-lying or flood-prone area and the water is rising.", 5),
    ("flood", "contact", "flood.deep", "With water waist-deep or higher, call 911 or the CDRRMO for rescue rather than attempting to cross the water yourself.", 1),

    # ---------------- typhoon
    ("typhoon", "immediate", "base", "Stay indoors in the strongest interior room, away from windows and glass doors.", 5),
    ("typhoon", "immediate", "base", "Keep updated on PAGASA Tropical Cyclone Wind Signals through radio or your phone.", 30),
    ("typhoon", "immediate", "typhoon.house_major", "Your house is seriously damaged — move to the sturdiest part of the structure and request help to evacuate once it is safe to move.", 2),
    ("typhoon", "immediate", "typhoon.house_minor", "Secure or move away from loose roofing and broken windows. Stay in an undamaged interior room.", 8),
    ("typhoon", "immediate", "typhoon.flooding", "Flooding is reported — follow flood safety: move to higher ground and do not cross floodwater.", 4),
    ("typhoon", "avoid", "base", "Do not go outside during the storm, including during a sudden calm (the eye) — strong winds return suddenly from the opposite direction.", 2),
    ("typhoon", "avoid", "typhoon.lines_down", "Stay far away from fallen trees and power lines and treat every wire as live. Report them to Meralco and the CDRRMO.", 1),
    ("typhoon", "avoid", "base", "Do not use candles or open flames near curtains or light materials during power outages; use flashlights.", 20),
    ("typhoon", "bring", "base", "Battery-powered radio, extra batteries, and rain gear.", 20),
    ("typhoon", "evacuate", "base", "Evacuate before landfall if you live in a coastal, low-lying, or landslide-prone area or in a house made of light materials, especially when authorities order pre-emptive evacuation.", 5),
    ("typhoon", "evacuate", "typhoon.house_major", "A seriously damaged house is not safe shelter. Go to an evacuation center as soon as it is safe to travel.", 2),
    ("typhoon", "contact", "typhoon.lines_down", "Report fallen or sparking power lines to Meralco (16211) and the CDRRMO.", 5),

    # ---------------- earthquake
    ("earthquake", "immediate", "quake.shaking_inside", "DROP, COVER, and HOLD ON: get under a sturdy table, protect your head and neck, and hold on until the shaking stops.", 1),
    ("earthquake", "immediate", "quake.shaking_outside", "Move to an open area away from buildings, trees, electric posts, and power lines. Drop down and protect your head.", 1),
    ("earthquake", "immediate", "quake.vehicle", "Pull over in an open area away from bridges, overpasses, and posts. Stay inside with your seatbelt on until the shaking stops.", 1),
    ("earthquake", "immediate", "base", "When the shaking stops, check yourself and others for injuries, then leave the building calmly using the stairs.", 5),
    ("earthquake", "immediate", "base", "Expect aftershocks. Drop, cover, and hold on every time the ground shakes.", 10),
    ("earthquake", "immediate", "quake.damaged", "The building may be unsafe. Get out once the shaking stops and do not re-enter until it has been inspected by authorities.", 3),
    ("earthquake", "immediate", "trapped", "If trapped under debris: cover your mouth with cloth, tap on a pipe or wall or use a whistle so rescuers can hear you. Shout only as a last resort to avoid inhaling dust.", 2),
    ("earthquake", "avoid", "base", "Do not run outside while the ground is shaking.", 1),
    ("earthquake", "avoid", "base", "Do not use elevators.", 2),
    ("earthquake", "avoid", "base", "Do not light matches or lighters until you are sure there are no gas leaks.", 3),
    ("earthquake", "avoid", "base", "Stay away from damaged buildings, walls, bridges, and steep slopes.", 4),
    ("earthquake", "bring", "base", "Sturdy shoes, hard hat or helmet if available, and dust masks.", 20),
    ("earthquake", "evacuate", "base", "If you are near the coast and the shaking was strong or long, move to high ground immediately — a tsunami may follow. Do not wait for an official warning.", 1),
    ("earthquake", "evacuate", "base", "Proceed to an open evacuation area or designated evacuation center if your building is damaged or authorities advise it.", 10),

    # ---------------- fire
    ("fire", "immediate", "base", "Alert everyone around you and get out. Call 911 / BFP Batangas City once you are outside.", 1),
    ("fire", "immediate", "fire.smoke", "Stay low under the smoke and cover your nose and mouth with a damp cloth.", 2),
    ("fire", "immediate", "fire.in_building", "Before opening a door, touch it with the back of your hand. If it is hot, use another exit. Close doors behind you to slow the fire.", 3),
    ("fire", "immediate", "trapped", "If you cannot get out: close the door, seal gaps with wet cloth, go to a window, signal for help, and call 911 with your exact location.", 2),
    ("fire", "immediate", "base", "If your clothes catch fire: STOP, DROP, and ROLL.", 8),
    ("fire", "immediate", "fire.nearby", "Prepare to leave: grab your go-bag, keep exits clear, and follow instructions from the BFP.", 5),
    ("fire", "avoid", "base", "Do not use elevators.", 1),
    ("fire", "avoid", "base", "Do not go back inside for belongings or pets.", 2),
    ("fire", "avoid", "base", "Do not hide in closets or bathrooms.", 3),
    ("fire", "avoid", "base", "Never use water on electrical, LPG, or cooking-oil fires.", 4),
    ("fire", "avoid", "fire.nearby", "Do not crowd the area or block roads — fire trucks need clear access.", 5),
    ("fire", "evacuate", "base", "Go to a safe assembly area upwind and away from the fire. Do not return until the BFP declares it safe.", 5),
    ("fire", "contact", "base", "Call BFP Batangas City or 911 immediately, even if you think someone else has already called.", 1),

    # ---------------- volcanic
    ("volcanic", "immediate", "base", "Monitor PHIVOLCS volcano bulletins for the current Alert Level and follow LGU advisories.", 10),
    ("volcanic", "immediate", "volcano.ashfall", "Stay indoors, close windows and doors, and seal gaps with damp cloth.", 2),
    ("volcanic", "immediate", "volcano.ashfall", "Wear an N95 mask (or a damp cloth if none is available) and protect your eyes with goggles. Avoid wearing contact lenses.", 3),
    ("volcanic", "immediate", "volcano.heavy_ash", "Heavy ash can collapse roofs. Clear ash only if it is safe, never alone, and wearing protection.", 5),
    ("volcanic", "immediate", "volcano.breathing", "Anyone with breathing difficulty, asthma, or heart or lung conditions should stay indoors and get medical help immediately if symptoms worsen.", 1),
    ("volcanic", "immediate", "volcano.evac_order", "An evacuation order is in effect for your area — evacuate now as directed by authorities.", 0),
    ("volcanic", "avoid", "base", "Do not enter restricted or permanent danger zones declared by PHIVOLCS.", 2),
    ("volcanic", "avoid", "volcano.ashfall", "Avoid driving in heavy ashfall — roads become slippery and visibility drops.", 3),
    ("volcanic", "avoid", "volcano.ashfall", "Cover water containers and food; do not use water that looks contaminated by ash.", 4),
    ("volcanic", "bring", "base", "N95 masks, goggles, and plastic covers for water and food.", 20),
    ("volcanic", "evacuate", "base", "Evacuate when PHIVOLCS raises the Alert Level and the LGU orders evacuation of your area.", 5),
    ("volcanic", "contact", "volcano.breathing", "For severe breathing difficulty call 911 or the Philippine Red Cross Emergency Medical Services.", 1),

    # ---------------- landslide
    ("landslide", "immediate", "landslide.signs", "Warning signs mean the slope may fail. Leave the area immediately and move away from the path of the slope.", 1),
    ("landslide", "immediate", "landslide.occurred", "Move away from the landslide area — more slides may follow. Stay clear until authorities assess it.", 2),
    ("landslide", "immediate", "landslide.rain", "During continuous heavy rain, stay alert to rumbling sounds, cracking trees, tilting posts, and creek water that suddenly turns muddy or drops.", 5),
    ("landslide", "immediate", "base", "Check for injured or trapped people near the slide without entering the slide area; guide rescuers to them.", 10),
    ("landslide", "avoid", "base", "Do not cross areas with moving debris or mudflow.", 1),
    ("landslide", "avoid", "base", "Avoid river valleys and low-lying areas below slopes during heavy rain.", 2),
    ("landslide", "avoid", "base", "Stay away from damaged power lines and broken water or gas lines.", 3),
    ("landslide", "evacuate", "landslide.slope", "Your home is on or below a slope — evacuate pre-emptively when heavy rain warnings are issued.", 2),
    ("landslide", "evacuate", "base", "Proceed to a designated evacuation center away from slopes when advised by authorities.", 5),

    # ---------------- other
    ("other", "immediate", "base", "Move away from the immediate danger to a safe place if you can do so safely.", 1),
    ("other", "immediate", "base", "Call 911 and describe what is happening, where you are, and how many people are affected.", 2),
    ("other", "avoid", "base", "Do not approach hazardous materials, unknown substances, damaged structures, or violent situations.", 2),
    ("other", "evacuate", "base", "Leave the area if instructed by responders or if conditions are getting worse.", 5),
]

# --------------------------------------------------------------------------
# Disaster Guide content (before/during/after/checklist/supplies/reminders/avoid)
# --------------------------------------------------------------------------
GUIDE = {
    "flood": {
        "before": [
            "Know if your home is in a flood-prone or low-lying area and identify the nearest designated evacuation center.",
            "Prepare a go-bag and keep it in an easy-to-reach, elevated place.",
            "Clear drainage and canals around your home of garbage.",
            "Store important documents in waterproof containers on a high shelf.",
            "Plan with your household where to meet and how to communicate if separated.",
        ],
        "during": [
            "Monitor PAGASA advisories and barangay announcements.",
            "Move to higher ground if water is rising — do not wait.",
            "Turn off electricity and LPG only if you are on dry ground and it is safe.",
            "Evacuate when authorities advise; take your go-bag.",
        ],
        "after": [
            "Return home only when authorities say it is safe.",
            "Have a qualified electrician check wiring before turning power back on.",
            "Clean and disinfect everything that got wet; throw away food touched by floodwater.",
            "Watch for signs of leptospirosis (fever, muscle pain) after wading in floodwater and consult a health center.",
        ],
        "checklist": [
            "Go-bag packed and checked", "Evacuation route known", "Emergency numbers saved",
            "Documents in waterproof bag", "Phone and power bank charged",
        ],
        "supplies": ["Rubber boots", "Raincoat", "Drinking water", "Ready-to-eat food", "Flashlight & batteries", "First aid kit"],
        "reminders": ["Floodwater can rise very quickly at night.", "Six inches of moving water can knock an adult down."],
        "avoid": ["Walking, swimming, or driving through floodwater", "Touching electrical equipment while wet", "Letting children play in floodwater"],
    },
    "typhoon": {
        "before": [
            "Follow PAGASA Tropical Cyclone Wind Signals and LGU advisories.",
            "Reinforce roofing and windows; trim branches near your house.",
            "Bring in or tie down loose outdoor items.",
            "Charge phones and power banks; prepare food and water for several days.",
            "Evacuate early if you live near the coast, on slopes, or in a light-material house.",
        ],
        "during": [
            "Stay indoors in the strongest room, away from windows.",
            "Do not go out during the calm eye of the storm.",
            "Keep a battery radio on for updates.",
            "Be ready for flooding and power outages.",
        ],
        "after": [
            "Stay away from fallen trees, damaged structures, and power lines.",
            "Report damaged lines to Meralco and the CDRRMO.",
            "Check your house for structural damage before re-entering.",
            "Boil or treat drinking water if supply may be contaminated.",
        ],
        "checklist": ["Roof and windows secured", "Go-bag ready", "Radio and batteries", "Water stored", "Evacuation center identified"],
        "supplies": ["Battery-powered radio", "Flashlight", "Rope and tarpaulin", "Drinking water", "Canned food"],
        "reminders": ["Wind Signal numbers indicate wind strength, not rainfall — heavy rain can come with any signal."],
        "avoid": ["Going outside during the storm", "Using candles near light materials", "Touching fallen wires"],
    },
    "earthquake": {
        "before": [
            "Secure heavy furniture, cabinets, and appliances to walls.",
            "Identify safe spots at home, school, and work (under sturdy tables, away from glass).",
            "Practice Drop, Cover, and Hold On with your household.",
            "Know the open evacuation areas near you.",
        ],
        "during": [
            "DROP, COVER, and HOLD ON until the shaking stops.",
            "If outdoors, move to an open area away from buildings, posts, and wires.",
            "If driving, pull over away from bridges and overpasses.",
            "If near the coast and the shaking is strong or long, move to high ground immediately after it stops.",
        ],
        "after": [
            "Check for injuries and give first aid if trained.",
            "Leave damaged buildings using the stairs and expect aftershocks.",
            "Check for gas leaks, fires, and electrical damage.",
            "Listen to PHIVOLCS and LGU advisories.",
        ],
        "checklist": ["Furniture anchored", "Safe spots identified", "Household drill done", "Go-bag ready", "Meeting place agreed"],
        "supplies": ["Whistle", "Sturdy shoes", "Dust masks", "Flashlight", "First aid kit"],
        "reminders": ["Most injuries come from falling objects — protect your head and neck."],
        "avoid": ["Running outside while shaking", "Using elevators", "Lighting matches before checking for gas leaks"],
    },
    "fire": {
        "before": [
            "Install smoke alarms and keep a fire extinguisher where you can reach it.",
            "Do not overload electrical outlets; replace damaged wiring.",
            "Store LPG tanks properly and check hoses for leaks.",
            "Plan two ways out of every room and agree on a meeting point outside.",
        ],
        "during": [
            "Alert everyone and get out immediately; call 911 / BFP once outside.",
            "Stay low under smoke and cover your nose and mouth.",
            "Feel doors before opening; use another exit if hot.",
            "Stop, Drop, and Roll if your clothes catch fire.",
        ],
        "after": [
            "Do not re-enter until the BFP says it is safe.",
            "Seek medical care for burns or smoke inhalation.",
            "Contact your barangay for assistance and documentation.",
        ],
        "checklist": ["Smoke alarm working", "Extinguisher available", "Escape plan practiced", "LPG checked"],
        "supplies": ["Fire extinguisher", "Fire blanket", "Flashlight", "First aid kit (burn dressing)"],
        "reminders": ["Smoke, not flames, causes most fire deaths."],
        "avoid": ["Using water on electrical or oil fires", "Going back inside for belongings", "Using elevators"],
    },
    "volcanic": {
        "before": [
            "Know the current PHIVOLCS Alert Level for Taal Volcano and other nearby volcanoes.",
            "Stock N95 masks, goggles, and plastic covers for water and food.",
            "Know your evacuation route and the nearest evacuation center.",
        ],
        "during": [
            "Stay indoors during ashfall; close windows and doors.",
            "Wear an N95 mask and goggles if you must go out.",
            "Evacuate immediately if ordered by authorities.",
            "Protect water sources and food from ash.",
        ],
        "after": [
            "Clear ash from roofs carefully — heavy ash can collapse roofs.",
            "Wet ash before sweeping to reduce dust.",
            "Watch for lahars (volcanic mudflows) during heavy rain.",
        ],
        "checklist": ["N95 masks available", "Goggles available", "Water covered", "Evacuation route known"],
        "supplies": ["N95 masks", "Goggles", "Plastic sheets", "Drinking water", "Medicines for respiratory conditions"],
        "reminders": ["Volcanic ash is abrasive and harmful to lungs and eyes."],
        "avoid": ["Entering danger zones", "Driving in heavy ashfall", "Wearing contact lenses in ashfall"],
    },
    "landslide": {
        "before": [
            "Know whether your area is landslide-prone (MGB geohazard maps).",
            "Watch for cracks in the ground, tilting trees or posts, and new springs.",
            "Plan an evacuation route away from slopes and river channels.",
        ],
        "during": [
            "Leave immediately if you notice warning signs or hear rumbling.",
            "Move away from the path of the slide, toward stable ground.",
            "Stay alert during continuous heavy rain, especially at night.",
        ],
        "after": [
            "Stay away from the slide area — more slides may follow.",
            "Check for injured or trapped people and guide rescuers to them.",
            "Report broken utility lines and damaged roads.",
        ],
        "checklist": ["Hazard area known", "Warning signs learned", "Go-bag ready", "Evacuation route away from slopes"],
        "supplies": ["Flashlight", "Whistle", "Rain gear", "First aid kit"],
        "reminders": ["Muddy or suddenly decreasing creek water can signal a landslide upstream."],
        "avoid": ["Staying below steep slopes during heavy rain", "Crossing debris flows", "Re-entering slide areas"],
    },
}
