from ..utils import attr_dict, readonly_dict, ConstantError, Result
import pytest

# def test_result() -> None:
#     ok_result = Result.ok(1)
#     err_result = Result.Err(1)

def test_attr_dict() -> None:
    ad = attr_dict(afloat=1.0, aint=1, abool=True)
    assert ad['afloat'] == 1.0
    assert ad['aint'] == 1
    assert ad['abool'] == True
    assert ad.afloat == 1.0
    assert ad.aint == 1
    assert ad.abool == True

    # Set keys like attributes
    ad.astring = "Sample string"
    assert ad['astring'] == "Sample string"
    assert ad.astring == "Sample string"

def test_readonly_dict() -> None:
    rd = readonly_dict(a=1, b=2)

    assert rd['a'] == 1
    assert rd['b'] == 2

    with pytest.raises(ConstantError):
        rd['c'] = 3
