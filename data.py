from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path
import re
from typing import Literal, Sequence

from yattag import Doc as XmlDoc
import pandas as pd


class Dataset:
    episodes: Sequence[Episode]

    def __init__(self, episodes: Sequence[Episode]) -> None:
        self.episodes = episodes

    @classmethod
    def load(cls) -> Dataset:
        data_dir = Path(__file__).resolve().parent / "data" / "episodes"

        episodes = list[Episode]()
        for path in data_dir.iterdir():
            title = path.name
            with open(path / "transcript.txt") as f:
                transcript = f.read()
            with open(path / "words.txt") as f:
                words_txt = f.read()
                words = parse_words(words_txt)
            with open(path / "lexems.txt") as f:

                def line():
                    return [w.replace("\n", "") for w in f.readline().split(", ")]

                kernel_words = line()
                close_words = line()
                far_words = line()
                lexems = Lexems(kernel_words, close_words, far_words)

            episodes.append(Episode(title, transcript, words, lexems))
        return cls(episodes)


def episodes_to_dataframe(
    episodes: Sequence[Episode],
    selected_part_of_speech: PartOfSpeech | None,
    only_with_multiple: bool,
) -> pd.DataFrame:
    entries = []
    for ep in episodes:
        for word in ep.words:
            if (
                only_with_multiple
                and how_many_episodes_where_word_appears(episodes, word.word) <= 1
            ):
                continue
            if (
                selected_part_of_speech is not None
                and selected_part_of_speech != word.part_of_speech
            ):
                continue
            entries.append(
                {
                    "episode": ep.title,
                    "word": f"{word.word} ({POS_MAPPING[word.part_of_speech]})",
                    "count": word.count,
                    # "layer": word.layer,
                }
            )
    df = pd.DataFrame(entries)
    df["count_sum"] = df.groupby("word")["count"].transform("sum")
    df = (
        df.sort_values("count_sum", ascending=False)
        .reset_index(drop=True)
        .drop(columns="count_sum")
    )
    df = df.pivot(index="word", columns="episode", values="count").reindex(
        index=df["word"].unique()
    )
    return df


POS_MAPPING = {
    "noun": "сущ",
    "adjective": "прил",
    "verb": "глаг",
    "adverb": "нареч",
}


def how_many_episodes_where_word_appears(episodes: Sequence[Episode], word: str) -> int:
    return sum(1 for episode in episodes if any(w.word == word for w in episode.words))


@dataclass
class Episode:
    title: str
    transcript: str
    words: Sequence[Word]
    lexems: Lexems

    def words_by_category(self, category: PartOfSpeech | None) -> Sequence[Word]:
        if category is None:
            return self.words
        return [w for w in self.words if w.part_of_speech == category]

    def word_count(self, category: PartOfSpeech | None = None) -> int:
        if category is not None:
            words = self.words_by_category(category)
        else:
            words = self.words
        sum = 0
        for word in words:
            sum += word.count
        return sum

    def __str__(self) -> str:
        return self.title


@dataclass
class Lexems:
    kernel_words: Sequence[str]
    close_words: Sequence[str]
    far_words: Sequence[str]

    def build_svg(self) -> str:
        doc = XmlDoc()
        with doc.tag("svg", xmlns="http://www.w3.org/2000/svg", viewBox="0 0 200 200"):
            for r in [90, 60, 30]:
                c, w, b = 100, "white", "black"
                doc.stag("circle", cx=c, cy=c, r=r, fill=w, stroke=b, stroke_width="1")

            def draw_words(words: Sequence[str], radius: float, font: float):
                for i, word in enumerate(words):
                    angle = 2 * pi / len(words) * i - 0.5 * pi
                    x = 100 + radius * cos(angle)
                    y = 100 + radius * sin(angle)
                    doc.line(
                        "text",
                        word,
                        x=x,
                        y=y,
                        **{"font-size": font, "text-anchor": "middle"},
                    )

            draw_words(self.kernel_words[:4], 8, 4)
            draw_words(self.kernel_words[4:], 20, 4)
            draw_words(self.close_words, 45, 4)
            draw_words(self.far_words, 75, 4)

        return doc.getvalue()


@dataclass
class Word:
    word: str
    count: int
    part_of_speech: PartOfSpeech
    layer = Literal["kernel", "close", "far"] | None

    @staticmethod
    def all_parts_of_speech() -> Sequence[PartOfSpeech]:
        return ["noun", "verb", "adjective", "adverb"]


type PartOfSpeech = Literal["noun", "verb", "adjective", "adverb"]


def parse_words(text: str) -> list[Word]:
    CATEGORY_MAP: dict[str, PartOfSpeech] = {
        "Существительные и местоимения": "noun",
        "Прилагательные": "adjective",
        "Глаголы": "verb",
        "Наречия": "adverb",
    }
    HEADER_REGEX = re.compile(r"^(.+?)\s*\(\d+\)\s*:\s*(.+)$")
    ENTRY_REGEX = re.compile(r"(.+?)\s*\((\d+)\)")

    entries = list[Word]()
    for line in text.strip().splitlines():
        header_match = HEADER_REGEX.match(line)
        if not header_match:
            raise ValueError("Expected header")
        category_txt, body = header_match.group(1), header_match.group(2)
        part_of_speech = CATEGORY_MAP.get(category_txt)
        if part_of_speech is None:
            raise ValueError(f"Unknown part of speech: {category_txt!r}")
        for part in body.split(";"):
            part = part.strip()
            if not part:
                continue
            entry_match = ENTRY_REGEX.match(part)
            if not entry_match:
                raise ValueError(f"Cannot parse entry: {part!r}")
            word = entry_match.group(1).strip()
            count = int(entry_match.group(2))
            entries.append(Word(word, count, part_of_speech))
    return entries
