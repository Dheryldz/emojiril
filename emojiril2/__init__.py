import re

from typing import Iterable, Callable
from bs4 import BeautifulSoup, NavigableString


class Emojitos:
    """Match shortname notation and replace aliases with other content."""

    def __init__(self, prefix: str = ':', suffix: str = ':') -> None:
        self.replacements = {}
        self.set_affixes(prefix, suffix)

    def __setitem__(self, alias: str, replacement: str | Callable[[str], str]) -> None:
        """Map alias to replacement string or callable."""
        self.replacements[alias] = replacement


    def set_affixes(self, prefix: str = ':', suffix: str = ':') -> None:
        """Update pattern with new prefix and suffix."""
        prefix = re.escape(prefix)
        suffix = re.escape(suffix)
        self.pattern = re.compile(
            fr'(?P<escaped>\\)?'
            fr'(?P<text>{prefix}(?P<alias>[^\s\n]+?){suffix})',
            re.UNICODE)

    def add(self, aliases: Iterable[str], replacement: str | Callable[[str], str]) -> None:
        """Map aliases to replacement string or callable."""
        for alias in aliases:
            self[alias] = replacement


    def _replace_text(self, match: re.Match) -> str:
        """
        Replace a matched shortname with its replacement
        string or the result of its replacement callable.
        """

        escaped, alias = match.group('escaped', 'alias')
        
        # If escaped, don't replace it
        # and instead return notation without backslash
        if escaped:
            return match.group('text')

        # If alias matches a replacement,
        # use that and call it if it is a callable
        if alias in self.replacements:
            replacement = self.replacements[alias]

            if isinstance(replacement, Callable):
                return replacement(alias)
            return replacement

        # If it's neither escaped nor matched
        # with a replacement, just return as is.
        return match.group(0)

    def replace(self, document: str) -> str:
        """
        Replace all instances of shortnames
        with replacements in the collection.
        """
        
        bs = BeautifulSoup(document, 'html.parser')

        # Find all text in tags that is not or does not contain a tag itself
        for child in bs.findAll(string=True, recursive=True):
            # Match pattern for shortnames and insert their replacements
            mixed = self.pattern.sub(self._replace_text, child.string)
            child.replace_with(NavigableString(mixed))

        return str(bs)