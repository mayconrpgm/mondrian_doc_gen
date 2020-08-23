from lxml import etree
from io import open
from pathlib import Path


class MondrianDocumentationBuilder(object):
    __templates_folder = ''
    __dimensions_dict = {}
    __dimensions_code = ''
    __num_dimensions = 0
    __cubes_code = ''
    __num_cubes = 0
    __documentation_code = ''

    def __init__(self, templates_folder):
        self.__templates_folder = templates_folder

    def __generate_code_cube(self, cube_id, cube_table, cube_schema, cube_name, cube_description, cube_dimensions, cube_measures):
        base_code = ''
        template_path = Path(self.__templates_folder +
                             "/documentation_cube_header.html")
        with open(template_path, "r") as t:
            base_code = t.read()
            base_code = base_code.replace('%{cube.id}', cube_id)
            base_code = base_code.replace('%{cube.table}', cube_table)
            base_code = base_code.replace('%{cube.schema}', cube_schema)
            base_code = base_code.replace('%{cube.name}', cube_name)
            base_code = base_code.replace(
                '%{cube.description}', cube_description)
            base_code = base_code.replace(
                '%{cube.dimensions}', cube_dimensions)
            base_code = base_code.replace('%{cube.measures}', cube_measures)

        return base_code

    def __generate_code_cube_level(self, level_name, level_type, level_description, level_column):
        base_code = ''
        template_path = Path(self.__templates_folder +
                             "/documentation_cube_levels.html")
        with open(template_path, "r") as t:
            base_code = t.read()
            base_code = base_code.replace('%{level.name}', level_name)
            base_code = base_code.replace('%{level.type}', level_type)
            base_code = base_code.replace(
                '%{level.description}', level_description)
            base_code = base_code.replace('%{level.column}', level_column)

        return base_code

    def __generate_code_dim_level(self, level_name, level_type, level_description, level_column):
        base_code = ''
        template_path = Path(self.__templates_folder +
                             "/documentation_dim_levels.html")
        with open(template_path, "r") as t:
            base_code = t.read()
            base_code = base_code.replace('%{level.name}', level_name)
            base_code = base_code.replace('%{level.type}', level_type)
            base_code = base_code.replace(
                '%{level.description}', level_description)
            base_code = base_code.replace('%{level.column}', level_column)

        return base_code

    def __generate_code_dimension(self, dim_id, dim_table, dim_schema, dim_name, dim_description, dim_levels):
        base_code = ''
        template_path = Path(self.__templates_folder +
                             "/documentation_dim_header.html")
        with open(template_path, "r") as t:
            base_code = t.read()
            base_code = base_code.replace('%{dimension.id}', dim_id)
            base_code = base_code.replace('%{dimension.table}', dim_table)
            base_code = base_code.replace('%{dimension.schema}', dim_schema)
            base_code = base_code.replace('%{dimension.name}', dim_name)
            base_code = base_code.replace(
                '%{dimension.description}', dim_description)
            base_code = base_code.replace('%{dimension.levels}', dim_levels)

        return base_code

    def __generate_code(self, schema_name, schema_description, num_cubes, cube_body, num_dimensions, dim_body):
        base_code = ''
        template_path = Path(self.__templates_folder +
                             "/documentation_wrapper.html")
        with open(template_path, "r") as t:
            base_code = t.read()
            base_code = base_code.replace('%{schema.name}', schema_name)
            base_code = base_code.replace(
                '%{schema.description}', schema_description)
            base_code = base_code.replace(
                '%{schema.num_cubes}', str(num_cubes))
            base_code = base_code.replace(
                '%{schema.num_dimensions}', str(num_dimensions))
            base_code = base_code.replace('%{cubes.body}', cube_body)
            base_code = base_code.replace('%{dimensions.body}', dim_body)

        return base_code

    def __parse_dimensions(self, schema_document):
        for dim in sorted(schema_document.xpath("/Schema/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            dimension_level_code = ''

            dim_name = dim.get('name')
            dim_caption = dim.get('caption', '')
            dim_description = dim.get('description', '')
            dim_table = dim.find('Hierarchy/Table').get('name', 'Undefined')
            dim_schema = dim.find('Hierarchy/Table').get('schema', 'N/A')

            for lvl in dim.iter("Level"):
                name = lvl.get('name')
                caption = lvl.get('caption', '')
                type = lvl.get('type', '')
                description = lvl.get('description', '')
                column = lvl.get('column', '')
                #print(name, caption, type, description, column)

                dimension_level_code += self.__generate_code_dim_level(
                    caption if caption != '' else name, type, description, column)
            
            self.__num_dimensions += 1

            self.__dimensions_dict[dim_name] = {
                'table': dim_table, 'caption': dim_caption, 'description': dim_description, 'usage': ''}
            self.__dimensions_code += self.__generate_code_dimension(
                dim_name, dim_table, dim_schema, dim_caption if dim_caption != '' else dim_name, dim_description, dimension_level_code)

    def __parse_degenerated_dimensions(self, schema_document):
        for dim in sorted(schema_document.xpath("/Schema/Cube/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            dimension_level_code = ''

            dim_caption = dim.get('caption', '')
            dim_description = dim.get('description', '')
            dim_table = dim.find('../Table').get('name', 'Undefined')
            dim_schema = dim.find('../Table').get('schema', 'N/A')
            dim_name = dim.get('name')
            dim_identifier = dim_table + '.' + dim_name

            for lvl in dim.iter("Level"):
                name = lvl.get('name')
                caption = lvl.get('caption', '')
                type = lvl.get('type', '')
                description = lvl.get('description', '')
                column = lvl.get('column', '')
                #print("Degenerated Dimension ", name, caption, type, description, column)

                dimension_level_code += self.__generate_code_dim_level(
                    caption if caption != '' else name, type, description, column)

            self.__num_dimensions += 1
            self.__dimensions_dict[dim_identifier] = {
                'table': dim_table, 'caption': dim_caption, 'description': dim_description, 'usage': ''}
            self.__dimensions_code += self.__generate_code_dimension(dim_identifier, dim_table, dim_schema, dim_caption if dim_caption !=
                                                                     '' else dim_name, dim_description, dimension_level_code)

    def __parse_cubes(self, schema_document):
        for cube in sorted(schema_document.xpath("/Schema/Cube"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            cube_dimensions_code = ''
            cube_measures_code = ''

            cube_name = cube.get('name')
            cube_caption = cube.get('caption', '')
            cube_description = cube.get('description', '')
            cube_table = cube.find('Table').get('name', 'Undefined')
            cube_schema = cube.find('Table').get('schema', 'N/A')

            for dim_usage in cube.iter("DimensionUsage"):
                name = dim_usage.get('name')
                caption = dim_usage.get('caption', '')
                source = dim_usage.get('source')
                type = 'Dimension'
                description = dim_usage.get('description', '')
                column = dim_usage.get('foreignKey', '')
                #print(name, caption, type, description, column)

                # Getting caption and description from the dimension definition in case it was not overrided in the cube
                caption = caption if caption != '' else self.__dimensions_dict[source]['caption']
                description = description if description != '' else self.__dimensions_dict[
                    source]['description']
                self.__dimensions_dict[source]['usage'] += (cube_name + ', ')

                table_caption = caption if caption != '' else name
                dimension_link = '<a href="#' + source + '">' + table_caption + '</a>'

                cube_dimensions_code += self.__generate_code_cube_level(
                    dimension_link, type, description, column)

            for dim_deg in cube.iter("Dimension"):
                name = dim_deg.get('name')
                caption = dim_deg.get('caption', '')
                source = cube_table + '.' + dim_deg.get('name')
                type = 'Degenerated Dimension'
                description = dim_deg.get('description', '')
                column = '--'
                #print(name, caption, type, description, column)

                self.__dimensions_dict[source]['usage'] += (cube_name + ', ')

                table_caption = caption if caption != '' else name
                dimension_link = '<a href="#' + source + '">' + table_caption + '</a>'

                cube_dimensions_code += self.__generate_code_cube_level(
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
                    cube_measures_code += self.__generate_code_cube_level(
                        caption if caption != '' else name, type, description, column)

            for c_measure in cube.iter("CalculatedMember"):
                name = c_measure.get('name')
                caption = c_measure.get('caption', '')
                type = 'Calculated Measure'
                description = c_measure.get('description', '')
                column = '--'
                #print(name, caption, type, description)

                cube_measures_code += self.__generate_code_cube_level(
                    caption if caption != '' else name, type, description, column)

            self.__cubes_code += self.__generate_code_cube(cube_name, cube_table, cube_schema, cube_caption if cube_caption !=
                                                           '' else cube_name, cube_description, cube_dimensions_code, cube_measures_code)
            self.__num_cubes += 1

    def parse_file(self, file_name, output_dir):
        file_path = Path(file_name)
        document = etree.parse(str(file_path))

        schema_name = document.getroot().get('name')
        schema_description = str(document.getroot().get('description') or '')

        self.__parse_dimensions(document)
        self.__parse_degenerated_dimensions(document)
        self.__parse_cubes(document)

        self.__documentation_code = self.__generate_code(
            schema_name, schema_description, self.__num_cubes, self.__cubes_code, self.__num_dimensions, self.__dimensions_code)

        print(file_name + " unused dimensions:")
        print({k: v for k, v in self.__dimensions_dict.items()
               if v['usage'] == ''})

        output_path = Path(output_dir + "/documentation_" + file_path.stem + '.html')

        with open(output_path, "w", encoding="utf-8") as d:
            d.write(self.__documentation_code)
