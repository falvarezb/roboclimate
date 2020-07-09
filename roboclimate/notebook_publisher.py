import subprocess
import logging

logger = logging.getLogger(__name__)

def publish_notebook():
    logging.info("publishing notebook")
    subprocess.call(['./nbconverter.sh'])


if __name__ == "__main__":
    publish_notebook()
    