#!/usr/bin/env python
# vim:fenc=utf-8
#
# Copyright © 2026 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

"""Test program for ADIF parser."""

import argparse
import sys
import traceback
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from adif_parser import ADIFWriter, ParseADIF


@dataclass
class QSORecord:
  """Represents a single QSO record for testing."""
  # pylint: disable=too-many-instance-attributes
  call: str
  freq: float
  qso_date: str
  time_on: str
  time_off: str
  band: str
  rst_sent: str = "599"
  rst_rcvd: str = "599"
  mode: str = "CW"
  note: str = ""
  comment: str = ""

  def __str__(self):
    qso_parts = []
    attribute_names = list(self.__dataclass_fields__.keys())  # pylint: disable=no-member
    for attr in attribute_names:
      value = str(getattr(self, attr))
      qso_parts.append(ADIFWriter.encode(attr, value))

    qso_parts.append("<EOR>")
    return ' '.join(qso_parts)


class ADIFTestData:
  """Manages test data for ADIF parser testing."""
  # pylint: disable=too-few-public-methods

  NOTE_TEXT = "Operating portable from the park\r\nSunny conditions, light wind\r\n73, John"
  QSO_RECORDS = [
    QSORecord("YT1A", 14.02, "20250125", "071826", "071826", "22M"),
    QSORecord("F4KIY", 14.0359, "20250125", "071343", "071343", "20M", comment="Radio world"),
    QSORecord("F4VOX", 14.0361, "20250125", "071611", "071611", "20M", comment="Great signal"),
    QSORecord("LZ2MP", 14.02, "20250125", "071850", "071850", "20M"),
    QSORecord("RX4HJ", 14.02, "20250125", "071910", "071910", "20M"),
    QSORecord("R4AY", 14.02, "20250125", "072034", "072034", "20M"),
    QSORecord("R3LC", 14.02, "20250125", "072059", "072059", "20M"),
    QSORecord("YQ8E", 14.02, "20250125", "072128", "072128", "20M"),
    QSORecord("YO3GNF", 14.02, "20250125", "072157", "072157", "20M"),
    QSORecord("R6DMT", 14.02, "20250125", "072234", "072234", "20M"),
    QSORecord("F8GAF", 3.73, "20250222", "060011", "060011", "80M", "59", "59", "SSB"),
    QSORecord("F5TYQ", 3.73, "20250222", "060020", "060020", "80M", "59", "59", "SSB"),
    QSORecord("PE1EWR", 3.73, "20250222", "060055", "060055", "80M", "59", "59", "SSB"),
    QSORecord("F4KJN", 3.73, "20250222", "060106", "060106", "80M", "59", "59", "SSB"),
    QSORecord("F8CRS", 3.73, "20250222", "060121", "060121", "80M", "59", "59", "SSB"),
    QSORecord("TM3P", 3.73, "20250222", "060132", "060132", "80M", "59", "59", "SSB"),
    QSORecord("SE4E", 7.106, "20250222", "062221", "062221", "40M", "59", "59", "SSB"),
    QSORecord("F4BDG", 3.73, "20250222", "062236", "062236", "80M", "59", "59", "SSB"),
    QSORecord("DC5CH", 7.106, "20250222", "062239", "062239", "40M", "59", "59", "SSB"),
    QSORecord("W1AW", 7.106, "20260531", "1230", "1230", "40M", "59", "59", "SSB", note=NOTE_TEXT),
    QSORecord("N0CALL", 14.200, "20230101", "1230", "1230", "20M", "59", "59", "SSB"),
    QSORecord("W1XYZ", 7.020, "20230102", "1000", "1000", "40M", "59", "59", "CW"),
  ]

  HEADER = {
    'PROGRAMID': 'DXLOG',
    'PROGRAMVERSION': '2.6.13',
    'CREATED_TIMESTAMP': '20250223 180506',
    'ADIF_VER': '3.1.5'
  }

  @classmethod
  def generate_adif_log(cls) -> str:
    """Generate ADIF log string from test records."""
    lines = [
      "Log exported from DXLog.net v2.6.13 at 2025-02-23 18:05:06Z",
      "<PROGRAMID:5>DXLOG",
      "<PROGRAMVERSION:6>2.6.13",
      "<CREATED_TIMESTAMP:15>20250223 180506",
      "<ADIF_VER:5>3.1.5",
      "<EOH>"
    ]

    for record in cls.QSO_RECORDS:
      lines.append(str(record))

    return "\n".join(lines)


