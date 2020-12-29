import threading
import tmdbsimple as tmdb
tmdb.API_KEY = 'API_KEY_HERE'

# Load in list of hosts
with open("hosts.txt") as hosts_file:
    hosts = hosts_file.read()


def _run_movie_provider(movie, provider_name, provider_source, cb):
    try:
        year = movie['release_date'][0:4]
        imdb_id_number = movie['imdb_id'][2:]
        url = provider_source.movie(imdb_id_number, movie['title'], movie['original_title'], [], year)
        results_raw = provider_source.sources(url, hosts, []) or []
        results = map(lambda obj: obj['url'], results_raw)
        cb(results)
    except:
        print("ERROR IN PROVIDER: " + provider_name)
        cb([])


def run_movie_providers(providers, tmdb_id, data_cb, done_cb):
    movie = tmdb.Movies(tmdb_id).info()
    movie_providers = filter(lambda p: hasattr(p[1], 'movie'), providers)
    finished_providers = {'count': 0}

    def cb(results):
        data_cb(results)
        finished_providers['count'] += 1
        if finished_providers['count'] == len(movie_providers):
            done_cb()

    workers = []
    for provider in movie_providers:
        worker = threading.Thread(target=_run_movie_provider, args=(movie, provider[0], provider[1], cb))
        workers.append(worker)
        worker.start()
