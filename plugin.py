# -*- coding: utf-8 -*-
import sys
try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

try:
    from urlparse import parse_qsl
except:
    from urllib.parse import parse_qsl

import plugin_param

import xbmcgui
import xbmcplugin

import mlpfrance

#NOTE: xbmcemull is an extension library not avalaible in a standard kodi (see kodi-dl on github).
try:
    import xbmcemull
    HAVE_EXTENSION = True
except ImportError:
    HAVE_EXTENSION = False

#TODO: xbmcemu special option: get parent path
#TODO: the same to list and choose avalaible language/format/resolution
#TODO: find a way to use the banner

_url = sys.argv[0]
_handle = int(sys.argv[1])

COUNTRY_TO_IETF = {
    "fr": "fr-FR",
    "qb": "fr-CA",
    "en": "en",
    "es": "es",
    "mx": "es-MX",
    "br": "pt-BR",
    "it": "it",
    "nl": "nl",
    "de": "de",
    "pl": "pl",
    "hu": "hu",
    "dk": "da",
    "no": "no",
    "se": "sv-SE",
    "fi": "fi",
    "ru": "ru",
    "ar": "ar"
}

if HAVE_EXTENSION:
    LANGUAGE_ORDER = map(lambda x: x.lower(), xbmcplugin.x_getLanguageOrder())
else:
    LANGUAGE_ORDER = ["fr", "en"]

RESOLUTION_ORDER = ["720p", "1080p", "480p", "360p"]
FORMAT_ORDER = ["mp4", "webm", "mkv"]

LANGUAGE_LINK_MAP = mlpfrance.LANGUAGE_LINK_MAP


MOVIE_DATA = {
    "eqg": "http://mlp-france.com/films/eqg.php",
    "rbr": "http://mlp-france.com/films/rbr.php",
    "fsg": "http://mlp-france.com/films/fsg.php",
    "loe": "http://mlp-france.com/films/loe.php",
    "mlp2017": "http://mlp-france.com/films/mlp2017.php",
}

def get_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def map_kodi_link(data, func):
    for category in data:
        for item in category[1]:
            item["kodi_link"] = func(item)
    return data


def select_prefered_media_url(data):
    return data["link_"+LANGUAGE_LINK_MAP[get_favorite_avalaible_language(data)]]

def get_favorite_avalaible_language(data):
    avalaible_language = []
    if data["link_vf"] != None:
        avalaible_language.append("fr")
    if data["link_vo"] != None:
        avalaible_language.append("en")
    return get_favorite_language_in_list(avalaible_language)

def get_favorite_language_in_list(list):
    print("fav lang")
    list_source = list
    list = map(lambda x: x.lower(), list)
    print(list)
    print(LANGUAGE_ORDER)
    # search for y_x -> y_x (exact match)
    for lang in LANGUAGE_ORDER:
        if len(lang.split("-")) >= 2:
            if lang.lower() in list:
                return list_source[list.index(lang.lower())]
    list_without_subtag = map(lambda x: x.split("-")[0], list)
    print(list_without_subtag)
    # search for y_x -> y or y_x -> y_z or y -> y
    for lang in LANGUAGE_ORDER:
        language_code = lang.split("-")[0].lower()
        if language_code in list_without_subtag:
            return list_source[list_without_subtag.index(language_code)]
    # default to the first language in list
    return list[0]


def country_code_to_ietf(country_code):
    return COUNTRY_TO_IETF[country_code.lower()]

def ietf_to_country_code(ietf):
    for country_code in COUNTRY_TO_IETF:
        if COUNTRY_TO_IETF[country_code] == ietf:
            return country_code

