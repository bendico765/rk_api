import re
import aiohttp
from bs4 import BeautifulSoup

__all__ = ["get_player_stats"]


def parse_last_connection_date(text: str) -> str:
    """
    Usando espressioni regolari, estrapola da text
    la data dell'ultima connessione effettuata
    da un giocatore e la restituisce in una stringa.
    """
    day = re.findall('[0-9][0-9] \w*', text)[0].split(' ')[0]
    month = re.findall('[0-9][0-9] \w*', text)[0].split(' ')[1]
    year = re.findall('\d\d\d\d', text)[0]
    return f'{day} {month} {year}'


def parse_stats(extra_info: str) -> str:
    """
    Estrapola dal testo lo stato del personaggio e lo restituisce come stringa
    """
    if 'is DEAD' in extra_info:
        return 'Dead'
    if 'is in retreat' in extra_info:
        return 'Retreat'
    if 'is in jail now' in extra_info:
        return 'Jail'
    if 'is, at present, set aside' in extra_info:
        return 'Set aside'
    return 'Active'


async def get_player_stats(login_username: str, login_password: str, username: str) -> dict:
    """
    Estrae le caratteristiche del personaggio specificato con l'username e le restituisce in un dizionario.

    Le caratteristiche restituite sono:
        -profile_link : link al profilo sul sito dei regni
        -complete_name: nome completo
        -residency: residenza
        -clan_name: nome del clan ('-' se non presente)
        -level: livello del personaggio
        -charism: punteggio carisma
        -strenght: punteggio forza
        -reputation: punteggio reputazione
        -intelligence: punteggio intelligenza
        -blason_image: link all'immagine del blasone sul profilo
        -status: status personaggio
        -sponsor: personaggio sponsor (l'eventuale referrer, '-' se non presente)
        -trusted_by_users: lista di personaggi ad aver dato la fiducia al giocatore
        -married: nome del personaggio sposo/a ('-' se non presente)
        -declared_users: lista di dichiarati
        -last_connection: data di ultima connessione del personaggio ('-' se non disponibile)
    """
    remove_special_chars = lambda string: string.replace('\n', '').replace('\t', '')
    url = f'https://www.renaissancekingdoms.com/ConnexionKC.php?fp={username}'
    payload = {
        'login': login_username,
        'password': login_password
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                raise ConnectionRefusedError
            html = await res.text()
            soup = BeautifulSoup(html, 'html.parser')
            if soup.find_all(class_='nomPersonnage') == []:
                raise KeyError  # pg inesistente
            profile_link = f"https://www.renaissancekingdoms.com/FichePersonnage.php?login={username}"
            complete_name = soup.find(class_='nomPersonnage').text
            residency = remove_special_chars(soup.find(class_='lieuPersonnage').text)
            level = soup.find(class_='niveauPersonnage').text
            charism = soup.find(id='moi_charisme').text
            strenght = soup.find(id='moi_force').text
            reputation = soup.find(id='moi_reputation').text
            intelligence = soup.find(id='moi_intelligence').text
            blason_image = soup.find(id='villeImageBlason')['src']
            # se il blasone del clan è un'immagine caricata dagli
            # utenti il link va bene cosi come è, altrimenti bisogna
            # togliere il punto iniziale ed aggiungere il link
            # del sito dei regni
            if blason_image[0] == '.':
                blason_image = 'https://lesroyaumes.cdn.oxv.fr' + blason_image[1:]
            # informazioni extra della quarta pagina
            clan_name = '-'
            sponsor = '-'
            trusted_by_users = []
            declared_users = []
            married = '-'
            last_connection = '-'
            extra_info_block = soup.find(class_="informationsHRP")
            for x in extra_info_block.findAll("div"):
                clan_block = x.find(class_="lien_default")
                if clan_block is not None and clan_block.has_attr("target") is True:
                    clan_name = clan_block.text
                if "sponsor" in x.text:
                    sponsor = x.find(class_="lien_default").text
            for x in extra_info_block.findAll('p'):
                if 'Married' in x.text:
                    married = x.find(class_="lien_default").text
                if "trust" in x.text:
                    trusted_by_users = [name.text for name in x.findAll("a")]
                if "login" in x.text:
                    last_connection = parse_last_connection_date(x.text)
            declared_block = soup.find(class_="FPContentBlocInfosElem")
            if declared_block.text != "\n\n":
                declared_users = remove_special_chars(declared_block.text).split(',')
            status = parse_stats(extra_info_block.text)
            return {
                'profile_link': profile_link,
                'complete_name': complete_name,
                'residency': residency,
                'clan_name': clan_name,
                'level': level,
                'charism': charism,
                'strenght': strenght,
                'reputation': reputation,
                'intelligence': intelligence,
                'blason_image': blason_image,
                'status': status,
                'sponsor': sponsor,
                'trusted_by_users': trusted_by_users,
                'married': married,
                'declared_users': declared_users,
                'last_connection': last_connection
            }

