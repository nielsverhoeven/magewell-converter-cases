# Coupon print log

One row per physical print attempt. Append, don't overwrite — a coupon usually gets reprinted after
a first-pass measurement changes a constant, and the history of what was tried is useful. When a
measurement leads to a `lib/mcc/constants.scad` edit, note the new value and date in the "Result /
constant updated" column so the log and `constants.scad` stay traceable to each other.

| Date | Coupon | Connector / variant | Filament brand & color | Plate / surface | Bed temp °C | Nozzle temp °C | Other settings (walls, brim, supports) | Measured result | Constant updated (file:symbol = value) | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |
| | | | | | | | | | | |
| | | | | | | | | | | |

## Template row (copy this)

```
| YYYY-MM-DD | <coupon> | <e.g. NAHDMI-W-B / N/A> | <brand, color> | <textured PEI + glue / other> | <e.g. 105-110> | <e.g. 260> | <5 walls, brim: yes/no, supports: none/tree under X> | <what you measured/observed> | <lib/mcc/constants.scad : MCC_X = value> | <anything else> |
```
