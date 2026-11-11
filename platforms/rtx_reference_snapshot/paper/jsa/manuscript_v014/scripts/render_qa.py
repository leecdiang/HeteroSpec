"""Render PDFs and numbered contact sheets for manual visual inspection."""
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'visual_pages'


def main():
    for name, filename in [('main', 'jsa-manuscript-v0.14.0.pdf'),
                           ('supplement', 'jsa-supplement-v0.14.0.pdf')]:
        directory = OUT / name
        directory.mkdir(parents=True, exist_ok=True)
        for previous in directory.glob('page-*.png'):
            previous.unlink()
        subprocess.run(['pdftoppm', '-r', '100', '-png', str(ROOT / 'output' / filename),
                        str(directory / 'page')], check=True)
        pages = sorted(directory.glob('page-*.png'))
        for start in range(0, len(pages), 4):
            sheet = Image.new('RGB', (1700, 2240), '#edf0f3')
            draw = ImageDraw.Draw(sheet)
            for position, path in enumerate(pages[start:start + 4]):
                page = Image.open(path).convert('RGB')
                page.thumbnail((850, 1100))
                x, y = (position % 2) * 850, (position // 2) * 1120
                sheet.paste(page, (x, y + 20))
                draw.text((x + 5, y + 2), f'{name} page {start + position + 1}', fill='black')
            sheet.save(OUT / f'{name}-{start + 1:02d}-{min(start + 4, len(pages)):02d}.png')
        print(name, len(pages), 'pages rendered; inspect the images manually')


if __name__ == '__main__':
    main()
