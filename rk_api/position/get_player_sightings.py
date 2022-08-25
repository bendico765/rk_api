import aiohttp
from bs4 import BeautifulSoup


__all__ = ["get_player_sightings"]


async def get_player_id(username: str) -> int:
    """
    Cerca l'id dell'username all'interno del tool ryence e lo restituisce.

    Se viene trovato, restituisce l'id del giocatore.

    Nel caso in cui l'id non sia trovato, viene lanciata  un'eccezione KeyError
    """
    async with aiohttp.ClientSession() as session:
        url = 'https://www.ryence.de/RK/evaluation/person/person_browser.php/post'
        payload = {"pname": username, "pSelectedIds": ""}
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                raise ConnectionRefusedError
            # parsing della pagina web
            html = await res.text()
            soup = BeautifulSoup(html, 'html.parser')
            general_table = soup.find(id='selectiontable').find('tbody')
            if general_table is None:  # questo attributo manca se l'username non è presente
                raise KeyError
            # ricerca dell'username nella tabella
            for row in general_table('tr'):
                row_username = row('td')[1].text
                row_username = row_username.replace('\n', '')
                if row_username == username:
                    player_id = row('td')[0].find('input')['value']
                    break
            else:
                raise KeyError
            return int(player_id)


async def get_player_sightings(username: str, number_of_sightings: int) -> dict:
    """
    Restituisce gli ultimi avvistamenti riguardanti il player cercato.

    Le informazioni sono reperite dal tool https://www.ryence.de/

    In caso di successo viene restituito un dizionario contenente il link
    al profilo dell'utente, ed una lista di dizionari contenente
    gli ultimi avvistamenti.

    Parametri:
        username (str): nome dell'utente di cui ricercare gli avvistamenti
        numberOfSightings (int): numero di avvistamenti da ricercare

    Formato del dizionario restituito:

    {
        "profile_link": ... ,
        "sighting_list":
        [
            {
                "date": ...
                "town": ...
                "province": ...
                "kingdom": ...
            },
            ...
        ]
    }

    """
    # ottenimento dell'id del player
    player_id = await get_player_id(username)
    # scarico la tabella e ne faccio il parsing
    remove_special_chars = lambda string: string.replace('\n', '').replace('\t', '')
    async with aiohttp.ClientSession() as session:
        url = 'https://www.ryence.de/RK/evaluation/person/person_overview.php'
        payload = {'pSelectedIds': player_id}
        async with session.post(url, data=payload) as res:
            if res.status != 200:
                raise ConnectionRefusedError
            html = await res.text()
            soup = BeautifulSoup(html, 'html.parser')
            # link al profilo dell'utente, a cui viene sostiuito il
            # reindirizzamento alla versione tedesca con quello alla
            # versione italiana
            profile_link = soup.find(id="persinfostable")('tbody')[0]('tr')[0]('td')[0]('a')[0]['href']
            profile_link = profile_link.replace(
                'http://www.diekoenigreiche.com/FichePersonnage.php?',
                'https://www.renaissancekingdoms.com/FichePersonnage.php?')
            table = soup.find(id='sightingstable')
            sighting_list = list()
            sighting_index = 0  # contatore degli avvistamenti
            for row in table('tr')[1:]:
                if sighting_index >= number_of_sightings:
                    break
                td = row('td')
                date = remove_special_chars(td[0].text)
                town = remove_special_chars(td[2].text)
                province = td[3].find('span')['title']
                kingdom = td[4].find('span').text
                sight_data = {
                    "date": date,
                    "town": town,
                    "province": province,
                    "kingdom": kingdom
                }
                sighting_list.append(sight_data)
                sighting_index += 1
            return {
                "profile_link": profile_link,
                "sighting_list": sighting_list
            }
