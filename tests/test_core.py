# coding: utf-8

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import *  # pylint:disable=redefined-builtin,unused-wildcard-import,wildcard-import,wrong-import-order

import itertools
import os
import shutil
import sys
import time

import cv2
import numpy
import pytest

try:
    from unittest import mock
except ImportError:
    import mock  # Python 2 backport

import stbt_core as stbt
from stbt_core import wait_until


# pylint:disable=redefined-outer-name,unused-argument


def test_that_slicing_a_Frame_is_still_a_Frame():
    f = stbt.Frame(numpy.zeros((720, 1280, 3), dtype=numpy.uint8),
                   time=1234)
    assert f.time == 1234
    assert f.width == 1280
    assert f.height == 720

    f1 = f[10:20, 10:, 0]
    assert isinstance(f1, stbt.Frame)
    assert f1.time == 1234
    assert f1.width == 1270
    assert f1.height == 10

    f2 = stbt.crop(f, stbt.Region(10, 10, 20, 20))
    assert isinstance(f2, stbt.Frame)
    assert f2.time == 1234
    assert f2.width == 20
    assert f2.height == 20

    f3 = f.copy()
    assert isinstance(f3, stbt.Frame)
    assert f3.time == 1234
    assert f3.width == 1280
    assert f3.height == 720
    assert (f.__array_interface__["data"][0] !=
            f3.__array_interface__["data"][0])

    f4 = stbt.Frame(f)
    assert f4.time == 1234
    assert f4.width == 1280
    assert f4.height == 720


def test_that_load_image_looks_in_callers_directory():
    # See also the test with the same name in
    # ./subdirectory/test_load_image_from_subdirectory.py

    stbt.TEST_PACK_ROOT = os.path.abspath(os.path.dirname(__file__))

    f = stbt.load_image("videotestsrc-redblue.png")
    assert numpy.array_equal(
        f,
        cv2.imread(os.path.join(os.path.dirname(__file__),
                                "videotestsrc-redblue.png")))
    assert f.filename == "videotestsrc-redblue.png"
    assert f.relative_filename == "videotestsrc-redblue.png"

    with pytest.raises(IOError):
        stbt.load_image("info2.png")


def test_load_image_with_unicode_filename():
    print(sys.getfilesystemencoding())
    shutil.copyfile(_find_file("Rothlisberger.png"),
                    _find_file("Röthlisberger.png"))
    assert stbt.load_image(u"Röthlisberger.png") is not None
    assert stbt.load_image(u"Röthlisberger.png".encode("utf-8")) is not None
    assert stbt.load_image(u"R\xf6thlisberger.png") is not None


def test_load_image_with_numpy_array():
    a = numpy.zeros((720, 1280, 3), dtype=numpy.uint8)
    img = stbt.load_image(a)
    assert (a.__array_interface__["data"][0] ==
            img.__array_interface__["data"][0])
    assert img.filename is None
    assert img.relative_filename is None
    assert img.absolute_filename is None
    assert img.width == 1280
    assert img.height == 720

    a = numpy.zeros((720, 1280), dtype=numpy.uint8)
    b = numpy.zeros((720, 1280, 1), dtype=numpy.uint8)
    c = numpy.zeros((720, 1280, 3), dtype=numpy.uint8)
    d = numpy.zeros((720, 1280, 4), dtype=numpy.uint8)

    channels = [(1,), (3,), (4,), (1, 3), (1, 4), (3, 4), (1, 3, 4)]
    for x in [a, b, c, d]:
        for y in channels:
            img = stbt.load_image(x, color_channels=y)
            assert img.shape[2] in y
            assert isinstance(img, stbt.Image)


def test_load_image_with_stbt_image():
    img1 = stbt.load_image("videotestsrc-redblue.png")
    img2 = stbt.load_image(img1)
    assert img1 is img2