def display_folder(folder):
    display_folder = True
    if len(folder) == 1:
        display_folder = False

    for sub_category in folder:
        if display_folder:
            if sub_category[0] != "":
                title_item = xbmcgui.ListItem(label = u"[B]{}[/B]".format(sub_category[0]))
                xbmcplugin.addDirectoryItem(_handle, "", title_item, False)
        for element_to_display in sub_category[1]:
            elem_item = xbmcgui.ListItem(label = element_to_display["name"])
            elem_item.setArt({"thumb": element_to_display["picture"]})
            is_folder = True
            if element_to_display["is_playable"]:
                elem_item.setProperty("IsPlayable", str(element_to_display["is_playable"]).lower())
                if "kind" in element_to_display:
                    elem_item.setInfo(element_to_display["kind"])
                else:
                    elem_item.setInfo(plugin_param.CATEGORY, {})
                is_folder = not element_to_display["is_playable"]
            xbmcplugin.addDirectoryItem(_handle, element_to_display["kodi_link"], elem_item, is_folder)
    xbmcplugin.endOfDirectory(_handle)

def play_video(video, avalaible_languages, selected_language):
    medias = video["media"]
    medias_by_resolution = {}
    for format_medias in medias:
        for resolution_media in medias[format_medias]:
            if resolution_media not in medias_by_resolution:
                medias_by_resolution[resolution_media] = {}
            medias_by_resolution[resolution_media][format_medias] = medias[format_medias][resolution_media]

    media_url = None

    for resolution in RESOLUTION_ORDER:
        if resolution not in medias_by_resolution:
            continue
        break_after_this = False
        for format in FORMAT_ORDER:
            if format in medias_by_resolution[resolution]:
                media_url = medias_by_resolution[resolution][format]
                break_after_this = True
                break
        if break_after_this:
            break

    video_item = xbmcgui.ListItem(path = media_url)
    if HAVE_EXTENSION:
        video_item.x_addAvalaibleLanguages(avalaible_languages)
    video_item.addStreamInfo("audio", { "language": selected_language})
    video_item.setInfo("video", {})
    xbmcplugin.setResolvedUrl(_handle, True, listitem=video_item)



def select_category():
    sub_category = [
        ["episodes", "list_seasons"],
        ["films", "list_films"],
        ["bonus officiel", "list_bonus", "http://mlp-france.com/source/banni%C3%A8re%20bonus.png"],
        ["mashup films", "list_mashups", "http://mlp-france.com/source/banni%C3%A8re%20Extras%20v2.png"],
        #TODO: commented data
        #["vidéos fandom", "list_fandoms"],
        #["mon petit poney (1983)", "list_mpps"],
        #["my little pony tales", "list_tales"],
        #["my little pony G3", "list_g3s"],
        #["littlest pet shop", "list_petshops"],
        #["star butterfly", "list_butterflys"],
        #["steven universe", "list_stevens"],
    ]
    for cat in sub_category:
        item = xbmcgui.ListItem(label = cat[0])
        if len(cat) >= 3:
            item.setArt({"thumb": cat[2]})
        xbmcplugin.addDirectoryItem(_handle, get_url(action=cat[1]), item, True)
    xbmcplugin.endOfDirectory(_handle)

def list_seasons():
    display_folder(map_kodi_link(mlpfrance.list_seasons(),
        lambda x: get_url(action="list_episodes", season=x["link"].split("/")[-1].split(".")[0])
    ))

def list_episodes(season):
    to_display = mlpfrance.list_episodes(season)
    for category in to_display:
        for item in category[1]:
            if season == "egms2":
                season_in_link = "egms"
            else:
                season_in_link = season

            if season_in_link == "egms":
                item["kodi_link"] = get_url(action="list_egms_episode", episode=select_prefered_media_url(item).split("=")[-1], have_vf = str(item["link_vf"] != None), have_vo = str(item["link_vo"] != None))
                item["is_playable"] = False
            else:
                item["kodi_link"] = get_url(action="play_episode", season=season_in_link, episode=select_prefered_media_url(item).split("=")[-1], language=get_favorite_avalaible_language(item))

    display_folder(
        to_display
    )

def play_episode(season, episode, language):
    #TODO: rewrite so language is not passed in parameter
    play_video(mlpfrance.get_episode(season, episode, language), [language], language)

