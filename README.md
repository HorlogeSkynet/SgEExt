# SgEExt &mdash; a Simple gemoji Emoji Extractor

> Pronounced _[sgɪksˈt]_

<p align="center">
	<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Emoji_u1f419.svg/240px-Emoji_u1f419.svg.png">
</p>

## Introduction

Let's have a talk about an _usual_ situation.  
You run a self-hosted _Jekyll_ blog, with the [jemoji](https://github.com/jekyll/jemoji) plugin loaded so as to "enhanced" your content with some emojis.  
You'd have noticed that [by default](https://github.com/jekyll/jemoji#emoji-images) the plugin renders your static pages with `<img>` whose `src` attributes are pointing to a _GitHub_'s (_Microsoft_'s) location.  
The latter means that **a third-party _is able_** (note that it _may_ not be the case) **to log people who consult your website**, and thus **is a privacy issue**.

So, at this step, you may have tried to [extract images](https://github.com/github/gemoji#extract-images) to serve it yourself, but **the operation is only possible from a macOS system** ('cause _Apple_ emojis are present within the system font, and... [gemoji is mainly using the "Apple's emoji character palette"](https://github.com/github/gemoji/blob/b04991b001e137c06cc56cebcabf0e458b5eea44/CONTRIBUTING.md#readme)).

Now that is said, you have some options :

* Buy an _Apple_ device
* Kindly ask a friend with an _Apple_ device to extract and send you those PNGs (cc @Naernon)
* Change your underneath emojis module / plugin / whatever
* Wait for the [gemoji project to use another set of emoji](https://github.com/github/gemoji/pull/72)
* **Download PNGs directly from _GitHub_**, and that is definitely what this is about !

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
python3 SgEExt.py --help
```

## How does it work ?

The script... :

* ... (after having tried locally) fetches [the emojis database hosted on _GitHub_](https://github.com/github/gemoji/raw/master/db/emoji.json) (**don't** click if you are on mobile)
* ... iterates through the elements and extracts their unicode value as hexadecimal
* ... uses the above result to download them from _GitHub_

## Compatibility

Although SgEExt has been developed with cross-platform constraints, it **has not been tested on _Windows_ yet**.  
Feedbacks are welcome, as usual.

_Apple_ users, [you **don't** have to go this way](https://github.com/github/gemoji#extract-images).
