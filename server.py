from bootstrap_scrapers import bootstrap_scrapers
from provider_runner import run_movie_providers
from websocket_server import WebsocketServer
import json

providers = bootstrap_scrapers()


def get_movie(client, server, req):
    tmdb_id = int(req)
    existing_movies = []

    def send_movies(movie_urls):
        new_urls = filter(lambda url: url not in existing_movies, movie_urls)
        existing_movies.extend(new_urls)
        if len(movie_urls):
            res = json.dumps({"type": "data", "data": movie_urls})
            server.send_message(client, res)

    def send_done():
        res = json.dumps({"type": "done"})
        server.send_message(client, res)

    run_movie_providers(providers, tmdb_id, send_movies, send_done)


server = WebsocketServer(9996, host='0.0.0.0')
server.set_fn_message_received(get_movie)
server.run_forever()
