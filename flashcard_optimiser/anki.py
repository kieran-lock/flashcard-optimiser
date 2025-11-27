from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from pathlib import Path
from random import randrange

from genanki import Package, Deck, Model, Note
from pydantic import BaseModel


def _random_id() -> int:
    return randrange(1 << 30, 1 << 31)


DEFAULT_CARD_TYPE = "KaTeX and Markdown Basic"
MODEL = Model(
    _random_id(),
    "Python Model",
    fields=[
        {"name": "Question"},
        {"name": "Answer"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Question}}",
            "afmt": "{{Answer}}",
        },
    ],
)


class QA(BaseModel):
    q: str
    a: str


class QAs(BaseModel):
    qas: list[QA]


@dataclass(slots=True)
class AnkiCard:
    deck_name: str
    card_type: str
    front: str
    back: str

    def serialize(self) -> dict[str, Any]:
        return {
            "deckName": self.deck_name,
            "modelName": self.card_type,
            "fields": {"Front": self.front, "Back": self.back},
        }
    
    def to_qa(self) -> QA:
        return QA(q=self.front, a=self.back)

    @classmethod
    def from_qa(cls, qa: QA, deck_name: str, card_type: str = DEFAULT_CARD_TYPE) -> AnkiCard:
        return cls(deck_name=deck_name, card_type=card_type, front=qa.q, back=qa.a)
    
    def pretty(self) -> str:
        return f"Front:\n{self.front}\n\nBack:\n{self.back}"


@dataclass(slots=True)
class Anki:
    @classmethod
    def create_package(cls, cards: list[AnkiCard]) -> Package:
        decks: dict[str, Deck] = {}
        for card in cards:
            deck = decks.get(card.deck_name)
            if deck is None:
                deck = Deck(_random_id(), card.deck_name)
                decks[card.deck_name] = deck
            note = Note(
                model=MODEL,
                fields=[card.front, card.back],
            )
            deck.add_note(note)
        return Package(list(decks.values()))
    
    @staticmethod
    def load_exported_cards(path: Path, card_type: str = DEFAULT_CARD_TYPE) -> list[AnkiCard]:
        cards = []
        for line in path.read_text().splitlines()[3:]:
            line = line.strip()
            if not line:
                continue 
            deck_name, question, answer = line.split("\t")
            cards.append(AnkiCard(deck_name=deck_name, card_type=card_type, front=question, back=answer))
        return cards
