"""Exercise the actual metadata stylesheet with Saxon/C.

Install saxonche, then run:
    python -m unittest discover -s Scripts/tests -v
"""

import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape

from saxonche import PySaxonProcessor


STYLESHEET = Path(__file__).resolve().parents[1] / "pressmint2meta.xsl"


class MetadataIdentifiersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.processor = PySaxonProcessor(license=False)
        cls.transform = cls.processor.new_xslt30_processor().compile_stylesheet(
            stylesheet_file=str(STYLESHEET)
        )

    def export(self, urns=(), urls=(), separator="|"):
        identifiers = "".join(
            f'<idno type="{kind}">{escape(value)}</idno>'
            for kind, values in (("URN", urns), ("URI", urls))
            for value in values
        )
        xml = f'''<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="PressMint-FR_test" xml:lang="fr">
          <teiHeader><fileDesc><titleStmt><title>Test</title></titleStmt>
            <sourceDesc><bibl><title level="j">Le Temps</title>
              <date when="1920-01-01"/>{identifiers}
            </bibl></sourceDesc></fileDesc>
            <profileDesc><langUsage><language ident="fr">French</language></langUsage></profileDesc>
          </teiHeader>
          <text><body><p xml:id="p1">First paragraph.</p><p xml:id="p2">Second paragraph.</p></body></text>
        </TEI>'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "issue.xml"
            source.write_text(xml, encoding="utf-8")
            self.transform.set_parameter("meta", self.processor.make_string_value(source.as_uri()))
            self.transform.set_parameter("multi-separator", self.processor.make_string_value(separator))
            output = self.transform.transform_to_string(source_file=str(source))
        rows = [line.split("\t") for line in output.splitlines()[1:]]
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(len(row), 13)
            self.assertEqual(row[2], "1920-01-01")
            self.assertEqual(row[3], "Le Temps")
            self.assertEqual(row[8], separator.join(urns))
            self.assertEqual(row[9], separator.join(urls))
        return rows

    def test_no_identifiers(self):
        self.export()

    def test_single_identifiers(self):
        self.export(urns=["ark:/12148/bpt6k243877q"], urls=["https://example.org/issue"])

    def test_original_french_sample_multiple_uris(self):
        self.export(urls=["ark:/12148/bpt6k243877q", "ark:/12148/cb34431794k", "ark:/12148/bc6p0j3t4"])

    def test_corrected_french_sample_multiple_urns(self):
        self.export(urns=["ark:/12148/bpt6k243877q", "ark:/12148/cb34431794k", "ark:/12148/bc6p0j3t4"])

    def test_multiple_identifiers_in_both_fields(self):
        self.export(urns=["urn:example:one", "urn:example:two"],
                    urls=["https://example.org/one", "https://example.org/two"])

    def test_custom_multi_separator(self):
        self.export(urns=["urn:example:one", "urn:example:two"],
                    urls=["https://example.org/one", "https://example.org/two"], separator=";")


if __name__ == "__main__":
    unittest.main()
