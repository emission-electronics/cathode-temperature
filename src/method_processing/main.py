import msgpack_numpy as mnp
import numpy as np
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import logging
import os

import click

plt.rcParams['figure.dpi'] = 300
plt.rcParams['figure.figsize'] = [6, 4]
plt.rcParams['font.size'] = 12
plt.rcParams['lines.markersize'] = 2.5
plt.rcParams['xtick.minor.visible'] = True
plt.rcParams['ytick.minor.visible'] = True
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.color'] = "#aaaaaa"
plt.rcParams['grid.alpha'] = 0.2
plt.rcParams['axes.grid.which'] = 'both'
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman"]

lg = logging.Logger(__name__, logging.INFO)

def export_grad_poly(path: Path, poly: np.poly1d) -> None:
    z = poly.coefficients

    if path.exists():
        lg.error(f"Graduation file {path} already exists")
        return

    with open(path, "xb") as f:
        mnp.dump(z, f)
    
def import_grad_poly(path: Path) -> np.poly1d:
    with open(path.resolve(), "rb") as f:
        z = np.array(mnp.load(f))
    return np.poly1d(z)

def import_image(path: Path, flags: int = cv2.IMREAD_GRAYSCALE, threshold: int = 40) -> np.ndarray:
    image = cv2.imread(str(path.resolve()), flags)
    image[image < threshold] = 0
    return image

def apply_grad_to_image(image: np.ndarray, grad_poly: np.poly1d, averaging_func = np.max, shift: int = 1) -> np.ndarray:
    image_processed = np.zeros_like(image)
    min_value = 0
    for i in range(1, image.shape[0] - 1):
        for j in range(1, image.shape[1] - 1):
            if image[i, j] == 0:
                continue
            window = image[i-shift:i+1+shift, j-shift:j+1+shift]
            value = averaging_func(window)
            image_processed[i, j] = value

            if min_value == 0:
                min_value = value
            min_value = min(min_value, value)

    image_processed[image_processed == 0] = min_value
    return grad_poly(image_processed)

def export_temperature_map(path: Path, temperature_map: np.ndarray, label: str = "Температура (K)"):
    plt.clf()
    plt.imshow(temperature_map, cmap='hot')
    plt.colorbar(label=label)
    plt.tight_layout()
    plt.savefig(path.resolve())

@click.group()
@click.option("--grad-name", default="ns11_ns7", help="Название градуировки (без расширения .grad)")
@click.option("--grad-dir", default="GRADUATION", help="Каталог с файлами градуировок")
@click.pass_context
def main(ctx, grad_name, grad_dir):
    ctx.ensure_object(dict)
    ctx.obj['GRAD_NAME'] = grad_name
    ctx.obj['GRAD_DIR'] = grad_dir

@click.command()
@click.option("--input-dir", default="INPUT_IMAGES", help="Каталог с изображениями для применения градуировки")
@click.option("--output-dir", default="OUTPUT_IMAGES", help="Каталог для сохранения результата градуировки")
@click.pass_context
def apply(ctx, input_dir, output_dir):
    cwd = Path().cwd()
    grad_name = ctx.obj['GRAD_NAME']
    grad_dir = ctx.obj['GRAD_DIR']

    grad_path = cwd / grad_dir / f"{grad_name}.grad"
    click.echo(f"Using graduation {grad_name}")
    
    input_path = cwd / input_dir
    output_path = cwd / output_dir
    input_path.mkdir(exist_ok=True)
    output_path.mkdir(exist_ok=True)

    try:
        for filename in os.listdir(input_path):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            grad_poly = import_grad_poly(grad_path)
            image = import_image(input_path / filename)
            processed = apply_grad_to_image(image, grad_poly)
            
            out_path = output_path / f"processed_{filename}"
            export_temperature_map(out_path, processed)
            
            click.echo(f"Processed {filename}")
            
    except FileNotFoundError as e:
        lg.error(f"File not found: {e}")
    except Exception as e:
        lg.error(f"Error processing files: {e}")

main.add_command(apply)

if __name__ == "__main__":
    main()
