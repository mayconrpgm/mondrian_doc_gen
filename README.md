# Mondrian Cube Schema Documentation Generator

A command line utility based on Python that parses the schema definition for mondrian cubes and generates a reposive HTML documentation based on the described metadata.

It reads the tables and columns definitions for cubes and dimensions and describe then using the `caption` and `description` tags inside each element to describe then in the documentation.

![](mondrian_doc_gen.gif)

## Requirements

### Python Version
You need Python 3.5+ to run the tool.

### Libraries
You need to have the Python library `lxml` installed.

## Usage
The usage is rather simple, all you have to do is call the python script `mondrian_doc_gen.py` passing the following parameters:

### _--schema_file_, -s
The path to the mondrian schema xml file.

### _--output_dir_, -o
The path to the directory where the documentation file will be recorded. The name of the documentation file will be documentation_\<schema file name without the extension\>.html.

### _--templates_dir_, -t
The path where the documentation templates are located. In this project there's a folder called `templates_html` contained the default ones. You may create your own templates if you need based on these.

Find below an example to create a documetantion for the schema file **steelwheels.mondrian.xml** and outputting it to the **output** directory using the templates located at the **templates_html** folder:

`python mondrian_doc_gen.py -s "steelwheels.mondrian.xml" -o "output/" -t "templates_html/"`

## Limitations
- The parser doesn't handle join clauses inside dimension definitions.
- Full dimension definitions inside cubes are not handled as well, only single column definitions and they are flagged as degenerated dimensions.
- Properties specific for Pentaho Analyser are not considered.

## Possible improvements
- Output documentation as a markdown file.
- Better error handling

## Credits

The bootstrap template used in this project was based on this [one](https://bootsnipp.com/snippets/7XqNK) created by the user [travislaynewilson](https://bootsnipp.com/travislaynewilson).
