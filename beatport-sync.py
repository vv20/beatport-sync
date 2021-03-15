import copy
import eyed3
import getpass
import json
import os
import requests
import sqlite3

BASE_URL = 'https://www.beatport.com/'
LIBRARY_URL = BASE_URL + 'api/v4/my/downloads'
DOWNLOAD_URL = BASE_URL + 'api/v4/catalog/tracks/purchase-download?order_item_download_id={}'
LOGIN_URL = BASE_URL + 'account/login'
LIBRARY_LOCATION = '/home/victor/Music/beatport/'
COMMON_HEADERS = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
}
CSRF_TOKEN = '_csrf_token'


class CookieNotFoundException(Exception):
    pass

class LoginFailedException(Exception):
    pass


def getLocalSettings():
    return {
            'LIBRARY_LOCATION': LIBRARY_LOCATION,
    }

def createDirectory(location):
    print('Creating directory {0}...'.format(location))
    pathSegments = location.split('/')
    path = '/'
    for segment in pathSegments:
        path += segment + '/'
        if not os.path.exists(path):
            os.mkdir(path)

def getLocalLibraryLocation():
    location = getLocalSettings()['LIBRARY_LOCATION']
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
    session.get(LOGIN_URL, headers=COMMON_HEADERS)
    headers = copy.copy(COMMON_HEADERS)
    headers['Referer'] = 'https://www.beatport.com/account/login?next=%2Flibrary%2Fdownloads'
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
    response = session.get(LIBRARY_URL, headers=COMMON_HEADERS)
    downloads = json.loads(response.content)['results']
    return {(getArtist(download), getTitle(download)): getId(download) for download in downloads}

def downloadTrack(trackId, session):
    print('downloading track ID {0}'.format(trackId))
    response = session.get(DOWNLOAD_URL.format(trackId), headers=COMMON_HEADERS)
    downloadUrl = json.loads(response.content)['download_url']
    response = session.get(downloadUrl, headers=COMMON_HEADERS)
    with open(getLocalLibraryLocation() + str(trackId) + '.mp3', 'xb') as dest:
        dest.write(response.content)

def downloadTracks(trackIds, session):
    for trackId in trackIds:
        downloadTrack(trackId, session)

def main():
    session = requests.Session()
    loginToBeatport(session)
    localLibraryLocation = getLocalLibraryLocation()
    localTracks = getLocalTracks(localLibraryLocation)
    remoteTracks = getRemoteTracks(session)
    tracksToDownload = set(remoteTracks.keys()) - localTracks
    print('{} tracks to download'.format(len(tracksToDownload)))
    downloadTracks([remoteTracks[t] for t in tracksToDownload], session)
    print('Successfully downloaded tracks')

if __name__ == '__main__':
    main()
