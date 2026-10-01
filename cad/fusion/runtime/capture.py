"""Viewport capture: a fixed set of views, saved as PNG.

Imports adsk. The camera is set from the model's bounding box with explicit eye, target and up vector; it
never uses Camera.viewOrientation, because that follows the ViewCube and is not the same in every document.
"""
import os

import adsk.core

from . import fusion_app, port

# view name -> (direction from the target to the eye, up vector); model frame, Z up
VIEWS = {
    "iso": ((1, -1, 1), (0, 0, 1)),
    "iso_back": ((-1, 1, 1), (0, 0, 1)),
    "iso_bottom": ((1, -1, -1), (0, 0, 1)),
    "top": ((0, 0, 1), (0, 1, 0)),
    "bottom": ((0, 0, -1), (0, 1, 0)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "back": ((0, 1, 0), (0, 0, 1)),
    "left": ((-1, 0, 0), (0, 0, 1)),
    "right": ((1, 0, 0), (0, 0, 1)),
}


def save_view(doc, box_mm, path, view, width=1600, height=1200):
    """Save one view of the document. box_mm = (min, max) of the solids in mm. Returns a dict or raises PortError."""
    if view not in VIEWS:
        raise port.PortError("unknown view %r" % view)
    a = fusion_app.app()
    if not doc.isActive:
        doc.activate()
    viewport = a.activeViewport
    if viewport is None or viewport.parentDocument.creationId != doc.creationId:
        raise port.PortError("the active viewport does not belong to the job's document")
    lo, hi = box_mm
    centre = [(l + h) / 2.0 / 10.0 for l, h in zip(lo, hi)]                  # mm -> cm
    reach = max(max(h - l for l, h in zip(lo, hi)) / 10.0, 1.0) * 3.0        # eye distance in cm
    direction, up = VIEWS[view]
    norm = sum(c * c for c in direction) ** 0.5
    eye = [c + d / norm * reach for c, d in zip(centre, direction)]
    camera = viewport.camera                                                 # a copy; assign it back below
    camera.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    camera.isSmoothTransition = False
    camera.target = adsk.core.Point3D.create(*centre)
    camera.eye = adsk.core.Point3D.create(*eye)
    camera.upVector = adsk.core.Vector3D.create(*up)
    camera.isFitView = True
    viewport.camera = camera
    viewport.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    viewport.refresh()
    if not viewport.saveAsImageFile(path, int(width), int(height)) or not os.path.isfile(path):
        raise port.PortError("the viewport image %s was not written" % path)
    return {"view": view, "width": int(width), "height": int(height)}
