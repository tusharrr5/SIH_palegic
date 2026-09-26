"""Explicit online refresh. Not called by bootstrap or recording startup."""

from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
import json, hashlib, datetime, concurrent.futures

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://services1.arcgis.com/qr14biwnHA6Vis6l/arcgis/rest/services/Deepwaterhorizon_Oilspill_WM/FeatureServer"
SOURCES = [
    (
        f"dwh-2010-05-{day}.geojson",
        BASE
        + f"/{layer}/query?"
        + urlencode(
            {
                "where": "1=1",
                "outFields": "*",
                "outSR": 4326,
                "f": "geojson",
                "resultRecordCount": 2000,
            }
        ),
    )
    for day, layer in [("17", 3), ("19", 4), ("20", 5)]
] + [
    (
        "dwh-metadata.json",
        "https://www.arcgis.com/sharing/rest/content/items/afafd2255f9d43bd8a5531de7e98c9a5?f=json",
    ),
    (
        "land-10m.geojson",
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_land.geojson",
    ),
    (
        "countries.geojson",
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson",
    ),
]


def fetch(pair):
    name, url = pair
    content = urlopen(url, timeout=90).read()
    obj = json.loads(content)
    if obj.get("error") or obj.get("exceededTransferLimit"):
        raise RuntimeError("Source incomplete: " + name)
    return (
        name,
        content,
        {
            "file": name,
            "url": url,
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "retrieved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "feature_count": len(obj.get("features", [])),
        },
    )


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fetch, SOURCES))
    # Write only after every download passed validation.
    for name, content, _ in results:
        (ROOT / "data/source" / name).write_bytes(content)
    (ROOT / "data/source/manifest.json").write_text(
        json.dumps(
            [
                e
                for e in json.loads((ROOT / "data/source/manifest.json").read_text())
                if e["file"] not in {r[0] for r in results}
            ]
            + [r[2] for r in results],
            indent=2,
        )
    )
    print(
        "Downloaded",
        len(results),
        "source artifacts. Existing database observations remain immutable.",
    )
