#!/usr/bin/env python3
"""Copia SQLite consistente y prueba de restauración local. No es backup del host."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile


def verify(path):
    ...


def backup(database, directory, keep=14):
    ...


def main():
    ...


if __name__ == '__main__':
    main()
