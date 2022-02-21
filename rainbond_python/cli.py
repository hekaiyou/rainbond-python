import os
import sys
import zipfile
import argparse
from pathlib import Path


def main():
    if len(sys.argv) == 1:
        sys.argv.append('--help')
    parser = argparse.ArgumentParser(description='Rainbond Python CLI')
    parser.add_argument('-c', '--create', help='Create Rainbond Python Component',
                        action='store', dest='component_name')
    args = parser.parse_args()

    if args.component_name:
        component_root = Path(__file__).resolve().parents[0]
        os.mkdir(args.component_name)
        example_dir = component_root / 'demos' / 'rainbond-python-demo.zip'
        extract(str(example_dir), args.component_name)
        print(
            'Successfully created `{0}` component. Run command:\n$ cd {0}\n$ pip3 install -r requirements.txt\n$ python3 app.py'.format(args.component_name))


def extract(z_file, path):
    """解压缩文件到指定目录"""
    f = zipfile.ZipFile(z_file, 'r')
    for file in f.namelist():
        f.extract(file, path)


if __name__ == '__main__':
    main()
