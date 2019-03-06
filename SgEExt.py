#!/usr/bin/env python3


import argparse
import json
import os
import re
import sys

from shutil import copyfile
from subprocess import check_output, CalledProcessError

import requests


# Emojis and "regular" images are served by GitHub here.
GITHUB_ASSETS_BASE_URL = "https://github.githubassets.com/images/icons/emoji/{}.png"


def open_and_load_emojis_db(file_path):
    """Open `file_path`, load its content as JSON and return it"""
    try:
        with open(file_path) as f_emojis_db:
            emojis_db = json.load(f_emojis_db)

    except (FileNotFoundError, json.JSONDecodeError) as error:
        emojis_db = None
        print(
            "Could not read or load the emojis database : {}".format(error),
            file=sys.stderr
        )

    return emojis_db


def download_file(url, path=None):
    """Download a file specified by `url` and save it locally under `path`"""
    # See <https://stackoverflow.com/a/16696317/10599709>
    file_name = url.split('/')[-1]

    if not path:
        path = os.getcwd()

    if not path.endswith(os.sep):
        path += os.sep

    if not os.path.exists(path):
        os.makedirs(path, mode=0o755)

    with requests.get(url, stream=True) as get_request:
        with open(path + file_name, 'wb') as f_image:
            for chunk in get_request.iter_content(chunk_size=8192):
                if chunk:
                    f_image.write(chunk)

            f_image.flush()


def main():
    """Simple entry point"""
    parser = argparse.ArgumentParser(
        description="A simple gemoji emojis extractor for non macOS users",
        prog="SGEE"
    )
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=os.getcwd() + os.sep + 'emojis',
        help="Extraction path location"
    )
    parser.add_argument(
        '-v', '--version',
        action='version', version="%(prog)s : 1.0"
    )

    args = parser.parse_args()
    if not args.directory.endswith(os.sep):
        args.directory += os.sep

    try:
        # Try to retrieve the path of the local installation of Gemoji Ruby gem.
        gem_wich_gemoji_output = check_output(
            ['gem', 'which', 'gemoji'],
            universal_newlines=True
        ).strip()

        # Now, try to extract its grand-parent location.
        # Usually : `/var/lib/gems/X.Y.Z/gems/gemoji-T.U.V/lib/gemoji.rb`
        # Please check <https://github.com/github/gemoji> project structure.
        gemoji_local_path = re.fullmatch(
            r'^(.+?{0}gemoji-.+?{0})lib{0}gemoji.rb$'.format(
                re.escape(os.sep)
            ),
            gem_wich_gemoji_output
        )

        # If the regex matched, extract the capturing group.
        if gemoji_local_path:
            gemoji_local_path = gemoji_local_path.group(1)

    except CalledProcessError:
        # Local gem not available ? Not an issue, we will figure something out.
        gemoji_local_path = None

    # Now, let's try to load the emojis database (JSON).
    emojis_db, emojis_db_local_file = None, None
    if gemoji_local_path:
        emojis_db = open_and_load_emojis_db(
            gemoji_local_path + 'db' + os.sep + 'emoji.json'
        )

    else:
        # If we don't have it locally, just temporarily fetch it from the GitHub project.
        download_file(
            "https://github.com/github/gemoji/raw/master/db/emoji.json"
        )
        emojis_db_local_file = os.getcwd() + os.sep + 'emoji.json'
        emojis_db = open_and_load_emojis_db(emojis_db_local_file)
        os.remove(emojis_db_local_file)

    # Iterate over the elements, looking for "real" emojis and "regular" images.
    for emoji in emojis_db:
        if 'emoji' in emoji:
            # Extract emoji unicode value, and format it as an hexadecimal string.
            unicode = ''.join(format(ord(char), 'x') for char in emoji['emoji'])
            url = GITHUB_ASSETS_BASE_URL.format('unicode/' + unicode)
            download_file(url, args.directory)

        else:
            # Those are GitHub "fake" emojis (regular images).
            image_name = emoji['aliases'][0]

            if gemoji_local_path:
                # We already have it locally somewhere, just copy it...
                image_name += '.png'
                copyfile(
                    gemoji_local_path + 'images' + os.sep + image_name,
                    args.directory + image_name
                )

            else:
                # I told you it was not an issue, let's download it as well !
                url = GITHUB_ASSETS_BASE_URL.format(image_name)
                download_file(url, args.directory)


if __name__ == '__main__':
    main()
