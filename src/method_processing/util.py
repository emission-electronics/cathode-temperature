from pathlib import Path
import numpy as np
from logging import getLogger as lg
import msgpack_numpy as mnp
import cv2

def export_grad_poly(path: Path, poly: np.poly1d) -> None:
    z = poly.coefficients

    if path.exists():
        lg(__name__).error(f"Graduation file {path} already exists")
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
