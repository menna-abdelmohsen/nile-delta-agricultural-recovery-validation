"""Study-area geometry definitions, reused verbatim from Paper 2
("Budget-Constrained Agricultural-to-Built Conversion Risk Ranking...",
JSTARS, this author group) for thesis-wide continuity.

Coordinates and bounding box copied from Paper 2, Section II.A:
  Primary window: El-Bagalat, Minyat El-Nasr, Dakahlia governorate, Egypt.
  Center: 31.165278 N, 31.627500 E.
  Bounding box: 31.582-31.673 E, 31.125-31.205 N.
  ~8.5 km extent, 30 m grid, 87,308 cells, EPSG:32636 (UTM Zone 36N).

  Geographic-transfer / holdout window: Mit Salsil, same governorate.
  Center: 31.1676 N, 31.8013 E (Paper 2 gives only a center point, not an
  explicit bounding box - reconstructed here as a box of the SAME extent
  as the primary window, centered on that point, for consistency; this
  approximation must be checked against Paper 2's original exported grid
  if/when that grid is available, since Paper 2 does not state the Mit
  Salsil box explicitly in the manuscript text extracted so far).

Do not edit these values without updating research_log.md with a dated
justification - they are the anchor for cross-paper comparability.
"""

from dataclasses import dataclass

EPSG_UTM36N = "EPSG:32636"


@dataclass(frozen=True)
class StudyWindow:
    name: str
    center_lat: float
    center_lon: float
    min_lon: float
    max_lon: float
    min_lat: float
    max_lat: float


EL_BAGALAT = StudyWindow(
    name="El-Bagalat",
    center_lat=31.165278,
    center_lon=31.627500,
    min_lon=31.582,
    max_lon=31.673,
    min_lat=31.125,
    max_lat=31.205,
)

# Reconstructed box (see module docstring caveat) - width/height matched to
# El-Bagalat's box (0.091 deg lon x 0.080 deg lat), centered on Paper 2's
# stated Mit Salsil point. TREAT AS APPROXIMATE until verified.
_MIT_SALSIL_LON_HALF = (EL_BAGALAT.max_lon - EL_BAGALAT.min_lon) / 2
_MIT_SALSIL_LAT_HALF = (EL_BAGALAT.max_lat - EL_BAGALAT.min_lat) / 2

MIT_SALSIL = StudyWindow(
    name="Mit Salsil",
    center_lat=31.1676,
    center_lon=31.8013,
    min_lon=31.8013 - _MIT_SALSIL_LON_HALF,
    max_lon=31.8013 + _MIT_SALSIL_LON_HALF,
    min_lat=31.1676 - _MIT_SALSIL_LAT_HALF,
    max_lat=31.1676 + _MIT_SALSIL_LAT_HALF,
)

# Geographic expansion (added 2026-09-21), per the explicit, evidence-based
# decision in research_log.md: after the corrected labeling protocol
# (strengthened 3/3-year historical mask + simultaneous-majority recovery
# rule) reduced the confirmed recovery-event count to a marginal N=11
# combined (El-Bagalat alone had only 1), the governing brief's own
# guidance was followed - "if the number of confirmed recoveries is too
# small... investigate scientifically legitimate expansion strategies
# such as... expanding the geographic study area using the same
# predefined protocol" - RATHER than loosening the just-corrected label
# definition to manufacture more positives.
#
# Two more Dakahlia-governorate towns were added, chosen by a real,
# reproducible rule (geocoded via the public OSM Nominatim API, not
# hand-picked for how much conversion they show) and using the IDENTICAL
# window size/shape and full pipeline as El-Bagalat/Mit Salsil, for
# methodological continuity within the same governorate already
# established by Paper 2.
_TALKHA_LON_HALF = _MIT_SALSIL_LON_HALF
_TALKHA_LAT_HALF = _MIT_SALSIL_LAT_HALF
TALKHA = StudyWindow(
    name="Talkha",
    center_lat=31.0522251,
    center_lon=31.3731608,
    min_lon=31.3731608 - _TALKHA_LON_HALF,
    max_lon=31.3731608 + _TALKHA_LON_HALF,
    min_lat=31.0522251 - _TALKHA_LAT_HALF,
    max_lat=31.0522251 + _TALKHA_LAT_HALF,
)

SHERBIN = StudyWindow(
    name="Sherbin",
    center_lat=31.2169810,
    center_lon=31.3517670,
    min_lon=31.3517670 - _TALKHA_LON_HALF,
    max_lon=31.3517670 + _TALKHA_LON_HALF,
    min_lat=31.2169810 - _TALKHA_LAT_HALF,
    max_lat=31.2169810 + _TALKHA_LAT_HALF,
)

ALL_WINDOWS = (EL_BAGALAT, MIT_SALSIL, TALKHA, SHERBIN)
ALL_WINDOW_NAMES = tuple(w.name.replace(" ", "_") for w in ALL_WINDOWS)


def to_ee_geometry(window: StudyWindow):
    """Return an ee.Geometry.Rectangle for the given window. Imports ee lazily
    so this module can be imported without an Earth Engine session for
    non-EE uses (e.g. plotting a reference map)."""
    import ee

    return ee.Geometry.Rectangle(
        [window.min_lon, window.min_lat, window.max_lon, window.max_lat],
        proj="EPSG:4326",
        geodesic=False,
    )
