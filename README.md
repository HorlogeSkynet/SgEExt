# SgEExt &mdash; a Simple gemoji Emoji Extractor

> Pronounced _[sgɪksˈt]_

<p align="center"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Emoji_u1f419.svg/240px-Emoji_u1f419.svg.png"></p>

## Introduction

Let's have a talk about an _usual_ situation.  
You run a self-hosted _Jekyll_ blog, with the [jemoji](https://github.com/jekyll/jemoji) plugin loaded so as to "enhance" your content with some emojis.  
You'd have noticed that [by default](https://github.com/jekyll/jemoji#emoji-images) the plugin renders your static pages with `<img>` whose `src` attributes are pointing to a _GitHub_'s (_Microsoft_'s) location.  
The latter means that **a third-party _is able_** (note that it _may_ not be the case) **to log people who consult your website**, and thus **is a privacy issue**.

So, at this step, you may have tried to [extract images](https://github.com/github/gemoji#extract-images) to serve it yourself, but **the operation is only possible from a macOS system** ('cause _Apple_ emojis are present within the system font, and... [gemoji is mainly using the "Apple's emoji character palette"](https://github.com/github/gemoji/blob/b04991b001e137c06cc56cebcabf0e458b5eea44/CONTRIBUTING.md#readme)).

Now that is said, there are your options :

* Buy an _Apple_ device
* Kindly ask a friend with an _Apple_ device to extract and send you those PNGs (cc [@Naernon](https://github.com/Naernon))
* Change your underneath emojis module / plugin / whatever
* Wait for the [gemoji project to use another set of emoji](https://github.com/github/gemoji/pull/72)
* **Download PNGs directly from _GitHub_**, and that is definitely what this project is about !

## Dependencies

* `python3`
* `python3-requests`

## Installation

### Manually

```bash
git clone https://github.com/HorlogeSkynet/SgEExt.git
```

## Usage

```bash
python3 sgeext.py --help

# Careful, running without any arguments would download the whole emojis palette !
# Resulting files will be set under `emoji/unicode/` (automatically created).
# Microsoft GitHub's emojis (images) will be set under `emoji/`.
python3 sgeext.py

# This directory structure will be created if it does not exist.
python3 sgeext.py -l joy -d emojis/images/

# Wanna force re-download of existing files ? Sure.
python3 sgeext.py -l joy relaxed sunglasses -d emojis/images/ -f

# Wanna save "real" emojis under their "real" name ? Sure.
python3 sgeext.py -l ok_hand -n

# Wanna download GitHub added "emojis" (mostly images) ? Sure.
python3 sgeext.py -l bow relaxed octocat trollface --verbose

# 'octocat' & 'trollface' would be ignored.
python3 sgeext.py -l bow relaxed octocat trollface --only-emojis

# Handle duplicates ('uk' and 'gb' refer to the same emoji).
python3 sgeext.py -l fr gb us jp uk jp gb it

# Wanna download the emojis currently being used in your (Jekyll) blog ? Sure.
python3 sgeext.py -l $(grep -hREo ':[a-z+-]+[a-z1-9_-]+:' /path/to/your/blog/_posts/*.md | sort | uniq | cut -d ':' -f 2) -d /path/to/your/blog/images/emojis/
```

## How does it work ?

The script... :

* ... (after having tried locally) fetches [the emojis database hosted on _GitHub_](https://github.com/github/gemoji/raw/master/db/emoji.json) (**don't** click if you are on mobile)
* ... iterates through the elements and extracts their unicode value as hexadecimal
* ... uses the above result to download them from _GitHub_

As `githubassets.com` is actually a CDN, it does not _look_ rate-limited.  
Anyway, I cannot take any responsibility for any inappropriate usage of this software.

## Compatibility

Although SgEExt has been developed with cross-platform constraints, it **has not been tested on _Windows_ yet**.  
Feedbacks are welcome, as usual.

_Apple_ users, [you **don't** have to go this way](https://github.com/github/gemoji#extract-images).
