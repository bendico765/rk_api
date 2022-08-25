import aiohttp
import json
import asyncio
import re
from base64 import b64encode
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO


__all__ = ["get_player_img"]


class ListeCalque:
	def __init__(self):
		self._calques = []

	def __str__(self):
		return str(self._calques)

	def ajoute_calque(self, src, zIndex, tag):
		self._calques.append(
			{
				"src": "https://www.renaissancekingdoms.com" + src[1:],
				"zIndex": int(zIndex),
				"tag": tag
			}
		)


def genere_contexte(login: str, sexe: str, code_visage: str, items: str) -> dict:
	"""
	Dato il dizionario contenuto dalla pagina html, lo parsa per estrapolarne le caratteristiche
	fisiche del personaggio
	"""
	default_code_visage = "M00000000000000000000"
	for i in range(1, len(default_code_visage)):
		if i >= len(code_visage):
			code_visage += default_code_visage[i]
	contexte = {
		"login": login.lower(),
		"sexe": sexe,
		"portraitPersonnalise": code_visage[0] == "P",
		"visage": int(code_visage[1]),
		"couleurPeau": int(code_visage[2]),
		"marques": int(code_visage[3]),
		"sourcils": int(code_visage[4]),
		"couleurSourcils": int(code_visage[5]),
		"yeux": int(code_visage[6]),
		"couleurYeux": int(code_visage[7]),
		"nez": int(code_visage[8]),
		"bouche": int(code_visage[9]),
		"couleurBouche": int(code_visage[10]),
		"cheveux": int(code_visage[11]),
		"couleurCheveux": int(code_visage[12]),
		"barbe": int(code_visage[13]),
		"couleurBarbe": int(code_visage[14]),
		"emotions": {
			"sourcils": int(code_visage[15]),
			"yeux": int(code_visage[16]),
			"iris": int(code_visage[17]),
			"nez": int(code_visage[18]),
			"bouche": int(code_visage[19]),
			"barbe": int(code_visage[20])
		},
		"postureMainG": 0,
		"postureMainD": 0,
		"slotsMasques": {},
		"format": "png"
	}
	for item in items:
		if item["postureMainG"] is not None and item["postureMainG"] != 0:
			contexte["postureMainG"] = item["postureMainG"]
		if item["postureMainD"] is not None and item["postureMainD"] != 0:
			contexte["postureMainD"] = item["postureMainD"]
		for slot in item["slotsMasques"]:
			regex = r"/([MF]_)(.*)/"
			correspondances = re.findall(regex, slot)
			if correspondances != []:
				if correspondances[1] == (sexe + "_"):
					contexte["slotsMasques"][correspondances[2]] = correspondances[2]
			else:
				contexte["slotsMasques"][slot] = slot
	return contexte


