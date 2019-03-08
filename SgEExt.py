#!/usr/bin/env python3


import argparse
import json
import logging
import os
import re

from shutil import copyfile
from subprocess import check_output, CalledProcessError, DEVNULL

import requests


# Emojis and "regular" images are served by GitHub here.
GITHUB_ASSETS_BASE_URL = "https://github.githubassets.com/images/icons/emoji/{}.png"


def open_and_load_emojis_db(file_path):
    """Open `file_path`, load its content as JSON and return it"""
    try:
        with open(file_path) as f_emojis_db:
            emojis_db = json.load(f_emojis_db)

    except (FileNotFoundError, json.JSONDecodeError) as error:
        emojis_db = []
        logging.error("Could not read or load the emojis database : %s", error)

    return emojis_db


def download_file(url, path=None):
    """
    Download a file specified by `url` and save it locally under `path`.
    Normalize path and / or create non-existing directory structure.
    See <https://stackoverflow.com/a/16696317/10599709>
    """

    if not path:
        path = os.getcwd()

    if not path.endswith(os.sep):
        path += os.sep

    if not os.path.exists(path):
        os.makedirs(path, mode=0o755)

    # We will save this entity under its remote name.
    file_name = path + url.split('/')[-1]
    logging.info("Downloading <%s> to \"%s\"", url, file_name)

    with requests.get(url, stream=True) as get_request:
        if get_request.status_code != 200:
            # This URL does not exist ; Don't try to download a thing !
            logging.warning("The URL above does not exist, can\'t download.")
            return

        with open(file_name, 'wb') as f_image:
            for chunk in get_request.iter_content(chunk_size=8192):
                if chunk:
                    f_image.write(chunk)

            f_image.flush()


def localize_emoji_install():
    """Return the root path of the local gemoji gem install, or `None`"""
    try:
        # Try to retrieve the path of the local installation of Gemoji Ruby gem.
        gem_wich_gemoji_output = check_output(
            ['gem', 'which', 'gemoji'],
            universal_newlines=True,
            stderr=DEVNULL
        ).strip()

        # Now, try to extract its grand-parent location.
        # Usually `/var/lib/gems/X.Y.Z/gems/gemoji-T.U.V/lib/gemoji.rb` on GNU/Linux.
        # Please check <https://github.com/github/gemoji> project structure.
        gemoji_local_path = re.fullmatch(
            r'^(.+?{0}gemoji-.+?{0})lib{0}gemoji.rb$'.format(
                re.escape(os.sep)
            ),
            gem_wich_gemoji_output
        )

        # If the regex matched, extract the capturing group.
        # Else, it would be `None` below.
        if gemoji_local_path:
            gemoji_local_path = gemoji_local_path.group(1)

    except (FileNotFoundError, CalledProcessError) as error:
        # Local gem not available ? Not an issue, we will figure something out.
        gemoji_local_path = None

    if not gemoji_local_path:
        logging.info("Localization of the gemoji gem installation failed : %s", error)

    return gemoji_local_path


def perform_emojis_extraction(path, subset):
    """
    Effectively perform the emojis extraction.
    By default, run extraction on the whole set.
    The `subset` parameter allows the user to provide a specific list of emojis.
    """

    gemoji_local_path = localize_emoji_install()

    # Now, let's try to load the emojis database (JSON).
    if gemoji_local_path:
        emojis_db = open_and_load_emojis_db(
            gemoji_local_path + 'db' + os.sep + 'emoji.json'
        )

    else:
        # If we don't have it locally, just temporarily fetch it from the GitHub project.
        download_file("https://github.com/github/gemoji/raw/master/db/emoji.json")
        emojis_db_local_file = os.getcwd() + os.sep + 'emoji.json'
        emojis_db = open_and_load_emojis_db(emojis_db_local_file)
        os.remove(emojis_db_local_file)
        logging.info(
            "The temporarily emojis database (\"%s\") has been removed.",
            emojis_db_local_file
        )

    # Iterate over the elements, looking for "real" emojis and "regular" images.
    i = 0
    for emoji in emojis_db:
        if subset:
            # Intersect our `subset` names with this emoji's aliases !
            # This allows us to "find" emojis whose user-supplied name is an alternative.
            match_name = set(emoji['aliases']) & set(subset)
            if not match_name:
                continue

            # The _first_ alias in the list is effectively used to compute its unicode value.
            first_alias = emoji['aliases'][0]

        if 'emoji' in emoji:
            # Extract emoji unicode value, and format it as an hexadecimal string.
            unicode = ''.join(format(ord(char), 'x') for char in emoji['emoji'])

            # Some emojis contain a "variation selector" at the end of their unicode value.
            # VS-15 : U+FE0E || VS-16 : U+FE0F
            unicode = re.sub(r'fe0[ef]$', '', unicode, re.IGNORECASE)

            logging.info("Unicode value of \'%s\' found : %s", first_alias, unicode)
            url = GITHUB_ASSETS_BASE_URL.format('unicode/' + unicode)
            download_file(url, path)

        else:
            # Those are GitHub "fake" emojis ("regular" images).
            image_name = first_alias

            if gemoji_local_path:
                # We already have it locally somewhere, just copy it...
                image_name += '.png'
                logging.info("Copying \'%s\' from your local system", image_name)
                copyfile(
                    gemoji_local_path + 'images' + os.sep + image_name,
                    path + image_name
                )

            else:
                # I told you it was not an issue, let's download it as well !
                url = GITHUB_ASSETS_BASE_URL.format(image_name)
                download_file(url, path)

        i += 1

        if subset:
            # The operations above _should_ be OK, we may remove this element from the set.
            subset.remove(match_name.pop())
            if not subset:
                # We reached the end of the user-supplied elements. We may stop the iteration.
                break

    # At this moment, `subset` contains only the elements that have not been found...
    if subset:
        logging.warning(
            "The following emojis have not been found : \'%s\'",
            '\', \''.join(subset)
        )

    logging.info("Successfully downloaded / copied %i emojis !", i)


def main():
    """Simple entry point"""
    parser = argparse.ArgumentParser(
        description="A simple gemoji emojis extractor for non macOS users",
        prog="SgEExt"
    )
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=os.getcwd() + os.sep + 'emojis',
        help="Extraction path location"
    )
    parser.add_argument(
        '-l', '--list',
        type=str,
        default=[],
        nargs='+',
        help="List of emojis aliases to operate on"
    )
    parser.add_argument(
        '--verbose',
        default=False,
        action='store_true'
    )
    parser.add_argument(
        '-v', '--version',
        action='version', version="%(prog)s : 1.3"
    )

    # Normalize the user-supplied target directory.
    args = parser.parse_args()
    if not args.directory.endswith(os.sep):
        args.directory += os.sep

    # Set format and level for logging.
    logging.basicConfig(
        format='[%(levelname)s] : %(message)s',
        level=(logging.INFO if args.verbose else logging.WARNING)
    )

    # EXTRACT ALL-THE-THINGS !
    perform_emojis_extraction(args.directory, args.list)


if __name__ == '__main__':
    main()
