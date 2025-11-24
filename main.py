from pathlib import Path
import json
import logging
from typing import List

from flashcard_atomiser import Anki, Gemini, AnkiCard, QAs


INPUT_FILE_PATH = Path("./exported.txt")
OUTPUT_LOG_PATH = Path("./flashcard_optimiser.log")
FLASHCARDS_OUT_PATH = Path("./flashcards_out")
GEM_NAME = "Flashcard Optimiser"
MODEL_NAME = "Thinking"


def setup_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", 
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    logger.info(f"Starting New Run. Input File: {INPUT_FILE_PATH}")
    logger.info("-" * 80)
    return logger


def main() -> None:
    logger = setup_logger(OUTPUT_LOG_PATH)
    intermediaries_created = 0
    dumps_created = 0
    old_cards: List[AnkiCard] = Anki.load_exported_cards(Path(INPUT_FILE_PATH))
    remaining_cards: List[AnkiCard] = list(old_cards)
    new_cards: List[AnkiCard] = []
    while remaining_cards:
        logger.info(f"Attempting to process batch. {len(remaining_cards)} cards remaining.")
        try:
            with Gemini.gem(GEM_NAME) as gemini:
                gemini = gemini.select_model(MODEL_NAME)
                for old_card in list(remaining_cards):
                    original_idx = old_cards.index(old_card)
                    logger.info(f"--- Processing card {original_idx + 1} / {len(old_cards)} ---")
                    gemini = gemini.select_gem(GEM_NAME)
                    raw_output = (
                        gemini.ask(
                            old_card.to_qa().model_dump_json()
                        )
                        .strip("`")
                        .removeprefix("json")
                        .removeprefix("JSON")
                        .strip()
                    )
                    try:
                        output = json.loads(raw_output)
                    except json.JSONDecodeError:
                        logger.warning(f"--- Skipping card {original_idx + 1} ---")
                        logger.warning("Gemini failed to output a coherent JSON response.")
                        logger.warning(f"Raw Response Was:\n{raw_output.replace('\n', "\n\t")}")
                        continue
                    new_cards_generated = 0
                    for qa in QAs.model_validate({"qas": output}).qas:
                        new_card = AnkiCard.from_qa(
                            qa,
                            deck_name=f"Gemini::{old_card.deck_name}",
                            card_type=old_card.card_type,
                        )
                        new_cards.append(new_card)
                        if new_cards and len(new_cards) % 30 == 0:
                            logger.info(f"Generated {len(new_cards)} cards so far...")
                            try:
                                Anki.create_package(new_cards).write_to_file(FLASHCARDS_OUT_PATH / Path(f"intermediary_{intermediaries_created + 1}.apkg"))
                                intermediaries_created += 1
                                logger.info(f"Intermediary Anki package {intermediaries_created} created successfully.")
                            except Exception as e:
                                logger.error(f"Failed to create intermediary Anki package: {e}")
                                continue
                        new_cards_generated += 1
                    logger.info(f"Successfully generated {new_cards_generated} new cards from old card {original_idx + 1}.")
                    remaining_cards.remove(old_card)
        except Exception as e:
            logger.error(f"Unexpected connection crash: {e}. Dumping progress and retrying...")
            try:
                Anki.create_package(new_cards).write_to_file(FLASHCARDS_OUT_PATH / Path(f"dump_{dumps_created + 1}.apkg"))
                dumps_created += 1
                logger.info(f"Dump Anki package {dumps_created} created successfully.")
            except Exception as e:
                logger.error(f"Failed to create dump Anki package: {e}")
            continue

    processed_count = len(old_cards) - len(remaining_cards)
    skipped_count = len(remaining_cards)
    
    logger.info("-" * 80)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"Total old cards loaded: {len(old_cards)}")
    logger.info(f"Total old cards successfully processed: {processed_count}")
    logger.warning(f"Total old cards skipped: {skipped_count}")
    logger.info(f"Total new cards generated: {len(new_cards)}")
    logger.info("-" * 80)
    
    Anki.create_package(new_cards).write_to_file(FLASHCARDS_OUT_PATH / Path("final_flashcards.apkg"))
    logger.info("Final Anki package created successfully.")


if __name__ == "__main__":
    main()