def list_egms_episode(episode, have_vf, have_vo):
    if have_vf == "True":
        prefix = "vf"
    else:
        prefix = "vo"

    main_item = xbmcgui.ListItem(label = "main video")
    main_item.setProperty("IsPlayable", "true")
    main_item.setInfo("video", {})
    xbmcplugin.addDirectoryItem(_handle, get_url(action="play_egms", episode=episode, have_vf=have_vf, have_vo=have_vo, channel=0), main_item, False)

    video_url = "http://mlp-france.com/episodes/egms/vo.php?ep={}".format(episode)
    video_data = mlpfrance.get_video_page(video_url)

    for choice in video_data["choices"]:
        choice_item = xbmcgui.ListItem(label = "choice - " + choice[0])
        choice_item.setProperty("IsPlayable", "true")
        choice_item.setInfo("video", {})
        xbmcplugin.addDirectoryItem(_handle, get_url(action="play_egms", episode=episode, have_vf=have_vf, have_vo=have_vo, channel=choice[1]), choice_item, False)

    xbmcplugin.endOfDirectory(_handle)

def play_egms(episode, channel, have_vf, have_vo):
    if have_vf == "True":
        post_fr = "vf.php?ep={}&ch={}".format(episode, channel)
    else:
        post_fr = "none"
    if have_vo == "True":
        post_en = "vo.php?ep={}&ch={}".format(episode, channel)
    else:
        post_en = "none"
    (post, lang, av_lang) = get_video_data_biling(post_fr, post_en)
    video_page_url = "http://mlp-france.com/episodes/egms/{}".format(post)
    play_video(mlpfrance.get_video_page(video_page_url), av_lang, lang)

def list_films():
    films = mlpfrance.list_films();
    films_data = {
        "EQUESTRIA GIRLS": {"direct": True, "link": "play_eqg"},
        "RAINBOW ROCKS": {"direct": False, "link": "list_rbr"},
        "FRIENDSHIP GAMES": {"direct": False, "link": "list_fsg"},
        "LEGEND OF EVERFREE": {"direct": True, "link": "play_loe"},
        "MY LITTLE PONY LE FILM": {"direct": False, "link": "list_mlp2017"}
    }
    for category in films:
        for film in category[1]:
            this_data = films_data[film["name"]]
            film["is_playable"] = this_data["direct"]
            film["kodi_link"] = get_url(action=this_data["link"])
    display_folder(films)

def display_movie_videos(elements, movie_id):
    nb = 0
    for elem in elements:
        item = xbmcgui.ListItem(label = elem[0])
        item.setProperty("IsPlayable", "true")
        item.setInfo("video", {})
        xbmcplugin.addDirectoryItem(_handle, get_url(action="play_movie", movie=movie_id, number=nb), item, False)
        nb += 1
    xbmcplugin.endOfDirectory(_handle)

def play_movie_video(movie_id, video_nb):
    video_element = mlpfrance.get_movie_avalaible_videos(MOVIE_DATA[movie_id])[video_nb]
    avalaible_languages = map(lambda x: country_code_to_ietf(x), video_element[1]["languages"])
    language = get_favorite_language_in_list(avalaible_languages)
    play_video(mlpfrance.get_video_page(video_element[1]["link"]+"?ep="+video_element[1]["lang_prefix"]+ietf_to_country_code(language).upper()), avalaible_languages, language)

def list_movie_folder_generic(movie_id):
    elements = mlpfrance.get_movie_avalaible_videos(MOVIE_DATA[movie_id])
    display_movie_videos(elements, movie_id)

def list_mlp2017():
    sub_category = [
        ["teaser", "list_mlp2017_teaser"],
        ["trailers", "list_mlp2017_trailers"],
        ["trailers TV", "list_mlp2017_trailers_tv"],
        ["behind the scene", "list_mlp2017_bth"], #TODO: there are some aditional file on needforponies that are absent here
        ["360° experience", "list_mlp2017_360"],
    ]
    film_item = xbmcgui.ListItem(label = "film")
    film_item.setInfo("video", {})
    film_item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(_handle, get_url(action="play_movie", movie="mlp2017", number=0), film_item, False)

    rainbow_item = xbmcgui.ListItem(label = "SIA - Rainbow")
    rainbow_item.setInfo("video", {})
    rainbow_item.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(_handle, "plugin://plugin.video.youtube/play/?video_id=paXOkGMyG8M", rainbow_item, False)

    for cat in sub_category:
        sub_category_item = xbmcgui.ListItem(label = cat[0])
        xbmcplugin.addDirectoryItem(_handle, get_url(action=cat[1]), sub_category_item, True)
    xbmcplugin.endOfDirectory(_handle)

