#!/usr/bin/env python3
"""Produce a comment-free, de-identified copy of a .docx.

Removes the comments part, its relationship, its content-type override, and the
in-body comment anchors; blanks the author fields in document properties.
Body text, tables, images and formatting are untouched.

  python3 tools/strip_docx_comments.py IN.docx OUT.docx
"""
import re, shutil, sys, zipfile

def strip(src, dst):
    zin = zipfile.ZipFile(src)
    names = zin.namelist()
    drop = {n for n in names if re.search(r'word/comments(Extended|Ids|Extensible)?\.xml$', n)
            or n.endswith('word/commentsExtended.xml')}
    zout = zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED)
    removed_anchors = 0
    for item in zin.infolist():
        if item.filename in drop:
            continue
        data = zin.read(item.filename)
        if item.filename == "word/document.xml":
            x = data.decode("utf8")
            before = len(x)
            # self-closing anchors and any commentReference run wrappers
            x = re.sub(r'<w:commentRangeStart[^>]*/>', '', x)
            x = re.sub(r'<w:commentRangeEnd[^>]*/>', '', x)
            x = re.sub(r'<w:r>(?:(?!</w:r>).)*?<w:commentReference[^>]*/>.*?</w:r>', '', x, flags=re.S)
            x = re.sub(r'<w:commentReference[^>]*/>', '', x)
            removed_anchors = before - len(x)
            data = x.encode("utf8")
        elif item.filename == "word/_rels/document.xml.rels":
            x = data.decode("utf8")
            x = re.sub(r'<Relationship[^>]*comments[^>]*/>', '', x)
            data = x.encode("utf8")
        elif item.filename == "[Content_Types].xml":
            x = data.decode("utf8")
            x = re.sub(r'<Override[^>]*comments[^>]*/>', '', x)
            data = x.encode("utf8")
        elif item.filename in ("docProps/core.xml", "docProps/app.xml"):
            x = data.decode("utf8")
            for tag in ("dc:creator", "cp:lastModifiedBy", "Company", "Manager"):
                x = re.sub(r'(<%s[^>]*>)[^<]*(</%s>)' % (tag, tag), r'\1\2', x)
            data = x.encode("utf8")
        zout.writestr(item, data)
    zin.close(); zout.close()
    return len(drop), removed_anchors

if __name__ == "__main__":
    d, a = strip(sys.argv[1], sys.argv[2])
    print(f"  {sys.argv[2].split('/')[-1]}: dropped {d} comment part(s), {a} bytes of anchors")
