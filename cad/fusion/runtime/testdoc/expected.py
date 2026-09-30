"""Analytic measures of the test part "TestBlock" for a parameter set. Pure Python.

Block L x W x H on the XY plane from the origin; optional through hole of diameter D; N pins of diameter d and
height h on the top face, clear of the hole and of each other.
"""
import math


def measures(values, hole_suppressed, wall=4.0):
    L, W, H = float(values["V_TEST_L"]), float(values["V_TEST_W"]), float(values["V_TEST_H"])
    D, n = float(values["V_TEST_HOLE_D"]), int(values["V_N_TEST_PINS"])
    d, h = wall * 1.5, wall / 2.0
    volume = L * W * H + n * math.pi * (d / 2) ** 2 * h
    area = 2 * (L * W + L * H + W * H) + n * math.pi * d * h
    if not hole_suppressed:
        volume -= math.pi * (D / 2) ** 2 * H
        area += math.pi * D * H - 2 * math.pi * (D / 2) ** 2
    return {"bbox": {"min": [0.0, 0.0, 0.0], "max": [L, W, H + h], "size": [L, W, H + h]},
            "volume_mm3": volume, "area_mm2": area, "solids": 1}
