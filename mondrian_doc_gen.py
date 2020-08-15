from lxml import etree
from io import open
import glob
import argparse
import sys
import os


def generate_html_cube(cube_id, cube_table, cube_name, cube_description, cube_dimensions, cube_measures):
    base_html = ''
    with open("documentation_cube_header.html", "r") as t:
        base_html = t.read()
        base_html = base_html.replace('%{cube.id}', cube_id)
        base_html = base_html.replace('%{cube.table}', cube_table)
        base_html = base_html.replace('%{cube.name}', cube_name)
        base_html = base_html.replace('%{cube.description}', cube_description)
        base_html = base_html.replace('%{cube.dimensions}', cube_dimensions)
        base_html = base_html.replace('%{cube.measures}', cube_measures)

    return base_html


def generate_html_cube_level(level_name, level_type, level_description, level_column):
    base_html = ''
    with open("documentation_cube_levels.html", "r") as t:
        base_html = t.read()
        base_html = base_html.replace('%{level.name}', level_name)
        base_html = base_html.replace('%{level.type}', level_type)
        base_html = base_html.replace(
            '%{level.description}', level_description)
        base_html = base_html.replace('%{level.column}', level_column)

    return base_html


def generate_html_dim_level(level_name, level_type, level_description, level_column):
    base_html = ''
    with open("documentation_dim_levels.html", "r") as t:
        base_html = t.read()
        base_html = base_html.replace('%{level.name}', level_name)
        base_html = base_html.replace('%{level.type}', level_type)
        base_html = base_html.replace(
            '%{level.description}', level_description)
        base_html = base_html.replace('%{level.column}', level_column)

    return base_html


def generate_html_dimension(dim_id, dim_table, dim_name, dim_description, dim_levels):
    base_html = ''
    with open("documentation_dim_header.html", "r") as t:
        base_html = t.read()
        base_html = base_html.replace('%{dimension.id}', dim_id)
        base_html = base_html.replace('%{dimension.table}', dim_table)
        base_html = base_html.replace('%{dimension.name}', dim_name)
        base_html = base_html.replace(
            '%{dimension.description}', dim_description)
        base_html = base_html.replace('%{dimension.levels}', dim_levels)

    return base_html


def generate_html(schema_name, schema_description, num_cubes, cube_body, num_dimensions, dim_body):
    base_html = ''
    with open("documentation_wrapper.html", "r") as t:
        base_html = t.read()
        base_html = base_html.replace('%{schema.name}', schema_name)
        base_html = base_html.replace(
            '%{schema.description}', schema_description)
        base_html = base_html.replace('%{schema.num_cubes}', str(num_cubes))
        base_html = base_html.replace(
            '%{schema.num_dimensions}', str(num_dimensions))
        base_html = base_html.replace('%{cubes.body}', cube_body)
        base_html = base_html.replace('%{dimensions.body}', dim_body)

    return base_html


