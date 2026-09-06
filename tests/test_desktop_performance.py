"""Offline regression checks. No account files, login or enrollment calls are used."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.path.isdir("C:/Windows/Fonts"):
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch, MagicMock

from PyQt5.QtCore import Qt, QItemSelectionModel, QPersistentModelIndex, QTimer
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QAbstractItemView

import modern_ui_production as ui
from course_query_ui import CourseQueryEngine, detect_campus
from ui_support import BufferedLogView, InterruptibleThread
from course_table_model import CourseTableModel


APP = QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)
if os.path.exists("C:/Windows/Fonts/msyh.ttc"):
    QFontDatabase.addApplicationFont("C:/Windows/Fonts/msyh.ttc")


def wait_until(predicate, timeout=2000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    return predicate()


class SleepingWorker(InterruptibleThread):
    def run(self):
        self.msleep(30000)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.mocks = ExitStack()
        self.mocks.enter_context(patch.object(ui.ProductionGlassmorphismUI, 'load_settings'))
        self.mocks.enter_context(patch.object(ui, 'load_accounts', return_value=[
            {'name': 'Demo', 'username': '000000', 'password': 'unused'}]))
        self.mocks.enter_context(patch.object(ui, 'load_courses', return_value={'Demo': ['101', '102']}))
        self.mocks.enter_context(patch.object(ui, 'load_delete_courses', return_value={}))
        self.mocks.enter_context(patch.object(ui, 'load_cookies_dict', return_value={'Demo': 'mock'}))
        self.window = ui.ProductionGlassmorphismUI()
        self.window.user_combo.setCurrentText('Demo')

    def tearDown(self):
        self.window.stop_selection()
        self.assertTrue(wait_until(lambda: not self.window._managed_workers))
        self.window.close()
        self.window.deleteLater()
        APP.processEvents()
        self.mocks.close()

    def test_stop_wakes_backoff_and_retains_running_thread(self):
        worker = SleepingWorker()
        self.window.is_running = True
        self.window.workers.append(worker)
        self.window._queue_worker(worker)
        self.assertTrue(wait_until(worker.isRunning))
        start = time.perf_counter()
        self.window.stop_selection()
        self.assertIn(worker, self.window._managed_workers)
        self.assertTrue(wait_until(lambda: not self.window._managed_workers))
        self.assertLess(time.perf_counter() - start, 1)
        self.assertFalse(self.window._stopping)
        self.assertTrue(self.window.start_stop_button.isEnabled())

    def test_cancelled_delayed_worker_never_starts_after_restart(self):
        worker = SleepingWorker()
        starts = []
        worker.started.connect(lambda: starts.append(True))
        self.window.is_running = True
        self.window._queue_worker(worker, 100)
        self.window.stop_selection()
        self.window.is_running = True
        QTest.qWait(150)
        self.assertEqual(starts, [])

    def test_stop_prework_prevents_next_drop_and_selection(self):
        calls = []
        worker = ui.PreWorkThread('mock', [
            {'courseCode': 'a', 'classNo': '1'}, {'courseCode': 'b', 'classNo': '2'}])

        def cancel(*args):
            calls.append(args)
            worker.stop()
            return 'mock result'

        completed = []
        worker.finished_signal.connect(lambda: completed.append(True))
        with patch.object(ui, 'cancelSC', side_effect=cancel):
            worker.start()
            self.assertTrue(worker.wait(1000))
        APP.processEvents()
        self.assertEqual(len(calls), 1)
        self.assertEqual(completed, [])

    def test_close_waits_for_inflight_request_without_blocking_ui(self):
        class RequestWorker(InterruptibleThread):
            def run(self):
                time.sleep(0.15)  # Simulate a request already in flight.

        self.window.show()
        self.window.is_running = True
        worker = RequestWorker()
        self.window._queue_worker(worker)
        self.assertTrue(wait_until(worker.isRunning))
        start = time.perf_counter()
        self.window.close()
        self.assertLess(time.perf_counter() - start, 0.1)
        self.assertTrue(self.window.isVisible())
        self.assertTrue(wait_until(lambda: not self.window.isVisible()))

    def test_empty_account_clears_plan(self):
        self.assertEqual(self.window.course_list.count(), 2)
        self.window.user_combo.setCurrentIndex(0)
        self.assertEqual(self.window.course_list.count(), 0)
        self.assertFalse(self.window.start_stop_button.isEnabled())

    def test_legacy_menu_items_are_removed_and_account_controls_are_present(self):
        menus = {action.text(): action.menu() for action in self.window.menuBar().actions()}
        self.assertEqual(set(menus), {'文件', '设置'})
        setting_items = {action.text() for action in menus['设置'].actions() if not action.isSeparator()}
        self.assertEqual(setting_items, {
            '管理选课人', '并发/查询间隔', '配置微信推送', '切换为浅色模式',
        })
        self.assertEqual(self.window.add_account_button.text(), '+')
        self.assertEqual(self.window.add_account_button.toolTip(), '添加选课人')

    def test_delete_key_removes_selected_planned_course(self):
        selection = self.window.course_list.selectionModel()
        selection.select(self.window.course_list.model().index(0, 0),
                         QItemSelectionModel.Select | QItemSelectionModel.Rows)
        selection.select(self.window.course_list.model().index(1, 0),
                         QItemSelectionModel.Select | QItemSelectionModel.Rows)
        with patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.Yes), \
             patch.object(ui, 'save_courses') as save:
            QTest.keyClick(self.window.course_list, Qt.Key_Delete)
            save.assert_called_once()
        self.assertEqual(save.call_args.args[0]['Demo'], [])
        self.assertEqual(self.window.course_list.count(), 0)

    def test_delete_key_removes_selected_drop_course(self):
        plan = {'Demo': [
            {'courseCode': 'A', 'classNo': '1'},
            {'courseCode': 'B', 'classNo': '2'},
        ]}
        with patch.object(ui, 'load_delete_courses', return_value=plan), \
             patch.object(ui, 'save_delete_courses') as save, \
             patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.Yes):
            self.window.on_user_changed('Demo')
            self.window.delete_course_list.setCurrentRow(1)
            QTest.keyClick(self.window.delete_course_list, Qt.Key_Delete)
            save.assert_called_once()
        self.assertEqual(save.call_args.args[0]['Demo'], [{'courseCode': 'A', 'classNo': '1'}])
        self.assertEqual(self.window.delete_course_list.count(), 1)

    def test_cookie_picker_filters_and_selects_visible_accounts(self):
        accounts = [
            {'name': 'Alice', 'username': '100', 'password': 'x'},
            {'name': 'Bob', 'username': '200', 'password': 'x'},
        ]
        dialog = ui.SelectAccountsDialog(self.window, accounts)
        dialog.search_input.setText('200')
        dialog.select_all_cb.setChecked(True)
        self.assertEqual([account['name'] for account in dialog.get_selected_accounts()], ['Bob'])
        self.assertGreaterEqual(dialog.width(), 520)
        dialog.close()

    def test_all_row_lists_support_ctrl_multi_selection(self):
        accounts = [
            {'name': 'Alice', 'username': '100', 'password': 'x'},
            {'name': 'Bob', 'username': '200', 'password': 'x'},
        ]
        cookie_dialog = ui.SelectAccountsDialog(self.window, accounts)
        manager = ui.ManageAccountsDialog(self.window, accounts)
        self.assertEqual(self.window.course_list.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertEqual(self.window.delete_course_list.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertEqual(cookie_dialog.account_tree.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertEqual(manager.account_list.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertEqual(self.window.query_panel.table.selectionMode(), QAbstractItemView.ExtendedSelection)
        cookie_dialog.close()
        manager.close()

    def test_account_removal_cleans_linked_configuration(self):
        account = {'name': 'Demo', 'username': '000000', 'password': 'unused'}
        dialog = ui.ManageAccountsDialog(self.window, [account])
        with patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.Yes), \
             patch.object(ui, 'save_accounts') as save_accounts, \
             patch.object(ui, 'load_courses', return_value={'Demo': ['101']}), \
             patch.object(ui, 'save_courses') as save_courses, \
             patch.object(ui, 'load_delete_courses', return_value={'Demo': [{'courseCode': 'x'}]}), \
             patch.object(ui, 'save_delete_courses') as save_delete, \
             patch.object(ui, 'load_cookies_dict', return_value={'Demo': 'cookie'}), \
             patch.object(ui, 'save_cookies_dict') as save_cookies:
            dialog._delete_account()
        save_accounts.assert_called_once_with([])
        save_courses.assert_called_once_with({})
        save_delete.assert_called_once_with({})
        save_cookies.assert_called_once_with({})
        dialog.close()

    def test_course_query_is_embedded_and_uses_selected_account(self):
        self.assertEqual(self.window.tabs.count(), 3)
        self.window.open_course_query()
        self.assertIs(self.window.tabs.currentWidget(), self.window.query_panel)
        self.assertFalse(self.window.start_stop_button.isVisible())
        self.assertEqual(self.window.query_panel._fetch_identity(), ('Demo', 'mock'))
        self.assertIsNotNone(self.window.query_panel.course_add_callback)
        self.window.dark_mode = False
        self.window.apply_glassmorphism_style()
        self.assertFalse(self.window.query_panel.dark_mode)

    def test_query_result_can_be_added_to_current_account(self):
        panel = self.window.query_panel
        panel.table_model.set_rows([
            {'cttId': '303', 'kcmc': '测试课程', 'maxCnt': 10, 'enrollCnt': 0},
            {'cttId': '304', 'kcmc': '测试课程二', 'maxCnt': 10, 'enrollCnt': 0},
        ])
        selection = panel.table.selectionModel()
        selection.select(panel.table_model.index(0, 0),
                         QItemSelectionModel.Select | QItemSelectionModel.Rows)
        selection.select(panel.table_model.index(1, 0),
                         QItemSelectionModel.Select | QItemSelectionModel.Rows)
        with patch.object(ui, 'save_courses') as save:
            panel._add_selected_course()
            self.assertEqual(save.call_count, 2)
            self.assertIn('303', save.call_args.args[0]['Demo'])
            self.assertIn('304', save.call_args.args[0]['Demo'])
        self.assertIn('2 门课程', panel.status_label.text())

    def test_background_cookie_login_keeps_event_loop_responsive(self):
        beats = []
        timer = QTimer()
        timer.timeout.connect(lambda: beats.append(True))
        timer.start(10)
        worker = ui.CookieUpdateWorker([{'name': 'Demo', 'username': 'mock', 'password': 'mock'}])

        def login(*args, **kwargs):
            time.sleep(0.12)
            return [{'name': 'session', 'value': 'mock'}]

        with patch.object(ui, 'get_cookies', side_effect=login), patch.object(ui, 'save_cookies_dict') as save:
            worker.start()
            self.assertTrue(wait_until(worker.isFinished))
            save.assert_called_once()
        timer.stop()
        self.assertGreaterEqual(len(beats), 3)

    def test_captcha_load_and_parent_close_keep_ui_responsive(self):
        def get_image(*args, **kwargs):
            time.sleep(0.12)
            response = MagicMock()
            response.__enter__.return_value = response
            response.content = b'invalid image for offline test'
            return response

        self.window.show()
        with patch('requests.get', side_effect=get_image) as get:
            dialog = ui.CaptchaDialog(self.window, 'session=mock')
            dialog.show()
            start = time.perf_counter()
            self.window.close()
            self.assertLess(time.perf_counter() - start, 0.1)
            self.assertTrue(self.window.isVisible())
            self.assertTrue(wait_until(lambda: dialog.image_worker is None))
            self.assertTrue(wait_until(lambda: not self.window.isVisible()))
            get.assert_called_once()
        dialog.deleteLater()


class ModelAndLogTests(unittest.TestCase):
    def test_campus_detection_uses_location_keywords(self):
        songjiang_locations = (
            '松A101', '第二教学楼（松江）', '大学生体育中心游泳馆', '刘翔体育场东区',
            '4号学院楼6062', '图文5号机房', '图文信息大楼B115',
            '化工楼506', '复材大楼C321', '综合实验楼128', '工程训练中心329',
        )
        for location in songjiang_locations:
            with self.subTest(location=location):
                self.assertEqual(detect_campus(location), '松江')
        for location in (
            '延A201', '第三教学楼（延安路校区）',
            '1教206', '2教4号机房', '3教1208', '4教204',
            '逸夫楼1楼展厅', '逸402', '中南楼102', '中南104',
            '旭日楼310', '管理楼106', '3北402', '3南501', '3主302',
            '中北459', 'IECB218',
        ):
            with self.subTest(location=location):
                self.assertEqual(detect_campus(location), '延安路')
        self.assertEqual(detect_campus('校外实践基地'), '')

    def test_campus_filter_matches_keyword_locations(self):
        data = {'courses': [
            {
                'kcbh': '1', 'kcmc': '体育',
                'timetable': {'classes': [{
                    'cttId': '1', 'maxCnt': 10, 'enrollCnt': 0,
                    'schedule': [{'classroom': '大学生体育中心', 'time_slot': '', 'weeks': ''}],
                }]},
            },
            {
                'kcbh': '2', 'kcmc': '设计',
                'timetable': {'classes': [{
                    'cttId': '2', 'maxCnt': 10, 'enrollCnt': 0,
                    'schedule': [{'classroom': '延安路校区三教', 'time_slot': '', 'weeks': ''}],
                }]},
            },
        ]}
        engine = CourseQueryEngine(data)
        self.assertEqual([row['cttId'] for row in engine.query(campus='松江')], ['1'])
        self.assertEqual([row['cttId'] for row in engine.query(campus='延安路')], ['2'])

    def test_campus_filter_uses_scope_fallback_and_rejects_unknown_location(self):
        data = {'courses': [{
            'kcbh': '1', 'kcmc': '测试课程',
            'timetable': {'classes': [
                {
                    'cttId': '1', 'maxCnt': 10, 'enrollCnt': 0,
                    'selection_scope': '延安路校区',
                    'schedule': [{'classroom': '4教102', 'time_slot': '周一.1.2节', 'weeks': '1-16周'}],
                },
                {
                    'cttId': '2', 'maxCnt': 10, 'enrollCnt': 0,
                    'schedule': [{'classroom': '未知地点', 'time_slot': '周一.1.2节', 'weeks': '1-16周'}],
                },
            ]},
        }]}
        engine = CourseQueryEngine(data)
        self.assertEqual(
            [row['cttId'] for row in engine.query(campus='延安路', day_filter=1)],
            ['1'],
        )
        self.assertEqual(engine.query(campus='松江', day_filter=1), [])

    def test_numeric_sort_and_replacement_with_empty_results(self):
        model = CourseTableModel()
        model.set_rows([{'maxCnt': n, 'enrollCnt': 0} for n in (100, 2, 20)])
        selection = QPersistentModelIndex(model.index(0, 5))
        model.sort(5, Qt.AscendingOrder)
        self.assertEqual([model.index(i, 5).data() for i in range(3)], ['2', '20', '100'])
        self.assertEqual(selection.row(), 2)
        self.assertEqual(selection.data(), '100')
        model.sort(5, Qt.DescendingOrder)
        self.assertEqual([model.index(i, 5).data() for i in range(3)], ['100', '20', '2'])
        model.set_rows([])
        self.assertEqual(model.rowCount(), 0)

    def test_logs_are_bounded_plain_text_and_clear_pending_queue(self):
        view = BufferedLogView()
        for i in range(10000):
            view.append(f'<b>{i}</b>')
        view.flush()
        self.assertLessEqual(view.document().blockCount(), 3000)
        self.assertIn('<b>9999</b>', view.toPlainText())
        view.append('pending')
        view.clear()
        view.flush()
        self.assertEqual(view.toPlainText(), '')
        view.deleteLater()

    def test_log_refresh_does_not_jump_while_reading_history(self):
        view = BufferedLogView()
        view.resize(400, 200)
        view.show()
        for i in range(200):
            view.append(str(i))
        view.flush()
        APP.processEvents()
        bar = view.verticalScrollBar()
        bar.setValue(20)
        view.append('new line')
        view.flush()
        self.assertEqual(bar.value(), 20)
        view.close()
        view.deleteLater()


if __name__ == '__main__':
    unittest.main()
