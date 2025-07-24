import click
import logging
import sys
from cmd_apply import apply

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

@click.group()
@click.option("--grad-name", default="ns11_ns77", help="Название градуировки (без расширения .grad)")
@click.option("--grad-dir", default="GRADUATION", help="Каталог с файлами градуировок")
@click.pass_context
def main(ctx, grad_name, grad_dir):
    ctx.ensure_object(dict)
    ctx.obj['GRAD_NAME'] = grad_name
    ctx.obj['GRAD_DIR'] = grad_dir

main.add_command(apply)

if __name__ == "__main__":
    main()
