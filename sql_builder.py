from lxml import etree
from io import open
from pathlib import Path
import argparse
import sys
import os


class DimensionLevel(object):
    name = ''
    caption = ''
    type = ''
    description = ''
    column = ''

class Dimension(object):
    id = ''
    name = ''
    table = ''
    primary_key = ''
    schema = ''
    caption = ''
    description = ''
    is_degenerated = False
    levels: list[DimensionLevel] = None

    def __init__(self) -> None:
        id = ''
        name = ''
        table = ''
        primary_key = ''
        schema = ''
        caption = ''
        description = ''
        is_degenerated = False
        levels: list[DimensionLevel] = None

    def table_full_name(self):
        return self.schema + '.' + self.table if self.schema != '' else self.table
    
    def add_level(self, level: DimensionLevel):
        if self.levels is None:
            self.levels = []

        self.levels.append(level)

class DimensionUsage(object):
    name = ''
    caption = ''
    source = ''
    description = ''
    foreign_key: str = None
    dimension: Dimension = None

class Measure(object):
    name = ''
    caption = ''
    description = ''
    column = ''
    aggregator = ''
    is_visible = True

class Cube(object):
    id = ''
    table = ''
    schema = ''
    caption = ''
    description = ''
    dimensions_usage: list[DimensionUsage] = []
    measures: list[Measure] = []
    aliases: dict[str, str] = {}

    def __build_table_alias(self, table_name: str):
        first_letters = [word[0] for word in table_name.split('_')]
        orig_alias = ''.join(first_letters)
        i = 2
        alias = orig_alias

        while alias in self.aliases:
            alias = orig_alias + str(i)
            i += 1

        self.aliases[alias] = table_name

        return alias
    
    def table_full_name(self):
        return self.schema + '.' + self.table if self.schema != '' else self.table

    def build_sql_select(self):
        sql_string_columns = []
        sql_string_from = ''
        sql_string_join = ''
        sql_string_group_order_by = ''

        fact_alias = self.__build_table_alias(self.table)

        sql_string_from = "FROM\n\t{} {}".format(self.table_full_name(), fact_alias)
        group_by_count = 0

        for dim_usage in self.dimensions_usage:
            dim = dim_usage.dimension
            dim_alias = self.__build_table_alias(dim.table)

            if not dim.is_degenerated:
                sql_string_join += '\nJOIN\n\t{} {} ON \n\t\t{}.{} = {}.{}'.format(dim.table_full_name(), dim_alias, fact_alias, dim_usage.foreign_key.lower(), dim_alias, dim.primary_key.lower())

            for level in dim.levels:
                sql_string_columns.append('{}.{} '.format(dim_alias, level.column.lower()))
                group_by_count += 1

        for measure in self.measures:
            if measure.is_visible:
                str_agg_format = measure.aggregator.lower() + '({alias}.{column}) AS {column}' \
                    if measure.aggregator.lower() not in ['distinct-count', 'distinct count'] \
                    else 'count(distinct {alias}.{column}) AS {column}'
                sql_string_columns.append(str_agg_format.format(alias=fact_alias, column=measure.column.lower()))

        sql_string_group_order_by = '\nGROUP BY {range}\nORDER BY {range}'.format(range=', '.join([str(i) for i in range(1, group_by_count)]))
        return 'SELECT\n\t{}\n{}{}\n{}\n;'.format('\n\t, '.join(sql_string_columns), sql_string_from, sql_string_join, sql_string_group_order_by)

class CalculatedMeasure(object):
    name = ''
    caption = ''
    description = ''
    formula = ''
    is_visible = True

