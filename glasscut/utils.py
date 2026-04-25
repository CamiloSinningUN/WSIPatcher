import functools
import threading
import time
from typing import Any, Callable, TypeVar, cast

import numpy as np
from PIL import Image
from skimage.util.dtype import img_as_ubyte # type: ignore

T = TypeVar("T")

def lazyproperty(f: Callable[..., T]) -> Any:
    """Decorator like @property, but evaluated only on first access.

    Like @property, this can only be used to decorate methods having only
    a `self` parameter, and is accessed like an attribute on an instance,
    i.e. trailing parentheses are not used. Unlike @property, the decorated
    method is only evaluated on first access; the resulting value is cached
    and that same value returned on second and later access without
    re-evaluation of the method.

    Like @property, this class produces a *data descriptor* object, which is
    stored in the __dict__ of the *class* under the name of the decorated
    method ('fget' nominally). The cached value is stored in the __dict__ of
    the *instance* under that same name.

    Because it is a data descriptor (as opposed to a *non-data descriptor*),
    its `__get__()` method is executed on each access of the decorated
    attribute; the __dict__ item of the same name is "shadowed" by the
    descriptor.

    While this may represent a performance improvement over a property, its
    greater benefit may be its other characteristics. One common use is to
    construct collaborator objects, removing that "real work" from the
    constructor, while still only executing once. It also de-couples client
    code from any sequencing considerations; if it's accessed from more than
    one location, it's assured it will be ready whenever needed.

    A lazyproperty is read-only. There is no counterpart to the optional
    "setter" (or deleter) behavior of an @property. This is critically
    important to maintaining its immutability and idempotence guarantees.
    Attempting to assign to a lazyproperty raises AttributeError
    unconditionally.
    The parameter names in the methods below correspond to this usage
    example::

        class Obj(object):

            @lazyproperty
            def fget(self):
                return 'some result'

        obj = Obj()

    Not suitable for wrapping a function (as opposed to a method) because it
    is not callable.
    """
    # pylint: disable=unused-variable
    return property(functools.lru_cache(maxsize=100)(f))


def np_to_pil(np_img: np.ndarray) -> Image.Image:
    """Convert a NumPy array to a PIL Image.

    Handles the conversion of different numpy array types (bool, float64, uint8, etc.)
    to a properly formatted PIL Image.

    Parameters
    ----------
    np_img : np.ndarray
        The image represented as a NumPy array.

    Returns
    -------
    PIL.Image.Image
        The image represented as PIL Image

    Examples
    --------
    >>> import numpy as np
    >>> from glasscut.utils import np_to_pil
    >>> float_array = np.random.rand(100, 100, 3)
    >>> pil_image = np_to_pil(float_array)
    """

    def _transform_bool(img_array: np.ndarray) -> np.ndarray:
        return img_array.astype(np.uint8) * 255

    def _transform_float(img_array: np.ndarray) -> np.ndarray:
        return (
            img_array.astype(np.uint8)
            if np.max(img_array) > 1
            else cast(np.ndarray, img_as_ubyte(img_array))
        )

    types_factory = {
        "bool": _transform_bool(np_img),
        "float64": _transform_float(np_img),
    }
    image_array = types_factory.get(str(np_img.dtype), np_img.astype(np.uint8))
    return Image.fromarray(image_array)


class Profiler:
    """Lightweight phase-based profiler with thread-safe accumulation.

    Zero overhead when *enabled* is ``False`` — all methods return immediately.

    Example
    -------
    >>> profiler = Profiler(enabled=True)
    >>> for i in range(100):
    ...     with profiler.phase("compute"):
    ...         _ = i ** 2
    >>> profiler.print_summary()
    """

    __slots__ = ("enabled", "_phases", "_lock")

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._phases: dict[str, float] = {}
        self._lock = threading.Lock()

    def phase(self, name: str) -> "_PhaseContext":
        return _PhaseContext(self, name)

    @property
    def phases(self) -> dict[str, float]:
        return dict(self._phases)

    def summary(self, sort: bool = True) -> str:
        items = list(self._phases.items())
        if sort:
            items.sort(key=lambda x: x[1], reverse=True)
        total = sum(t for _, t in items)
        lines = ["----Profile ----"]
        for name, elapsed in items:
            pct = 100.0 * elapsed / total if total else 0.0
            lines.append(f"  {name:<48s} {elapsed:8.4f}s  ({pct:5.1f}%)")
        lines.append(f"  {'TOTAL':<48s} {total:8.4f}s  (100.0%)")
        return "\n".join(lines)

    def print_summary(self, sort: bool = True) -> None:
        if self.enabled:
            print(self.summary(sort=sort))

    def record(self, name: str, elapsed: float) -> None:
        with self._lock:
            self._phases[name] = self._phases.get(name, 0.0) + elapsed

    def reset(self) -> None:
        self._phases.clear()

    def __copy__(self) -> "Profiler":
        return Profiler(enabled=self.enabled)

    def __deepcopy__(self, memo: dict[object, object]) -> "Profiler":
        return Profiler(enabled=self.enabled)


class _PhaseContext:
    __slots__ = ("_profiler", "_name", "_t0")

    def __init__(self, profiler: Profiler, name: str) -> None:
        self._profiler = profiler
        self._name = name

    def __enter__(self) -> "_PhaseContext":
        if self._profiler.enabled:
            self._t0 = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        if self._profiler.enabled:
            elapsed = time.perf_counter() - self._t0
            self._profiler.record(self._name, elapsed)