def genere_corps(liste_calque: ListeCalque, contexte: dict):
	slots = {
		"mainD": {"nom": "MainD", "zIndex": 2001},
		"mainG": {"nom": "MainG", "zIndex": 17000},
		"sousVetements": {"nom": "SousVetements", "zIndex": 2002},
		"visage": {"nom": "Visage", "zIndex": 7200},
		"cheveuxAvants": {"nom": "CheveuxAvants", "zIndex": 10000},
		"cheveuxIntermediaires": {"nom": "CheveuxIntermediaires", "zIndex": 7000},
		"cheveuxArrieres": {"nom": "CheveuxArrieres", "zIndex": 1500},
		"corps": {"nom": "Corps", "zIndex": 2000},
		"cheveux": {"nom": "Cheveux", "zIndex": 10000},
		"personnage": {"nom": "Personnage", "zIndex": 20000},
		"ombre": {"nom": "Ombre", "zIndex": 10}
	}
	if slots["personnage"]["nom"] in contexte["slotsMasques"]:
		return
	racine_images = "./images/personnages_midas/"
	if contexte["sexe"] == "F":
		racine_images += "femmes/corps/"
	else:
		racine_images += "hommes/corps/"
	if slots["mainG"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}mainGauche_p{}_m{}{}.{}".format(
				racine_images,
				contexte["couleurPeau"],
				contexte["postureMainG"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["mainG"]["zIndex"],
            "corps"
		)
	if slots["mainD"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}mainDroite_p{}_m{}{}.{}".format(
				racine_images,
				contexte["couleurPeau"],
				contexte["postureMainD"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["mainD"]["zIndex"],
			"corps"
		)
	if slots["cheveuxAvants"]["nom"] not in contexte["slotsMasques"] and slots["cheveux"]["nom"] not in contexte[ "slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}cheveuxAvants_{}_c{}{}.{}".format(
				racine_images,
				contexte["cheveux"],
				contexte["couleurCheveux"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["cheveuxAvants"]["zIndex"],
			"visage"
		)
	if slots["visage"]["nom"] not in contexte["slotsMasques"]:
		if contexte["sexe"] != "F":
			liste_calque.ajoute_calque(
				"{}barbe_{}_c{}_e{}{}.{}".format(
					racine_images,
					contexte["barbe"],
					contexte["couleurBarbe"],
					contexte["emotions"]["barbe"],
					contexte["resolution"],
					contexte["format"]
				),
				slots["visage"]["zIndex"] + 7,
				"visage"
			)
		liste_calque.ajoute_calque(
			"{}marques_{}_p{}{}.{}".format(
			    racine_images,
			    contexte["marques"],
			    contexte["couleurPeau"],
			    contexte["resolution"],
			    contexte["format"]
			),
			slots["visage"]["zIndex"] + 6,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}sourcils_{}_c{}_e{}{}.{}".format(
				racine_images,
				contexte["sourcils"],
				contexte["couleurSourcils"],
				contexte["emotions"]["sourcils"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"] + 5,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}yeux_{}_p{}_e{}{}.{}".format(
				racine_images,
				contexte["yeux"],
				contexte["couleurPeau"],
				contexte["emotions"]["yeux"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"] + 4,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}iris_0_c{}_e{}{}.{}".format(
				racine_images,
				contexte["couleurYeux"],
				contexte["emotions"]["iris"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"] + 3,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}nez_{}_p{}_e{}{}.{}".format(
				racine_images,
				contexte["nez"],
				contexte["couleurPeau"],
				contexte["emotions"]["nez"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"] + 2,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}bouche_{}_c{}_p{}_e{}{}.{}".format(
				racine_images,
				contexte["bouche"],
				contexte["couleurBouche"],
				contexte["couleurPeau"],
				contexte["emotions"]["bouche"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"] + 1,
			"visage"
		)
		liste_calque.ajoute_calque(
			"{}visage_{}_p{}{}.{}".format(
				racine_images,
				contexte["visage"],
				contexte["couleurPeau"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["visage"]["zIndex"],
			"visage"
		)
	if slots["cheveuxIntermediaires"]["nom"] not in contexte["slotsMasques"] and slots["cheveux"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}cheveuxIntermediaires_{}_c{}{}.{}".format(
				racine_images,
				contexte["cheveux"],
				contexte["couleurCheveux"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["cheveuxIntermediaires"]["zIndex"],
			"visage"
		)
	if slots["sousVetements"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}sousVetements{}.{}".format(
				racine_images,
				contexte["resolution"],
				contexte["format"]
			),
			slots["sousVetements"]["zIndex"],
			"corps"
		)
	if slots["corps"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}corps_p{}{}.{}".format(
				racine_images,
				contexte["couleurPeau"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["corps"]["zIndex"],
			"corps"
		)
	if slots["cheveuxArrieres"]["nom"] not in contexte["slotsMasques"] and slots["cheveux"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}cheveuxArrieres_{}_c{}{}.{}".format(
				racine_images,
				contexte["cheveux"],
				contexte["couleurCheveux"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["cheveuxArrieres"]["zIndex"],
			"visage"
		)
	if slots["ombre"]["nom"] not in contexte["slotsMasques"]:
		liste_calque.ajoute_calque(
			"{}ombre{}.{}".format(
				racine_images,
				contexte["resolution"],
				contexte["format"]
			),
			slots["ombre"]["zIndex"],
			"corps"
		)
	if "portraitPersonnalise" in contexte and "login" in contexte:
		liste_calque.ajoute_calque(
			"{}/portraitsPersonnalises/{}_0{}.{}".format(
				"./images/personnages_midas/",
				contexte["login"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["cheveuxArrieres"]["zIndex"],
			"visagePersonnalise"
		)
		liste_calque.ajoute_calque(
			"{}/portraitsPersonnalises/{}_1{}.{}".format(
				"./images/personnages_midas/",
				contexte["login"],
				contexte["resolution"],
				contexte["format"]
			),
			slots["cheveuxAvants"]["zIndex"],
			"visagePersonnalise"
		)


def get_src_equipement(contexte: dict, item: dict, i: int = 0):
	nom = item["nom"]
	if "declinaison" in item and item["declinaison"] != "" and int(item["declinaison"]) != 99:
		nom += "_d{}".format(item["declinaison"])
	if "dependCouleurPeau" in item and item["dependCouleurPeau"]:
		nom += "_p{}".format(contexte["couleurPeau"]);
	if "dependPostureMainG" in item and item["dependPostureMainG"]:
		nom += "_m{}".format(contexte["postureMainG"]);
	if "dependPostureMainD" in item and item["dependPostureMainD"]:
		nom += "_n{}".format(contexte["postureMainD"]);
	nom += f"_{i}"
	if contexte["sexe"] == "F":
		tmp = "femmes"
	else:
		tmp = "hommes"
	src = "{}{}/vetements/{}{}.{}".format("./images/personnages_midas/", tmp, nom, contexte["resolution"], contexte["format"])
	if item["slot"] == "Fond":
		src = "{}fonds/{}{}.{}".format("./images/personnages_midas/", nom, contexte["resolution"], contexte["format"])
	else:
		if item["slot"] == "Cadre":
			src = "{}cadres/{}{}.{}".format("./images/personnages_midas/", nom, contexte["resolution"], contexte["format"])
	return src


def genere_equipement(liste_calque: ListeCalque, contexte: dict, item: dict):
	if item["slot"] in contexte["slotsMasques"]:
		return
	for i in range(len(item["zIndexCalques"])):
		zIndex = item["zIndexCalques"][i]
		src = get_src_equipement(contexte, item, i)
		liste_calque.ajoute_calque(src, zIndex, item["slot"])


def genere_apercu(infosApercu: dict):
	slots_masques = []
	contexte = genere_contexte(infosApercu["login"], infosApercu["sexe"], infosApercu["codeVisage"], infosApercu["equipement"])
	liste_calque = ListeCalque()
	contexte["format"] = "png"
	contexte["resolution"] = "_@2X"
	for slot_a_masquer in slots_masques:
		contexte["slotsMasques"][slot_a_masquer] = slot_a_masquer
	genere_corps(liste_calque, contexte)
	for item in infosApercu["equipement"]:
		genere_equipement(liste_calque, contexte, item)
	return liste_calque


async def download_metadata(username: str, login_username: str, login_password: str) -> dict:
	"""
	Accede al sito dei regni utilizzando le credenziali passate come parametri e
	scarica i metadati inerenti l'aspetto del player cercato, restituendoli all'interno di un dizionario

	Parametri:
		username (str): l'username del player di cui scaricare le informazioni
		login_username (str): username dell'utente con cui accedere al sito dei regni
		login_password (str): password con cui accedere al sito dei regni

	Restituisce:
		(dict): dizionario contenente le informazioni sull'aspetto ed equipaggiamento del giocatore cercato.
	"""
	request_url = f"https://www.renaissancekingdoms.com/ZoomPersonnage.php?login={username}"
	async with aiohttp.ClientSession() as session:
		payload = {
			"login": login_username,
			"password": login_password
		}
		async with session.post(f'https://www.renaissancekingdoms.com/ConnexionKC.php?fp={username}', data=payload) as _:
			async with session.get(request_url) as res:
				html = await res.text()
				soup = BeautifulSoup(html, 'html.parser')
				items_block = soup.find(class_='apercu_personnage_rar')
				return json.loads(items_block.text)


async def download_image(url: str) -> "<class bytes>":
	"""
	Scarica il contenuto dell'url specificato come parametro e lo restituisce.

	Parametri:
		url (str): url da cui scaricare il contenuto

	Restituisce:
		(class bytes): contenuto scaricato
	"""
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as res:
			if res.status == 200:
				return await res.read()
			else:
				return None


async def download_data(username: str, login_username: str, login_password: str) -> list:
	"""
	Accede al sito dei regni utilizzando le credenziali passate come parametri e
	scarica i file immagine che compongono l'aspetto del player cercato, restituendoli
	all'interno di una lista.

	Parametri:
		username (str): l'username del player di cui scaricare le immagine
		login_username (str): username dell'utente con cui accedere al sito dei regni
		login_password (str): password con cui accedere al sito dei regni

	Restituisce:
		(list): lista contenente i file immagine (di tipo <class bytes>) che compono l'aspetto dell'utente
	"""
	mysort = lambda x: x["zIndex"]
	# ottenimento metadati sull'immagine del personaggio
	elements = await download_metadata(username, login_username, login_password)
	# ottenimento degli url dei file immagine da scaricare
	liste_calque = genere_apercu(elements)
	liste_calque._calques.sort(key=mysort)
	# ottenimento immagini
	tasks = [asyncio.ensure_future(download_image(item["src"])) for item in liste_calque._calques]
	return await asyncio.gather(*tasks)


def compose_images(raw_images: list) -> "<class bytes>":
	"""
	La funzione compone le immagini passate come parametro, iterando
	la lista e sovrapponendo le immagini una dopo l'altra; la funzione
	restituisce poi il risultato finale.

	Parametri:
		raw_images (list): la lista di immagini da comporre; un elemento può essere il nome di un file su disco o un
							flusso di bytes
	Restituisce:
		(<class bytes>): l'immagine risultante
	"""
	file_object = BytesIO()
	# conversione delle immagini in immagini RGBA
	convert_function = lambda img: Image.open(img).convert("RGBA")
	images = map(convert_function, raw_images)
	# creazione dell'immagine finale
	result_img = Image.new("RGBA", (512, 1024))
	for image in images:
		result_img = Image.alpha_composite(result_img, image)
	result_img.save(file_object, format="PNG")
	return file_object.getvalue()


async def get_player_img(login_username:str, login_password:str, username: str) -> dict:
	# ottenimento delle immagini dei singoli vestiti
	images = await download_data(username, login_username, login_password)
	# eliminazione delle immagini non recuperate
	filtered_results = filter(lambda x: x is not None, images)
	# impacchettamento delle immagini in flussi di bytes
	wrapped_images = map(BytesIO, filtered_results)
	# composizione delle immagini
	result_bytes = compose_images(wrapped_images)
	base64_bytes = b64encode(result_bytes)
	base64_string = base64_bytes.decode("utf-8")
	return base64_string
