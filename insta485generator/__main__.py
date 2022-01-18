import sys
from pathlib import Path
import shutil
import errno
import click
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape


@click.command()
@click.argument('INPUT_DIR', type=click.Path(exists=True, path_type=Path))
@click.option('-o', '--output', type=click.Path(path_type=Path, writable=True),
              help='Output directory.')
@click.option('-v', '--verbose', help='Print more output.', is_flag=True)
def main(input_dir, output_dir, verbose):
    """Build static HTML site from directory of HTML templates and plain files."""
    INPUT_DIR = input_dir
    path = Path(INPUT_DIR)
    # check if necessary directories and files exist
    if not path.exists():
        sys.exit(f'Input directory \'{path}\' does not exist, exiting.')
    elif not (path / 'templates/').exists():
        sys.exit(f'Input directory \'{path}\\templates\' does not exist, exiting.')
    try:
        json_f = path / 'config.json'
        config = json.load(json_f)
    except FileNotFoundError:
        sys.exit('\'config.json\' does not exist.')
    dest_dir = path / 'html/'
    if dest_dir.exists():
        sys.exit(f'{dest_dir} already exists in the current directory, exiting.')
    else:
        Path.mkdir(dest_dir)

    # render
    tmp_path = path / 'templates/'
    env = Environment(
        loader=FileSystemLoader(str(tmp_path)),
        autoescape=select_autoescape(['html', 'xml']),
    )
    templates_names = list(map(str, tmp_path.glob('*.html')))
    names_with_context = {dictionary['template']: dictionary['context'] for dictionary in config}
    config_names = [name for name, context in names_with_context.items()]
    if not sorted(config_names) == sorted(templates_names):
        sys.exit('template names in \'config.json\' does not match those in templates folder')
    for name in templates_names:
        template = env.get_template(name)
        result = template.render(names_with_context[name])
        with open(dest_dir / name, 'w') as f:
            f.write(result)
            f.close()

    # check if there is static directory
    if (path/'static/').exists():
        static_path = path/'static/'
        try:
            shutil.copytree(static_path, dest_dir)
        except OSError as exc:
            if exc in (errno.ENOTDIR, errno.EINVAL):
                shutil.copy(static_path, dest_dir)
            else:
                raise


if __name__ == "__main__":
    main()
