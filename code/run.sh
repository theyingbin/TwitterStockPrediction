#!/bin/bash
pip install tweepy
pip install -U textblob
python -m textblob.download_corpora

python bucketify.py 
python predictor.py
