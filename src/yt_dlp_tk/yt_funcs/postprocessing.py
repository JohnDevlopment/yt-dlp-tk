"""Post-processing module."""

from __future__ import annotations
from yt_dlp.postprocessor.common import PostProcessor, PostProcessingError
from pathlib import Path
from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from typing import Any

class RenameFixFilePP(PostProcessor):
    """Renames a file."""

    def run(self, info: dict[str, Any]):
        ext: str = '.' + info['ext']
        print("extension:", ext)

        filepath: str = info['filepath']
        infile = Path('./' + filepath).resolve()

        def _re_sub(m: re.Match) -> str:
            if m[0] == ' ':
                return '_'
            return ''

        filepath = re.sub(r'[\[\]() ]', _re_sub, filepath)
        outfile = Path('./' + filepath).resolve()

        try:
            infile.rename(outfile)
        except FileNotFoundError as exc:
            raise PostProcessingError(str(exc))
        except PermissionError as exc:
            raise PostProcessingError(str(exc))

        info['filepath'] = outfile.name

        return [], info
