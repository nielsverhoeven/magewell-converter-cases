"""Expression constants and the capacity table shared by the case builders (issue #81, plan 3.2).

Strings and tuples only, no function: every builder writes the same text for the same place.  The frame is the assembly
frame, which is the OpenSCAD model frame; the datum is the corner of the footprint on the exterior floor.
"""
from __future__ import annotations

XL = "-V_CASE_L / 2"                      # minus X outer face      (equals the datum)
XH = "V_CASE_L / 2"                       # plus X outer face
YL = "-V_CASE_W / 2"                      # far wall outer face      (equals the datum)
YH = "V_CASE_W / 2"                       # patch wall outer face
XIL = "-V_CASE_L / 2 + MCC_WALL"          # inner faces
XIH = "V_CASE_L / 2 - MCC_WALL"
YIL = "-V_CASE_W / 2 + MCC_WALL"
YIH = "V_CASE_W / 2 - MCC_T_PATCH"
YSEAT = "V_CASE_W / 2 - MCC_PANEL_BEZEL_T"
YTG = "V_CASE_W / 2 - MCC_TG_PATCH_INSET"
FT = "MCC_FLOOR_T"
ZT = "V_CASE_Z_TOP"
ZLID = "V_CASE_Z_TOP + MCC_LID_T"
ZC = "V_CONN_Z"
FX = "V_CASE_L / 2 - MCC_FASTENER_INSET"  # corner fastener, plus side; the minus side is expr.neg(FX)
FY = "V_CASE_W / 2 - MCC_FASTENER_INSET"
DATUM = (XL, YL, None)

# The one table of capacities of the generator (verdict B1): the keys and values of cad.layout.CAPACITY.  No module holds a
# count of its own; every loop over a group iterates one of the tuples below.  test_case_plan.py proves the table against the
# key set of the parameter sets in both directions.
CAPACITY = {"slots": 4, "far_ribs": 5, "far_low": 3, "far_high": 2, "exhaust": 1, "negx": 1, "lid": 2, "fan_rings": 3}
RUN = "ABC"
SLOTS = tuple(range(1, CAPACITY["slots"] + 1))
FAR_RIBS = tuple(range(1, CAPACITY["far_ribs"] + 1))
VENT_FAR_LOW = tuple("FarLo" + c for c in RUN[:CAPACITY["far_low"]])
VENT_FAR_HIGH = tuple("FarUp" + c for c in RUN[:CAPACITY["far_high"]])
VENT_EXH = tuple("Exh" + c for c in RUN[:CAPACITY["exhaust"]])
VENT_NEGX = tuple("NegX" + c for c in RUN[:CAPACITY["negx"]])
VENT_LID = tuple("Lid" + c for c in RUN[:CAPACITY["lid"]])
GRILLE_REJOIN_RINGS = tuple(range(1, CAPACITY["fan_rings"]))   # the outermost ring is never a feature (D81.8)
