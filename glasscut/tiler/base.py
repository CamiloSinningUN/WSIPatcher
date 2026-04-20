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

        # Build a display thumbnail and map coordinates using exact size ratios.
        thumbnail = slide.thumbnail.copy()
        if scale_factor > 0:
            target_w = max(1, int(slide.dimensions[0] / scale_factor))
            target_h = max(1, int(slide.dimensions[1] / scale_factor))
            thumbnail = thumbnail.resize((target_w, target_h))

        # Default color: a single green outline for all boxes.
        if colors is None:
            colors = [(0, 255, 0)]

        # Get tile boxes
        boxes = self.get_tile_boxes(slide)

        # Scale coordinates for thumbnail (slide dimensions -> thumbnail dimensions)
        slide_w, slide_h = slide.dimensions
        thumb_w, thumb_h = thumbnail.size
        x_ratio = thumb_w / slide_w
        y_ratio = thumb_h / slide_h
        thumb_draw = ImageDraw.Draw(thumbnail, "RGBA")

        for i, (x, y, tile_w, tile_h) in enumerate(boxes):
            # Map both box corners independently to reduce rounding artifacts.
            left = int(round(x * x_ratio))
            top = int(round(y * y_ratio))
            right = int(round((x + tile_w) * x_ratio)) - 1
            bottom = int(round((y + tile_h) * y_ratio)) - 1

            # Clip to thumbnail bounds
            left = max(0, min(left, thumbnail.width))
            top = max(0, min(top, thumbnail.height))
            right = max(0, min(right, thumbnail.width - 1))
            bottom = max(0, min(bottom, thumbnail.height - 1))

            if right <= left or bottom <= top:
                continue

            # Draw rectangle
            color = colors[i % len(colors)]

            thumb_draw.rectangle(
                [left, top, right, bottom],
                outline=color,
                width=linewidth,
            )

        return thumbnail
