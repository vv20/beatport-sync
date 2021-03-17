import copy
import eyed3
import getpass
import json
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = 'https://www.beatport.com/'
LIBRARY_URL = BASE_URL + 'api/v4/my/downloads'
DOWNLOAD_URL = BASE_URL + 'api/v4/catalog/tracks/purchase-download?order_item_download_id={}'
LOGIN_URL = BASE_URL + 'account/login'
CSRF_TOKEN = '_csrf_token'
LOCAL_SETTINGS_LOCATION = '{0}/.beatport-sync.config'.format(os.path.expanduser('~'))
DEFAULT_LOCAL_LIBRARY_LOCATION = '~/Music/beatport/'


class SettingsKey():
    LIBRARY_LOCATION = 'LIBRARY_LOCATION'
    PARALLELISATION = 'PARALLELISATION'

class LoginFailedException(Exception):
    pass


def getLibraryLocation():
    location = input('Location of your local Beatport library: ')
    location = os.path.expanduser(location)
    if not location.endswith('/'):
        location += '/'
    return location

def getParallelisation():
    noOfThreads = input('How many tracks would you like to be able to download in parallel (number of threads)? ')
    noOfThreads = int(noOfThreads)
    return noOfThreads

def createLocalSettings():
    settings = {
            SettingsKey.LIBRARY_LOCATION: getLibraryLocation(),
            SettingsKey.PARALLELISATION: getParallelisation(),
    }
    with open(LOCAL_SETTINGS_LOCATION, 'x') as f:
        f.write(json.dumps(settings))
    return settings

def getLocalSettings():
    if not os.path.exists(LOCAL_SETTINGS_LOCATION):
        print('Local settings not detected- creating settings configuration under {0}'.format(LOCAL_SETTINGS_LOCATION))
        return createLocalSettings()
    with open(LOCAL_SETTINGS_LOCATION, 'r') as f:
        return json.loads(f.read())

def createDirectory(location):
    print('Creating directory {0}...'.format(location))
    pathSegments = location.split('/')
    path = '/'
    for segment in pathSegments:
        path += segment + '/'
        if not os.path.exists(path):
            os.mkdir(path)

def getLocalLibraryLocation():
    location = getLocalSettings().get(SettingsKey.LIBRARY_LOCATION, DEFAULT_LOCAL_LIBRARY_LOCATION)
    if not os.path.exists(location):
        createDirectory(location)
    return location

def getLocalTracks(libraryLocation):
    filesInLib = os.listdir(libraryLocation)
    filesInLib = [f for f in filesInLib if f.endswith('.mp3')]
    tracks = [eyed3.load(libraryLocation + f) for f in filesInLib]
    return set([(track.tag.artist, track.tag.title) for track in tracks])

def getUsername():
    return input('Beatport username: ')

def getPassword():
    return getpass.getpass('Beatport password: ')

def loginToBeatport(session):
    print('Logging in to Beatport...')
    session.get(LOGIN_URL)
    headers = {
            'Referer':'https://www.beatport.com/account/login?next=%2Flibrary%2Fdownloads'
    }
    response = session.post(LOGIN_URL, headers=headers, data={
        CSRF_TOKEN: session.cookies[CSRF_TOKEN],
        'username': getUsername(),
        'password': getPassword()
    })
    if response.status_code < 400:
        print('Login successful')
    else:
        print('Login failed')
        raise LoginFailedException()

def getArtist(download):
    return download['artists'][0]['name']

def getTitle(download):
    return '{0} ({1})'.format(download['name'], download['mix_name'])

def getId(download):
    return download['order_item_download_id']

def getRemoteTracks(session):
    response = session.get(LIBRARY_URL)
    downloads = json.loads(response.content)['results']
    return {(getArtist(download), getTitle(download)): getId(download) for download in downloads}

def downloadTrack(trackId, session):
    print('Downloading track ID {0}'.format(trackId))
    response = session.get(DOWNLOAD_URL.format(trackId))
    downloadUrl = json.loads(response.content)['download_url']
    response = session.get(downloadUrl)
    with open(getLocalLibraryLocation() + str(trackId) + '.mp3', 'xb') as dest:
        dest.write(response.content)
    print('Track ID {0} download finished.'.format(trackId))

def getNumberOfThreads():
    return getLocalSettings().get(SettingsKey.PARALLELISATION, 1)

def downloadTracks(trackIds, session):
    with ThreadPoolExecutor(getNumberOfThreads()) as executor:
        futures = [executor.submit(downloadTrack, trackId, session) for trackId in trackIds]
        while not all([future.done() for future in futures]):
            print('Receiving data...')
            time.sleep(1)

def main():
    session = requests.Session()
    loginToBeatport(session)
    localLibraryLocation = getLocalLibraryLocation()
    localTracks = getLocalTracks(localLibraryLocation)
    remoteTracks = getRemoteTracks(session)
    tracksToDownload = set(remoteTracks.keys()) - localTracks
    print('Tracks to download: {0}'.format(len(tracksToDownload)))
    downloadTracks([remoteTracks[t] for t in tracksToDownload], session)
    print('Successfully downloaded tracks')

if __name__ == '__main__':
    main()
