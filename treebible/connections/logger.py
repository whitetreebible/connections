

import logging
log = logging.getLogger(__name__)

def init_logger():
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(message)s')
    log.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    log.addHandler(ch)

init_logger()
