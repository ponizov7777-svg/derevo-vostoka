#!/usr/bin/env python3
"""
Post-process AI-generated grayscale heightmaps for CNC relief carving.

Removes common lighting artifacts (edge highlights, contact shadows),
forces a flat black background, smooths relief, and normalizes height range.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_closing, gaussian_filter, grey_closing, grey_opening, laplace, sobel


def load_grayscale(path: Path) -> np.ndarray:
    image = Image.open(path).convert("L")
    return np.asarray(image, dtype=np.float64)


def save_grayscale(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clipped = np.clip(array, 0, 255).astype(np.uint8)
    Image.fromarray(clipped, mode="L").save(path)


def relief_mask(array: np.ndarray, background_threshold: float) -> np.ndarray:
    return array > background_threshold


def build_stable_relief_mask(
    array: np.ndarray,
    background_threshold: float,
    *,
    dilate_size: int = 7,
) -> np.ndarray:
    """
    Fixed relief mask captured before contrast steps can darken grooves to black.

    Dilates the initial foreground and fills interior holes so paw prints, text
    grooves and other recessions stay inside the mask even when pixel values
    drop below background_threshold during processing.
    """
    from scipy.ndimage import binary_dilation, binary_fill_holes

    mask = array > background_threshold
    if dilate_size > 1:
        structure = np.ones((dilate_size, dilate_size), dtype=bool)
        mask = binary_dilation(mask, structure=structure)
    return binary_fill_holes(mask)


def fill_relief_holes(
    array: np.ndarray,
    mask: np.ndarray,
    *,
    background_threshold: float,
    relief_floor: float,
    inpaint_sigma: float = 4.0,
) -> np.ndarray:
    """Replace black holes inside the stable relief mask with local smoothed values."""
    if relief_floor <= 0 and not np.any(mask & (array <= background_threshold)):
        result = array.copy()
        result[~mask] = 0.0
        return result

    safe = array.copy()
    safe[~mask] = relief_floor
    inpainted = gaussian_filter(safe, sigma=inpaint_sigma)

    result = array.copy()
    holes = mask & (result <= background_threshold)
    if np.any(holes):
        result[holes] = inpainted[holes]

    if relief_floor > 0:
        result[mask] = np.maximum(result[mask], relief_floor)

    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def force_black_background(array: np.ndarray, background_threshold: float) -> np.ndarray:
    result = array.copy()
    result[array <= background_threshold] = 0.0
    return result


def flatten_directional_lighting(
    array: np.ndarray,
    mask: np.ndarray,
    sigma: float,
    strength: float,
) -> np.ndarray:
    """
    Remove low-frequency lighting gradients (e.g. left slope brighter than right).

    Uses homomorphic-style correction in log space to flatten multiplicative
    shading while preserving larger relief shapes.
    """
    if sigma <= 0 or strength <= 0:
        return array

    safe = np.maximum(array, 1.0)
    log_img = np.log(safe)

    weights = mask.astype(np.float64)
    log_weighted = log_img * weights
    weight_sum = gaussian_filter(weights, sigma=sigma)
    log_low = gaussian_filter(log_weighted, sigma=sigma) / (weight_sum + 1e-6)

    log_center = float(np.median(log_low[mask]))
    log_corrected = log_img - strength * (log_low - log_center)

    result = np.exp(log_corrected)
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def suppress_lighting_artifacts(
    array: np.ndarray,
    mask: np.ndarray,
    morph_size: int,
    highlight_strength: float,
    shadow_strength: float,
) -> np.ndarray:
    """Remove thin bright rims and dark contact grooves via morphological top-hats."""
    if morph_size < 3:
        return array

    footprint = np.ones((morph_size, morph_size), dtype=bool)
    opened = grey_opening(array, footprint=footprint)
    closed = grey_closing(array, footprint=footprint)

    white_tophat = np.maximum(array - opened, 0.0)
    black_tophat = np.maximum(closed - array, 0.0)

    result = array - highlight_strength * white_tophat + shadow_strength * black_tophat
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def clamp_local_outliers(
    array: np.ndarray,
    mask: np.ndarray,
    window: int,
    highlight_margin: float,
    shadow_margin: float,
) -> np.ndarray:
    """Clamp pixels that spike above/below their local neighborhood."""
    from scipy.ndimage import percentile_filter

    if window < 3:
        return array

    local_p90 = percentile_filter(array, 90, size=window, mode="nearest")
    local_p10 = percentile_filter(array, 10, size=window, mode="nearest")
    local_median = percentile_filter(array, 50, size=window, mode="nearest")

    result = array.copy()
    highlight_spikes = mask & (array > local_p90 + highlight_margin)
    shadow_grooves = mask & (array < local_p10 - shadow_margin)

    result[highlight_spikes] = local_median[highlight_spikes]
    result[shadow_grooves] = local_median[shadow_grooves]
    result[~mask] = 0.0
    return result


def smooth_relief(array: np.ndarray, mask: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0:
        return array

    smoothed = gaussian_filter(array, sigma=sigma)
    result = array.copy()
    result[mask] = smoothed[mask]
    result[~mask] = 0.0
    return result


def upscale_array(array: np.ndarray, scale: float) -> np.ndarray:
    if scale <= 1.0:
        return array

    image = Image.fromarray(np.clip(array, 0, 255).astype(np.uint8), mode="L")
    new_size = (int(round(image.width * scale)), int(round(image.height * scale)))
    upscaled = image.resize(new_size, Image.Resampling.LANCZOS)
    return np.asarray(upscaled, dtype=np.float64)


def compress_contrast(
    array: np.ndarray,
    mask: np.ndarray,
    *,
    percentile_low: float,
    percentile_high: float,
    output_low: float,
    output_high: float,
    strength: float,
) -> np.ndarray:
    """Map relief values into a narrower range for low-contrast, foggy relief."""
    values = array[mask]
    if values.size == 0:
        return array

    low = float(np.percentile(values, percentile_low))
    high = float(np.percentile(values, percentile_high))
    if high <= low:
        high = low + 1.0

    normalized = np.clip((array - low) / (high - low), 0.0, 1.0)
    mid = 0.5
    compressed = mid + (normalized - mid) * strength
    scaled = compressed * (output_high - output_low) + output_low

    result = array.copy()
    result[mask] = scaled[mask]
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def apply_fog_haze(
    array: np.ndarray,
    mask: np.ndarray,
    *,
    haze_strength: float,
    haze_gray: float,
) -> np.ndarray:
    """Blend relief toward a soft gray to create a misty look."""
    if haze_strength <= 0:
        return array

    result = array.copy()
    result[mask] = array[mask] * (1.0 - haze_strength) + haze_gray * haze_strength
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def build_edge_reference(
    upscaled: np.ndarray,
    mask: np.ndarray,
    *,
    contrast_strength: float,
    output_low: float,
    output_high: float,
) -> np.ndarray:
    """Sharper, higher-contrast reference for restoring stone edges and letter corners."""
    working = smooth_relief(upscaled, mask, sigma=1.2)
    return compress_contrast(
        working,
        mask,
        percentile_low=2.0,
        percentile_high=98.0,
        output_low=output_low * 0.92,
        output_high=min(output_high * 1.12, 210.0),
        strength=min(contrast_strength * 1.45, 0.95),
    )


def enhance_relief_edges(
    foggy: np.ndarray,
    edge_reference: np.ndarray,
    mask: np.ndarray,
    *,
    edge_percentile: float,
    sharpen_strength: float,
    edge_weight_sigma: float,
) -> np.ndarray:
    """Blend crisp edge geometry back into a soft-fog base at stones and text."""
    if sharpen_strength <= 0:
        return foggy

    ref = edge_reference.copy()
    ref[~mask] = 0.0

    grad = np.hypot(sobel(ref, axis=0), sobel(ref, axis=1))
    corners = np.abs(laplace(ref))
    grad_norm = grad / (float(grad[mask].max()) + 1e-6)
    corner_norm = corners / (float(corners[mask].max()) + 1e-6)
    edge_signal = np.maximum(grad_norm, corner_norm * 0.9)

    threshold = float(np.percentile(edge_signal[mask], edge_percentile))
    edge_weight = np.clip((edge_signal - threshold) / (1.0 - threshold + 1e-6), 0.0, 1.0)
    edge_weight = gaussian_filter(edge_weight * mask.astype(np.float64), sigma=edge_weight_sigma)
    edge_weight = np.clip(edge_weight, 0.0, 1.0) * sharpen_strength

    result = foggy.copy()
    blend = edge_weight[mask]
    result[mask] = foggy[mask] * (1.0 - blend) + ref[mask] * blend
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def darken_contour_lines(
    array: np.ndarray,
    mask: np.ndarray,
    *,
    strength: float,
    morph_size: int = 5,
    darken_amount: float = 34.0,
) -> np.ndarray:
    """Deepen dark contour grooves and shadow sides of relief edges."""
    if strength <= 0:
        return array

    from scipy.ndimage import percentile_filter

    footprint = np.ones((morph_size, morph_size), dtype=bool)
    closed = grey_closing(array, footprint=footprint)
    dark_lines = np.maximum(closed - array, 0.0)

    grad = np.hypot(sobel(array, axis=0), sobel(array, axis=1))
    edge_threshold = float(np.percentile(grad[mask], 58.0))
    edge_active = grad >= edge_threshold

    line_signal = dark_lines / (float(dark_lines[mask].max()) + 1e-6)
    local_med = percentile_filter(array, 50, size=7, mode="nearest")
    dark_side = array <= local_med

    weight = line_signal * edge_active.astype(np.float64) * dark_side.astype(np.float64)
    peak = float(weight[mask].max())
    if peak > 0:
        weight = weight / peak

    result = array.copy()
    result[mask] = array[mask] - strength * darken_amount * weight[mask]
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def _line_kernel(size: int, angle_deg: int, width: int = 1) -> np.ndarray:
    kernel = np.zeros((size, size), dtype=bool)
    center = size // 2
    for offset in range(-center, center + 1):
        if angle_deg == 0:
            row, col = center, center + offset
        elif angle_deg == 90:
            row, col = center + offset, center
        elif angle_deg == 45:
            row, col = center + offset, center + offset
        else:
            row, col = center + offset, center - offset
        for delta in range(-(width // 2), width // 2 + 1):
            if angle_deg in (0, 90):
                rr, cc = (row + delta, col) if angle_deg == 0 else (row, col + delta)
            elif angle_deg == 45:
                rr, cc = row + delta, col
            else:
                rr, cc = row, col + delta
            if 0 <= rr < size and 0 <= cc < size:
                kernel[rr, cc] = True
    return kernel


def connect_stippled_lines(
    array: np.ndarray,
    mask: np.ndarray,
    *,
    strength: float,
    local_sigma: float = 6.0,
    dark_offset: float = 5.0,
    connect_size: int = 9,
    line_depth: float = 26.0,
    soften_sigma: float = 1.3,
) -> np.ndarray:
    """Connect broken dark dots into continuous groove lines."""
    if strength <= 0:
        return array

    local = gaussian_filter(array, sigma=local_sigma)
    dark_gap = np.maximum(local - array - dark_offset, 0.0)
    dark_gap[~mask] = 0.0

    connected = dark_gap.copy()
    for size in (5, connect_size, connect_size + 2):
        footprint = np.ones((size, size), dtype=bool)
        connected = np.maximum(connected, grey_closing(dark_gap, footprint=footprint))

    for angle in (0, 45, 90, 135):
        footprint = _line_kernel(connect_size + 2, angle, width=2)
        connected = np.maximum(connected, grey_closing(dark_gap, footprint=footprint))

    dark_binary = connected > np.percentile(connected[mask], 72.0)
    dark_binary = binary_closing(dark_binary, structure=np.ones((5, 5), dtype=bool))

    line_weight = gaussian_filter(dark_binary.astype(np.float64), sigma=soften_sigma)
    peak = float(line_weight[mask].max())
    if peak > 0:
        line_weight = line_weight / peak

    target = local - line_depth
    result = array.copy()
    blend = np.clip(line_weight * strength, 0.0, 1.0)
    carved = np.minimum(target, array)
    result[mask] = array[mask] * (1.0 - blend[mask]) + carved[mask] * blend[mask]
    result[~mask] = 0.0
    return np.clip(result, 0.0, 255.0)


def postprocess_soft_fog(
    array: np.ndarray,
    *,
    background_threshold: float = 18.0,
    upscale: float = 2.0,
    smooth_sigma: float = 8.0,
    smooth_passes: int = 2,
    contrast_strength: float = 0.42,
    output_low: float = 48.0,
    output_high: float = 168.0,
    haze_strength: float = 0.28,
    haze_gray: float = 112.0,
    final_smooth_sigma: float = 2.5,
    edge_sharpen: float = 0.55,
    edge_percentile: float = 68.0,
    edge_weight_sigma: float = 0.55,
    contour_darken: float = 0.0,
    connect_lines: float = 0.0,
    stable_mask_dilate: int = 7,
    relief_floor: float = 0.0,
) -> np.ndarray:
    """
    Upscale, heavily smooth, and compress contrast for soft foggy heightmaps.

    Produces gentle relief without sharp brightness steps — suitable when the
    source texture is too harsh for CNC carving.
    """
    working = upscale_array(array, upscale)
    working = force_black_background(working, background_threshold)
    stable_mask = build_stable_relief_mask(
        working,
        background_threshold,
        dilate_size=stable_mask_dilate,
    )
    floor = relief_floor if relief_floor > 0 else max(output_low * 0.82, background_threshold + 6.0)
    mask = stable_mask.copy()
    upscaled_ref = working.copy()

    for _ in range(max(1, smooth_passes)):
        working = smooth_relief(working, mask, sigma=smooth_sigma)

    working = compress_contrast(
        working,
        mask,
        percentile_low=2.0,
        percentile_high=98.0,
        output_low=output_low,
        output_high=output_high,
        strength=contrast_strength,
    )

    working = apply_fog_haze(
        working,
        mask,
        haze_strength=haze_strength,
        haze_gray=haze_gray,
    )

    working = smooth_relief(working, mask, sigma=final_smooth_sigma)

    if edge_sharpen > 0:
        edge_ref = build_edge_reference(
            upscaled_ref,
            mask,
            contrast_strength=contrast_strength,
            output_low=output_low,
            output_high=output_high,
        )
        working = enhance_relief_edges(
            working,
            edge_ref,
            mask,
            edge_percentile=edge_percentile,
            sharpen_strength=edge_sharpen,
            edge_weight_sigma=edge_weight_sigma,
        )

    if contour_darken > 0:
        working = darken_contour_lines(working, mask, strength=contour_darken)

    if connect_lines > 0:
        working = connect_stippled_lines(working, mask, strength=connect_lines)

    return fill_relief_holes(
        working,
        mask,
        background_threshold=background_threshold,
        relief_floor=floor,
    )


def normalize_height_range(
    array: np.ndarray,
    mask: np.ndarray,
    percentile_low: float,
    percentile_high: float,
    max_white: float,
) -> np.ndarray:
    values = array[mask]
    if values.size == 0:
        return array

    low = float(np.percentile(values, percentile_low))
    high = float(np.percentile(values, percentile_high))
    if high <= low:
        high = low + 1.0

    scaled = (array - low) / (high - low) * max_white
    result = np.clip(scaled, 0.0, max_white)
    result[~mask] = 0.0
    return result


def postprocess(
    array: np.ndarray,
    *,
    background_threshold: float = 18.0,
    flatten_sigma: float = 45.0,
    flatten_strength: float = 1.0,
    morph_size: int = 7,
    highlight_strength: float = 0.85,
    shadow_strength: float = 0.75,
    outlier_window: int = 15,
    highlight_margin: float = 8.0,
    shadow_margin: float = 6.0,
    smooth_sigma: float = 1.2,
    percentile_low: float = 1.0,
    percentile_high: float = 99.0,
    max_white: float = 235.0,
) -> np.ndarray:
    working = force_black_background(array, background_threshold)
    mask = relief_mask(working, background_threshold)

    working = flatten_directional_lighting(
        working,
        mask,
        sigma=flatten_sigma,
        strength=flatten_strength,
    )
    mask = relief_mask(working, background_threshold)

    working = suppress_lighting_artifacts(
        working,
        mask,
        morph_size=morph_size,
        highlight_strength=highlight_strength,
        shadow_strength=shadow_strength,
    )
    mask = relief_mask(working, background_threshold)

    working = clamp_local_outliers(
        working,
        mask,
        window=outlier_window,
        highlight_margin=highlight_margin,
        shadow_margin=shadow_margin,
    )
    mask = relief_mask(working, background_threshold)

    working = smooth_relief(working, mask, sigma=smooth_sigma)
    mask = relief_mask(working, background_threshold)

    working = normalize_height_range(
        working,
        mask,
        percentile_low=percentile_low,
        percentile_high=percentile_high,
        max_white=max_white,
    )
    return working


def default_output_path(input_path: Path, output_dir: Path | None, suffix: str) -> Path:
    if output_dir is None:
        return input_path.with_name(f"{input_path.stem}{suffix}{input_path.suffix}")

    return output_dir / f"{input_path.stem}{suffix}{input_path.suffix}"


def collect_inputs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.png")))
            files.extend(sorted(path.glob("*.jpg")))
            files.extend(sorted(path.glob("*.jpeg")))
            files.extend(sorted(path.glob("*.webp")))
        elif path.is_file():
            files.append(path)
        else:
            print(f"Skip missing path: {path}", file=sys.stderr)
    return files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Post-process grayscale heightmaps for CNC carving."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input image file(s) or folder(s) with PNG/JPG images.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Output folder. Default: same folder as input with suffix.",
    )
    parser.add_argument(
        "--suffix",
        default="_processed",
        help="Suffix for output files when --output-dir is not used.",
    )
    parser.add_argument(
        "--background-threshold",
        type=float,
        default=18.0,
        help="Pixels at or below this value become pure black background.",
    )
    parser.add_argument(
        "--flatten-sigma",
        type=float,
        default=45.0,
        help="Smoothing radius for directional lighting removal.",
    )
    parser.add_argument(
        "--flatten-strength",
        type=float,
        default=1.0,
        help="How strongly to flatten left/right lighting gradients (0-1+).",
    )
    parser.add_argument(
        "--no-flatten-lighting",
        action="store_true",
        help="Skip directional lighting flattening step.",
    )
    parser.add_argument(
        "--morph-size",
        type=int,
        default=7,
        help="Morphology window for highlight/shadow removal.",
    )
    parser.add_argument(
        "--highlight-strength",
        type=float,
        default=0.85,
        help="How strongly to suppress bright edge highlights (0-1).",
    )
    parser.add_argument(
        "--shadow-strength",
        type=float,
        default=0.75,
        help="How strongly to fill dark contact shadows (0-1).",
    )
    parser.add_argument(
        "--smooth-sigma",
        type=float,
        default=1.2,
        help="Gaussian smoothing strength for relief areas.",
    )
    parser.add_argument(
        "--max-white",
        type=float,
        default=235.0,
        help="Upper brightness cap after normalization.",
    )
    parser.add_argument(
        "--mode",
        choices=("cnc", "soft-fog"),
        default="cnc",
        help="Processing mode: cnc (default) or soft-fog (upscale + smooth + low contrast).",
    )
    parser.add_argument(
        "--upscale",
        type=float,
        default=2.0,
        help="Upscale factor for soft-fog mode (default: 2.0).",
    )
    parser.add_argument(
        "--fog-smooth-sigma",
        type=float,
        default=8.0,
        help="Main Gaussian smoothing in soft-fog mode.",
    )
    parser.add_argument(
        "--fog-smooth-passes",
        type=int,
        default=2,
        help="How many smoothing passes to apply in soft-fog mode.",
    )
    parser.add_argument(
        "--contrast-strength",
        type=float,
        default=0.42,
        help="Contrast compression in soft-fog mode (lower = softer, foggier).",
    )
    parser.add_argument(
        "--output-low",
        type=float,
        default=48.0,
        help="Minimum relief brightness after soft-fog compression.",
    )
    parser.add_argument(
        "--output-high",
        type=float,
        default=168.0,
        help="Maximum relief brightness after soft-fog compression.",
    )
    parser.add_argument(
        "--haze-strength",
        type=float,
        default=0.28,
        help="Fog haze blend strength in soft-fog mode (0-1).",
    )
    parser.add_argument(
        "--haze-gray",
        type=float,
        default=112.0,
        help="Target gray level for fog haze in soft-fog mode.",
    )
    parser.add_argument(
        "--final-smooth-sigma",
        type=float,
        default=2.5,
        help="Final light smoothing pass in soft-fog mode.",
    )
    parser.add_argument(
        "--edge-sharpen",
        type=float,
        default=0.55,
        help="Restore crisp stone/text edges on soft-fog result (0=off, 1=max).",
    )
    parser.add_argument(
        "--edge-percentile",
        type=float,
        default=68.0,
        help="Gradient percentile for edge sharpening mask in soft-fog mode.",
    )
    parser.add_argument(
        "--edge-weight-sigma",
        type=float,
        default=0.55,
        help="Softness of the edge sharpening mask in soft-fog mode.",
    )
    parser.add_argument(
        "--contour-darken",
        type=float,
        default=0.0,
        help="Darken contour grooves and edge valleys in soft-fog mode (0=off).",
    )
    parser.add_argument(
        "--connect-lines",
        type=float,
        default=0.0,
        help="Connect stippled dark dots into continuous lines in soft-fog mode (0=off).",
    )
    parser.add_argument(
        "--stable-mask-dilate",
        type=int,
        default=7,
        help="Dilate initial relief mask in soft-fog mode to keep recessions inside relief.",
    )
    parser.add_argument(
        "--relief-floor",
        type=float,
        default=0.0,
        help="Minimum brightness inside relief (0 = auto from output-low). Prevents black holes.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    files = collect_inputs(args.inputs)
    if not files:
        print("No input images found.", file=sys.stderr)
        return 1

    for input_path in files:
        output_path = default_output_path(input_path, args.output_dir, args.suffix)
        source = load_grayscale(input_path)
        if args.mode == "soft-fog":
            result = postprocess_soft_fog(
                source,
                background_threshold=args.background_threshold,
                upscale=args.upscale,
                smooth_sigma=args.fog_smooth_sigma,
                smooth_passes=args.fog_smooth_passes,
                contrast_strength=args.contrast_strength,
                output_low=args.output_low,
                output_high=args.output_high,
                haze_strength=args.haze_strength,
                haze_gray=args.haze_gray,
                final_smooth_sigma=args.final_smooth_sigma,
                edge_sharpen=args.edge_sharpen,
                edge_percentile=args.edge_percentile,
                edge_weight_sigma=args.edge_weight_sigma,
                contour_darken=args.contour_darken,
                connect_lines=args.connect_lines,
                stable_mask_dilate=args.stable_mask_dilate,
                relief_floor=args.relief_floor,
            )
        else:
            result = postprocess(
                source,
                background_threshold=args.background_threshold,
                flatten_sigma=0.0 if args.no_flatten_lighting else args.flatten_sigma,
                flatten_strength=args.flatten_strength,
                morph_size=args.morph_size,
                highlight_strength=args.highlight_strength,
                shadow_strength=args.shadow_strength,
                smooth_sigma=args.smooth_sigma,
                max_white=args.max_white,
            )
        save_grayscale(output_path, result)
        print(f"OK [{args.mode}]: {input_path} -> {output_path} ({result.shape[1]}x{result.shape[0]})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
