"""Tests for VOC→YOLO conversion and annotation parsing."""

import textwrap
from pathlib import Path

import pytest

from pcb_vision.data_prep import CLASSES, parse_voc_xml, voc_box_to_yolo


class TestVocBoxToYolo:
    def test_centered_box(self):
        # A 200x100 box centered in a 1000x500 image
        cx, cy, w, h = voc_box_to_yolo((400, 200, 600, 300), 1000, 500)
        assert cx == pytest.approx(0.5)
        assert cy == pytest.approx(0.5)
        assert w == pytest.approx(0.2)
        assert h == pytest.approx(0.2)

    def test_top_left_box(self):
        cx, cy, w, h = voc_box_to_yolo((0, 0, 100, 50), 1000, 500)
        assert cx == pytest.approx(0.05)
        assert cy == pytest.approx(0.05)
        assert w == pytest.approx(0.1)
        assert h == pytest.approx(0.1)

    def test_values_normalized_to_unit_range(self):
        cx, cy, w, h = voc_box_to_yolo((2900, 1500, 3034, 1586), 3034, 1586)
        for v in (cx, cy, w, h):
            assert 0.0 <= v <= 1.0


class TestParseVocXml:
    @pytest.fixture
    def sample_xml(self, tmp_path: Path) -> Path:
        content = textwrap.dedent("""\
            <annotation>
                <filename>01_mouse_bite_08.jpg</filename>
                <size><width>3034</width><height>1586</height><depth>3</depth></size>
                <object>
                    <name>mouse_bite</name>
                    <bndbox>
                        <xmin>1018</xmin><ymin>1281</ymin><xmax>1058</xmax><ymax>1318</ymax>
                    </bndbox>
                </object>
                <object>
                    <name>mouse_bite</name>
                    <bndbox>
                        <xmin>837</xmin><ymin>1099</ymin><xmax>874</xmax><ymax>1147</ymax>
                    </bndbox>
                </object>
            </annotation>
        """)
        p = tmp_path / "01_mouse_bite_08.xml"
        p.write_text(content)
        return p

    def test_parses_filename_and_size(self, sample_xml: Path):
        filename, width, height, objects = parse_voc_xml(sample_xml)
        assert filename == "01_mouse_bite_08.jpg"
        assert (width, height) == (3034, 1586)

    def test_parses_all_objects(self, sample_xml: Path):
        _, _, _, objects = parse_voc_xml(sample_xml)
        assert len(objects) == 2
        name, box = objects[0]
        assert name == "mouse_bite"
        assert box == (1018, 1281, 1058, 1318)


class TestClasses:
    def test_canonical_class_order(self):
        assert CLASSES == [
            "missing_hole",
            "mouse_bite",
            "open_circuit",
            "short",
            "spur",
            "spurious_copper",
        ]