def generate_list_of_youtube_video_to_play(videos_data):
    #video_data = [{"id": youtube_video_id, "label": label}]
    for videos in videos_data:
        yt_video_item = xbmcgui.ListItem(label = videos["label"])
        yt_video_item.setProperty("IsPlayable", "true")
        yt_video_item.setInfo("video", {})
        xbmcplugin.addDirectoryItem(_handle, "plugin://plugin.video.youtube/play/?video_id="+videos["id"], yt_video_item, False)
    xbmcplugin.endOfDirectory(_handle)

# all of those doesn't read data from the website, maybe read picture and some property from youtube (does the youtube plugin allow this ?)
def list_mlp2017_teaser():
    generate_list_of_youtube_video_to_play([
        {"label": "[FR] [Teaser officiel #1] My Little Pony Le Film", "id": "FImgmkUx3OM"},
        {"label": "[EN] My Little Pony: The Movie (2017) BIG Announcement! – Emily Blunt, Sia, Zoe Saldana", "id": "HUutTv-WBfQ"}
    ])

def list_mlp2017_trailers():
    generate_list_of_youtube_video_to_play([
        {"label": "[FR] MY LITTLE PONY LE FILM - Bande-annonce - exclusivement au cinéma le 18 octobre", "id": "VLidyno9cNo"},
        {"label": "[EN] My Little Pony: The Movie - Official Trailer Debut 🦄", "id": "aeQe_mZcyf8"},
        {"label": "[EN] My Little Pony: The Movie - 'Ponies Got the Beat' Official Trailer #2 🦄", "id": "sNJOisDTYEg"}
    ])

def list_mlp2017_trailers_tv():
    generate_list_of_youtube_video_to_play([
        {"label": "[FR] MY LITTLE PONY : LE FILM - Bande-annonce #2 🌈 [VF]", "id": "DVEzYqhz6FU"},
        {"label": "[EN] My Little Pony: The Movie (2017) Official TV Spot – ‘So Sweet’ - Emily Blunt, Sia, Zoe Saldana", "id": "xSwfaMOEvcE"},
        {"label": "[EN] My Little Pony: The Movie (2017) Official TV Spot – ‘Behind the Scenes’", "id": "l3YR9gjlydc"},
        {"label": "[EN] My Little Pony: The Movie (2017) Official TV Spot – ‘Generations’ - Emily Blunt, Sia, Zoe Saldana", "id": "K4QzmATKTbc"},
        {"label": "[EN] My Little Pony the Movie - America's Got Talent Exclusive Sneak Peak", "id": "RMukLlbKcSE"}
    ])

def list_mlp2017_bth():
    generate_list_of_youtube_video_to_play([
        {"label": "[EN] BEHIND THE SCENES My Little Pony Movie 2017 Voice Actor Trailer!", "id": "xVhzDRotk10"}
    ])

def list_mlp2017_360():
    generate_list_of_youtube_video_to_play([
        {"label": "My Little Pony: The Movie – 360 Seaquestria Experience", "id": "YJDU_-kpk9U"},
        {"label": "My Little Pony: The Movie (2017) 360º Pirates Image", "id": "Bg8SSmO2wlU"}
    ])

def list_bonus():
    elements = mlpfrance.get_list_page_data("http://mlp-france.com/extras/bonus.php", True)
    section_nb = 0
    for key in elements:
        key_item = xbmcgui.ListItem(label = key[0])
        xbmcplugin.addDirectoryItem(_handle, get_url(action = "list_bonus_videos", section_nb=section_nb), key_item, True)
        section_nb += 1
    xbmcplugin.endOfDirectory(_handle)

