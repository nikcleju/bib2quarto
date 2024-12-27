#!/bin/bash

# Run the Python script with optional --config argument using micromamba run
micromamba run -n bib2quarto python /home/ncleju/Work/bib2quarto/bib2quarto.py "$@"
