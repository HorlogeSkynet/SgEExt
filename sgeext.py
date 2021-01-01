#!/usr/bin/env python3

"""
SgEExt is a Simple gemoji Emoji Extractor script, to download (mostly from GitHub) gemoji PNGs.
The logic is simple but offers some options, just run `[python3] sgeext[.py] -h` to list them.
"""


import argparse
import json
import logging
import os
import re

from shutil import copyfile
from subprocess import check_output, CalledProcessError, DEVNULL
from typing import List, Optional

import requests  # pylint: disable=import-error


# Emojis and "regular" images are served by GitHub here.
GITHUB_ASSETS_BASE_URL = "https://github.githubassets.com/images/icons/emoji/{}.png"
# The emojis database from the gemoji project is hosted here.
EMOJI_DB_URL = "https://github.com/github/gemoji/raw/master/db/emoji.json"


def open_and_load_emojis_db(file_path: str) -> List[dict]:
    """Open `file_path`, load its content as JSON and return it"""
    try:
        with open(file_path, encoding='utf-8') as f_emojis_db:
            emojis_db = json.load(f_emojis_db)

    except (FileNotFoundError, json.JSONDecodeError) as error:
        emojis_db = []
        logging.error("Could not read or load the emojis database : %s.", error)

    return emojis_db


def download_file(url: str, path: str = None, force: bool = False, real_name: str = None) -> bool:
    """
    Download a file specified by `url` and save it locally under `path`.
    Normalize path and / or create non-existing directory structure.
    Returns `True` on success, and `False` on error.
    See <https://stackoverflow.com/a/16696317/10599709>
    """
    if not path:
        path = os.getcwd()
    elif not os.path.exists(path):
        os.makedirs(path, mode=0o755)

    # Save this entity under the specified name, or directly its remote name.
    if real_name:
        file_name = os.path.join(path, real_name + '.png')
    else:
        file_name = os.path.join(path, url.split('/')[-1])

    if not force and os.path.exists(file_name):
        # This file already exists, skip it when running non-force mode.
        logging.info(
            "The file \"%s\" already exists, run `-f` to download it again.",
            file_name
        )
        return True

    logging.info("Downloading <%s> to \"%s\"", url, file_name)

    with requests.get(url, stream=True) as get_request:
        if get_request.status_code != 200:
            # This URL does not exist ; Don't try to download a thing !
            logging.warning("The URL above does not exist, can\'t download.")
            return False

        with open(file_name, 'wb') as f_image:
            for chunk in get_request.iter_content(chunk_size=8192):
                if chunk:
                    f_image.write(chunk)

            f_image.flush()

    return True


def localize_emoji_install() -> Optional[str]:
    """Return the root path of the local gemoji gem install, or `None`"""
    try:
        # Try to retrieve the path of the local installation of Gemoji Ruby gem.
        gem_wich_gemoji_output = check_output(
            ['gem', 'which', 'gemoji'],
            universal_newlines=True,
            stderr=DEVNULL
        ).strip()
    except (FileNotFoundError, CalledProcessError) as error:
        # Local gem not available ? Not an issue, we will figure something out.
        logging.info("Localization of the gemoji gem installation failed : %s.", error)
        return None

    # Now, try to extract its grand-parent location.
    # Usually `/var/lib/gems/X.Y.Z/gems/gemoji-T.U.V/lib/gemoji.rb` on GNU/Linux.
    # Please check <https://github.com/github/gemoji> project structure.
    gemoji_local_path = re.fullmatch(
        r"^(.+?{0}gemoji-.+?{0})lib{0}gemoji\.rb$".format(re.escape(os.sep)),
        gem_wich_gemoji_output
    )
    if not gemoji_local_path:
        logging.info(
            "gemoji looks installed on your system, but couldn\'t locate it precisely."
            " Please open an issue on the project repository."
        )
        return None

    logging.info("Found gemoji gem installation folder : \'%s\'.", gemoji_local_path.group(1))
    return gemoji_local_path.group(1)


def retrieve_emoji_db(gemoji_local_path: str = None) -> List[dict]:
    """
    This function tries anyhow to open and load an emoji database.
    It may end up locally (see `gemoji_local_path`), or remote (gemoji sources on GitHub).
    """
    # Now, let's try to load the emojis database (JSON).
    if gemoji_local_path:
        return open_and_load_emojis_db(
            os.path.join(gemoji_local_path + 'db', 'emoji.json')
        )

    # If we don't have it locally, just temporarily fetch it from the GitHub project.
    download_file(EMOJI_DB_URL)
    emojis_db_local_file = os.path.join(os.getcwd(), 'emoji.json')
    emojis_db = open_and_load_emojis_db(emojis_db_local_file)
    os.remove(emojis_db_local_file)
    logging.info(
        "The temporarily emojis database (\"%s\") has been removed.",
        emojis_db_local_file
    )

    return emojis_db


