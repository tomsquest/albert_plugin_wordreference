# WordReference Translations in Albert Launcher

This plugin helps you **quickly translate words** using [WordReference.com](https://www.wordreference.com/) directly from [Albert Launcher](https://albertlauncher.github.io/).

Albert will display translations with the same formatting as WordReference, including grammatical information and example sentences.

## Features

- 🌐 Translate words between multiple languages
- 🔤 Show grammatical information (noun, verb, adjective, etc.)
- 📝 Display example sentences
- 🌟 Format results similar to WordReference's website
- 📋 Copy translations with a single click
- 🔗 Open full translation in browser

## Setup

1. Make the plugin directory

```
mkdir -p ~/.local/share/albert/python/plugins/wordreference
```

2. Download the plugin files

```
# Option 1: Clone the repository
git clone https://github.com/tomsquest/albert-wordreference-plugin.git ~/.local/share/albert/python/plugins/wordreference

# Option 2: Download the __init__.py file directly
wget -O ~/.local/share/albert/python/plugins/wordreference/__init__.py https://raw.githubusercontent.com/tomsquest/albert-wordreference-plugin/main/__init__.py
```

3. Enable the plugin in `Settings > Plugins` and tick `WordReference`

   Albert will automatically install the required dependencies.

5. The trigger is `w`, so use it followed by a language pair and word to translate. 
You can change the trigger in Albert settings.

## Usage

The format to translate words is:

```
w[language_pair] [word]
```

Where `language_pair` is a 4-letter code with source and target languages.

### Examples:

- `wenfr hello` - Translate "hello" from English to French
- `wfren bonjour` - Translate "bonjour" from French to English
- `wende computer` - Translate "computer" from English to German
- `wesen gracias` - Translate "gracias" from Spanish to English

### Supported Language Pairs

The plugin supports all language pairs available on WordReference, including:

- `enfr` - English to French
- `fren` - French to English
- `enes` - English to Spanish
- `esen` - Spanish to English
- `ende` - English to German
- `deen` - German to English
- `enit` - English to Italian
- `iten` - Italian to English
- And many more...

## License

MIT License