class MondrianFileParser(object):
    __mondrian_file_path = ''
    __dimensions_dict: dict[str, Dimension] = {}
    __cubes_dict: dict[str, Cube] = {}


    def __init__(self, mondrian_file_path):
        self.__mondrian_file_path = mondrian_file_path
        self.parse_file()

    def __parse_dimensions(self, schema_document):
        for dim_element in sorted(schema_document.xpath("/Schema/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            dim = Dimension()
            dim.id = dim_element.get('name')
            dim.table = dim_element.find('Hierarchy/Table').get('name', 'Undefined')
            dim.schema = dim_element.find('Hierarchy/Table').get('schema', '')
            dim.primary_key = dim_element.find('Hierarchy').get('primaryKey', '')
            dim.name = dim_element.get('name')
            dim.caption = dim_element.get('caption', '')
            dim.description = dim_element.get('description', '')

            for lvl_element in dim_element.iter("Level"):
                dim_level = DimensionLevel()

                dim_level.name = lvl_element.get('name')
                dim_level.caption = lvl_element.get('caption', '')
                dim_level.type = lvl_element.get('type', '')
                dim_level.description = lvl_element.get('description', '')
                dim_level.column = lvl_element.get('column', '')
                dim.add_level(dim_level)

            self.__dimensions_dict[dim.id] = dim
            

    def __parse_degenerated_dimensions(self, schema_document):
        for dim_element in sorted(schema_document.xpath("/Schema/Cube/Dimension"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            dim = Dimension()

            dim.caption = dim_element.get('caption', '')
            dim.description = dim_element.get('description', '')
            dim.table = dim_element.find('../Table').get('name', 'Undefined')
            dim.schema = dim_element.find('../Table').get('schema', 'N/A')
            dim.name = dim_element.get('name')
            dim.id = dim.table + '.' + dim.name
            dim.is_degenerated = True

            for lvl_element in dim_element.iter("Level"):
                dim_level = DimensionLevel()

                dim_level.name = lvl_element.get('name')
                dim_level.caption = lvl_element.get('caption', '')
                dim_level.type = lvl_element.get('type', '')
                dim_level.description = lvl_element.get('description', '')
                dim_level.column = lvl_element.get('column', '')
                dim.add_level(dim_level)

            self.__dimensions_dict[dim.id] = dim

    def __parse_cubes(self, schema_document):
        for cube_element in sorted(schema_document.xpath("/Schema/Cube"), key=lambda x: x.get('caption') if x.get('caption', '') != '' else x.get('name')):
            cube = Cube()
            cube.id = cube_element.get('name')
            cube.caption = cube_element.get('caption', '')
            cube.description = cube_element.get('description', '')
            cube.table = cube_element.find('Table').get('name', 'Undefined')
            cube.schema = cube_element.find('Table').get('schema', '')

            for dim_usage_element in cube_element.iter("DimensionUsage"):
                dim_usage = DimensionUsage()

                dim_usage.name = dim_usage_element.get('name')
                dim_usage.caption = dim_usage_element.get('caption', '')
                dim_usage.source = dim_usage_element.get('source')
                dim_usage.description = dim_usage_element.get('description', '')
                dim_usage.foreign_key = dim_usage_element.get('foreignKey', '')

                dim_usage.dimension = self.__dimensions_dict[dim_usage.source]
                cube.dimensions_usage.append(dim_usage)

            for dim_deg in cube_element.iter("Dimension"):
                dim_usage = DimensionUsage()

                dim_usage.name = dim_deg.get('name')
                dim_usage.caption = dim_deg.get('caption', '')
                dim_usage.source = cube.table + '.' + dim_deg.get('name')
                dim_usage.description = dim_deg.get('description', '')
                dim_usage.dimension = self.__dimensions_dict[dim_usage.source]
                cube.dimensions_usage.append(dim_usage)

            for measure_element in cube_element.iter("Measure"):
                measure = Measure()

                measure.name = measure_element.get('name')
                measure.caption = measure_element.get('caption', '')
                measure.description = measure_element.get('description', '')
                measure.column = measure_element.get('column', '')
                measure.aggregator = measure_element.get('aggregator', '')
                measure.is_visible = measure_element.get('visible', 'true') == 'true'

                cube.measures.append(measure)

            for c_measure_element in cube_element.iter("CalculatedMember"):
                calculated_measure = CalculatedMeasure()

                calculated_measure.name = c_measure_element.get('name')
                calculated_measure.caption = c_measure_element.get('caption', '')
                calculated_measure.description = c_measure_element.get('description', '')

            self.__cubes_dict[cube.id] = cube

    def parse_file(self):
        file_path = Path(self.__mondrian_file_path)
        document = etree.parse(str(file_path))

        schema_name = document.getroot().get('name')
        schema_description = str(document.getroot().get('description') or '')

        self.__parse_dimensions(document)
        self.__parse_degenerated_dimensions(document)
        self.__parse_cubes(document)

        for cube_key in self.__cubes_dict:
            print(cube_key)
            print(self.__cubes_dict[cube_key].build_sql_select())


def main():   
    parser = argparse.ArgumentParser(
        epilog='Example command: python mondian_doc_gen.py --schema_file "steelwheels.mondrian.xml" --output_dir "output/" --templates_dir "templates_html/" ')
    parser.add_argument('--schema_file', '-s', type=str,
                        help='The path for the input schema file that will be parsed', required=True)

    try:
        args = parser.parse_args()
        print(args)

        parsed_file = MondrianFileParser(args.schema_file)
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)



if __name__ == '__main__':
    main()