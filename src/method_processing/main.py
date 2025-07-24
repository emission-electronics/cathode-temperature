import click
import logging
import sys

from cmd_apply import apply
from cmd_grad import grad

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

@click.group()
@click.option("--debug", is_flag=True, help="Включить логгинг дебага")
@click.option("--grad-name", default="ns11_ns7", help="Название градуировки (без расширения .grad)")
@click.option("--grad-dir", default="GRADUATION", help="Каталог с файлами градуировок")
@click.pass_context
def main(ctx: click.Context, debug: bool, grad_name: str, grad_dir: str):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    ctx.ensure_object(dict)
    ctx.obj['GRAD_NAME'] = grad_name
    ctx.obj['GRAD_DIR'] = grad_dir

main.add_command(apply)
main.add_command(grad)

if __name__ == "__main__":
    main()
