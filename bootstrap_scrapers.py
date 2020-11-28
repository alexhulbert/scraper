import os
import sys
import shutil
from UserDict import UserDict

# Uncomment to use local kodi addondev repo
# sys.path.append(os.path.join(os.getcwd(), 'kodi-addondev', 'src'))

import requests
import zipfile
from git import Repo
from lxml import etree

import xbmc
from kodi_addon_dev import repo, tesseract
from kodi_addon_dev.support import Addon, setup_paths

ADDON_TEMP_DIR = '/tmp/kodi-addondev.WM_Esa'
SCRAPERS_REPO_DIR = os.path.join(ADDON_TEMP_DIR, 'script.module.openscrapers')
SCRAPER_ADDON_URLS = {
    'the_crew': 'https://raw.githubusercontent.com/thecrewwh/zips/master/_zip/script.module.thecrew',
    'shadow': 'https://raw.githubusercontent.com/thecrewwh/zips/master/_zip/plugin.video.shadow',
    'tempest': 'https://raw.githubusercontent.com/Tempest0580/tempest/master/zips/plugin.video.tempest'
}


def bootstrap_scrapers():
    # Set up temp dir
    if not os.path.exists(ADDON_TEMP_DIR):
        os.mkdir(ADDON_TEMP_DIR)
    setup_paths(False)

    # Clone latest openscrapers into temp dir
    if not os.path.exists(SCRAPERS_REPO_DIR):
        Repo.clone_from('git://github.com/a4k-openproject/script.module.openscrapers', SCRAPERS_REPO_DIR)

    # Add openscrapers to python path
    sys.path.append(SCRAPERS_REPO_DIR)
    sys.path.append(os.path.join(SCRAPERS_REPO_DIR, 'lib'))

    # Add alternative scrapers to python path
    folders = ['en', 'en_OnlyDebrid', 'en_Torrent']
    for addon_name, addon_url in SCRAPER_ADDON_URLS.items():
        new_addon_folders = import_addon(addon_name, addon_url)
        folders += new_addon_folders

    return init_openscrapers(folders)


def init_openscrapers(folders):
    addon = Addon.from_path(SCRAPERS_REPO_DIR)

    # Monkey patch settings object to enable all providers
    class AllProviderDict(UserDict, object):
        def get(self, key, default=''):
            return "true" if key.startswith("provider.") else super(AllProviderDict, self).get(key, default)
    addon.settings = AllProviderDict()

    # Create kodi mock module
    cached = repo.LocalRepo([], [], addon)
    deps = cached.load_dependencies(addon)
    xbmc.session = tesseract.Tesseract(addon, deps, cached)

    # Initialize openscrapers with passed scraper folders
    from lib import openscrapers
    return openscrapers.sources(folders)


def import_addon(name, url):
    # TODO: Check if addon already exists
    # Get url of latest zip file from addon.xml
    metadata = etree.XML(requests.get(url + '/addon.xml').text.encode())
    zip_url = '%s/%s-%s.zip' % (url, metadata.get('id'), metadata.get('version'))
    addon_zip = requests.get(zip_url)

    # Make empty temp dir for addon
    temp_dir = os.path.join(ADDON_TEMP_DIR, 'tmp')
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.mkdir(temp_dir)

    # Unzip addon into temp dir
    zip_file_path = os.path.join(temp_dir, 'addon.zip')
    with open(zip_file_path, 'wb') as addon_zip_file:
        addon_zip_file.write(addon_zip.content)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    os.remove(zip_file_path)

    # Find scraper directories
    scraper_dirs = []
    for addon_subdir in os.walk(temp_dir):
        folder_name = addon_subdir[0].split('/')[-1]
        if folder_name == 'en' or folder_name.startswith('en_'):
            scraper_dirs.append(addon_subdir[0])
    if len(scraper_dirs) is 0:
        for addon_subdir in os.walk(temp_dir):
            folder_name = addon_subdir[0].split('/')[-1]
            if folder_name == 'sources':
                scraper_dirs.append(addon_subdir[0])

    # Move scraper directories to openscrapers and remove temp folder
    for index, scraper_dir in enumerate(scraper_dirs):
        sources_dir = os.path.join(SCRAPERS_REPO_DIR, 'lib', 'openscrapers', 'sources_openscrapers')
        new_source_dir = os.path.join(sources_dir, '%s_%i' % (name, index))
        if os.path.exists(new_source_dir):
            shutil.rmtree(new_source_dir)
        shutil.move(scraper_dir, new_source_dir)
        change_addon_imports(new_source_dir)
    shutil.rmtree(temp_dir)

    # Return list of scraper folders created by function
    return ['%s_%i' % (name, index) for index in range(len(scraper_dirs))]


# Change all imports from resources.lib to openscrapers
def change_addon_imports(scraper_dir):
    for parent_dir, _dirs, files in os.walk(scraper_dir):
        for file_name in files:
            scraper_file_dir = os.path.join(parent_dir, file_name)
            with open(scraper_file_dir) as scraper_file:
                new_file_contents = scraper_file.read().replace('from resources.lib', 'from openscrapers')
            with open(scraper_file_dir, 'w') as scraper_file:
                scraper_file.write(new_file_contents)
