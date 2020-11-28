import threading
from time import sleep
from imdb import IMDb
from bootstrap_scrapers import bootstrap_scrapers

# Load in list of hosts
with open("hosts.txt") as hosts_file:
    hosts = hosts_file.read()

# Prompt user for movie id and retrieve details
imdb = raw_input("Enter IMDB Movie ID [6751668]: ")
if imdb == '':
    imdb = '6751668'
ia = IMDb()
movie_info = ia.get_movie(imdb)
year = movie_info['year']
title = movie_info['title']
localtitle = title
try:
    localtitle = movie_info['canonical title']
except:
    pass

# Worker thread to get link from provider
FINISHED_PROVIDERS = 0
RESOLVED_URLS = []
def worker_thread(provider_name, provider_source):
    global FINISHED_PROVIDERS
    global RESOLVED_URLS
    try:
        if hasattr(provider_source, 'movie'):
            url = provider_source.movie(imdb, title, localtitle, [], year)
            print(url)
            results = provider_source.sources(url, hosts, [])
            if results is None or len(results) == 0:
                pass # print("No results for " + provider_name)
            else:
                for result in results:
                    RESOLVED_URLS.append(result['url'])
    except:
        print("ERROR IN PROVIDER: " + provider_name)
    FINISHED_PROVIDERS += 1


# Get provider list
providers = bootstrap_scrapers()

# Spawn worker threads
workers = []
for provider in providers:
    worker = threading.Thread(target=worker_thread, args=(provider[0], provider[1]))
    workers.append(worker)
    worker.start()

# Wait for workers to finish
while FINISHED_PROVIDERS < len(workers):
    sleep(1)

# Display scraped urls
print("-----------------------")
print("FINISHED FETCHING URLS:")
print("\n".join(RESOLVED_URLS))
