from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# Import wrpy components for WordReference translation
from wrpy import WordReference, get_available_dicts

from albert import *

md_iid: str = "3.0"
md_version: str = "1.0"
md_name: str = "WordReference"
md_description: str = "Translate words using WordReference"
md_license: str = "MIT"
md_url: str = "https://github.com/tomsquest/albert-wordreference-plugin"
md_authors: List[str] = ["@tomsquest"]
md_lib_dependencies: List[str] = ["wrpy"]

plugin_icon: Path = Path(__file__).parent / "wordreference.svg"


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self) -> None:
        PluginInstance.__init__(self)
        TriggerQueryHandler.__init__(self)

        # Get available dictionaries from wrpy
        self.available_dicts: Dict[str, Dict[str, str]] = get_available_dicts()

        # Cache for WordReference instances
        self.wr_instances: Dict[str, WordReference] = {}

    def supportsFuzzyMatching(self) -> bool:
        return False

    def setFuzzyMatching(self, enabled: bool) -> None:
        pass

    def defaultTrigger(self) -> str:
        return "w"

    def handleTriggerQuery(self, query: Query) -> None:
        """Handle translation queries"""
        query_str: str = query.string.strip()

        # Empty query - show usage info
        if not query_str:
            self._show_usage(query)
            return

        # Try to parse as "enfr hello" format (language codes followed by text)
        parts: List[str] = query_str.split(maxsplit=1)
        if len(parts) < 2 or len(parts[0]) != 4:
            self._show_usage(query)
            return

        lang_pair: str = parts[0].lower()
        text_to_translate: str = parts[1]

        # Check if the language pair is supported
        if lang_pair not in self.available_dicts:
            self._show_invalid_language_pair(query, lang_pair)
            return

        # Perform translation
        self._translate(query, lang_pair, text_to_translate)

    def _show_usage(self, query: Query) -> None:
        """Show usage instructions"""
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

        # Show some examples
        examples: List[Tuple[str, str]] = [
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
        """Show error for invalid language pair"""
        query.add(
            StandardItem(
                id="translator_invalid_pair",
                text=f"Invalid language pair: {lang_pair}",
                subtext="Please use one of the supported language pairs",
                iconUrls=[f"file:{plugin_icon}"],
            )
        )

        # Show some supported language pairs
        count: int = 0
        for code, details in self.available_dicts.items():
            if count >= 10:  # Limit to 10 examples
                break

            # Skip non-working dictionaries mentioned in documentation
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
            count += 1

    def _translate(self, query: Query, lang_pair: str, text: str) -> None:
        """Perform the actual translation using WordReference"""
        try:
            info(f"Starting translation for '{text}' with language pair '{lang_pair}'")

            # Get or create WordReference instance
            if lang_pair not in self.wr_instances:
                info(f"Creating new WordReference instance for '{lang_pair}'")
                self.wr_instances[lang_pair] = WordReference(lang_pair)

            # Get translation
            info(f"Calling WordReference.translate() for '{text}'")
            result: Optional[Dict[str, Any]] = self.wr_instances[lang_pair].translate(
                text
            )

            # Log the result structure
            info(f"Translation result received: {type(result)}")
            debug(
                f"Result keys: {result.keys() if result and isinstance(result, dict) else 'None'}"
            )

            if not result or "translations" not in result or not result["translations"]:
                info(f"No translations found for '{text}'")
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

            # Add result URL as an action
            url: str = result.get("url", "")
            info(f"Translation URL: {url}")

            # Don't display source info as a separate item
            # Just log it for debugging
            info(
                f"Word: {result['word']} ({result['from_lang']} to {result['to_lang']})"
            )
            info(f"Translation URL: {url}")

            # Log translation sections
            info(f"Processing {len(result['translations'])} translation sections")

            # Process each translation section
            for section_idx, section in enumerate(result["translations"]):
                section_title: str = section.get("title", f"Section {section_idx + 1}")
                info(f"Processing section {section_idx + 1}: {section_title}")

                for entry_idx, entry in enumerate(section.get("entries", [])):
                    # Skip first entry if it's just displaying the original word
                    if (
                        section_idx == 0
                        and entry_idx == 0
                        and entry.get("from_word", {}).get("source", "").lower()
                        == text.lower()
                    ):
                        continue

                    context: str = entry.get("context", "")
                    info(f"  Entry {entry_idx + 1} context: {context}")

                    # Get the source word details
                    from_word: Dict[str, str] = entry.get("from_word", {})
                    source: str = from_word.get("source", text)
                    from_grammar: str = from_word.get("grammar", "")

                    # Source examples
                    from_example: str = entry.get("from_example", "")

                    # Process each translation
                    to_words: List[Dict[str, str]] = entry.get("to_word", [])
                    info(f"  Processing {len(to_words)} translations for this entry")

                    for to_idx, to_word in enumerate(to_words):
                        meaning: str = to_word.get("meaning", "")
                        notes: str = to_word.get("notes", "")
                        grammar: str = to_word.get("grammar", "")

                        info(
                            f"    Translation {to_idx + 1}: '{meaning}' (grammar: {grammar}, notes: {notes})"
                        )

                        # Format the display text in WordReference style
                        source_with_grammar: str = f"{source}"
                        if from_grammar:
                            source_with_grammar += f" {from_grammar}"

                        target_with_grammar: str = f"{meaning}"
                        if grammar:
                            target_with_grammar += f" {grammar}"

                        if notes:
                            target_with_grammar += f" ({notes})"

                        display_text: str = (
                            f"{source_with_grammar} → {target_with_grammar}"
                        )

                        # Format examples for subtext
                        subtext_parts: List[str] = []
                        if context:
                            subtext_parts.append(f"{context}")

                        # Add examples
                        example_parts: List[str] = []
                        if from_example:
                            example_parts.append(from_example)

                        to_examples: List[str] = entry.get("to_example", [])
                        if to_examples and to_idx < len(to_examples):
                            example_text: str = to_examples[to_idx]
                            example_parts.append(example_text)

                        if example_parts:
                            subtext_parts.append(" ⟹ ".join(example_parts))

                        subtext: str = (
                            "\n".join(subtext_parts)
                            if subtext_parts
                            else f"{section_title}"
                        )

                        # Create unique ID for this result
                        result_id: str = (
                            f"translator_result_{section_idx}_{entry_idx}_{to_idx}"
                        )

                        # Create the item
                        result_item: StandardItem = StandardItem(
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

                        # Add URL action if available
                        if url:
                            result_item.actions.append(
                                Action(
                                    "open",
                                    "Open in browser",
                                    lambda url=url: openUrl(url),
                                )
                            )

                        query.add(result_item)

            info(
                f"Translation for '{text}' completed successfully with {len(query.results) if hasattr(query, 'results') else 'some'} results"
            )

        except Exception as e:
            error_msg: str = f"Translation error: {str(e)}"
            critical(error_msg)

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
                "text": "WordReference Plugin",
                "widget_properties": {"textFormat": "Qt::MarkdownText"},
            },
            {
                "type": "label",
                "text": 'Use "w" trigger followed by language pair and word.\nFor example: "w enfr hello" to translate from English to French.',
                "widget_properties": {"textFormat": "Qt::MarkdownText"},
            },
        ]
