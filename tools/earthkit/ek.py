"""Import the earthkit components in a safe order.

Importing earthkit.geo before earthkit.transforms makes the interpreter abort at exit (double free in a native
library; seen with earthkit 1.0.0, earthkit-geo 1.2.0, earthkit-transforms 1.0.0 on Python 3.12). Importing
transforms first avoids it, so every script should use:  from tools.earthkit.ek import ekd, transforms, geo, ...
"""
import earthkit.transforms as transforms  # noqa: E402  (must precede earthkit.geo)
import earthkit.data as ekd
import earthkit.geo as geo
import earthkit.hydro as hydro
import earthkit.meteo as meteo
import earthkit.plots as plots

# Note (earthkit-data 1.x): from_source() returns a data object; call .to_fieldlist() / .to_xarray() on it.
# Note: `import earthkit.meteo` does not import submodules; use `from earthkit.meteo import thermo`.
__all__ = ['ekd', 'transforms', 'geo', 'hydro', 'meteo', 'plots']
