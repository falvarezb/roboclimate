import subprocess
import logging

def run_notebook():
    logging.info("running notebook")
    subprocess.call(['./nbconverter.sh'])


if __name__ == "__main__":
    run_notebook()