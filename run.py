"""
AgriAgent Phase 2 Master CLI Entry Point (run.py)
Supports local files, folders, direct HTTP/HTTPS PDF/HTML URLs, and AI-driven ingestion.
"""

import os
import re
import csv
import json
import time
import sqlite3
import hashlib
import argparse
import tempfile
import httpx
from datetime import datetime, timezone

from agent1_classifier import Agent1Classifier
from agent2_ingestion import Agent2Ingestion
from agent2b_live_gis import Agent2BLiveGIS
from agent3_task import Agent3TaskNormalizer

def download_url_to_temp(url: str) -> str:
    """Downloads a remote PDF or web document to a temporary local file."""
    print(f"[DOWNLOADER] Fetching remote source: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        with httpx.Client(verify=False, timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            suffix = ".pdf" if ".pdf" in url.lower() else (".html" if ".html" in url.lower() else ".txt")
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tf.write(resp.content)
            tf.close()
            print(f"[DOWNLOADER] Successfully cached remote source to temporary file: {tf.name}")
            return tf.name
    except Exception as e:
        raise RuntimeError(f"Failed to download URL '{url}': {e}")

def main():
    parser = argparse.ArgumentParser(description="AgriAgent Phase 2 Master CLI Runner")
    parser.add_argument("--input", type=str, default=None, help="Local file path, directory, or HTTP/HTTPS PDF/HTML URL")
    parser.add_argument("--inject-fault", action="store_true", help="Trigger live fault injection & SelfCorrectionNode recovery")
    parser.add_argument("--reset-db", action="store_true", help="Cleanly rebuild database before committing")
    args = parser.parse_args()

    orchestrator = MultiAgentOrchestrator(db_path="db/assam_agri_phase2.db")
    
    input_target = args.input
    temp_file_to_cleanup = None

    if input_target and (input_target.startswith("http://") or input_target.startswith("https://")):
        temp_file_to_cleanup = download_url_to_temp(input_target)
        input_target = temp_file_to_cleanup

    try:
        committed, retries = orchestrator.run_pipeline(
            surprise_input=input_target, inject_fault=args.inject_fault, reset_db=args.reset_db
        )
        print(f"[SUCCESS] Committed {committed} validated records to db/assam_agri_phase2.db (Retries={retries}) | SQL dump updated in db/dump.sql")
    finally:
        if temp_file_to_cleanup and os.path.exists(temp_file_to_cleanup):
            os.remove(temp_file_to_cleanup)

if __name__ == "__main__":
    main()
