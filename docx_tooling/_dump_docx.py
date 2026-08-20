#!/usr/bin/env python3
"""Dump a docx as a flat text outline (paragraphs + table markers + comments)
for before/after diffing. Usage: python _dump_docx.py <path>"""
import sys, zipfile
from xml.etree import ElementTree as ET
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
z = zipfile.ZipFile(sys.argv[1])
root = ET.fromstring(z.read('word/document.xml'))
body = root.find(f'{W}body')
for el in body:
    tag = el.tag.split('}')[1]
    if tag == 'p':
        txt = ''.join(t.text or '' for t in el.iter(f'{W}t'))
        print("P| " + txt)
    elif tag == 'tbl':
        rows = el.findall(f'{W}tr')
        for tr in rows:
            cells = [' '.join(t.text or '' for t in tc.iter(f'{W}t')) for tc in tr.findall(f'{W}tc')]
            print("T| " + " || ".join(cells))
        print(f"T| --- ({len(rows)} rows) ---")
if 'word/comments.xml' in z.namelist():
    cr = ET.fromstring(z.read('word/comments.xml'))
    for c in cr.findall(f'{W}comment'):
        a = c.get(f'{W}author'); txt = ''.join(t.text or '' for t in c.iter(f'{W}t'))
        print(f"C| {a}: {txt}")
