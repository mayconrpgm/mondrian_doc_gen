from io import open
from MondrianDocumentationBuilder import MondrianDocumentationBuilder
import glob
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        epilog='Example command: python mondian_doc_gen.py --schema_file "steelwheels.mondrian.xml" --output_dir "output/" --templates_dir "templates_html/" ')
    parser.add_argument('--schema_file', '-s', type=str,
                        help='The path for the input schema file that will be parsed', required=True)
    parser.add_argument('--output_dir', '-o', type=str, default='output/',
                        help='The path to the directory where the output documentation will be stored', required=False)
    parser.add_argument('--templates_dir', '-t', type=str, default='templates_html/',
                        help='The path to the directory containing the documentation code templates. The default value is "templates_html/"', required=False)

    try:
        args = parser.parse_args()

        print(args)

        doc_builder = MondrianDocumentationBuilder(args.templates_dir)

        doc_builder.parse_file(args.schema_file, args.output_dir)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)


if __name__ == '__main__':
    main()