def parse_file(file_name, output_dir):
    document = etree.parse(file_name)

    schema_name = document.getroot().get('name')
    schema_description = str(document.getroot().get('description') or '')

    cubes_html = ''
    dimensions_html = ''
    dimensions_dict = {}
    documentation_html = ''
    num_cubes = 0
    num_dimensions = 0

    # HANDLING DIMENSIONS
    for dim in sorted(document.xpath("/Schema/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
        dimension_level_html = ''

        dim_name = dim.get('name')
        dim_caption = dim.get('caption', '')
        dim_description = dim.get('description', '')
        dim_table = dim.find('Hierarchy/Table').get('name', 'Undefined')

        for lvl in dim.iter("Level"):
            name = lvl.get('name')
            caption = lvl.get('caption', '')
            type = lvl.get('type', '')
            description = lvl.get('description', '')
            column = lvl.get('column', '')
            #print(name, caption, type, description, column)

            dimension_level_html += generate_html_dim_level(
                caption if caption != '' else name, type, description, column)
            num_dimensions += 1

        dimensions_dict[dim_name] = {
            'table': dim_table, 'caption': dim_caption, 'description': dim_description, 'usage': ''}
        dimensions_html += generate_html_dimension(
            dim_name, dim_table, dim_caption if dim_caption != '' else dim_name, dim_description, dimension_level_html)

    # HANDLING DEGENERATED DIMENSIONS
    for dim in sorted(document.xpath("/Schema/Cube/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
        dimension_level_html = ''

        dim_caption = dim.get('caption', '')
        dim_description = dim.get('description', '')
        dim_table = dim.find('../Table').get('name', 'Undefined')
        dim_name = dim.get('name')
        dim_identifier = dim_table + '.' + dim_name

        for lvl in dim.iter("Level"):
            name = lvl.get('name')
            caption = lvl.get('caption', '')
            type = lvl.get('type', '')
            description = lvl.get('description', '')
            column = lvl.get('column', '')
            #print("Degenerated Dimension ", name, caption, type, description, column)

            dimension_level_html += generate_html_dim_level(
                caption if caption != '' else name, type, description, column)
            num_dimensions += 1

        dimensions_dict[dim_identifier] = {
            'table': dim_table, 'caption': dim_caption, 'description': dim_description, 'usage': ''}
        dimensions_html += generate_html_dimension(dim_identifier, dim_table, dim_caption if dim_caption !=
                                                   '' else dim_name, dim_description, dimension_level_html)

    # HANDLING CUBES
    for cube in sorted(document.xpath("/Schema/Cube"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
        cube_dimensions_html = ''
        cube_measures_html = ''

        cube_name = cube.get('name')
        cube_caption = cube.get('caption', '')
        cube_description = cube.get('description', '')
        cube_table = cube.find('Table').get('name', 'Undefined')

        for dim_usage in cube.iter("DimensionUsage"):
            name = dim_usage.get('name')
            caption = dim_usage.get('caption', '')
            source = dim_usage.get('source')
            type = 'Dimension'
            description = dim_usage.get('description', '')
            column = dim_usage.get('foreignKey', '')
            #print(name, caption, type, description, column)

            # Getting caption and description from the dimension definition in case it was not overrided in the cube
            caption = caption if caption != '' else dimensions_dict[source]['caption']
            description = description if description != '' else dimensions_dict[
                source]['description']
            dimensions_dict[source]['usage'] += (cube_name + ', ')

            table_caption = caption if caption != '' else name
            dimension_link = '<a href="#' + source + '">' + table_caption + '</a>'

            cube_dimensions_html += generate_html_cube_level(
                dimension_link, type, description, column)

        for dim_deg in cube.iter("Dimension"):
            name = dim_deg.get('name')
            caption = dim_deg.get('caption', '')
            source = cube_table + '.' + dim_deg.get('name')
            type = 'Degenerated Dimension'
            description = dim_deg.get('description', '')
            column = '--'
            #print(name, caption, type, description, column)

            dimensions_dict[source]['usage'] += (cube_name + ', ')

            table_caption = caption if caption != '' else name
            dimension_link = '<a href="#' + source + '">' + table_caption + '</a>'

            cube_dimensions_html += generate_html_cube_level(
                dimension_link, type, description, column)

        for measure in cube.iter("Measure"):
            name = measure.get('name')
            caption = measure.get('caption', '')
            type = 'Measure'
            description = measure.get('description', '')
            column = measure.get('column', '')
            visible = measure.get('visible', '')
            #print(name, caption, type, description, column)

            if visible != 'false':
                cube_measures_html += generate_html_cube_level(
                    caption if caption != '' else name, type, description, column)

        for c_measure in cube.iter("CalculatedMember"):
            name = c_measure.get('name')
            caption = c_measure.get('caption', '')
            type = 'Calculated Measure'
            description = c_measure.get('description', '')
            column = '--'
            #print(name, caption, type, description)

            cube_measures_html += generate_html_cube_level(
                caption if caption != '' else name, type, description, column)

        cubes_html += generate_html_cube(cube_name, cube_table, cube_caption if cube_caption !=
                                         '' else cube_name, cube_description, cube_dimensions_html, cube_measures_html)
        num_cubes += 1

    documentation_html = generate_html(
        schema_name, schema_description, num_cubes, cubes_html, num_dimensions, dimensions_html)

    print(file_name + " unused dimensions:")
    print({k: v for k, v in dimensions_dict.iteritems() if v['usage'] == ''})

    with open("output/documentation_" + file_name[0:file_name.rfind('.')] + ".html", "w", encoding="utf-8") as d:
        d.write(documentation_html)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        epilog='Example command: python mondian_doc_gen.py --schema_file "steelwheels.mondrian.xml" --output_dir "output/" ')
    parser.add_argument('--schema_file', '-s',
                        help='The path for the input schema file that will be parsed', required=True)
    parser.add_argument(
        '--output_dir', '-o', help='The path to the directory where the output documentation will be stored', required=True)

    try:
        args = parser.parse_args()

        print(args)

        parse_file(args.schema_file, args.output_dir)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)