class ADIFTestRunner:
  """Runs tests on ADIF parser functionality."""

  def __init__(self):
    self.test_data = ADIFTestData()
    self.log_content = self.test_data.generate_adif_log()

  def test_header(self, parser: ParseADIF) -> bool:
    """Test header parsing."""
    for key, expected_value in self.test_data.HEADER.items():
      actual_value = parser.header.get(key)
      assert actual_value == expected_value, (f"Header mismatch: {key} "
                                              f"expected '{expected_value}' "
                                              f"got '{actual_value}'")

    print("✓ Header validation passed")
    return True

  def test_qso_records(self, parser: ParseADIF) -> int:
    """Test QSO record parsing against expected data."""
    records_tested = 0

    for idx, (actual, expected) in enumerate(zip(parser, self.test_data.QSO_RECORDS)):
      records_tested = idx

      # Validate each field
      assert actual.get('CALL') == expected.call, f"Record {idx}: CALL mismatch"
      assert actual.get('BAND') == expected.band, f"Record {idx}: BAND mismatch"
      assert float(actual.get('FREQ', 0)) == expected.freq, f"Record {idx}: FREQ mismatch"
      assert actual.get('QSO_DATE') == expected.qso_date, f"Record {idx}: QSO_DATE mismatch"
      assert actual.get('TIME_ON') == expected.time_on, f"Record {idx}: TIME_ON mismatch"
      assert actual.get('TIME_OFF') == expected.time_off, f"Record {idx}: TIME_OFF mismatch"
      assert actual.get('COMMENT') == expected.comment, f"Record {idx}: COMMENT mismatch"

      # Validate optional fields
      if expected.note:
        assert actual.get('NOTE') == expected.note, f"Record {idx}: NOTE mismatch"

    print(f"✓ {records_tested + 1} QSO records validated successfully")
    return records_tested + 1

  def test_write_output(self, parser: ParseADIF, output_dir: Path) -> None:
    """Test writing output files."""
    writer = ADIFWriter(parser)
    output_dir.mkdir(exist_ok=True)

    test_formats = [
      ("ADIF", writer.write, ".adi"),
      ("XML", writer.write_xml, ".xml"),
      ("CSV", writer.write_csv, ".csv"),
    ]
    adif_path = output_dir / "adif_test"

    for fmt, method, suffix in test_formats:
      filepath = adif_path.with_suffix(suffix)
      method(filepath)
      print(f"✓ {fmt} file written to {filepath}")

  def run_all_tests(self, output_dir: Path = Path("/tmp")) -> bool:
    """Run all tests and return success status."""
    print("=" * 60)
    print("ADIF Parser Test Suite")
    print("=" * 60)
    try:
      with StringIO(self.log_content) as fd:
        parser = ParseADIF(fd)

        self.test_header(parser)
        record_count = self.test_qso_records(parser)
        self.test_write_output(parser, output_dir)

        print("\n" + "=" * 60)
        print("All tests passed successfully!")
        print(f"Processed {record_count} QSO records")
        print("=" * 60)
      return True

    except AssertionError as e:
      print(f"\nTest failed: {e}")
      return False
    except Exception as e:  # pylint: disable=broad-exception-caught
      print(f"\nUnexpected error: {e}")
      traceback.print_exc()
      return False


def main():
  """Main entry point for the test program."""

  parser = argparse.ArgumentParser(description="Test ADIF parser functionality")
  parser.add_argument("--output-dir", type=Path, default=Path("/tmp"),
                      help="Directory for output files (default: /tmp)")
  args = parser.parse_args()

  # Run tests
  runner = ADIFTestRunner()
  success = runner.run_all_tests(args.output_dir)

  # Exit with appropriate code
  sys.exit(0 if success else 1)


if __name__ == "__main__":
  main()
