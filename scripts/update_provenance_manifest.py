#!/usr/bin/env python3
"""Generate the canonical provenance manifest for SIH-ENNORE-2017.

Complies with Phase 2C Section 6:
  - artifact_id
  - source
  - dataset
  - time_range
  - spatial_bounds
  - retrieved_at
  - checksum (SHA-256)
  - provenance_class (from: OBSERVED, REANALYSIS, DERIVED, ILLUSTRATIVE, TRAINING, SYNTHETIC)
  - data_status
  - is_synthetic
  - processing_method
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/demo/ennore-2017"
OUTPUT_FILE = PACKAGE / "provenance_manifest.json"


def get_sha256(filepath: Path) -> str:
    if filepath.exists() and filepath.is_file():
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    return None


ARTIFACTS = [
    {
        "artifact_id": "art-incident-json",
        "name": "Incident identity",
        "file": "incident.json",
        "source": "Published inquiry records and maritime databases (ITOPF, Kamarajar Port Authority, Ministry of Shipping India)",
        "provider": "ITOPF, Kamarajar Port Authority, DGS India",
        "dataset": "SIH-ENNORE-2017 canonical record",
        "source_type": "official_and_media_records",
        "time_range": ["2017-01-28T08:00:00Z", "2017-01-28T08:00:00Z"],
        "spatial_bounds": [80.33, 13.28, 80.33, 13.28],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-28T08:00:00Z",
        "provenance_class": "DERIVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Compilation of publicly documented accident facts and multi-source cross-referencing",
        "processing_steps": [
            "Compilation of publicly documented facts",
            "Cross-referencing multiple sources"
        ],
        "limitations": [
            "Coordinates are approximate — exact collision position from inquiry report",
            "Spill volume is an estimate from secondary sources"
        ],
        "licence_or_usage_note": "Public domain facts — compiled from open government and inquiry sources"
    },
    {
        "artifact_id": "art-sar-metadata",
        "name": "SAR scene metadata",
        "file": "sar/scene_metadata.json",
        "source": "Copernicus Data Space Ecosystem (CDSE) — https://dataspace.copernicus.eu/",
        "provider": "Copernicus Data Space Ecosystem (CDSE)",
        "dataset": "Sentinel-1 GRD Level-1",
        "source_type": "satellite_observation",
        "time_range": ["2017-01-29T00:31:32Z", "2017-01-29T00:31:57Z"],
        "spatial_bounds": [78.219948, 11.888502, 80.810555, 13.841207],
        "retrieved_at": "2026-09-26T09:50:37Z",
        "observed_at": "2017-01-29T00:31:32Z",
        "provenance_class": "OBSERVED",
        "data_status": "METADATA_ONLY",
        "is_synthetic": False,
        "processing_method": "CDSE OData catalogue discovery, scene selection, and footprint intersection verification",
        "processing_steps": [
            "Scene identification from CDSE catalogue query",
            "Metadata extraction and coordinate bounding box validation",
            "Incident intersection check with collision point"
        ],
        "limitations": [
            "METADATA_ONLY — actual SAR raster not yet downloaded (requires CDSE account)",
            "No automated ML oil detection performed on raster"
        ],
        "licence_or_usage_note": "ESA Copernicus Open Access Policy — free and open"
    },
    {
        "artifact_id": "art-sar-search-results",
        "name": "Sentinel-1 search results",
        "file": "sar/sentinel1_search_results.json",
        "source": "CDSE OData catalogue API",
        "provider": "Copernicus Data Space Ecosystem (CDSE)",
        "dataset": "Sentinel-1 catalogue",
        "source_type": "catalogue_search",
        "time_range": ["2017-01-23T08:00:00Z", "2017-02-02T08:00:00Z"],
        "spatial_bounds": [79.8, 12.9, 81.0, 13.7],
        "retrieved_at": "2026-09-26T09:50:37Z",
        "observed_at": None,
        "provenance_class": "OBSERVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "OData API query with CSC.Intersects polygon filter and GRD mode",
        "processing_steps": [
            "OData API query with spatial/temporal filters",
            "Result parsing and metadata extraction"
        ],
        "limitations": [
            "Reflects catalogue contents as of search date",
            "Product download requires authenticated CDSE session"
        ],
        "licence_or_usage_note": "CDSE catalogue metadata is freely accessible"
    },
    {
        "artifact_id": "art-observed-slick",
        "name": "Oil slick polygon",
        "file": "spill/observed_slick.geojson",
        "source": "Digitised from published incident reports and media satellite composites",
        "provider": "PALEGIC project team",
        "dataset": "ITOPF, The Hindu, NRSC media reports",
        "source_type": "secondary_source_digitisation",
        "time_range": ["2017-01-29T04:30:00Z", "2017-01-29T04:30:00Z"],
        "spatial_bounds": [80.32, 13.25, 80.36, 13.31],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-29T04:30:00Z",
        "provenance_class": "ILLUSTRATIVE",
        "data_status": "ILLUSTRATIVE",
        "is_synthetic": False,
        "processing_method": "Manual polygon digitisation from published maps; topological validation",
        "processing_steps": [
            "Review of published newspaper maps and satellite imagery reports",
            "Manual polygon digitisation in WGS84",
            "Topology validation (valid MultiPolygon)"
        ],
        "limitations": [
            "NOT the output of automated SAR oil detection",
            "Shape and area (~4.2 km²) are approximate"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication"
    },
    {
        "artifact_id": "art-detection-metadata",
        "name": "Slick detection metadata",
        "file": "spill/detection_metadata.json",
        "source": "PALEGIC project team / published incident records",
        "provider": "PALEGIC project team",
        "dataset": "Historical validation mask metadata",
        "source_type": "metadata_specification",
        "time_range": ["2017-01-29T04:30:00Z", "2017-01-29T04:30:00Z"],
        "spatial_bounds": [80.32, 13.25, 80.36, 13.31],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-29T04:30:00Z",
        "provenance_class": "ILLUSTRATIVE",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Documentation of slick polygon origin and explicitly preventing false AI claims",
        "processing_steps": [
            "Metadata compilation",
            "Label enforcement (ILLUSTRATIVE)"
        ],
        "limitations": [
            "Defines contract for future ML model integration",
            "Currently describes illustrative digitized mask"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication"
    },
    {
        "artifact_id": "art-ais-tracks",
        "name": "Candidate vessel tracks",
        "file": "ais/tracks.json",
        "source": "Formal accident investigation reports and DG Shipping coordinates",
        "provider": "PALEGIC project team (reconstructed for training)",
        "dataset": "Collision case training tracks (BW Maple & Dawn Kancheepuram)",
        "source_type": "training_reconstruction",
        "time_range": ["2017-01-27T18:00:00Z", "2017-01-28T03:30:00Z"],
        "spatial_bounds": [80.30, 13.22, 80.38, 13.35],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-28T03:30:00Z",
        "provenance_class": "TRAINING",
        "data_status": "TRAINING",
        "is_synthetic": True,
        "processing_method": "Waypoint reconstruction from inquiry reports with realistic kinematics and reception gaps",
        "processing_steps": [
            "Extraction of published key positions and times from inquiry reports",
            "Interpolation of intermediate positions with realistic speed/course",
            "Addition of documented AIS reception gaps",
            "Kinematic plausibility checks"
        ],
        "limitations": [
            "TRAINING data — not authentic recorded terrestrial/satellite AIS NMEA strings",
            "Intermediate points are interpolated between inquiry-documented positions",
            "Must never be promoted to OBSERVED"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication (synthetic training data)"
    },
    {
        "artifact_id": "art-ais-provenance",
        "name": "AIS provenance specification",
        "file": "ais/provenance.json",
        "source": "PALEGIC project team",
        "provider": "PALEGIC project team",
        "dataset": "AIS provenance contract",
        "source_type": "provenance_metadata",
        "time_range": ["2017-01-27T18:00:00Z", "2017-01-28T03:30:00Z"],
        "spatial_bounds": [80.30, 13.22, 80.38, 13.35],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": None,
        "provenance_class": "TRAINING",
        "data_status": "COMPLETE",
        "is_synthetic": True,
        "processing_method": "Contract specification and UI warning enforcement",
        "processing_steps": [
            "Specification of TRAINING provenance class",
            "Definition of UI warnings and limitations"
        ],
        "limitations": [
            "Enforces that synthetic tracks cannot be misrepresented as observed data"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication"
    },
    {
        "artifact_id": "art-metocean-wind",
        "name": "ERA5 wind contract",
        "file": "metocean/wind.json",
        "source": "ECMWF Copernicus Climate Data Store (CDS)",
        "provider": "ECMWF Copernicus Climate Data Store (CDS)",
        "dataset": "reanalysis-era5-single-levels",
        "source_type": "reanalysis_product",
        "time_range": ["2017-01-27T00:00:00Z", "2017-01-31T23:00:00Z"],
        "spatial_bounds": [79.5, 12.5, 81.0, 14.0],
        "retrieved_at": None,
        "observed_at": None,
        "provenance_class": "REANALYSIS",
        "data_status": "NOT_LOADED",
        "is_synthetic": False,
        "processing_method": "Clean fail closed architecture; refuses constant fallbacks until CDSAPI retrieval executes",
        "processing_steps": [
            "Contract specification for 10 m wind components (u10, v10)",
            "Download script implementation (scripts/fetch_era5_wind.py)",
            "Clean failure mechanism when credentials are absent"
        ],
        "limitations": [
            "NOT_LOADED — requires CDS API key in ~/.cdsapirc",
            "Application refuses to substitute fictional constants"
        ],
        "licence_or_usage_note": "Copernicus licence — free for commercial and non-commercial purposes"
    },
    {
        "artifact_id": "art-metocean-currents",
        "name": "CMEMS current contract",
        "file": "metocean/currents.json",
        "source": "Copernicus Marine Service (CMEMS)",
        "provider": "Copernicus Marine Service (CMEMS)",
        "dataset": "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "source_type": "reanalysis_product",
        "time_range": ["2017-01-27T00:00:00Z", "2017-01-31T00:00:00Z"],
        "spatial_bounds": [79.5, 12.5, 81.0, 14.0],
        "retrieved_at": None,
        "observed_at": None,
        "provenance_class": "REANALYSIS",
        "data_status": "NOT_LOADED",
        "is_synthetic": False,
        "processing_method": "Clean fail closed architecture; refuses constant fallbacks until CMEMS subset executes",
        "processing_steps": [
            "Contract specification for near-surface currents (uo, vo)",
            "Download script implementation (scripts/fetch_cmems_currents.py)",
            "Clean failure mechanism when credentials are absent"
        ],
        "limitations": [
            "NOT_LOADED — requires CMEMS credentials",
            "Application refuses to substitute fictional constants"
        ],
        "licence_or_usage_note": "Copernicus Marine Service licence — free and open"
    },
    {
        "artifact_id": "art-metocean-provenance",
        "name": "Metocean provenance specification",
        "file": "metocean/provenance.json",
        "source": "PALEGIC project team",
        "provider": "PALEGIC project team",
        "dataset": "Metocean provenance contract",
        "source_type": "provenance_metadata",
        "time_range": ["2017-01-27T00:00:00Z", "2017-01-31T23:00:00Z"],
        "spatial_bounds": [79.5, 12.5, 81.0, 14.0],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": None,
        "provenance_class": "REANALYSIS",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Enforcement of REANALYSIS provenance and prohibition of hidden fallbacks",
        "processing_steps": [
            "Definition of REANALYSIS provenance class for wind and currents",
            "Refusal rules for fictional constant substitution"
        ],
        "limitations": [
            "Enforces that un-loaded metocean data is clearly reported to user"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication"
    },
    {
        "artifact_id": "art-timeline-events",
        "name": "Master timeline",
        "file": "timeline/events.json",
        "source": "Ministry of Shipping inquiry reports, port authority logs, media timelines",
        "provider": "ITOPF, Ministry of Shipping India, Kamarajar Port",
        "dataset": "Accident timeline compiled from official records",
        "source_type": "official_and_media_records",
        "time_range": ["2017-01-28T03:30:00Z", "2017-02-05T12:00:00Z"],
        "spatial_bounds": [80.30, 13.20, 80.36, 13.35],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-28T03:30:00Z",
        "provenance_class": "DERIVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Chronological sequencing and event classification from official inquiry documents",
        "processing_steps": [
            "Timeline compilation from published investigation reports",
            "Event-by-event provenance tagging",
            "Chronological ordering and consistency validation"
        ],
        "limitations": [
            "Timestamps are derived from published reports (precision: minutes)",
            "Some event times vary slightly between different sources"
        ],
        "licence_or_usage_note": "Public domain facts — compiled from open government sources"
    },
    {
        "artifact_id": "art-evidence-bundle",
        "name": "Evidence bundle",
        "file": "evidence/evidence.json",
        "source": "PALEGIC investigation case model",
        "provider": "PALEGIC project team",
        "dataset": "Investigation evidence items for SIH-ENNORE-2017",
        "source_type": "compiled_evidence",
        "time_range": ["2017-01-28T03:30:00Z", "2017-01-29T12:00:00Z"],
        "spatial_bounds": [79.8, 12.5, 81.0, 14.0],
        "retrieved_at": "2026-09-25T00:00:00Z",
        "observed_at": "2017-01-28T03:30:00Z",
        "provenance_class": "DERIVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Case evidence assembly with strict individual provenance tracking",
        "processing_steps": [
            "Compilation of physical evidence items",
            "Provenance classification for each item",
            "Linking evidence to timeline events and case findings"
        ],
        "limitations": [
            "Evidence items reflect the current prototype state",
            "Synthetic and illustrative items are explicitly tagged"
        ],
        "licence_or_usage_note": "CC0-1.0 — Public Domain Dedication"
    },
    {
        "artifact_id": "art-ais-retrieval-guide",
        "name": "Historical AIS retrieval guide",
        "file": "ais/HISTORICAL_AIS_RETRIEVAL.md",
        "source": "PALEGIC technical documentation",
        "provider": "PALEGIC project team",
        "dataset": "AIS data acquisition documentation",
        "source_type": "technical_documentation",
        "time_range": ["2017-01-27T00:00:00Z", "2017-01-30T00:00:00Z"],
        "spatial_bounds": [79.8, 12.5, 81.0, 14.0],
        "retrieved_at": "2026-09-26T00:00:00Z",
        "observed_at": None,
        "provenance_class": "DERIVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Documentation of retrieval pathways, search parameters, and authentication steps",
        "processing_steps": [
            "Documentation of retrieval methods for GFW, MarineTraffic, VesselFinder, DGS India",
            "Vessel identity verification and alias listing"
        ],
        "limitations": [
            "Documents external data sources; does not guarantee availability from third parties"
        ],
        "licence_or_usage_note": "Documentation — all rights reserved to PALEGIC project"
    },
    {
        "artifact_id": "art-sar-readme",
        "name": "SAR acquisition documentation",
        "file": "sar/README.md",
        "source": "PALEGIC technical documentation",
        "provider": "PALEGIC project team",
        "dataset": "SAR data acquisition documentation",
        "source_type": "technical_documentation",
        "time_range": ["2017-01-28T00:00:00Z", "2017-01-30T00:00:00Z"],
        "spatial_bounds": [78.2, 11.8, 81.1, 15.3],
        "retrieved_at": "2026-09-26T00:00:00Z",
        "observed_at": None,
        "provenance_class": "DERIVED",
        "data_status": "COMPLETE",
        "is_synthetic": False,
        "processing_method": "Documentation of CDSE search, verified scene footprint, and download procedure",
        "processing_steps": [
            "Documentation of CDSE API usage",
            "Deprecation notice for ESA SciHub",
            "Listing of candidate scenes and verification commands"
        ],
        "limitations": [
            "Requires CDSE credentials for raster download"
        ],
        "licence_or_usage_note": "Documentation — all rights reserved to PALEGIC project"
    }
]


def main():
    for art in ARTIFACTS:
        filepath = PACKAGE / art["file"]
        art["checksum"] = get_sha256(filepath)

    manifest_data = {
        "manifest_version": "2.0",
        "incident_id": "SIH-ENNORE-2017",
        "sih_problem_id": "26143",
        "generated_at": "2026-09-26T10:20:00Z",
        "description": "Comprehensive provenance manifest for SIH-ENNORE-2017 canonical incident. Every artifact is classified according to official SIH 26143 provenance taxonomy.",
        "allowed_provenance_classes": [
            "OBSERVED",
            "REANALYSIS",
            "DERIVED",
            "ILLUSTRATIVE",
            "TRAINING",
            "SYNTHETIC"
        ],
        "data_objects": ARTIFACTS
    }

    OUTPUT_FILE.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False) + "\n")
    print(f"Generated {len(ARTIFACTS)} artifact entries in {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
