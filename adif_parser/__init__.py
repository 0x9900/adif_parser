#! /usr/bin/env python
# vim:fenc=utf-8
#
# Copyright © 2024-2026 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import IO, Any, Callable, Dict, Iterator, List, TypeAlias, TypeVar
from xml.dom import minidom

__version__ = "0.2.3"
__comment__ = 'This ADIF file was created by https://github.com/0x9900/adif_parser'

ADIF_VERSION = "3.1.7"

# Pre-compiled regexes (moved outside class for reuse)
TAG_PATTERN = re.compile(r'<([^:>]+):(\d+)>([^<]*)')
EOH_PATTERN = re.compile(r'<eoh>', re.IGNORECASE)
EOR_PATTERN = re.compile(r'<eor>', re.IGNORECASE)

T = TypeVar('T')
ARecord: TypeAlias = Dict[str, str | int | float]
AData: TypeAlias = List[ARecord]


def try_convert(val: Any, converter: Callable[[Any], T]) -> str | T:
  try:
    return converter(val)
  except ValueError:
    return val


class ParseADIF:
  # Set for O(1) lookups instead of tuple checks
  FLOAT_TAGS = frozenset(['FREQ', 'FREQ_RX'])
  NON_FLOAT_TAGS = frozenset(['BAND', 'QSO_DATE', 'TIME_ON', 'QSO_DATE_OFF', 'TIME_OFF'])

  def __init__(self, file_descriptor: IO[str]) -> None:
    self._header: AData | None = None
    self._data: AData | None = None

    text = file_descriptor.read()
    self.parse_adif(text)

  def __iter__(self) -> Iterator[ARecord]:
    """ The iteration will be empty if there is no data """
    if self._data is None:
      return iter([])
    return iter(self._data)

  def _new_header(self) -> dict:
    timestamp = datetime.now()
    header = {
      'ADIF_VER': ADIF_VERSION,
      'CREATED_TIMESTAMP': timestamp.strftime('%Y%m%d %H%M%S'),
      'PROGRAMID': 'parse_adif',
      'PROGRAMVERSION': __version__,
    }
    return header

  def write(self, file_descriptor: IO[str]) -> None:
    header = self._new_header()

    # write the header
    print(__comment__, file=file_descriptor)

    for key, val in header.items():
      print(self.encode(key, val), file=file_descriptor)

    print('<EOH>', file=file_descriptor)

    # write the records
    if self._data is None:
      return

    for contact in self._data:
      record = []
      for key, val in contact.items():
        record.append(self.encode(key, val))
      print(' '.join(record), end=' <EOR>\n', file=file_descriptor)

  def write_xml(self, file_descriptor: IO[str]) -> None:
    """Create XML with attributes"""
    header_data = self._new_header()
    root = ET.Element('ADX')

    # write the header
    header = ET.SubElement(root, 'HEADER')

    for key, value in header_data.items():
      child = ET.SubElement(header, key)
      child.text = str(value)

    records = ET.SubElement(root, 'RECORDS')
    for item in self._data:
      record = ET.SubElement(records, 'RECORD')
      for key, value in item.items():
        child = ET.SubElement(record, key)
        child.text = str(value)

    xml_string = ET.tostring(root, encoding='unicode')
    final_xml = f'<?xml version="1.0" ?>\n<!-- {__comment__} -->\n{xml_string}\n'
    dom = minidom.parseString(final_xml)
    print(dom.toprettyxml(indent="  "), file=file_descriptor)

  @staticmethod
  def encode(key: str, val: str | int | float):
    if isinstance(val, str):
      val = val.strip()
    elif isinstance(val, (int, float)):
      val = str(val)

    return f'<{key.upper()}:{len(val)}>{val}'

  @property
  def header(self) -> AData:
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
      self._header = ParseADIF.parse_lines(parts[0])
      self._data = ParseADIF.parse_lines(parts[1])
    else:
      self._data = ParseADIF.parse_lines(parts[0])

  @staticmethod
  def parse_lines(data: str) -> AData:
    records = []

    # Split records based on <eor>
    raw_records = EOR_PATTERN.split(data)

    for raw_record in raw_records:
      record = {}
      # Use finditer directly
      for match in TAG_PATTERN.finditer(raw_record):
        tag_name, length_str, _ = match.groups()  # ignore the regex-captured value
        length = int(length_str)
        value_start = match.start(3)  # start of group 3 in the original string
        value = raw_record[value_start:value_start + length]

        tag_name = tag_name.strip().upper()
        if tag_name in ParseADIF.FLOAT_TAGS:
          value = try_convert(value, float)
        elif tag_name not in ParseADIF.NON_FLOAT_TAGS:
          value = try_convert(value, int)

        record[tag_name] = value

      if record:
        records.append(record)

    return records
