"""Off-screen drawing half of the showcase renders (issue #74): PyVista (VTK) to a palette PNG.

The only file of the showcase pipeline that needs OpenGL. `scripts/showcase.py` imports it lazily, so the
pytest job never does. On a headless Linux runner run under `xvfb-run -a` with Mesa software GL
(packages xvfb, libgl1-mesa-dri, libglx-mesa0). Imports neither `build` nor `bambu_project` nor cad/.

`render_scene` takes duck-typed arguments so this file does not import `showcase`:
  meshes  iterable of objects with .path, .colour, .opacity, .offset (x, y, z)
  camera  object with .position, .focal, .up, .view_angle (vertical, degrees)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np

MIN_INK_FRACTION = 0.005      # a picture with less than this share of non-background pixels is a failure


def render_scene(
    meshes: Iterable, camera, size: tuple[int, int], out_png: Path, *,
    background: str = "#f2f3f5", palette_colours: int = 128,
) -> None:
    """Draw `meshes` from `camera` into a `size` PNG at `out_png` (8-bit palette, optimised).

    Raises RuntimeError when the result is (almost) only background, so a broken GL setup can never
    ship an empty image."""

    import pyvista as pv   # lazy: importing this module must stay possible without GL (and without pillow)
    from PIL import Image

    meshes = list(meshes)
    pv.OFF_SCREEN = True
    plotter = pv.Plotter(off_screen=True, window_size=[int(size[0]), int(size[1])])
    try:
        plotter.set_background(background)
        # Fixed camera-relative lights (key from upper left, weak fill from the right): the same shading
        # in every view, and side faces (dovetail flanks, hole walls) read against flat faces.
        plotter.remove_all_lights()
        for position, intensity in (((-1.0, 1.0, 1.5), 0.75), ((1.0, -0.3, 1.0), 0.25)):
            plotter.add_light(pv.Light(
                position=position, focal_point=(0.0, 0.0, 0.0), intensity=intensity, light_type="camera light",
            ))
        for spec in meshes:
            mesh = pv.read(str(spec.path))
            dx, dy, dz = spec.offset
            if dx or dy or dz:
                mesh.translate((dx, dy, dz), inplace=True)
            plotter.add_mesh(
                mesh, color=spec.colour, opacity=float(spec.opacity),
                smooth_shading=False, show_edges=False, specular=0.0, ambient=0.3, diffuse=0.8,
            )
        if any(float(s.opacity) < 1.0 for s in meshes):
            plotter.enable_depth_peeling(number_of_peels=8, occlusion_ratio=0.0)
        plotter.enable_anti_aliasing("ssaa")

        cam = plotter.camera
        cam.position = tuple(camera.position)
        cam.focal_point = tuple(camera.focal)
        cam.up = tuple(camera.up)
        cam.parallel_projection = False
        cam.view_angle = float(camera.view_angle)
        plotter.renderer.reset_camera_clipping_range()
        image = plotter.screenshot(return_img=True)
    finally:
        plotter.close()

    pixels = np.asarray(image)[..., :3]
    bg = np.array([int(background[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.uint8)
    ink = float(np.mean(np.any(np.abs(pixels.astype(int) - bg.astype(int)) > 8, axis=-1)))
    if ink < MIN_INK_FRACTION:
        raise RuntimeError(
            f"{Path(out_png).name}: the render is empty ({ink:.4%} non-background pixels) — check the GL setup"
        )

    quantised = Image.fromarray(pixels, "RGB").quantize(colors=palette_colours, dither=Image.Dither.NONE)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    quantised.save(out_png, format="PNG", optimize=True)
