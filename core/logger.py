import logging


def setup_logger(config):
    log_level = config["logging"]["level"]
    log_file = config["logging"]["file"]

    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
    )

    return logging.getLogger("rapids")
