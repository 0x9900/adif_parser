#! /usr/bin/env python
# vim:fenc=utf-8
#
# Copyright © 2024 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

import re
from typing import IO, Any, Callable, Dict, List, TypeAlias, TypeVar

# Pre-compiled regexes (moved outside class for reuse)
TAG_PATTERN = re.compile(r'<([^:>]+):(\d+)>([^<]*)')
EOH_PATTERN = re.compile(r'<eoh>', re.IGNORECASE)
EOR_PATTERN = re.compile(r'<eor>', re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r'\s+')

# Set for O(1) lookups instead of tuple checks
FLOAT_TAGS = frozenset(['FREQ', 'FRED_RX'])
NON_FLOAT_TAGS = frozenset(['BAND', 'QSO_DATE', 'TIME_ON', 'QSO_DATE_OFF', 'TIME_OFF'])

T = TypeVar('T')
AData: TypeAlias = List[Dict[Any, Any]]


def try_convert(val: Any, converter: Callable[[Any], T]) -> Any | T:
  try:
    return converter(val)
  except ValueError:
    return val


class ParseADIF:
  def __init__(self, file_descriptor: IO[str]) -> None:
    self._header: AData | None
    self._data: AData | None

    text = file_descriptor.read()
    self.parse_adif(text)

  def write(self, file_descriptor: IO[str]) -> None:
    print('This ADIF file was created by https://github.com/0x9900/adif_parser',
          file=file_descriptor)
    for key, val in self.header[0].items():
      print(self.encode(key, val), file=file_descriptor)
    print('<EOH>')
    for contact in self.contacts:
      record = []
      for key, val in contact.items():
        record.append(self.encode(key, val))
      print(' '.join(record), file=file_descriptor)

  @staticmethod
  def encode(key: str, val: str | int | float):
    if isinstance(val, str):
      val = val.strip()
    elif isinstance(val, (int, float)):
      val = str(val)

    return f'<{key.upper()}:{len(val)}>{val}'

  @property
  def header(self) -> AData:
    assert self._header
    return self._header

  @property
  def contacts(self) -> AData:
    assert self._data
    return self._data

  def parse_adif(self, text: str) -> None:
    # Normalize whitespace in one pass
    text = WHITESPACE_PATTERN.sub(' ', text.strip())

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
        tag_name, _length, value = match.groups()
        # Strip only once and convert to upper
        value = value.strip()
        if not value:
          continue

        tag_name = tag_name.strip().upper()
        if tag_name in FLOAT_TAGS:
          value = try_convert(value, float)
        elif tag_name not in NON_FLOAT_TAGS:
          value = try_convert(value, int)

        record[tag_name] = value

      if record:
        records.append(record)

    return records