def test_load_image_from_filename_with_color_channels():
    files = [
        "videotestsrc-greyscale.png",
        "videotestsrc-greyscale-alpha.png",
        "completely-transparent.png",
        "with-alpha-but-completely-opaque.png",
        "uint16.png",
    ]
    channels = [(1,), (3,), (4,), (1, 3), (1, 4), (3, 4), (1, 3, 4)]
    for f in files:
        for c in channels:
            print(f, c)
            img = stbt.load_image(f, color_channels=c)
            assert img.shape[2] in c
            assert isinstance(img, stbt.Image)


def test_that_load_image_with_nonexistent_image_raises_ioerror():
    with pytest.raises(IOError, match="No such file: idontexist.png"):
        stbt.load_image("idontexist.png")


def test_crop():
    img = stbt.load_image("action-panel.png")
    cropped = stbt.crop(img, stbt.Region(x=1045, y=672, right=1081, bottom=691))
    reference = stbt.load_image("action-panel-blue-button.png")
    assert numpy.array_equal(reference, cropped)

    # It's a view onto the same memory:
    assert cropped[0, 0, 0] == img[672, 1045, 0]
    assert img[672, 1045, 0] != 0
    cropped[0, 0, 0] = 0
    assert img[672, 1045, 0] == 0

    assert img.filename == "action-panel.png"
    assert cropped.filename == img.filename

    # Region is clipped to the frame boundaries:
    assert numpy.array_equal(
        stbt.crop(img, stbt.Region(x=1045, y=672, right=1280, bottom=720)),
        stbt.crop(img, stbt.Region(x=1045, y=672, right=1281, bottom=721)))
    assert numpy.array_equal(
        stbt.crop(img, stbt.Region(x=0, y=0, right=10, bottom=10)),
        stbt.crop(img, stbt.Region(x=float("-inf"), y=float("-inf"),
                                   right=10, bottom=10)))

    # But a region entirely outside the frame is not allowed:
    with pytest.raises(TypeError):
        stbt.crop(img, None)
    with pytest.raises(ValueError):
        stbt.crop(img, stbt.Region(x=-10, y=-10, right=0, bottom=0))


def test_region_intersect():
    r1 = stbt.Region(0, 0, right=20, bottom=10)
    r2 = stbt.Region(5, 5, right=25, bottom=15)
    expected = stbt.Region(5, 5, right=20, bottom=10)
    assert expected == stbt.Region.intersect(r1, r2)
    with pytest.raises(AttributeError):
        r1.intersect(r2)  # pylint:disable=no-member


def test_region_bounding_box():
    r1 = stbt.Region(0, 0, right=20, bottom=10)
    r2 = stbt.Region(5, 5, right=25, bottom=15)
    expected = stbt.Region(0, 0, right=25, bottom=15)
    assert expected == stbt.Region.bounding_box(r1, r2)
    with pytest.raises(AttributeError):
        r1.bounding_box(r2)  # pylint:disable=no-member


r = stbt.Region(x=10, y=20, width=20, height=30)


@pytest.mark.parametrize("kwargs,expected", [
    # No change
    (dict(x=10), r),
    (dict(x=10, width=20), r),
    (dict(x=10, right=30), r),

    # Allowed  # pylint:disable=line-too-long
    (dict(x=11), stbt.Region(x=11, y=r.y, width=19, height=r.height)),
    (dict(width=19), stbt.Region(x=10, y=r.y, width=19, height=r.height)),
    (dict(right=29), stbt.Region(x=10, y=r.y, width=19, height=r.height)),
    (dict(x=11, width=20), stbt.Region(x=11, y=r.y, width=20, height=r.height)),
    (dict(x=11, right=21), stbt.Region(x=11, y=r.y, width=10, height=r.height)),
    (dict(x=11, right=21, y=0, height=5), stbt.Region(x=11, y=0, width=10, height=5)),
])
def test_region_replace(kwargs, expected):
    assert r.replace(**kwargs) == expected


@pytest.mark.parametrize("kwargs", [
    dict(x=1, width=2, right=3),
    dict(y=1, height=2, bottom=3),
])
def test_region_replace_value_error(kwargs):
    with pytest.raises(ValueError):
        r.replace(**kwargs)


