from PIL import Image
from collections import Iterable
from itertools import tee

class Pixels2D(object):
    
    def __init__(self, pixels_or_image, width=None, size=None):
        if isinstance(pixels_or_image, Image.Image):
            self.data = list(pixels_or_image.getdata())
            self.width = pixels_or_image.width
        elif hasattr(pixels_or_image, '__getitem__'):
            if width == size == None:
                raise ValueError("Specify 'width' or 'size' in arguments.")

            self.data = list(pixels_or_image)
            self.width = width if width != None else size[0]
        else:
            raise ValueError("Pass 1D pixels list or image in argument 'pixels_or_image'.")

    
    def _get_index(self, xy):
        if isinstance(xy, int):
            return xy
        if isinstance(xy, tuple) and len(xy) == 2:
            x, y = xy
            return y * self.width + x
        raise IndexError()

    __getitem__ = lambda self, xy: self.data.__getitem__(self._get_index(xy))
    __setitem__ = lambda self, xy, value: self.data.__setitem__(self._get_index(xy), value)


class PixelSet(set):
    img = None
    size = None
    origin = (0, 0)

    @classmethod
    def from_image(cls, img, value=1):
        self = cls.from_pixels(img.getdata(), img.size, value=value, origin=(0, 0))
        self.img = img
        return self

    @classmethod
    def from_pixels(cls, pixels, size, value=1, origin=(0, 0)):
        width, height = size

        self = cls(map(lambda (i, p): (i % width - origin[0], i / width - origin[1]), filter(lambda (i, p): p == value, enumerate(pixels))))
        self.size = size
        self.origin = origin
        return self

    def to_image(self, value=1, size=None, origin=None):
        size = size or self.size or self.img.size
        origin = origin or self.origin
        if not size:
            raise ValueError('Size of image to generate is unknown.')

        pixels = Pixels2D([0] * (size[0] * size[1]), size=size)
        for x, y in self:
            pixels[x + origin[0], y + origin[1]] = value

        img = Image.new('1', size)
        img.putdata(pixels.data)
        return img

    @property
    def complement(self):
        if not self.size:
            raise ValueError('Size of image to generate is unknown.')

        width, height = self.size
        result = PixelSet([(x, y) for x in range(width) for y in range(height)]) - self
        result.size = self.size
        result.origin = self.origin

        return result


class ImageFunction(object):
    
    def __init__(self, func, domain):
        if not callable(func):
            raise ValueError('`func` is not a callable.')
        if not isinstance(domain, Iterable):
            raise ValueError('`domain` is not iterable.')

        self.func = func
        self.domain = domain

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __iter__(self):
        self.domain, ret = tee(self.domain)
        return ret

    @classmethod
    def from_image(cls, img):
        return cls(
            func=img.getpixel,
            domain=((x, y) for x in xrange(img.width) for y in xrange(img.height))
        )

    def to_image(self, *args):
        ret = Image.new(*args)
        for p in self:
            ret.putpixel(p, self(p))

        return ret


