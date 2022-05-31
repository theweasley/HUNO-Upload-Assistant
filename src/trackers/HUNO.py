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

class HUNO():
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
        if meta['anon'] == 0 and bool(distutils.util.strtobool(self.config['TRACKERS']['HUNO'].get('anon', "False"))) == False:
            anon = 0
        else:
            anon = 1

        if meta['bdinfo'] != None:
            mi_dump = None
            bd_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/BD_SUMMARY_00.txt", 'r', encoding='utf-8').read()
        else:
            mi_dump = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/MEDIAINFO.txt", 'r', encoding='utf-8').read()
            bd_dump = None
        desc = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[HUNO]DESCRIPTION.txt", 'r').read()
        open_torrent = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[HUNO]{meta['clean_name']}.torrent", 'rb')
        files = {'torrent': open_torrent}
        data = {
            'name' : await self.get_name(meta),
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
        url = f"https://hawke.uno/api/torrents/upload?api_token={self.config['TRACKERS']['HUNO']['api_key'].strip()}"

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

    async def get_name(self, meta):
        # Copied from Prep.get_name() then modified to match HUNO's naming convention.
        # It was much easier to build the name from scratch than to alter the existing name.

        type = meta.get('type', "")
        title = meta.get('title',"")
        alt_title = meta.get('aka', "")
        year = meta.get('year', "")
        resolution = meta.get('resolution', "")
        audio = meta.get('audio', "").replace("DD+", "DDP")
        audio_lang = next(x for x in meta["mediainfo"]["media"]["track"] if x["@type"] == "Audio").get('Language_String', "English")
        service = meta.get('service', "")
        season = meta.get('season', "")
        episode = meta.get('episode', "")
        repack = meta.get('repack', "")
        if repack.strip():
            repack = f"[{repack}]"
        three_d = meta.get('3D', "")
        tag = meta.get('tag', "").replace("-", "- ")
        source = meta.get('source', "")
        uhd = meta.get('uhd', "")
        hdr = meta.get('hdr', "")
        if not hdr.strip():
            hdr = "SDR"
        distributor = meta.get('distributor', "")
        if meta.get('is_disc', "") == "BDMV": #Disk
            video_codec = meta.get('video_codec', "")
            region = meta.get('region', "")
        elif meta.get('is_disc', "") == "DVD":
            region = meta.get('region', "")
            dvd_size = meta.get('dvd_size', "")
        else:
            video_codec = meta.get('video_codec', "")
            video_encode = meta.get('video_encode', "").replace(".", "")
        edition = meta.get('edition', "")
        search_year = meta.get('search_year', "")
        if not search_year.strip():
            search_year = year

        #YAY NAMING FUN
        if meta['category'] == "MOVIE": #MOVIE SPECIFIC
            if type == "DISC": #Disk
                if meta['is_disc'] == 'BDMV':
                    name = f"{title} {alt_title} ({year}) {three_d} {edition} ({resolution} {region} {uhd} {source} {video_codec} {hdr} {audio} {audio_lang} {tag}) {repack}"
                elif meta['is_disc'] == 'DVD': 
                    name = f"{title} {alt_title} ({year}) {edition} {source} {dvd_size} {audio} {audio_lang} {tag}) {repack}"
                elif meta['is_disc'] == 'HDDVD':
                    name = f"{title} {alt_title} ({year}) {edition} {source} {audio} {audio_lang} {tag}) {repack}"
            elif type == "REMUX" and source == "BluRay": #BluRay Remux
                name = f"{title} {alt_title} ({year}) {three_d} {edition} ({resolution} {uhd} {source} REMUX {video_codec} {hdr} {audio} {audio_lang} {tag}) {repack}" 
            elif type == "REMUX" and source in ("PAL DVD", "NTSC DVD"): #DVD Remux
                name = f"{title} {alt_title} ({year}) {edition} {source} REMUX {audio} {audio_lang} {tag}) {repack}" 
            elif type == "ENCODE": #Encode
                name = f"{title} {alt_title} ({year}) {edition} ({resolution} {uhd} {source} {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}"  
            elif type == "WEBDL": #WEB-DL
                name = f"{title} {alt_title} ({year}) {edition} ({resolution} {uhd} {service} WEB-DL {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}"
            elif type == "WEBRIP": #WEBRip
                name = f"{title} {alt_title} ({year}) {edition} ({resolution} {uhd} {service} WEBRip {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}"
            elif type == "HDTV": #HDTV
                name = f"{title} {alt_title} ({year}) {edition} ({resolution} HDTV {video_encode} {audio} {audio_lang} {tag}) {repack}"
        elif meta['category'] == "TV": #TV SPECIFIC
            if type == "DISC": #Disk
                if meta['is_disc'] == 'BDMV':
                    name = f"{title} ({search_year}) {alt_title} {season}{episode} {three_d} {edition} ({resolution} {region} {uhd} {source} {video_codec} {hdr} {audio} {audio_lang} {tag}) {repack}"
                if meta['is_disc'] == 'DVD':
                    name = f"{title} {alt_title} {season}{episode}{three_d} {edition} {source} {dvd_size} {audio} {audio_lang} {tag}) {repack}"
                elif meta['is_disc'] == 'HDDVD':
                    name = f"{title} {alt_title} ({year}) {edition} {source} {audio} {audio_lang} {tag}) {repack}"
            elif type == "REMUX" and source == "BluRay": #BluRay Remux
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {three_d} {edition} ({resolution} {uhd} {source} REMUX {video_codec} {hdr} {audio} {audio_lang} {tag}) {repack}" #SOURCE
            elif type == "REMUX" and source in ("PAL DVD", "NTSC DVD"): #DVD Remux
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {edition} {source} REMUX {audio} {audio_lang} {tag}) {repack}" #SOURCE
            elif type == "ENCODE": #Encode
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {edition} ({resolution} {uhd} {source} {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}" #SOURCE
            elif type == "WEBDL": #WEB-DL
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {edition} ({resolution} {uhd} {service} WEB-DL {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}"
            elif type == "WEBRIP": #WEBRip
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {edition} ({resolution} {uhd} {service} WEBRip {video_encode} {hdr} {audio} {audio_lang} {tag}) {repack}"
            elif type == "HDTV": #HDTV
                name = f"{title} ({search_year}) {alt_title} {season}{episode} {edition} ({resolution} HDTV {video_encode} {audio} {audio_lang} {tag}) {repack}"

        return ' '.join(name.split())

    async def get_cat_id(self, category_name):
        category_id = {
            'MOVIE': '1',
            'TV': '2',
            }.get(category_name, '0')
        return category_id

    async def get_type_id(self, type):
        type_id = {
            'REMUX': '2',
            'WEBDL': '3',
            'WEBRIP': '3',
            'ENCODE': '15',
            'DISC': '1',
            }.get(type, '0')
        return type_id

    async def get_res_id(self, resolution):
        resolution_id = {
            'Other':'10',
            '4320p': '1',
            '2160p': '2',
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
        HUNO_torrent = Torrent.read(f"{meta['base_dir']}/tmp/{meta['uuid']}/BASE.torrent")
        HUNO_torrent.metainfo['announce'] = self.config['TRACKERS']['HUNO']['announce_url'].strip()
        HUNO_torrent.metainfo['info']['source'] = "HUNO"
        Torrent.copy(HUNO_torrent).write(f"{meta['base_dir']}/tmp/{meta['uuid']}/[HUNO]{meta['clean_name']}.torrent", overwrite=True)
        return

    async def edit_desc(self, meta):
        base = open(f"{meta['base_dir']}/tmp/{meta['uuid']}/DESCRIPTION.txt", 'r').read()
        with open(f"{meta['base_dir']}/tmp/{meta['uuid']}/[HUNO]DESCRIPTION.txt", 'w') as desc:
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

            desc.write("\n[center][url=https://github.com/theweasley/HUNO-Upload-Assistant]Created by HUNO's Upload Assistant[/url][/center]")
            desc.close()
        return




    async def search_existing(self, meta):
        dupes = []
        cprint("Searching for existing torrents on site...", 'grey', 'on_yellow')
        url = "https://hawke.uno/api/torrents/filter"
        params = {
            'api_token' : self.config['TRACKERS']['HUNO']['api_key'].strip(),
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