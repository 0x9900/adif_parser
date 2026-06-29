#! /usr/bin/env python
# vim:fenc=utf-8
#
# Copyright © 2024-2026 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

import csv
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Callable, Dict, Iterator, List, TypeAlias
from xml.dom import minidom

__version__ = "0.2.5"
__comment__ = 'This ADIF file was created by https://github.com/0x9900/adif_parser'

ADIF_VERSION = "1.8"

# Pre-compiled regexes (moved outside class for reuse)
TAG_PATTERN = re.compile(r'<([^:>]+):(\d+)>([^<]*)')
EOH_PATTERN = re.compile(r'<eoh>', re.IGNORECASE)
EOR_PATTERN = re.compile(r'<eor>', re.IGNORECASE)

AValues: TypeAlias = str | int | float
ARecord: TypeAlias = Dict[str, AValues]
AData: TypeAlias = List[ARecord]


def try_convert_to_numeric(val: Any, converter: Callable[[Any], AValues]) -> AValues:
  try:
    return converter(val)
  except ValueError:
    return val


class ParseADIF:
  # Set for O(1) lookups instead of tuple checks
  FLOAT_TAGS = frozenset(['FREQ', 'FREQ_RX'])
  NON_FLOAT_TAGS = frozenset(['BAND', 'QSO_DATE', 'TIME_ON', 'QSO_DATE_OFF', 'TIME_OFF'])

  def __init__(self, file_descriptor: IO[str]) -> None:
    self._header: ARecord | None = None
    self._data: AData | None = None

    text = file_descriptor.read()
    self.parse_adif(text)

  def __iter__(self) -> Iterator[ARecord]:
    """ The iteration will be empty if there is no data """
    if self._data is None:
      return iter([])
    return iter(self._data)

  @property
  def header(self) -> ARecord:
    if self._header is None:
      raise ValueError('No header found in the ADIF file')
    return self._header

  @property
  def contacts(self) -> AData:
    if self._data is None:
      raise ValueError('No data found in the ADIF file')
    return self._data

  def parse_adif(self, text: str) -> None:
    # Split on <eoh>
    parts = EOH_PATTERN.split(text, maxsplit=1)

    if len(parts) == 2:
      self._header = ParseADIF.parse_lines(parts[0]).pop()
      self._data = ParseADIF.parse_lines(parts[1])
    else:
      self._data = ParseADIF.parse_lines(parts[0])

  @staticmethod
  def parse_one_line(raw_record: str) -> dict:
    """Parse a single raw ADIF record into a dictionary of tags and values."""
    record = {}

    try:
      for match in TAG_PATTERN.finditer(raw_record):
        tag_name, length_str, _ = match.groups()  # ignore the regex-captured value
        length = int(length_str)
        value_start = match.start(3)  # start of group 3 in the original string
        value: AValues = raw_record[value_start:value_start + length]

        tag_name = tag_name.strip().upper()
        if tag_name in ParseADIF.FLOAT_TAGS:
          value = try_convert_to_numeric(value, float)
        elif tag_name not in ParseADIF.NON_FLOAT_TAGS:
          value = try_convert_to_numeric(value, int)

        record[tag_name] = value

    except (ValueError, IndexError) as err:
      raise ValueError(f"Malformed ADIF record: {raw_record}") from err

    return record

  @staticmethod
  def parse_lines(data: str) -> AData:
    """Parse ADIF data containing multiple records separated by <eor>."""
    records = []

    # Split records based on <eor>
    raw_records = EOR_PATTERN.split(data)

    for raw_record in raw_records:
      if not raw_record:  # Skip empty records
        continue
      if record := ParseADIF.parse_one_line(raw_record):
        records.append(record)

    return records


class ADIFWriter:

  def __init__(self, adif: ParseADIF) -> None:
    self.header: ARecord | None = self._new_header()
    self.contacts: AData | None = adif.contacts

  def write(self, filename: str | Path) -> None:
    if isinstance(filename, str):
      filename = Path(filename)

    with filename.open('w', newline="", encoding='utf-8') as fd:
      # write the header
      print(__comment__, file=fd)
      header: dict = self.header or {}
      for key, val in header.items():
        print(self.encode(key, val), file=fd)
      print('<EOH>', file=fd)

      # write the records
      data = self.contacts or []
      for contact in data:
        record = []
        for key, val in [(k, str(v)) for k, v in contact.items()]:
          record.append(self.encode(key, val))
        print(' '.join(record), end=' <EOR>\n', file=fd)

  def write_xml(self, filename: Path) -> None:
    """Write an XML file"""
    if isinstance(filename, str):
      filename = Path(filename)

    root = ET.Element('ADX')

    # write the header
    xml_header = ET.SubElement(root, 'HEADER')
    adi_header: dict = self.header or {}
    for key, value in adi_header.items():
      child = ET.SubElement(xml_header, key)
      child.text = str(value)

    records = ET.SubElement(root, 'RECORDS')
    data = self.contacts or []
    for item in data:
      record = ET.SubElement(records, 'RECORD')
      for key, value in [(k, str(v)) for k, v in item.items()]:
        child = ET.SubElement(record, key)
        child.text = str(value)

    xml_string = self.xml_to_string(root)
    with filename.open('w', encoding='utf-8') as fd:
      print(xml_string, file=fd)

  def write_csv(self, filename: Path) -> None:
    """Write a CSV file"""
    if isinstance(filename, str):
      filename = Path(filename)

    data = self.contacts or []
    fieldnames = sorted({key for row in data for key in row})

    with filename.open('w', newline='', encoding='utf-8') as fd:
      print(f'# {__comment__}', file=fd)
      header: dict = self.header or {}
      for key, value in header.items():
        print(f'# {key}: {value}', file=fd)

      writer = csv.DictWriter(fd, fieldnames=fieldnames)
      writer.writeheader()
      writer.writerows(data)

  @staticmethod
  def _new_header() -> ARecord | None:
    timestamp = datetime.now()
    header: ARecord = {
      'ADIF_VER': ADIF_VERSION,
      'CREATED_TIMESTAMP': timestamp.strftime('%Y%m%d %H%M%S'),
      'PROGRAMID': 'parse_adif',
      'PROGRAMVERSION': __version__,
    }
    return header

  @staticmethod
  def encode(key: str, val: AValues):
    if isinstance(val, str):
      val = val.strip()
    elif isinstance(val, (int, float)):
      val = str(val)

    return f'<{key.upper()}:{len(val)}>{val}'

  @staticmethod
  def xml_to_string(root: ET.Element) -> str:
    xml_string = ET.tostring(root, encoding='unicode')
    final_xml = f'<?xml version="1.0" ?>\n<!-- {__comment__} -->\n{xml_string}\n'
    dom = minidom.parseString(final_xml)
    return dom.toprettyxml(indent="  ")
