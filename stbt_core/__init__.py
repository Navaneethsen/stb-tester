# coding: utf-8
"""Main stb-tester python module. Intended to be used with `stbt run`.

See `man stbt` and http://stb-tester.com for documentation.

Copyright 2012-2013 YouView TV Ltd and contributors.
Copyright 2013-2018 stb-tester.com Ltd.
License: LGPL v2.1 or (at your option) any later version (see
https://github.com/stb-tester/stb-tester/blob/master/LICENSE for details).
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from builtins import *  # pylint:disable=redefined-builtin,unused-wildcard-import,wildcard-import,wrong-import-order

from contextlib import contextmanager

from _stbt.black import (
    is_screen_black)
from _stbt.config import (
    ConfigurationError,
    get_config)
from _stbt.diff import (
    FrameDiffer,
    MotionDiff,
    MotionResult)
from _stbt.frameobject import (
    for_object_repository,
    FrameObject)
from _stbt.grid import (
    Grid)
from _stbt.imgutils import (
    crop,
    Frame,
    Image,
    load_image,
    save_frame)
from _stbt.keyboard import (
    Keyboard)
from _stbt.logging import (
    debug)
from _stbt.match import (
    ConfirmMethod,
    match,
    match_all,
    MatchMethod,
    MatchParameters,
    MatchResult,
    MatchTimeout,
    wait_for_match)
from _stbt.motion import (
    detect_motion,
    MotionTimeout,
    wait_for_motion)
from _stbt.multipress import (
    MultiPress)
from _stbt.ocr import (
    apply_ocr_corrections,
    match_text,
    ocr,
    OcrEngine,
    OcrMode,
    set_global_ocr_corrections,
    TextMatchResult)
from _stbt.precondition import (
    as_precondition,
    PreconditionError)
from _stbt.transition import (
    press_and_wait,
    StrictDiff,
    TransitionStatus,
    wait_for_transition_to_end)
from _stbt.types import (
    NoVideo,
    Position,
    Region,
    UITestError,
    UITestFailure)
from _stbt.utils import (
    to_native_str)
from _stbt.wait import (
    wait_until)

__all__ = [to_native_str(x) for x in [
    "apply_ocr_corrections",
    "as_precondition",
    "ConfigurationError",
    "ConfirmMethod",
    "crop",
    "debug",
    "detect_motion",
    "draw_text",
    "for_object_repository",
    "Frame",
    "FrameDiffer",
    "FrameObject",
    "frames",
    "get_config",
    "get_frame",
    "Grid",
    "Image",
    "is_screen_black",
    "Keyboard",
    "last_keypress",
    "load_image",
    "match",
    "match_all",
    "match_text",
    "MatchMethod",
    "MatchParameters",
    "MatchResult",
    "MatchTimeout",
    "MotionDiff",
    "MotionResult",
    "MotionTimeout",
    "MultiPress",
    "NoVideo",
    "ocr",
    "OcrEngine",
    "OcrMode",
    "Position",
    "PreconditionError",
    "press",
    "press_and_wait",
    "press_until_match",
    "pressing",
    "Region",
    "save_frame",
    "set_global_ocr_corrections",
    "StrictDiff",
    "TextMatchResult",
    "TransitionStatus",
    "UITestError",
    "UITestFailure",
    "wait_for_match",
    "wait_for_motion",
    "wait_for_transition_to_end",
    "wait_until",
]]

# Functions available to stbt scripts
# ===========================================================================


def last_keypress():
    """Returns information about the last key-press sent to the device under
    test.

    See the return type of `stbt.press`.

    Added in v32.
    """
    return _dut.last_keypress()


def press(key, interpress_delay_secs=None, hold_secs=None):
    """Send the specified key-press to the device under test.

    :param str key:
        The name of the key/button.

        If you are using infrared control, this is a key name from your
        lircd.conf configuration file.

        If you are using HDMI CEC control, see the available key names
        `here <https://github.com/stb-tester/stb-tester/blob/v28/_stbt/control_gpl.py#L18-L117>`__.
        Note that some devices might not understand all of the CEC commands in
        that list.

    :type interpress_delay_secs: int or float
    :param interpress_delay_secs:
        The minimum time to wait after a previous key-press, in order to
        accommodate the responsiveness of the device-under-test.

        This defaults to 0.3. You can override the global default value by
        setting ``interpress_delay_secs`` in the ``[press]`` section of
        :ref:`.stbt.conf`.

    :type hold_secs: int or float
    :param hold_secs:
        Hold the key down for the specified duration (in seconds). Currently
        this is implemented for the infrared, HDMI CEC, and Roku controls.
        There is a maximum limit of 60 seconds.

    :returns:
        An object with the following attributes:

        * **key** (*str*) – the name of the key that was pressed.
        * **start_time** (*float*) – the time just before the keypress started
          (in seconds since the unix epoch, like ``time.time()`` and
          ``stbt.Frame.time``).
        * **end_time** (*float*) – the time when transmission of the keypress
          signal completed.
        * **frame_before** (`stbt.Frame`) – the most recent video-frame just
          before the keypress started. Typically this is used by functions like
          `stbt.press_and_wait` to detect when the device-under-test reacted to
          the keypress.

    * Added in v29: The ``hold_secs`` parameter.
    * Added in v30: Returns an object with keypress timings, instead of
      ``None``.
    """
    return _dut.press(key, interpress_delay_secs, hold_secs)


def pressing(key, interpress_delay_secs=None):
    """Context manager that will press and hold the specified key for the
    duration of the ``with`` code block.

    For example, this will hold KEY_RIGHT until ``wait_for_match`` finds a
    match or times out::

        with stbt.pressing("KEY_RIGHT"):
            stbt.wait_for_match("last-page.png")

    The same limitations apply as `stbt.press`'s ``hold_secs`` parameter.
    """
    return _dut.pressing(key, interpress_delay_secs)


def draw_text(text, duration_secs=3):
    """Write the specified text to the output video.

    :param str text: The text to write.

    :param duration_secs: The number of seconds to display the text.
    :type duration_secs: int or float
    """
    debug(text)
    return _dut.draw_text(text, duration_secs)


def press_until_match(
        key,
        image,
        interval_secs=None,
        max_presses=None,
        match_parameters=None,
        region=Region.ALL):
    """Call `press` as many times as necessary to find the specified image.

    :param key: See `press`.

    :param image: See `match`.

    :type interval_secs: int or float
    :param interval_secs:
        The number of seconds to wait for a match before pressing again.
        Defaults to 3.

        You can override the global default value by setting ``interval_secs``
        in the ``[press_until_match]`` section of :ref:`.stbt.conf`.

    :param int max_presses:
        The number of times to try pressing the key and looking for the image
        before giving up and raising `MatchTimeout`. Defaults to 10.

        You can override the global default value by setting ``max_presses``
        in the ``[press_until_match]`` section of :ref:`.stbt.conf`.

    :param match_parameters: See `match`.
    :param region: See `match`.

    :returns: `MatchResult` when the image is found.
    :raises: `MatchTimeout` if no match is found after ``timeout_secs`` seconds.
    """
    return _dut.press_until_match(
        key, image, interval_secs, max_presses, match_parameters, region)


def frames(timeout_secs=None):
    """Generator that yields video frames captured from the device-under-test.

    For example::

        for frame in stbt.frames():
            # Do something with each frame here.
            # Remember to add a termination condition to `break` or `return`
            # from the loop, or specify `timeout_secs` — otherwise you'll have
            # an infinite loop!
            ...

    See also `stbt.get_frame`.

    :type timeout_secs: int or float or None
    :param timeout_secs:
      A timeout in seconds. After this timeout the iterator will be exhausted.
      That is, a ``for`` loop like ``for f in stbt.frames(timeout_secs=10)``
      will terminate after 10 seconds. If ``timeout_secs`` is ``None`` (the
      default) then the iterator will yield frames forever but you can stop
      iterating (for example with ``break``) at any time.

    :rtype: Iterator[stbt.Frame]
    :returns:
      An iterator of frames in OpenCV format (`stbt.Frame`).
    """
    return _dut.frames(timeout_secs)


def get_frame():
    """Grabs a video frame from the device-under-test.

    :rtype: stbt.Frame
    :returns: The most recent video frame in OpenCV format.

    Most Stb-tester APIs (`stbt.match`, `stbt.FrameObject` constructors, etc.)
    will call ``get_frame`` if a frame isn't specified explicitly.

    If you call ``get_frame`` twice very quickly (faster than the video-capture
    framerate) you might get the same frame twice. To block until the next
    frame is available, use `stbt.frames`.

    To save a frame to disk pass it to :ocv:pyfunc:`cv2.imwrite`. Note that any
    file you write to the current working directory will appear as an artifact
    in the test-run results.
    """
    return _dut.get_frame()


# Internal
# ===========================================================================

class UnconfiguredDeviceUnderTest(object):
    # pylint:disable=unused-argument
    def last_keypress(self):
        return None

    def press(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.press isn't configured to run on your hardware")

    def pressing(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.pressing isn't configured to run on your hardware")

    def draw_text(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.draw_text isn't configured to run on your hardware")

    def press_until_match(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.press_until_match isn't configured to run on your hardware")

    def frames(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.frames isn't configured to run on your hardware")

    def get_frame(self, *args, **kwargs):
        raise RuntimeError(
            "stbt.get_frame isn't configured to run on your hardware")


_dut = UnconfiguredDeviceUnderTest()


@contextmanager
def _set_dut_singleton(dut):
    global _dut
    old_dut = dut
    try:
        _dut = dut
        yield dut
    finally:
        _dut = old_dut
