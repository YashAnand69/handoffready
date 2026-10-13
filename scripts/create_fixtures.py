"""Create original CC0 synthetic sample deliverables; no customer data or AI output."""
from pathlib import Path
import shutil
from PIL import Image, ImageDraw

TARGET = Path(__file__).resolve().parents[1] / "fixtures"


def main() -> None:
    TARGET.mkdir(exist_ok=True)
    (TARGET / "brief.txt").write_text(
        "Deliver a transparent PNG logo and an SVG logo.\n"
        "Deliver exactly three distinct 1080 × 1080 PNG launch images.\n"
        "Provide a guide explaining how to update the website contact email.\n", encoding="utf-8")
    (TARGET / "maintenance-notes.md").write_text(
        "# Maintaining the website\n\nTo update the contact email, open the site editor, "
        "select the Contact section, change the Email field, and publish the site. "
        "Send a test message to verify the new address.\n", encoding="utf-8")
    (TARGET / "contact-guide.md").write_text("# Client guide\n\nWelcome to your new website.\n", encoding="utf-8")
    for filename, color, size in [
        ("launch-01.png", "#d8e4da", (1080, 1080)),
        ("launch-02.png", "#eed8bd", (1080, 1080)),
        ("launch-wrong-size.png", "#c7d4e3", (1200, 900)),
    ]:
        image = Image.new("RGB", size, color)
        draw = ImageDraw.Draw(image)
        draw.rectangle((70, 70, size[0] - 70, size[1] - 70), outline="#274537", width=8)
        draw.ellipse((150, 150, 380, 380), fill="#274537")
        draw.line((150, 500, size[0] - 150, 500), fill="#274537", width=18)
        image.save(TARGET / filename)
    shutil.copyfile(TARGET / "launch-02.png", TARGET / "launch-03-duplicate.png")
    opaque = Image.new("RGBA", (400, 160), "#f8f4e9")
    ImageDraw.Draw(opaque).rectangle((50, 40, 120, 110), fill="#274537")
    opaque.save(TARGET / "logo-opaque.png")
    transparent = Image.new("RGBA", (400, 160), (0, 0, 0, 0))
    ImageDraw.Draw(transparent).rectangle((50, 40, 120, 110), fill="#274537")
    transparent.save(TARGET / "logo-transparent.png")
    (TARGET / "logo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="160" viewBox="0 0 400 160">'
        '<rect x="40" y="40" width="80" height="80" fill="#274537"/>'
        '<path d="M60 80L76 96L108 60" fill="none" stroke="#f8f4e9" stroke-width="8"/>'
        '</svg>\n', encoding="utf-8")
    (TARGET / "README.md").write_text(
        "# Synthetic demo files\n\nAll files in this directory are original synthetic examples dedicated to CC0 1.0. "
        "They contain no client data or model results. Regenerate with scripts/create_fixtures.py.\n\n"
        "The faulty packet uses logo-opaque.png, logo.svg, launch-01.png, launch-02.png, "
        "launch-03-duplicate.png, launch-wrong-size.png, contact-guide.md and maintenance-notes.md. "
        "The duplicate is byte-identical; the opaque PNG has an alpha channel but no transparent pixels. "
        "logo-transparent.png is a correction fixture.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
