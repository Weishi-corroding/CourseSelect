"""Generate offline previews and compare table population with the committed version.

Run from the repository root: python tools/preview_desktop.py
Account data is mocked. Only the public local course catalog is read.
"""
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
if Path('C:/Windows/Fonts').is_dir():
    os.environ.setdefault('QT_QPA_FONTDIR', 'C:/Windows/Fonts')

from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication
import modern_ui_production as ui
from course_query_ui import CourseQueryUI, CourseQueryEngine


def main():
    app = QApplication([])
    app.setStyle('Fusion')
    if Path('C:/Windows/Fonts/msyh.ttc').exists():
        QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
    output = ROOT / 'artifacts' / 'desktop-preview'
    output.mkdir(parents=True, exist_ok=True)
    with patch.object(ui.ProductionGlassmorphismUI, 'load_settings'), \
         patch.object(ui, 'load_accounts', return_value=[{'name': '演示账号', 'username': '20260000'}]), \
         patch.object(ui, 'load_courses', return_value={'演示账号': ['1234501', '1234502', '1234503']}), \
         patch.object(ui, 'load_delete_courses', return_value={}):
        window = ui.ProductionGlassmorphismUI()
        window.user_combo.setCurrentText('演示账号')
        window.show()
        for dark in (True, False):
            window.dark_mode = dark
            window.apply_glassmorphism_style()
            app.processEvents()
            window.grab().save(str(output / f"workspace-{'dark' if dark else 'light'}.png"))
        window.resize(960, 700)
        app.processEvents()
        window.grab().save(str(output / 'workspace-compact.png'))
        window.query_panel._load_file(str(ROOT / 'courses_full.json'))
        window.open_course_query()
        app.processEvents()
        window.grab().save(str(output / 'workspace-course-query.png'))
        account_samples = [
            {'name': '演示账号', 'username': '20260000', 'password': 'hidden'},
            {'name': '第二账号', 'username': '20260001', 'password': 'hidden'},
        ]
        cookie_dialog = ui.SelectAccountsDialog(window, account_samples)
        cookie_dialog.show()
        app.processEvents()
        cookie_dialog.grab().save(str(output / 'cookie-update-dialog.png'))
        cookie_dialog.close()
        account_dialog = ui.ManageAccountsDialog(window, account_samples)
        account_dialog.show()
        app.processEvents()
        account_dialog.grab().save(str(output / 'manage-accounts-dialog.png'))
        account_dialog.close()
        window.close()

    catalog = json.loads((ROOT / 'courses_full.json').read_text(encoding='utf-8'))
    results = CourseQueryEngine(catalog).query()
    source = subprocess.run(['git', 'show', 'HEAD:course_query_ui.py'], cwd=ROOT,
                            capture_output=True, check=True, encoding='utf-8').stdout
    namespace = {'__name__': 'baseline_query', '__file__': str(ROOT / 'course_query_ui.py')}
    exec(compile(source, 'baseline_query.py', 'exec'), namespace)
    baseline = namespace['CourseQueryUI']()
    current = CourseQueryUI()

    def measure(window):
        samples = []
        for _ in range(5):
            window._populate_table([])
            start = time.perf_counter()
            window._populate_table(results)
            samples.append((time.perf_counter() - start) * 1000)
        return round(statistics.median(samples), 2)

    report = {
        'rows': len(results), 'columns': 12,
        'baseline_populate_ms': measure(baseline),
        'updated_populate_ms': measure(current),
        'note': 'Median of 5 offline runs; population only, excluding network, parsing and first paint.',
    }
    current.show()
    app.processEvents()
    current.grab().save(str(output / 'course-query.png'))
    (output / 'benchmark.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    current.close()
    baseline.close()


if __name__ == '__main__':
    main()
