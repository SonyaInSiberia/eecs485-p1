"""Take in HTML Templates from default or output directory and render them"""
import sys
import os
from pathlib import Path
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
import errno
import json
import click
from jinja2 import Environment, FileSystemLoader, select_autoescape


@click.command()
@click.argument('INPUT_DIR', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path, writable=True),
              help='Output directory.')
@click.option('-v', '--verbose', help='Print more output.', is_flag=True)
def main(output, verbose, input_dir):
    """Templated static website generator."""
    verbose_actions = {'cp': 'Copied', 'rd': 'Rendered'}

    def print_verbose_message(action, src, dst):
        print(f'{action} {src} -> {dst}')

    input_directory = input_dir
    path = Path(input_directory)
    # check if necessary directories and files exist
    if not path.exists():
        sys.exit(f'Input directory \'{path}\' does not exist, exiting.')
    elif not (path / 'templates/').exists():
        sys.exit(f'Input directory \'{path}\\templates\' does not exist, exiting.')
    try:
        json_f = path / 'config.json'
        with open(json_f, 'r', encoding='utf-8') as file:
            config = json.load(file)
    except FileNotFoundError:
        sys.exit('\'config.json\' does not exist.')

    # render
    tmp_path = path / 'templates/'
    env = Environment(
        loader=FileSystemLoader(str(tmp_path)),
        autoescape=select_autoescape(['html', 'xml']),
    )
    templates_names = list(map(str, [x.name for x in tmp_path.glob('**/*.html')]))
    names_with_context_n_url = {dictionary['template']: (dictionary['context'], dictionary['url'])
                                for dictionary in config}
    config_names = [name for name, tup in names_with_context_n_url.items()]
    # output path and checks
    dest_dir = path / 'html/'
    if not isinstance(output, type(None)):
        dest_dir = output
    if dest_dir.exists():
        sys.exit(f'{dest_dir} already exists in the current directory, exiting.')

    if not sorted(config_names) == sorted(templates_names):
        sys.exit('template names in \'config.json\' does not match those in templates folder')
    for dictionary in config:
        name = dictionary['template']
        template = env.get_template(name)
        result = template.render(dictionary['context'])
        url_stripped = dictionary['url'].lstrip('/')
        os.makedirs(dest_dir / url_stripped)
        dest_path = dest_dir / url_stripped / name
        with open(dest_path, 'w', encoding='utf-8') as file:
            file.write(result)
            file.close()
        if verbose:
            print_verbose_message(verbose_actions['rd'], name, dest_path)

    # check if there is static directory
    if (path / 'static/').exists():
        static_path = path / 'static/'
        try:
            copy_tree(str(static_path), str(dest_dir))
            if verbose:
                print_verbose_message(verbose_actions['cp'], static_path, dest_dir)
        except OSError as exc:
            if exc in (errno.ENOTDIR, errno.EINVAL):
                copy_file(str(static_path), str(dest_dir))
                if verbose:
                    print_verbose_message(verbose_actions['cp'], static_path, dest_dir)
            else:
                raise


if __name__ == "__main__":
    main()