def handle_emoji_extraction(
        emoji: dict,
        first_alias: str,
        path: str,
        force: bool,
        real_names: bool
    ):
    """Simple function reduce `perform_emojis_extraction` cyclomatic complexity"""

    # Extract emoji unicode value, and format it as an hexadecimal string.
    unicode = ''.join(format(ord(char), 'x') for char in emoji['emoji'])

    # Some emojis contain a "variation selector" at the end of their unicode value.
    # VS-15 : U+FE0E || VS-16 : U+FE0F
    unicode = re.sub(r'fe0[ef]$', '', unicode, re.IGNORECASE)

    # For "shrugging" emojis only (`1f937-*`), we have to replace `200d` by a real hyphen.
    unicode = re.sub(r'^(1f937)(?:200d)(.*)$', r'\1-\2', unicode, re.IGNORECASE)

    # For "flags" emojis only (`1f1??1f1??`), we have to add an extra hyphen...
    unicode = re.sub(r'^(1f1)(..)(1f1)(..)$', r'\1\2-\3\4', unicode, re.IGNORECASE)

    logging.info("Unicode value of \'%s\' found : %s", first_alias, unicode)

    return download_file(
        url=GITHUB_ASSETS_BASE_URL.format('unicode/' + unicode),
        path=os.path.join(path, 'unicode'),
        force=force,
        real_name=(first_alias if real_names else None)
    )


def handle_github_emojis(
        first_alias: str, path: str, force: bool, gemoji_local_path: str = None
    ) -> bool:
    """Simple function reducing `perform_emojis_extraction` cyclomatic complexity"""
    if not gemoji_local_path:
        # I told you it was not an issue, let's download it as well !
        return download_file(
            url=GITHUB_ASSETS_BASE_URL.format(first_alias),
            path=path,
            force=force
        )

    # We already have it locally somewhere, just copy it...
    image_name = first_alias + '.png'
    image_local_path = os.path.join(path, image_name)
    if not force and os.path.exists(image_local_path):
        # This file already exists, skip it when running non-force mode.
        logging.info(
            "The file \"%s\" already exists, run `-f` to copy it again.",
            image_local_path
        )
    else:
        logging.info("Copying \'%s\' from your local system.", image_local_path)
        copyfile(
            os.path.join(gemoji_local_path, 'images', image_name),
            image_local_path
        )

    return True


def perform_emojis_extraction(
        path: str, force: bool, subset: List[str], real_names: bool, only_real_emojis: bool
    ):
    """
    Effectively perform the emojis extraction.
    By default, run extraction on the whole set.
    The `subset` parameter allows the user to provide a specific list of emojis.
    """

    gemoji_local_path = localize_emoji_install()
    emojis_db = retrieve_emoji_db(gemoji_local_path)

    # Iterate over the elements, looking for "real" emojis and "regular" images.
    i = 0
    for emoji in emojis_db:
        if subset:
            # Intersect our `subset` names with this emoji's aliases !
            # This allows us to "find" emojis whose user-supplied name is an alternative.
            # For instance : Match `bow`, even if its "official" name is `bowing_man`.
            match_names = set(emoji['aliases']) & set(subset)
            if not match_names:
                continue

            # The _first_ alias in the list is effectively used to compute its unicode value.
            first_alias = emoji['aliases'][0]

        if 'emoji' in emoji:
            if handle_emoji_extraction(emoji, first_alias, path, force, real_names):
                i += 1

        elif not only_real_emojis:
            # Those are GitHub "fake" emojis ("regular" images).
            if handle_github_emojis(first_alias, path, force, gemoji_local_path):
                i += 1

        if subset:
            # The operations above _should_ be OK, we may remove these elements from the set.
            for match_name in match_names:
                subset.remove(match_name)
            if not subset:
                # We reached the end of the user-supplied elements. We may stop the iteration.
                break

    # At this moment, `subset` contains only the elements that have not been found...
    if subset:
        logging.warning(
            "The following emojis have not been found : \'%s\'",
            "\', \'".join(subset)
        )

    logging.info("Successfully downloaded / copied %i emojis !", i)


def main():
    """Simple entry point"""
    parser = argparse.ArgumentParser(
        description="A simple gemoji emojis extractor (for non macOS users)"
    )
    parser.add_argument(
        '-d', '--directory',
        type=str,
        default=os.path.join(os.getcwd(), 'emoji'),
        help="Extraction path location"
    )
    parser.add_argument(
        '-f', '--force',
        default=False,
        action='store_true',
        help="Force file download, even if they already exist"
    )
    parser.add_argument(
        '-l', '--list',
        type=str,
        default=[],
        nargs='+',
        help="List of emojis aliases to operate on"
    )
    parser.add_argument(
        '-n', '--names',
        default=False,
        action='store_true',
        help="Save emojis under their \"real\" name instead of unicode"
    )
    parser.add_argument(
        '-o', '--only-emojis',
        default=False,
        action='store_true',
        help="Ignores \"fake\" emojis (images) added by GitHub"
    )
    parser.add_argument(
        '-v', '--verbose',
        default=False,
        action='store_true',
        help="Show debugging logs and monitor progression"
    )
    parser.add_argument(
        '--version',
        action='version', version="%(prog)s : 2.5.0"
    )

    # Normalize the user-supplied target directory.
    args = parser.parse_args()

    # Set format and level for logging.
    logging.basicConfig(
        format="[%(levelname)s] : %(message)s",
        level=(logging.INFO if args.verbose else logging.WARNING)
    )

    # EXTRACT ALL-THE-THINGS !
    perform_emojis_extraction(args.directory, args.force, args.list, args.names, args.only_emojis)


if __name__ == '__main__':
    main()
