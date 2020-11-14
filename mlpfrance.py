# -*- coding: utf-8 -*-

# note: https doesn't work (redirect to another site)
import os

from bs4 import BeautifulSoup
import bs4
import requests
try:
    from urllib import urlopen
except:
    from urllib.request import urlopen

try:
    from urllib.error import HTTPError
    use_httperror = True
except ImportError:
    use_httperror = False

import json
import sys

LANGUAGE_LINK_MAP = {
    "fr": "vf",
    "en": "vo"
}

def get_soup(url, fix_p = False, birthday_b_fix = False):
    print("mlpfrance: fetching {}".format(url))
    r = requests.get(url)
    content = r.content
    if fix_p:
        content = content.replace(b"<p>", b"").replace(b"</p>", b"") # due to some malformed html
    if birthday_b_fix:
        content = content.replace(b"Joyeux Anniversaire !</b><br>", b"Joyeux Anniversaire !<br>")
    return BeautifulSoup(content, "html.parser")

def get_good_url(post, url):
    url = os.path.dirname(url)

    if post[0] == "/":
        return "http://mlp-france.com"+post
    elif post[:4] == "http":
        return post
    else:
        while post[:3] == "../":
            post = post[3:]
            url = os.path.dirname(url)
        return os.path.join(url, post)

def is_element_presentation(elem):
    if type(elem) == bs4.element.NavigableString:
        return True
    if elem.name == "img":
        return True
    if elem.get("class") in ["copyrights"]:
        return True
    if elem.get("class") == [u"barre"]:
        return True

def get_header_link_list(category, url = "http://mlp-france.com/accueil.php"):
    soup = get_soup(url)

    barre = soup.find("div", attrs={"class": "barre"})

    for menu in barre.find_all("li", attrs={"class": "menu"}):
        menu_text_elem = menu.find("b")
        if menu_text_elem == None:
            menu_text_elem = menu.find("strong")
        menu_name = menu_text_elem.text.strip().encode("utf8")
        if menu_name == category:
            menu_data = []
            for menu_element in menu.find_all("li"):
                menu_data.append({
                    "link": get_good_url(menu_element.find("a").get("href"), url),
                    "text": menu_element.find("a").text.encode("utf8")
                })
            return menu_data, soup
    return None, soup

def get_list_page_data(url, fix_p = False, soup = None):
    if soup == None:
        soup = get_soup(url, fix_p, birthday_b_fix = True)

    elements = [] #[(category_name, [{name=.., url=.., ...}, ...]), ...] , category_name default to ""
    actual_category = ""

    for child in soup.find("div", attrs={"class": "page"}).children:
        elems = []
        found_video_childrens = []
        if is_element_presentation(child):
            continue

        elif child.name == "ul" or child.name == "table":
            if child.name == "ul":
                for li in child.find_all("li"):
                    elems.append(li)
            else:
                for td in child.find_all("td"):
                    elems.append(td)

        elif child.name == "p":
            found_child = False
            for link in child.find_all("a"):
                picture_element = link.find("img")
                if picture_element:
                    picture = get_good_url(picture_element.get("src"), url)
                    name = None
                else:
                    picture = None
                    try:
                        name = link.find("b").text
                    except:
                        continue
                #get label if possible
                sub_page = {
                    "picture": picture,
                    "link": get_good_url(link.get("href"), url),
                    "name": name,
                }
                found_video_childrens.append(sub_page)
                found_child = True

            if not found_child:
                if len(child.find_all("span", attrs={"class": "large"})) != 0:
                    actual_category = child.find("b").text.strip()
                    if len(child.find_all("a")) != 0:
                        elems.append(child)

        elif child.name == "span" and fix_p:
            if child.get("class") == None:
                continue
            if "large" in child.get("class"):
                actual_category = child.find("b").text
        else:
            print("maybe missing", child)

        for elem in elems:
            if elem.text.strip() == "":
                continue
            if elem.find("img") != None:
                picture = get_good_url(elem.find("img").get("src"), url)
            else:
                picture = None
            sub_text = None
            for s in elem:
                if type(s) != bs4.element.NavigableString:
                    continue
                if s.strip() in ["", "VF", "VOSTFR"]:
                    continue
                sub_text = s
                break

            if elem.find_all("b") != []:
                name = elem.find_all("b")[-1].text
            else:
                name = None

            if sub_text != None:
                if name == None:
                    name = sub_text
                else:
                    name = "[B]"+sub_text+"[/B] - "+name

            if name == None:
                print(elem)
                raise

            #TODO: also get the episode number
            episode = {
                "picture": picture,
                "name": name,
                "link_vo": None,
                "link_vf": None,
                "is_video": True,
                "is_playable": True,
                "links": []
            }
            for link in elem.find_all("a"):
                if link.text in ["VOSTFR", "VO"]:
                    episode["link_vo"] = link.get("href")
                elif link.text == "VF":
                    episode["link_vf"] = link.get("href")
                episode["links"].append(get_good_url(link.get("href"), url))

            found_video_childrens.append(episode)


        if found_video_childrens != []:
            should_append = True
            for elem in elements:
                if elem[0] == actual_category:
                    elem[1].extend(found_video_childrens)
                    should_append = False
            if should_append:
                elements.append((actual_category, found_video_childrens))

    return elements

def merge_with_header(content, header):
    for category in content:
        for link in category[1]:
            for menu in header:
                if menu["link"] == link["link"]:
                    link["name"] = menu["text"]
    return content

def map_playable(content, is_playable):
    for category in content:
        for item in category[1]:
            item["is_playable"] = is_playable
    return content

