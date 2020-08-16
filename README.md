# Mondrian Cube Schema Documentation Generator

A command line utility based on Python that parses the schema definition for mondrian cubes and generates a html documentation based on the described metadata.

## Requirements

### Python Version
You need Python 2.7 to run the tool.

### Libraries
You need to have the Python library `lxml` installed.

## Usage


## Limitations
- The parser doesn't handle join clauses inside dimension definitions.
- Full dimension definitions inside cubes are not handled as well.

## Possible improvements
- Modify the script to work with Python 3.
- Output documentation as a markdown file.

## Credits

The bootstrap template used in this project was based on this [one](https://bootsnipp.com/snippets/7XqNK) created by the user [travislaynewilson](https://bootsnipp.com/travislaynewilson).
