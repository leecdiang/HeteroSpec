"""Offline figure preflight; run after build_figures.py.

Checks the delivered PDFs, data identity, plotted marker coverage and text bounds.
It does not prescribe titles, figure count or number of panels. Optional raster
and grayscale exports support visual review, which remains necessary for layout.
Requires PyMuPDF, Pillow and the Poppler pdffonts utility.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import fitz

P = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--render', action='store_true', help='Also save color and grayscale PDF renders.')
parser.add_argument('--render-dir', type=Path, default=P/'generated/figure_previews')
args = parser.parse_args()
if not __debug__:
    raise RuntimeError('Run this preflight without Python -O so assertions remain active.')
manifest = json.loads((P/'FIGURE_MANIFEST.json').read_text())
layout = json.loads((P/'generated/FIGURE_LAYOUT_CHECK.json').read_text())
identities = json.loads((P/'revision/FIGURE_INPUT_IDENTITY.json').read_text())

data_checks = []
for item in identities['files']:
    data = (P/item['path']).read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    assert blob == item['git_blob_sha1'], item['path']
    assert sha256 == item['sha256'], item['path']
    data_checks.append({'path': item['path'], 'git_blob_sha1': blob, 'sha256': sha256})

hash_inputs = {'analysis_sha256': 'generated/analysis.json',
               'added_root_points_sha256': 'data_added/application_root_ratios.json',
               'rewrite_source_projection_sha256': 'data_added/rewrite_figure_sources.json'}
for field, path in hash_inputs.items():
    expected = hashlib.sha256((P/path).read_bytes()).hexdigest()
    assert all(item[field] == expected for item in manifest), path

for item in layout:
    assert not item['text_outside_canvas'], (item['figure'], item['text_outside_canvas'])
    boxes = item['text_boxes']
    for i, first in enumerate(boxes):
        x0, y0, x1, y1 = first['bbox_px']
        first_area = max(0, x1-x0)*max(0, y1-y0)
        for second in boxes[i+1:]:
            u0, v0, u1, v1 = second['bbox_px']
            second_area = max(0, u1-u0)*max(0, v1-v0)
            overlap = max(0, min(x1,u1)-max(x0,u0))*max(0, min(y1,v1)-max(y0,v0))
            assert overlap <= .03*min(first_area,second_area)+.01, (item['figure'], first['text'], second['text'])

# Every referenced generated figure is represented in the manifest and delivered.
tex_files = list(P.glob('*.tex')) + list((P/'sections').glob('*.tex'))
references = set()
for path in tex_files:
    references.update(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{(figures/[^}]+)\}', path.read_text()))
produced = {f"figures/{item['file']}.pdf" for item in manifest}
assert references <= produced, sorted(references-produced)

if args.render:
    from PIL import Image, ImageDraw, ImageOps
    args.render_dir.mkdir(parents=True, exist_ok=True)

pdf_checks = []
for item in manifest:
    name = item['file']
    for suffix in ('pdf', 'svg', 'png'):
        assert (P/'figures'/f'{name}.{suffix}').is_file(), (name, suffix)
    if item['expected_marker_count'] is not None:
        assert item['plotted_marker_count'] == item['expected_marker_count'], name
    assert item['clipped_marker_count'] == 0, name
    path = P/'figures'/f'{name}.pdf'
    document = fitz.open(path)
    assert len(document) == 1, name
    page = document[0]
    size = [page.rect.width/72, page.rect.height/72]
    assert max(abs(a-b) for a,b in zip(size,item['size_in'])) < .002, name
    fonts = subprocess.run(['pdffonts', str(path)], check=True, capture_output=True, text=True)
    assert not fonts.stderr.strip(), (name,fonts.stderr)
    font_rows = fonts.stdout.splitlines()[2:]
    assert font_rows and all('yes yes yes' in row for row in font_rows), (name,font_rows)
    spans = [span for block in page.get_text('dict')['blocks'] if 'lines' in block
             for line in block['lines'] for span in line['spans']]
    assert spans and not any('\ufffd' in span['text'] for span in spans), name
    assert len(page.get_images()) == 0, name
    if args.render:
        pix = page.get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False)
        rendered = args.render_dir/f'{name}_pdf.png'
        pix.save(rendered)
        ImageOps.grayscale(Image.open(rendered)).save(args.render_dir/f'{name}_gray.png')
    pdf_checks.append({'figure': name, 'pdf_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'size_in': size, 'font_sizes_pt': sorted({round(s['size'],3) for s in spans}),
                       'embedded_fonts': font_rows, 'raster_image_count': 0,
                       'plotted_marker_count': item['plotted_marker_count'],
                       'expected_marker_count': item['expected_marker_count'],
                       'clipped_marker_count': item['clipped_marker_count']})
    document.close()

if args.render:
    width, height = 900, 640
    rows = (len(manifest)+2)//3
    sheet = Image.new('RGB',(width*3,height*rows),'white')
    draw = ImageDraw.Draw(sheet)
    for i,item in enumerate(manifest):
        im = Image.open(args.render_dir/f"{item['file']}_gray.png").convert('RGB')
        im.thumbnail((width-30,height-50))
        x, y = (i%3)*width,(i//3)*height
        draw.text((x+15,y+10),item['file'],fill='black')
        sheet.paste(im,(x+15,y+35))
    sheet.save(args.render_dir/'all_figures_grayscale.png')

report = {'pdfs': pdf_checks, 'unchanged_numeric_inputs': data_checks,
          'referenced_figures': sorted(references),
          'canvas_bounds_passed': True, 'text_overlap_screen_passed': True,
          'manual_review_required': 'Inspect actual PDF renders, grayscale encodings and the compiled manuscript.'}
out = P/'generated/FIGURE_PDF_CHECK.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(f"Figure preflight PASS: {len(pdf_checks)} vector PDFs; {len(data_checks)} unchanged numeric inputs; all referenced exports and embedded fonts checked.")
