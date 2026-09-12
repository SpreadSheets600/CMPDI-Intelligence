"""Markdown to DOCX. Reports are composed as markdown (headings, tables,
bold, lists) and converted into real Word elements, so markdown syntax never
leaks into the document the officer opens."""

import markdown
from docx import Document
from htmldocx import HtmlToDocx


def markdown_to_document(md_text: str, base_document=None) -> Document:
    # python-docx's Document is a factory function, so no | None annotation
    html = markdown.markdown(md_text, extensions=["tables"])
    doc = base_document or Document()
    HtmlToDocx().add_html_to_document(html, doc)
    return doc
