from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
PNG_PATH = ASSETS_DIR / "caffeine_icon.png"
ICO_PATH = ASSETS_DIR / "caffeine_icon.ico"


def main() -> int:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    image = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((24, 24, 488, 488), radius=96, fill=(22, 50, 79, 255))
    draw.rounded_rectangle((72, 72, 440, 440), radius=72, fill=(247, 243, 235, 255))

    bond = (32, 53, 77, 255)
    orange = (214, 130, 22, 255)
    teal = (31, 122, 79, 255)
    blue = (31, 95, 139, 255)

    hexagon = [(164, 232), (212, 156), (300, 156), (348, 232), (304, 308), (216, 308)]
    pentagon = [(300, 156), (372, 206), (346, 286), (304, 308), (348, 232)]
    draw.line(hexagon + [hexagon[0]], fill=bond, width=18, joint="curve")
    draw.line(pentagon + [pentagon[0]], fill=bond, width=18, joint="curve")
    draw.line((212, 156, 304, 308), fill=bond, width=12)
    draw.line((164, 232, 348, 232), fill=bond, width=12)
    draw.line((216, 308, 346, 286), fill=bond, width=12)

    for x, y, color, radius in (
        (140, 148, orange, 26),
        (392, 180, orange, 26),
        (256, 372, teal, 26),
        (220, 232, blue, 20),
        (316, 232, blue, 20),
        (270, 288, blue, 20),
    ):
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    image.save(PNG_PATH)
    image.save(ICO_PATH, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"generated: {PNG_PATH}")
    print(f"generated: {ICO_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
