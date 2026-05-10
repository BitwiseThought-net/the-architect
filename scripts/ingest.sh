#!/bin/bash
docker exec -it $(basename "$PWD") python ingest.py