def get_video_page(url):
    soup = get_soup(url)
    video_script_tag = soup.find("div", attrs={"id": "makamour"}).next_element.next_element
    if sys.version_info.major == 3:
        video_script = video_script_tag.children.__next__()
    else:
        video_script = video_script_tag.text

    video_script = video_script.split("NPlayer(document.querySelector('#makamour'), ")[-1].split(");\n")[0]

    video_script = video_script.replace("'", "\"");
    video_data_parsed = json.loads(video_script)

    to_del = []
    for media_folder_key in video_data_parsed:
        if media_folder_key == "subtitle":
            continue
        media_folder = video_data_parsed[media_folder_key]
        if type(media_folder) != dict:
            continue
        for data_key in media_folder:
            if media_folder[data_key].startswith("http://195.154.136.128/VOTVBirthday"):
                to_del.append((media_folder_key, data_key))

    for d in to_del:
        del video_data_parsed[d[0]][d[1]]

    #TODO: subtitles
    videos_files = {
        "mp4": video_data_parsed["mp4"],
        "webm": video_data_parsed["webm"],
        "mkv": {}
    }

    #try:
    possible_download_hd = video_script_tag.next_element.next_element.next_element.next_element
    if possible_download_hd.find("img") != None:
        if possible_download_hd.find("img").get("src") != "../../source/dl-blue4vo.png":
            videos_files["mkv"]["1080p"] = possible_download_hd.get("href")
    #except AttributeError:
    #    pass

    maybe_choice = video_script_tag.next_sibling.next_sibling
    choices = []
    for choice in maybe_choice.find_all("a", attrs={"class": "link"}):
        choices.append((choice.text, choice.get("href").split("ch=")[-1]))

    return {
        "media": videos_files,
        "choices": choices
    }

def get_movie_avalaible_videos(url):
    soup = get_soup(url)

    avalaible_videos = [] # under the form [(label, {"languages": [...], link: ...})]
    actual_section = ""

    for child in soup.find("div", attrs={"class": "page"}).children:
        actual_language = []
        prefix = ""
        link = None
        if is_element_presentation(child):
            continue
        elif child.name == "ul":
            for li in child.find_all("li"):
                if li.find("a") != None:
                    link = get_good_url(li.find("a").get("href").split("?")[0], url)
                    lang = li.find("a").get("href").split("=")[-1].lower()
                    if len(lang) > 2:
                        prefix = lang[:-2]
                        lang = lang[-2:]
                    actual_language.append(lang)
        elif child.name == "p":
            if child.find("b") != None:
                actual_section = child.find("b").text
        else:
            print("maybe missing ", child)

        if len(actual_language) != 0:
            found = False
            for elem in avalaible_videos:
                if elem[0] == actual_section:
                    elem[1]["languages"].extend(actual_language)
                    found = True
                    break
            if not found:
                avalaible_videos.append((actual_section, {"languages": actual_language, "link": link, "lang_prefix": prefix}))

    return avalaible_videos

def list_seasons():
    url = "http://mlp-france.com/episodes/index.php"
    header, soup = get_header_link_list("ÉPISODES", url)
    content = get_list_page_data(url, soup = soup)
    return map_playable(merge_with_header(content, header), False)

def list_episodes(season):
    return get_list_page_data("http://mlp-france.com/episodes/{}.php".format(season), True)

def get_episode(season, episode, language):
    video_url = "http://mlp-france.com/episodes/{}/{}.php?ep={}".format(season, LANGUAGE_LINK_MAP[language], episode)
    return get_video_page(video_url)

def get_music_page_data(url):
    soup = get_soup(url, fix_p=True)
    result = [] #under the form [(name, {"path", "title", "artist", "image", "length"})] ("length" is in second, int)
    actual_name = "undefined"
    for child in soup.find("div", attrs={"class": "page"}).children:
        if is_element_presentation(child):
            continue
        elif child.name == "b": #NOTE: this only work because fix_p is set to true
            actual_name = child.text
        elif child.name == "script":
            if child.get("src") != None:
                continue
            if sys.version_info.major == 3:
                json_string = child.children.__next__().split("var playlist = ")[1].split("];")[0] + "]"
            else:
                json_string = child.text.split("var playlist = ")[1].split("];")[0] + "]"

            new_json_string = ""
            for line in json_string.split("\n"):
                line = line.strip()
                if len(line) == 0:
                    continue
                if line[0] in ["{", "}", "[", "]"]:
                    new_json_string += line + "\n"
                else:
                    first_elem = line.split(" ")[0][:-1]
                    if line[-1] == ",":
                        line = line[:-2]
                        post = ","
                    else:
                        line = line[:-1]
                        post = ""

                    value = line[len(first_elem)+3:].replace("\"", "\\\"").strip()
                    new_line = "\""+first_elem+"\": \""+value+"\""+post
                    new_json_string += new_line + "\n"

            music_dict = json.loads(new_json_string)
            for music in music_dict:
                old_length_split = music["length"].split(":")
                if old_length_split[0] == "": # happen here: http://mlp-france.com/extras/chansons/saison2.php
                    old_length_split[0] = 0
                music["length"] = int(old_length_split[0])*60+int(old_length_split[1])
                if "image" in music:
                    music["image"] = get_good_url(music["image"], url)
                else:
                    music["image"] = None
            result.append((actual_name, music_dict))

    return result


def list_films():
    url = "http://mlp-france.com/films/index.php"
    header, soup = get_header_link_list("FILMS", url)
    content = get_list_page_data(url, soup = soup)
    return merge_with_header(content, header)
