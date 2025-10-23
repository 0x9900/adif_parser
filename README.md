# ADIF Parser

A Python library for parsing ADIF (Amateur Data Interchange Format) files used in amateur radio.

## What Does This Library Do?

`adif_parser` is a Python library that reads and parses ADIF files, converting them into structured data.

## Installation

```bash
pip install adif-parser
```

Or install from source:

```bash
git clone https://github.com/0x9900/adif_parser.git
cd adif_parser
pip install .
```

## Usage

### Basic Example

```python
from adif_parser import parse_adif

# Parse an ADIF file
with open('logbook.adi', 'r') as f:
    records = parse_adif(f)

# Iterate through contacts
for record in records:
    print(f"Callsign: {record.get('CALL')}")
    print(f"Date: {record.get('QSO_DATE')}")
    print(f"Time: {record.get('TIME_ON')}")
    print(f"Frequency: {record.get('FREQ')}")
    print(f"Mode: {record.get('MODE')}")
    print("---")
```

## Common ADIF Fields

The parser extracts standard ADIF fields including:

- `CALL`: Callsign contacted
- `QSO_DATE`: Date of contact (YYYYMMDD)
- `TIME_ON`: Start time of contact (HHMMSS)
- `BAND`: Operating band (e.g., "20M", "40M")
- `FREQ`: Operating frequency in MHz
- `MODE`: Operating mode (e.g., "SSB", "CW", "FT8")
- `RST_SENT`: Signal report sent
- `RST_RCVD`: Signal report received
- `NAME`: Name of operator contacted
- `QTH`: Location of station contacted
- `GRIDSQUARE`: Maidenhead grid square
- `COUNTRY`: DXCC entity name
- `STATE`: State/province
- And many more defined in the ADIF specification

## Use Cases

This library is useful for:

- Converting ADIF logs to other formats (CSV, JSON, databases)
- Analyzing amateur radio contact logs
- Building statistics and visualizations from logbook data
  - https://bsdworld.org/misc/FD-Stats-W6UQ-2025.html
- Migrating data between different logging programs
- Creating custom reporting tools
- Award tracking and verification
- Contest log processing

Example ADIF format:
```
<CALL:6>W1AW <QSO_DATE:8>20231015 <TIME_ON:6>143000 <BAND:3>20M <MODE:3>SSB <EOR>
```

## License

See the LICENSE file in the repository for license information.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on GitHub.

## Links

- GitHub Repository: https://github.com/0x9900/adif_parser
- ADIF Specification: https://adif.org/

## Support

For questions, bug reports, or feature requests, please open an issue on the GitHub repository.
