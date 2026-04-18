import functools
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