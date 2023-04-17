# Main module

from .view import YtdlptkInterface
from .model import Model
from .presenter import Presenter
from argparse import ArgumentParser
from pathlib import Path

def parse_args():
    parser = ArgumentParser('yt-dlp-tk')
    parser.add_argument('--log-file', type=Path, default=Path())

def main () -> None:
    model = Model()
    view = YtdlptkInterface()
    presenter = Presenter(model, view)
    presenter.run()

if __name__ == "__main__":
    main()
