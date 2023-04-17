from __future__ import annotations
from ..interface import ExTree, ExText, ExEntry, InState
from tkinter import Tk
from typing import cast, Any
import pytest, time

@pytest.fixture
def root() -> Tk:
    root = Tk()
    root.title("pytest")
    return root

def has_base_methods(obj: object):
    for meth in ['configure', 'config', 'cget']:
        assert hasattr(obj, meth), f"{type(obj).__name__} missing {meth} method"

def test_ExTree() -> None:
    tree = ExTree()

    has_base_methods(tree)

    assert isinstance(tree.cget('height'), int)

    assert not tree.cget('scrolly')
    assert not tree.cget('scrollx')

    tree.configure(scrolly=True)
    assert tree.cget('scrolly')
    tree.configure(scrolly=False)

    tree.configure(scrollx=True)
    assert tree.cget('scrollx')
    tree.configure(scrollx=False)

    with InState(tree, ('disabled',)):
        assert tree.instate(('disabled',))

class TestExText:
    @pytest.fixture
    def text(self, root: Tk) -> ExText:
        return ExText(cast(Any, root),
                      disabledbackground='#333333',
                      normalbackground='white')

    def test_states(self, text: ExText) -> None:
        text.state('disabled')
        assert text.state() == 'disabled'
        assert text.instate('disabled')

        text.state('normal')
        assert text.state() == 'normal'
        assert text.instate('normal')

        with InState(text, 'disabled'):
            assert text.state() == 'disabled'
            assert text.instate('disabled')

            assert text.instate('disabled', lambda: print('disabled')) is None
            assert text.instate('normal', lambda: print('normal')) is None

        assert text.state() == 'normal'
        assert text.instate('normal')

    def test_backgrounds(self, text: ExText, root: Tk) -> None:
        # Color conversion function
        assert text._tk_color_name_to_number('white') == '#ffffff'
        assert text._tk_color_name_to_number('#333333') == '#333333'

        assert text.cget('normalbackground') == '#ffffff'
        assert text.cget('disabledbackground') == '#333333'

        assert text.cget('background') == '#ffffff'
        with InState(text, 'disabled'):
            assert text.cget('background') == '#333333'

    # def test_scrollbar(self, text: ExText) -> None:
    #     text.configure(scrolly=True)
    #     assert text.y_scrollbar_mapped
        
    #     text.configure(scrolly=False)
    #     assert not text.y_scrollbar_mapped

class TestExEntry:
    @pytest.fixture
    def entry(self, root: Tk) -> ExEntry:
        return ExEntry(cast(Any, root), scrollx=True)
