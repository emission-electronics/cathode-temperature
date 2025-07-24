from pathlib import Path
from logging import getLogger as lg
import os
import re

import numpy as np
import click

from util import export_grad_poly, import_image

# TODO: T on I calibration
T = lambda I: 108.0958765*I*I*I-511.9765339*I*I+1617.95649045*I+537.60415503

# IMPORTANT: for vertical wire
def wire_brightness(image: np.ndarray, choose_percentage: float = .3) -> tuple[np.floating, np.floating]:
    def j_maxs(img_array):
        res = []
        for i in range(img_array.shape[0]):
            res.append(np.argmax(img_array[i]))
        return np.array(res)
    
    i_arr = np.arange(image.shape[0])
    j_max = j_maxs(image)
    Y_max = image[i_arr, j_max]

    # filter very low values
    idx = (Y_max > Y_max.mean() * .8)
    i_arr = i_arr[idx]
    j_max = j_max[idx]
    Y_max = image[i_arr, j_max]

    # choose_percentage points in center
    center = len(Y_max) // 2
    shift = int(len(Y_max) * choose_percentage) // 2
    Y_max = Y_max[center - shift:center + shift + 1]

    return np.mean(Y_max), np.std(Y_max)

def grad_poly_fit(means: np.ndarray, temperatures: np.ndarray, fit_order: int = 5) -> np.poly1d:
    popt = np.polyfit(means, temperatures, fit_order, cov=False, full=False)
    return np.poly1d(popt)

@click.command()
@click.option("--overwrite", is_flag=True, help="Разрешить перезапись градуировки")
@click.pass_context
def grad(ctx: click.Context, overwrite: bool):
    cwd = Path().cwd()
    grad_dir = cwd / str(ctx.obj['GRAD_DIR'])
    grad_name = ctx.obj['GRAD_NAME']
    grad_path = grad_dir / f"{grad_name}.grad"

    click.echo(f"Using graduation {grad_name}")

    if grad_path.exists():
        if not overwrite:
            click.echo(f"Graduation file {grad_path} already exist")
            return
        grad_path.unlink()

    means = []
    temperatures = []
    try:
        for filename in os.listdir(grad_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            
            image = import_image(grad_dir / filename)

            match = re.search(r'\d{4}', filename)
            if match is None:
                lg(__name__).error(f"There is no current value in filename: {filename}")
                continue

            current = np.float64(match.group()) / 1000
            temperature = T(current)
            mean, _ = wire_brightness(image)

            click.echo(f"Processed {filename}:\t{current=:.2f}A\t{temperature=:.2f}K\t{mean=:.2f}")
            means.append(mean)
            temperatures.append(temperature)
        
        p = grad_poly_fit(np.array(means), np.array(temperatures))
        click.echo("Result:")
        click.echo(p)
        click.echo()

        export_grad_poly(grad_path, p)
        click.echo(f"Graduation file {grad_path} created")
            
    except FileNotFoundError as e:
        lg(__name__).error(f"File not found: {e}")
    except Exception as e:
        lg(__name__).error(f"Error: {e}")
