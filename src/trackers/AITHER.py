# -*- coding: utf-8 -*-
# import discord
import asyncio
from torf import Torrent
import requests
from difflib import SequenceMatcher
from termcolor import cprint
import distutils.util
import json
from pprint import pprint

# from pprint import pprint

class AITHER():
    """
    Edit for Tracker:
        Edit BASE.torrent with announce and source
        Check for duplicates
        Set type/category IDs
        Upload
    """
    def __init__(self, config):
        self.config = config
        pass
    
    async def upload(self, meta):
        await self.edit_torrent(meta)
        cat_id = await self.get_cat_id(meta['category'])
        type_id = await self.get_type_id(meta['type'])
        resolution_id = await self.get_res_id(meta['resolution'])
        await self.edit_desc(meta)
        aither_name = await self.edit_name(meta)
        if meta['anon'] == 0 and bool(distutils.util.strtobool(self.config['TRACKERS']['AITHER'].get('anon', "False"))) == False:
            anon = 0
        else:
            anon = 1
        if meta['bdinfo'] != None:
            mi_dump = None
            bd_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/BD_SUMMARY_00.txt", 'r', encoding='utf-8').read()
        else:
            mi_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'r', encoding='utf-8').read()
            bd_dump = None
        desc = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[AITHER]DESCRIPTION.txt", 'r').read()
        open_torrent = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[AITHER]{meta['clean_name']}.torrent", 'rb')
        files = {'torrent': open_torrent}
        data = {
            'name' : aither_name,
            'description' : desc,
            'mediainfo' : mi_dump,
            'bdinfo' : bd_dump, 
            'category_id' : cat_id,
            'type_id' : type_id,
            'resolution_id' : resolution_id,
            'tmdb' : meta['tmdb'],
            'imdb' : meta['imdb_id'].replace('tt', ''),
            'tvdb' : meta['tvdb_id'],
            'mal' : meta['mal_id'],
            'igdb' : 0,
            'anonymous' : anon,
            'stream' : meta['stream'],
            'sd' : meta['sd'],
            'keywords' : meta['keywords'],
            # 'internal' : 0,
            # 'featured' : 0,
            # 'free' : 0,
            # 'double_up' : 0,
            # 'sticky' : 0,
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0'
        }
        url = f"https://aither.cc/api/torrents/upload?api_token={self.config['TRACKERS']['AITHER']['api_key'].strip()}"
        
        if meta['debug'] == False:
            response = requests.post(url=url, files=files, data=data, headers=headers)
            try:
                # pprint(data)
                print(response.json())
            except:
                cprint("It may have uploaded, go check")
                # cprint(f"Request Data:", 'cyan')
                # pprint(data)
                return 
        else:
            cprint(f"Request Data:", 'cyan')
            pprint(data)
        open_torrent.close()



    async def edit_name(self, meta):
        aither_name = meta['name']
        with open(f"{meta.get('base_dir')}/tmp/{meta.get('uuid')}/MediaInfo.json", 'r', encoding='utf-8') as f:
            mi = json.load(f)
        
        has_eng_audio = False
        for track in mi['media']['track']:
            if track['@type'] == "Audio":
                if track.get('Language', 'None') == 'en':
                    has_eng_audio = True
        if not has_eng_audio:
            audio_lang = mi['media']['track'][2].get('Language_String', "").upper()
            aither_name = aither_name.replace(meta['resolution'], f"{audio_lang} {meta['resolution']}")

        aither_name = aither_name.replace(meta['video_encode'], meta['video_encode'].replace('.', ''))
        return aither_name

    async def get_cat_id(self, category_name):
        category_id = {
            'MOVIE': '1', 
            'TV': '2', 
            }.get(category_name, '0')
        return category_id

    async def get_type_id(self, type):
        type_id = {
            'DISC': '1', 
            'REMUX': '2',
            'WEBDL': '4', 
            'WEBRIP': '5', 
            'HDTV': '6',
            'ENCODE': '3'
            }.get(type, '0')
        return type_id

    async def get_res_id(self, resolution):
        resolution_id = {
            '8640p':'10', 
            '4320p': '1', 
            '2160p': '2', 
            '1440p' : '3',
            '1080p': '3',
            '1080i':'4', 
            '720p': '5',  
            '576p': '6', 
            '576i': '7',
            '480p': '8', 
            '480i': '9'
            }.get(resolution, '10')
        return resolution_id




    async def edit_torrent(self, meta):
        AITHER_torrent = Torrent.read(f"{meta['base_dir']}/tmp/{meta['uuid']}/BASE.torrent")
        AITHER_torrent.metainfo['announce'] = self.config['TRACKERS']['AITHER']['announce_url'].strip()
        AITHER_torrent.metainfo['info']['source'] = "Aither"
        AITHER_torrent.metainfo['comment'] = "Created by L4G's Upload Assistant"
        Torrent.copy(AITHER_torrent).write(f"{meta['base_dir']}/tmp/{meta['uuid']}/[AITHER]{meta['clean_name']}.torrent", overwrite=True)
        return 
        
    async def edit_desc(self, meta):
        base = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/DESCRIPTION.txt", 'r').read()
        with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[AITHER]DESCRIPTION.txt", 'w') as desc:
            desc.write(base)
            images = meta['image_list']
            if len(images) > 0: 
                desc.write("[center]")
                for each in range(len(images)):
                    web_url = images[each]['web_url']
                    img_url = images[each]['img_url']
                    desc.write(f"[url={web_url}][img=350]{img_url}[/img][/url]")
                    if (each + 1) % 3 == 0:
                        desc.write("\n")
                desc.write("[/center]")

            desc.write("\n[center][url=https://aither.cc/forums/topics/1349]Created by L4G's Upload Assistant[/url][/center]")
            desc.close()
        return 

   


    async def search_existing(self, meta):
        dupes = []
        cprint("Searching for existing torrents on site...", 'grey', 'on_yellow')
        url = "https://aither.cc/api/torrents/filter"
        params = {
            'api_token' : self.config['TRACKERS']['AITHER']['api_key'].strip(),
            'tmdbId' : meta['tmdb'],
            'categories[]' : await self.get_cat_id(meta['category']),
            'types[]' : await self.get_type_id(meta['type']),
            'resolutions[]' : await self.get_res_id(meta['resolution']),
            'name' : ""
        }
        if meta['category'] == 'TV':
            params['name'] = f"{meta.get('season', '')}{meta.get('episode', '')}"
        if meta.get('edition', "") != "":
            params['name'] + meta['edition']
        params['name'] + meta['audio']
        try:
            response = requests.get(url=url, params=params)
            response = response.json()
            for each in response['data']:
                result = [each][0]['attributes']['name']
                # difference = SequenceMatcher(None, meta['clean_name'], result).ratio()
                # if difference >= 0.05:
                dupes.append(result)
        except:
            cprint('Unable to search for existing torrents on site. Either the site is down or your API key is incorrect', 'grey', 'on_red')
            await asyncio.sleep(5)

        return dupes