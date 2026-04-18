"""Base Tiler abstract class for tile extraction strategies."""

from abc import ABC, abstractmethod
from typing import Generator, List, Tuple, Optional
from PIL import Image

from glasscut.slides import Slide
from glasscut.tile import Tile


class Tiler(ABC):
    """Abstract base class for tile extraction strategies.

    A Tiler is responsible for determining which tiles to extract from a slide
    and providing them to the user. Different tiling strategies can be implemented
    by subclassing this class.

    This class is similar to HistoLab's Tiler protocol but uses ABC for easier
    extension and default implementations in GlassCut's style.

    Example:
        >>> class MyCustomTiler(Tiler):
        ...     def extract(self, slide, magnification):
        ...         # Implement custom logic
        ...         pass
        ...     def get_tile_coordinates(self, slide, magnification):
        ...         # Return list of (x, y) coordinates
        ...         pass
    """

    @abstractmethod
    def extract(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> Generator[Tile, None, None]:
        """Extract tiles from slide.

        This is the main method for tile extraction. It yields Tile objects
        one at a time in order, allowing for efficient memory usage on large slides.

        Parameters
        ----------
        slide : Slide
            The slide object to extract tiles from
        magnification : int | float
            Target magnification for extraction (e.g., 20, 40)
        tile_size : Tuple[int, int], optional
            Size of tiles (width, height) in pixels. Default is (512, 512).

        Yields
        ------
        Tile
            Individual tile objects with image, coordinates, and metadata

        Raises
        ------
        MagnificationError
            If the requested magnification is not available on this slide
        TileSizeOrCoordinatesError
            If generated coordinates are invalid for the slide

        Example:
            >>> slide = Slide("slide.svs")
            >>> tiler = GridTiler(tile_size=(512, 512), overlap=50)
            >>> for tile in tiler.extract(slide, magnification=20):
            ...     tile.save(f"tile_{tile.coords}.png")
        """
        pass

    @abstractmethod
    def get_tile_coordinates(
        self,
        slide: Slide,
        magnification: int | float,
        tile_size: Tuple[int, int] = (512, 512),
    ) -> List[Tuple[int, int]]:
        """Get all tile coordinates without extracting images.

        This method only computes which tiles would be extracted without
        actually reading images from the slide. Useful for planning,
        filtering, or batch processing.

        Parameters
        ----------
        slide : Slide
            The slide object
        magnification : int | float
            Target magnification
        tile_size : Tuple[int, int], optional
            Size of tiles (width, height) in pixels. Default is (512, 512).

        Returns
        -------
        List[Tuple[int, int]]
            List of (x, y) coordinates in Level 0 coordinates

        Example:
            >>> tiler = GridTiler(tile_size=(512, 512))
            >>> coords = tiler.get_tile_coordinates(slide, magnification=20)
            >>> print(f"Will extract {len(coords)} tiles")
        """
        pass

    def visualize(
        self,
        slide: Slide,
        magnification: int | float = 5,
        tile_size: Tuple[int, int] = (512, 512),
        scale_factor: int = 32,
        colors: Optional[List[Tuple[int, int, int]]] = None,
        alpha: int = 200,
        linewidth: int = 1,
    ) -> Image.Image:
        """Visualize tile grid on a slide thumbnail.

        This method creates a thumbnail of the slide and draws the tile grid
        on top of it. Useful for verifying tiling strategy before processing.

        Parameters
        ----------
        slide : Slide
            The slide object to visualize
        magnification : int | float, optional
            Target magnification. Default is 5 (low power for visualization).
        tile_size : Tuple[int, int], optional
            Size of tiles (width, height). Default is (512, 512).
        scale_factor : int, optional
            Scale factor for thumbnail downsampling. Default is 32.
        colors : List[Tuple[int, int, int]], optional
            RGB colors for tile rectangles. If None, uses a cycle of colors.
            Default is None.
        alpha : int, optional
            Transparency alpha value for rectangles (0-255). Default is 200.
        linewidth : int, optional
            Width of rectangle lines in pixels. Default is 1.

        Returns
        -------
        PIL.Image.Image
            Thumbnail image with tile grid drawn on it

        Example:
            >>> tiler = GridTiler(tile_size=(512, 512))
            >>> viz_image = tiler.visualize(slide)
            >>> viz_image.show()
        """
        from PIL import ImageDraw
        import copy

        # Get thumbnail
        thumbnail = slide.thumbnail.copy()

        # Default colors (cycle through these)
        if colors is None:
            colors = [
                (0, 255, 0),  # Green
                (255, 0, 0),  # Red
                (0, 0, 255),  # Blue
                (255, 255, 0),  # Yellow
            ]

        # Get coordinates
        coords = self.get_tile_coordinates(slide, magnification, tile_size)

        # Scale coordinates for thumbnail (slide dimensions -> thumbnail dimensions)
        scale = scale_factor  # Simple scale for now
        thumb_draw = ImageDraw.Draw(thumbnail, "RGBA")

        for i, (x, y) in enumerate(coords):
            # Scale down coordinates
            scaled_x = x // scale
            scaled_y = y // scale
            scaled_w = tile_size[0] // scale
            scaled_h = tile_size[1] // scale

            # Bounds for rectangle
            left = scaled_x
            top = scaled_y
            right = scaled_x + scaled_w
            bottom = scaled_y + scaled_h

            # Clip to thumbnail bounds
            left = max(0, min(left, thumbnail.width))
            top = max(0, min(top, thumbnail.height))
            right = max(0, min(right, thumbnail.width))
            bottom = max(0, min(bottom, thumbnail.height))

            # Draw rectangle
            color = colors[i % len(colors)]
            color_with_alpha = (*color, alpha)

            thumb_draw.rectangle(
                [left, top, right, bottom],
                outline=color,
                width=linewidth,
            )

        return thumbnail
