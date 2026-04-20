"""Base Tiler abstract class for tile extraction strategies."""

from abc import ABC, abstractmethod
from typing import Generator
from PIL import Image

from glasscut.slides import Slide
from glasscut.tile import Tile



class Tiler(ABC):
    """Abstract base class for tile extraction strategies.

    A Tiler is responsible for determining which tiles to extract from a slide
    and providing them to the user. Different tiling strategies can be implemented
    by subclassing this class.
    """

    @abstractmethod
    def extract(
        self,
        slide: Slide,
    ) -> Generator[Tile, None, None]:
        """Extract tiles from slide.

        This is the main method for tile extraction. It yields Tile objects
        one at a time in order, allowing for efficient memory usage on large slides.

        Parameters
        ----------
        slide : Slide
            The slide object to extract tiles from

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
            >>> for tile in tiler.extract(slide):
            ...     tile.save(f"tile_{tile.coords}.png")
        """
        pass

    @abstractmethod
    def get_tile_boxes(
        self,
        slide: Slide,
    ) -> list[tuple[int, int, int, int]]:
        """Get all tile boxes without extracting images.

        This method computes which tile regions would be extracted without
        actually reading images from the slide. Useful for planning,
        filtering, or batch processing.

        Parameters
        ----------
        slide : Slide
            The slide object

        Returns
        -------
        list[tuple[int, int, int, int]]
            List of tile boxes as ``(x, y, width, height)`` in level-0 space.

        Example:
            >>> tiler = GridTiler(tile_size=(512, 512))
            >>> boxes = tiler.get_tile_boxes(slide)
            >>> print(f"Will extract {len(boxes)} tiles")
        """
        pass

    def visualize(
        self,
        slide: Slide,
        scale_factor: int = 32,
        colors: list[tuple[int, int, int]] | None = None,
        linewidth: int = 1,
    ) -> Image.Image:
        """Visualize tile grid on a slide thumbnail.

        This method creates a thumbnail of the slide and draws the tile grid
        on top of it. Useful for verifying tiling strategy before processing.

        Parameters
        ----------
        slide : Slide
            The slide object to visualize
        scale_factor : int, optional
            Scale factor for thumbnail downsampling. Default is 32.
        colors : list[tuple[int, int, int]] | None, optional
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

        # Get tile boxes
        boxes = self.get_tile_boxes(slide)

        # Scale coordinates for thumbnail (slide dimensions -> thumbnail dimensions)
        scale = scale_factor  # Simple scale for now
        thumb_draw = ImageDraw.Draw(thumbnail, "RGBA")

        for i, (x, y, tile_w, tile_h) in enumerate(boxes):
            # Scale down coordinates
            scaled_x = x // scale
            scaled_y = y // scale
            scaled_w = tile_w // scale
            scaled_h = tile_h // scale

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

            thumb_draw.rectangle(
                [left, top, right, bottom],
                outline=color,
                width=linewidth,
            )

        return thumbnail
