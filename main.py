import requests
import xml.etree.ElementTree as ET
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import NumberValidator

base_url = "https://api.geekdo.com/xmlapi"

def main():
    action = inquirer.select(
        message="What do you want to do:",
        choices=[
            Choice(value="collection", name="Get my collection"),
            Choice(value="by_id", name="Find a game by ID" ),
            Choice(value="by_name", name="Find a game by name"),
            Choice(value=None, name="Exit"),
        ],
        default="collection",
    ).execute()

    if action:

        if ("collection" == action):
            username = inquirer.text(message="What's your BGG username?").execute()

            get_collection(username)

        if ("by_id" == action):
            id = inquirer.text(message="What's the ID?", validate=NumberValidator()).execute()

            get_boardgame_by_id(id, True)

        if ("by_name" == action):
            name = inquirer.text(message="What's the name of the game?").execute()

            search_boardgame(name)

def get_collection(username = ""):

    if ("" == username ):
        return

    collection = []
    wishlist = []

    collection_route = f"{base_url}/collection/{username}"

    print(f"Looking for this user's BGG collection: {username}\n")

    root = get_xml_root(collection_route)

    if ("" == root):
        return

    for item in root.iter('item'):
        status = item.find('status')
        owned = status.get('own')
        wishlisted = status.get('wishlist')

        name = item.find('name').text

        if ( "1" == owned ):
            collection.append(name)

        if ( "1" == wishlisted ):
            wishlist.append(name)

    if ( 0 < len(collection) ):
        print(f"I found these games in your collection:\n")

        for gaem in collection:
            print(f"{gaem}\r")
    else:
        print("I found no games in your collection.")

    if ( 0 < len(wishlist) ):
        print(f"\nI also found these games on your wishlist:\n")

        for gaem in wishlist:
            print(f"{gaem}\r")

def get_boardgame_by_id(id = 0, command=False):

    if (0==id):
        return

    boardgame_route = f"{base_url}/boardgame/{id}"

    if ( command ):
        print(f"Looking for a game with this ID: {id}\n")

    root = get_xml_root(boardgame_route)

    name = root.find('boardgame/name[@primary="true"]').text

    designer_node = root.find('boardgame/boardgamedesigner')

    if ( designer_node is not None ):
        designer = designer_node.text

    published = root.find('boardgame/yearpublished').text
    min_players = root.find('boardgame/minplayers').text
    max_players = root.find('boardgame/maxplayers').text

    player_poll = root.find('boardgame/poll[@name="suggested_numplayers"]')
    best_playercount = parse_suggest_player_polls(player_poll)
    player_string = f"It plays between {min_players} and {max_players} players"

    if command:
        print(f"I have found this game: {name}.\n")
    else:
        print(f"I have found a game with that name!\n")

    if designer_node is not None:
        print(f"It was designed by {designer} and published in {published}.\n")
    else:
        print(f"I've no idea who designed it, but it was published in {published}.\n")

    if ( 0 != best_playercount ):
        player_string += f", but polls suggest that it's best with {best_playercount} players."
    else:
        player_string += "."

    print(player_string)

def search_boardgame(query = ""):

    if (""==query):
        return

    search_route = f"{base_url}/search?search={query}"

    print(f"Looking for a game with this query: \"{query}\"\n")

    root = get_xml_root(search_route)

    results = root.findall('boardgame')
    result_count = len(results)

    if ( 0 == result_count ):
        retry = inquirer.confirm(message="I've found nothing. Want to try again?", default=True).execute()

        if retry:
            new_query = inquirer.text(message="Okay, great. What's the name of the game?", default=query).execute()

            search_boardgame(new_query)

        else:
            return

    if (1 < result_count):
        found_games = []
        game_id = 0

        for game in root.iter('boardgame'):
            name = game.find('name')

            if (None != name):
                found_games.append(name.text)

                if name.text == query:
                    game_id = game.get("objectid")

        if query in found_games and 0 != game_id:
            get_boardgame_by_id( game_id )

        else:
            retry = inquirer.confirm(message=f"I've found {result_count} results, but none match your search query exactly. Would you like to refine your search?", default=True).execute()

            if retry:
                new_query = inquirer.text(message="Okay, great. What game are you looking for?", default=query).execute()

                search_boardgame(new_query)
            else:
                print(f"No problem, here are the games I did find:\n")

                for gaem in found_games:
                    print(f"{gaem}\r")

            return

    if (1 == result_count):
        game_id = root.find('boardgame').get("objectid")

        get_boardgame_by_id( game_id )

def get_xml_root(route = ""):

    if ("" == route):
        return

    req = requests.get(route)
    root = ET.fromstring(req.content)

    return root

def parse_suggest_player_polls(poll = ""):

    if ( "" == poll ):
        return 0

    best_playercount = 0
    most_votes = 0

    for result in poll.iter('results'):
        poll_player_count = result.get('numplayers')

        for result_count in result.iter('result'):
            vote_name = result_count.get("value")

            if ( "Best" != vote_name ):
                continue

            vote_count = int(result_count.get('numvotes'))

            if vote_count > most_votes:
                most_votes = vote_count
                best_playercount = poll_player_count

    return best_playercount

if __name__ == "__main__":
    main()
