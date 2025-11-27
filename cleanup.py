from pathlib import Path
import logging

from flashcard_optimiser import Gemini


OUTPUT_LOG_PATH = Path("./chat_cleanup.log")
NUMBER_TO_DELETE = 0
NTH_MOST_RECENT = 0


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
    return logger


def main() -> None:
    logger = setup_logger(OUTPUT_LOG_PATH)
    with Gemini.web() as gemini:
        for idx in range(NUMBER_TO_DELETE):
            gemini = gemini.delete_recent_chat(idx=NTH_MOST_RECENT)
            logger.info(f"Delete recent chat {idx + 1} successfully.")


if __name__ == "__main__":
    main()
