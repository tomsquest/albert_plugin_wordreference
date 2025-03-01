from pathlib import Path
from typing import List, Dict, Any, Tuple

from wrpy import WordReference, get_available_dicts

from albert import *

md_iid = "3.0"
md_version = "1.0"
md_name = "WordReference"
md_description = "Translate words using WordReference"
md_license = "MIT"
md_url = "https://github.com/tomsquest/albert-wordreference-plugin"
md_authors = ["@tomsquest"]
md_lib_dependencies = ["wrpy"]

plugin_icon = Path(__file__).parent / "wordreference.svg"


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)
        self.available_dicts: Dict[str, Dict[str, str]] = get_available_dicts()
        self.wr_instances: Dict[str, WordReference] = {}

    def supportsFuzzyMatching(self) -> bool:
        return False

    def setFuzzyMatching(self, enabled: bool) -> None:
        pass

    def defaultTrigger(self) -> str:
        return "w"

    def handleTriggerQuery(self, query: Query) -> None:
        query_str = query.string.strip()
        if not query_str:
            self._show_usage(query)
            return

        parts = query_str.split(maxsplit=1)
        if len(parts) < 2 or len(parts[0]) != 4:
            self._show_usage(query)
            return

        lang_pair, text_to_translate = parts[0].lower(), parts[1]
        if lang_pair not in self.available_dicts:
            self._show_invalid_language_pair(query, lang_pair)
            return

        self._translate(query, lang_pair, text_to_translate)

    def _show_usage(self, query: Query) -> None:
        query.add(
            StandardItem(
                id="translator_usage",
                text="WordReference Translation",
                subtext="Format: [language_pair] [word] (e.g., 'enfr hello')",
                iconUrls=[f"file:{plugin_icon}"],
                inputActionText=f"{query.trigger}enfr ",
                actions=[
                    Action(
                        "copy", "Copy format", lambda: setClipboardText("enfr hello")
                    )
                ],
            )
        )

        examples = [
            ("enfr hello", "English to French"),
            ("fren bonjour", "French to English"),
            ("ende computer", "English to German"),
            ("esen gracias", "Spanish to English"),
        ]

        for i, (example, desc) in enumerate(examples):
            query.add(
                StandardItem(
                    id=f"translator_example_{i}",
                    text=f"Example: {example}",
                    subtext=desc,
                    iconUrls=[f"file:{plugin_icon}"],
                    inputActionText=f"{query.trigger}{example}",
                    actions=[
                        Action(
                            "use",
                            "Use this example",
                            lambda ex=example: setClipboardText(f"{query.trigger}{ex}"),
                        )
                    ],
                )
            )

    def _show_invalid_language_pair(self, query: Query, lang_pair: str) -> None:
        query.add(
            StandardItem(
                id="translator_invalid_pair",
                text=f"Invalid language pair: {lang_pair}",
                subtext="Please use one of the supported language pairs",
                iconUrls=[f"file:{plugin_icon}"],
            )
        )

        how_many_examples = 8
        for code, details in list(self.available_dicts.items())[:how_many_examples]:
            if code in ["esca", "ruen"]:
                continue

            query.add(
                StandardItem(
                    id=f"translator_pair_{code}",
                    text=f"{code}: {details['from']} to {details['to']}",
                    subtext=f"Language pair for translating from {details['from']} to {details['to']}",
                    iconUrls=[f"file:{plugin_icon}"],
                    inputActionText=f"{query.trigger}{code} ",
                    actions=[
                        Action(
                            "use",
                            "Use this language pair",
                            lambda c=code: setClipboardText(f"{query.trigger}{c} "),
                        )
                    ],
                )
            )

    def _translate(self, query: Query, lang_pair: str, text: str) -> None:
        try:
            if lang_pair not in self.wr_instances:
                self.wr_instances[lang_pair] = WordReference(lang_pair)

            result = self.wr_instances[lang_pair].translate(text)
            if not result or "translations" not in result or not result["translations"]:
                query.add(
                    StandardItem(
                        id="translator_no_results",
                        text="No translation results found",
                        subtext=f"Could not translate '{text}' from {result.get('from_lang', '')} to {result.get('to_lang', '')}",
                        iconUrls=[f"file:{plugin_icon}"],
                        actions=[
                            Action(
                                "retry", "Try again", lambda t=text: setClipboardText(t)
                            )
                        ],
                    )
                )
                return

            url = result.get("url", "")
            for section_idx, section in enumerate(result["translations"]):
                section_title = section.get("title", f"Section {section_idx + 1}")

                for entry_idx, entry in enumerate(section.get("entries", [])):
                    if (
                        section_idx == 0
                        and entry_idx == 0
                        and entry.get("from_word", {}).get("source", "").lower()
                        == text.lower()
                    ):
                        continue

                    context = entry.get("context", "")
                    from_word: Dict[str, str] = entry.get("from_word", {})
                    source = from_word.get("source", text)
                    from_grammar = from_word.get("grammar", "")
                    from_example = entry.get("from_example", "")

                    to_words: List[Dict[str, str]] = entry.get("to_word", [])
                    for to_idx, to_word in enumerate(to_words):
                        meaning = to_word.get("meaning", "")
                        notes = to_word.get("notes", "")
                        grammar = to_word.get("grammar", "")

                        source_with_grammar = f"{source} {from_grammar}".strip()
                        target_with_grammar = (
                            f"{meaning} {grammar} ({notes})".strip()
                        )

                        display_text = (
                            f"{source_with_grammar} → {target_with_grammar}"
                        )

                        subtext_parts = [context] if context else []
                        example_parts = (
                            [from_example] if from_example else []
                        )
                        to_examples: List[str] = entry.get("to_example", [])
                        if to_examples and to_idx < len(to_examples):
                            example_parts.append(to_examples[to_idx])

                        if example_parts:
                            subtext_parts.append(" ⟹ ".join(example_parts))

                        subtext = (
                            "\n".join(subtext_parts) if subtext_parts else section_title
                        )

                        result_id = (
                            f"translator_result_{section_idx}_{entry_idx}_{to_idx}"
                        )

                        result_item = StandardItem(
                            id=result_id,
                            text=display_text,
                            subtext=subtext,
                            iconUrls=[f"file:{plugin_icon}"],
                            actions=[
                                Action(
                                    "copy",
                                    "Copy translation",
                                    lambda meaning=meaning: setClipboardText(meaning),
                                )
                            ],
                        )

                        if url:
                            result_item.actions.append(
                                Action(
                                    "open",
                                    "Open in browser",
                                    lambda url=url: openUrl(url),
                                )
                            )

                        query.add(result_item)

        except Exception as e:
            critical(f"Translation error: {str(e)}")

            query.add(
                StandardItem(
                    id="translator_error",
                    text="Translation error",
                    subtext=str(e),
                    iconUrls=[f"file:{plugin_icon}"],
                    actions=[
                        Action(
                            "copy",
                            "Copy error",
                            lambda err=str(e): setClipboardText(err),
                        )
                    ],
                )
            )

    def configWidget(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "label",
                "text": 'Use `w` trigger followed by language pair and word.\n\nFor example: `wenfr hello` to '
                        'translate from English to French.\n\n`w` is the default trigger but can be remapped in the '
                        'Albert settings.',
                "widget_properties": {"textFormat": "Qt::MarkdownText"},
            },
        ]
