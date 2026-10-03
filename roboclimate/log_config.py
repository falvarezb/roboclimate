import logging

logger = logging.getLogger()
if len(logger.handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logger.setLevel(logging.INFO)
else:
    logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level='INFO', filename='weather.log')