def test_region_translate():
    with pytest.raises(TypeError):
        # Both region and y provided
        stbt.Region(2, 3, 2, 1).translate(stbt.Region(0, 0, 1, 1), 5)


@pytest.mark.parametrize("frame,mask,threshold,region,expected", [
    # pylint:disable=line-too-long
    ("black-full-frame.png", None, None, stbt.Region.ALL, True),
    ("videotestsrc-full-frame.png", None, None, stbt.Region.ALL, False),
    ("videotestsrc-full-frame.png", "videotestsrc-mask-non-black.png", None, stbt.Region.ALL, True),
    ("videotestsrc-full-frame.png", "videotestsrc-mask-no-video.png", None, stbt.Region.ALL, False),
    ("videotestsrc-full-frame.png", "videotestsrc-mask-no-video.png", None, stbt.Region.ALL, False),
    ("videotestsrc-full-frame.png", None, 20, stbt.Region(x=160, y=180, right=240, bottom=240), True),
    # Threshold bounds for almost-black frame:
    ("almost-black.png", None, 3, stbt.Region.ALL, True),
    ("almost-black.png", None, 2, stbt.Region.ALL, False),
])
def test_is_screen_black(frame, mask, threshold, region, expected):
    frame = stbt.load_image(frame)
    assert expected == bool(
        stbt.is_screen_black(frame, mask, threshold, region))


def test_is_screen_black_result():
    frame = stbt.load_image("almost-black.png")
    result = stbt.is_screen_black(frame)
    assert result
    assert numpy.all(result.frame == frame)
    assert result.black is True


def test_is_screen_black_with_numpy_mask():
    frame = stbt.load_image("videotestsrc-full-frame.png")
    mask = numpy.zeros((240, 320), dtype=numpy.uint8)
    mask[180:240, 160:213] = 255
    assert stbt.is_screen_black(frame, mask)


def test_is_screen_black_with_numpy_mask_and_region():
    frame = stbt.load_image("videotestsrc-full-frame.png")
    region = stbt.Region(x=160, y=180, right=320, bottom=240)
    mask = numpy.zeros((60, 160), dtype=numpy.uint8)
    mask[:, :80] = 255
    assert stbt.is_screen_black(frame, mask, 20, region)

    mask[:, :] = 255
    assert not stbt.is_screen_black(frame, mask, 20, region)


class C(object):
    """A class with a single property, used by the tests."""
    def __init__(self, prop):
        self.prop = prop

    def __repr__(self):
        return "C(%r)" % self.prop

    def __eq__(self, other):
        return isinstance(other, C) and self.prop == other.prop

    def __ne__(self, other):
        return not self.__eq__(other)


class f(object):
    """Helper factory for wait_until selftests. Creates a callable object that
    returns the specified values one by one each time it is called.

    Values are specified as space-separated characters. `.` means `None` and
    `F` means `False`.
    """

    mapping = {".": None, "F": False, "C1": C(1), "C2": C(2), "C3": C(3)}

    def __init__(self, spec):
        self.spec = spec
        self.iterator = itertools.cycle(f.mapping.get(x, x)
                                        for x in self.spec.split())

    def __repr__(self):
        return "f(%r)" % self.spec

    def __call__(self):
        time.sleep(1)
        v = next(self.iterator)
        sys.stderr.write("f() -> %s\n" % v)
        return v


@pytest.fixture(scope="function")
def mock_time():
    """Mocks out `time.time()` and `time.sleep()` so that time only advances
    when you call `time.sleep()`.
    """

    t = [1497000000]

    def _time():
        sys.stderr.write("time.time() -> %s\n" % t[0])
        return t[0]

    def _sleep(n):
        sys.stderr.write("time.sleep(%s)\n" % n)
        t[0] += n

    with mock.patch("time.time", _time), mock.patch("time.sleep", _sleep):
        yield