def get_vid_url(elem, action):
    post_fr = "none"
    post_en = "none"
    for link in elem["links"]:
        print(link)
        file_name = link.split(".php")[0].split("/")[-1]
        if file_name in ["kar", "comic", "egm", "com", "ds"]:
            link_lang = "en"
        elif file_name == "divers":
            if link[-2:] == "EN":
                link_lang = "en"
            elif link[-2:] == "FR":
                link_lang = "fr"
            else:
                link_lang = "en"
        else:
            link_lang = file_name[-2:]
            link_lang_map = {
                "vo": "en",
                "vf": "fr",
                "st": "fr"
            }
            if link_lang not in ["fr", "en"]:
                link_lang = link_lang_map[link_lang]
        if link_lang == "fr":
            post_fr = link.split("/")[-1]
        else:
            post_en = link.split("/")[-1]
    return get_url(action=action, post_fr=post_fr, post_en=post_en)

def list_bonus_videos(section_nb):
    elements = mlpfrance.get_list_page_data("http://mlp-france.com/extras/bonus.php", True)
    elements_to_display = mlpfrance.map_playable(
        map_kodi_link(
            [elements[int(section_nb)]],
            lambda x: get_vid_url(x, "play_bonus_video")
        ),
        True
    )
    display_folder(elements_to_display)

def get_video_data_biling(post_fr, post_en):
    if post_fr == "none":
        return (post_en, "en", ["en"])
    elif post_en == "none":
        return (post_fr, "fr", ["fr"])
    else:
        lang = get_favorite_language_in_list(["fr", "en"])
        avalaible_language = ["fr", "en"]
        if lang == "fr":
            return (post_fr, "fr", avalaible_language)
        else:
            return (post_fr, "en", avalaible_language)

def play_bonus_video(post_fr, post_en):
    (post, lang, avalaible_language) = get_video_data_biling(post_fr, post_en)
    video_page_url = "http://mlp-france.com/extras/bonus/{}".format(post)
    play_video(mlpfrance.get_video_page(video_page_url), avalaible_language, lang)

def list_mashups():
    elements = mlpfrance.get_list_page_data("http://mlp-france.com/extras/mashup.php", True)
    elements_to_display = mlpfrance.map_playable(
        map_kodi_link(
            elements,
            lambda x: get_vid_url(x, "play_mashup_video")
        ),
        True
    )
    display_folder(elements_to_display)

def play_mashup_video(post_fr, post_en):
    (post, lang, avalaible_lang) = get_video_data_biling(post_fr, post_en)
    video_page_url = "http://mlp-france.com/extras/mashup/{}".format(post)
    play_video(mlpfrance.get_video_page(video_page_url), avalaible_lang, lang)

##########
# MUSICS #
##########
def music_category_map(element):
    static_name_map = {
        "eqg": "Equestria Girls",
        "rbr": "Rainbow Rocks",
        "fsg": "Friendship Games",
        "loe": "Legend Of Everfree",
        "movie": "My Little Pony: Le Film",
    }
    suffix = element["link"].split("/")[-1].split(".")[0]
    if suffix == "extended":
        element["kodi_link"] = get_url(action="display_album", page=suffix, number=0)
    else:
        element["kodi_link"] = get_url(action="list_albums", page=suffix)
    if element["name"] == None:
        if suffix.startswith("saison"):
            season_nb = suffix.split("saison")[-1]
            element["name"] = "Saison {}".format(season_nb)
        else:
            element["name"] = static_name_map[suffix]
    return element

def select_music_categories():
    elements = mlpfrance.map_playable(
        mlpfrance.get_list_page_data("http://mlp-france.com/extras/chansons.php"),
        False
    )
    #TODO: this is ugly
    elements = [('', map(music_category_map, elements[0][1]))]
    karaoke_item = xbmcgui.ListItem(label = "karaoké")
    xbmcplugin.addDirectoryItem(_handle, get_url(action="list_bonus_videos", section_nb=7), karaoke_item, True)
    display_folder(elements)