class Zero(object):
    def __bool__(self):
        return False

    def __eq__(self, other):
        return isinstance(other, Zero)


@pytest.mark.parametrize("f,kwargs,expected", [
    # wait_until returns on success
    (f(". a b"), {}, "a"),
    (f("F a b"), {}, "a"),

    # wait_until tries one last time after reaching timeout_secs
    (f("F T"), {"timeout_secs": 1}, "T"),
    (f("F T"), {"timeout_secs": 0.1}, "T"),
    (f("F F T"), {"timeout_secs": 1}, False),

    # wait_until with zero timeout tries once
    (lambda: True, {"timeout_secs": 0}, True),

    # predicate behaviour
    (f("a b b"), {"predicate": lambda x: x == "b"}, "b"),
    (f("F F F"), {"predicate": lambda x: x == "b"}, False),
    (f("C1 C2"), {"predicate": lambda x: x.prop == 2}, C(2)),
    (f("C1 C2"), {"predicate": lambda x: x.prop == 3}, None),

    # stable_secs behaviour
    (f("a b b"), {}, "a"),
    (f("a b b"), {"stable_secs": 1}, "b"),
    (f("a b c"), {"stable_secs": 1}, None),
    (f("C1 C2 C3"), {"stable_secs": 1,
                     "predicate": lambda x: 2 <= x.prop <= 3}, C(2)),

    # timeout_secs elapsed
    #        |   ┌ stable_secs needed
    #        v   v
    (f("a b b b b b b b b b b"), {"timeout_secs": 3, "stable_secs": 3}, None),

    # Timeout reached
    #        | ┌ stable_secs reached
    #        v v
    (f("a b b b a a a a a a a"), {"timeout_secs": 3, "stable_secs": 2}, "b"),

    # Falsey values
    (f("F F F"), {}, False),
    (f("F F F"), {"stable_secs": 1}, False),
    (Zero, {"interval_secs": 1}, Zero()),
    (Zero, {"interval_secs": 1, "stable_secs": 1}, Zero()),
])
def test_wait_until(mock_time, f, kwargs, expected):
    assert wait_until(f, **kwargs) == expected


def test_that_wait_until_times_out(mock_time):
    assert not wait_until(Zero, interval_secs=1)
    assert time.time() == 1497000010


def test_that_wait_until_returns_first_stable_value(mock_time):

    def MR(match, x):
        time.sleep(1)  # advance the mock time by 1 second
        return stbt.MatchResult(
            time.time(), match, stbt.Region(x=x, y=0, width=10, height=2),
            first_pass_result=1,
            frame=numpy.random.randint(0, 255, (2, 2, 3)).astype(numpy.uint8),
            image="reference.png")

    def g():
        yield MR(False, x=1)
        yield MR(True, x=2)
        yield MR(True, x=3)
        yield MR(True, x=4)
        yield MR(True, x=4)
        yield MR(True, x=4)
        yield MR(True, x=4)
        yield MR(True, x=4)

    results = g()

    def match():
        return next(results)

    result = wait_until(match, predicate=lambda x: x and x.region,
                        stable_secs=2)
    assert result.match
    assert result.region.x == 4
    assert result.time == 1497000004


def test_that_wait_until_doesnt_compare_return_values(mock_time):
    class MR(object):
        def __init__(self, eq_allowed=False):
            time.sleep(1)  # advance the mock time by 1 second
            self.eq_allowed = eq_allowed

        def __eq__(self, other):
            if self.eq_allowed:
                return isinstance(other, MR)
            else:
                assert False, "Got unexpected call to MR.__eq__"

        def __ne__(self, other):
            return not self.__eq__(other)

    result = wait_until(MR)
    assert isinstance(result, MR)

    # But it does compare values if you specify `stable_secs`
    with pytest.raises(AssertionError):
        result = wait_until(MR, stable_secs=2)


def _find_file(path, root=os.path.dirname(os.path.abspath(__file__))):
    return os.path.join(root, path)