def list_albums(page):
    album_list = mlpfrance.get_music_page_data("http://mlp-france.com/extras/chansons/{}.php".format(page))
    nb = 0
    for album in album_list:
        album_name = album[0]
        album_thumb = album[1][0]["image"]
        album_item = xbmcgui.ListItem(label = album_name)
        album_item.setArt({"thumb": album_thumb})
        xbmcplugin.addDirectoryItem(_handle, get_url(action="display_album", page=page, number=nb), album_item, True)
        nb += 1
    xbmcplugin.endOfDirectory(_handle)

def display_album(page, number):
    album = mlpfrance.get_music_page_data("http://mlp-france.com/extras/chansons/{}.php".format(page))[int(number)]
    loop_nb = 0
    for music in album[1]:
        music_item = xbmcgui.ListItem(label = music["title"], path = music["path"])
        music_item.setProperty("IsPlayable", "true")
        #TODO: reuse the code for metadata in play_album_music
        music_item.setInfo("music", {
            "title": music["title"],
            "artist": music["artist"],
        })
        #TODO: make use of length
        xbmcplugin.addDirectoryItem(_handle, get_url(action="play_album_music", page=page, number=number, music_id=loop_nb), music_item, False)
        loop_nb += 1
    xbmcplugin.endOfDirectory(_handle)

def play_album_music(page, number, music_id):
    music = mlpfrance.get_music_page_data("http://mlp-france.com/extras/chansons/{}.php".format(page))[int(number)][1][int(music_id)]
    music_item = xbmcgui.ListItem(label = music["title"], path = music["path"])
    xbmcplugin.setResolvedUrl(_handle, True, music_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        action = params["action"]
        if action == 'list_seasons':
            list_seasons()
        elif action == "list_episodes":
            list_episodes(params["season"])
        elif action == "play_episode":
            play_episode(params["season"], params["episode"], params["language"])
        elif action == "list_egms_episode":
            list_egms_episode(params["episode"], params["have_vf"], params["have_vo"])
        elif action == "play_egms":
            play_egms(params["episode"], params["channel"], params["have_vf"], params["have_vo"])
        elif action == "list_films":
            list_films()
        elif action == "play_movie":
            play_movie_video(params["movie"], int(params["number"]))
        elif action == "play_eqg":
            play_movie_video("eqg", 0)
        elif action == "list_rbr":
            list_movie_folder_generic("rbr")
        elif action == "list_fsg":
            list_movie_folder_generic("fsg")
        elif action == "play_loe":
            play_movie_video("loe", 0)
        elif action == "list_mlp2017":
            list_mlp2017()
        elif action == "list_mlp2017_teaser":
            list_mlp2017_teaser()
        elif action == "list_mlp2017_trailers":
            list_mlp2017_trailers()
        elif action == "list_mlp2017_trailers_tv":
            list_mlp2017_trailers_tv()
        elif action == "list_mlp2017_bth":
            list_mlp2017_bth()
        elif action == "list_mlp2017_360":
            list_mlp2017_360()
        elif action == "list_bonus":
            list_bonus()
        elif action == "list_bonus_videos":
            list_bonus_videos(params["section_nb"])
        elif action == "play_bonus_video":
            play_bonus_video(params["post_fr"], params["post_en"])
        elif action == "list_mashups":
            list_mashups()
        elif action == "play_mashup_video":
            play_mashup_video(params["post_fr"], params["post_en"])
        # musics
        #TODO: karaoké also in here
        elif action == "list_albums":
            list_albums(params["page"])
        elif action == "display_album":
            display_album(params["page"], params["number"])
        elif action == "play_album_music":
            play_album_music(params["page"], params["number"], params["music_id"])
        else:
            raise ValueError('action not reconized in paramstring: {0}'.format(paramstring))
    else:
        if plugin_param.CATEGORY == "video":
            select_category()
        else:
            select_music_categories()

# ["chansons", "list_songs"],
if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
