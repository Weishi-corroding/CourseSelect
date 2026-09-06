"""Course rows are rendered on demand instead of allocating one widget item per cell."""
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QFont


class CourseTableModel(QAbstractTableModel):
    HEADERS = ("课程代码", "课程编号", "课程名称", "学分", "班级", "容量",
               "已申请", "已录取", "余量", "教师", "校区", "上课时间")
    KEYS = ("kcbh", "cttId", "kcmc", "xf", "classNo", "maxCnt",
            "enrollCnt", "applyCnt", None, "teacher", "campus", "schedule")
    NUMERIC_COLUMNS = {3, 5, 6, 7, 8}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        self.available_color = QColor("#69d7ad")
        self.full_color = QColor("#e997a0")
        self.bold_font = QFont()
        self.bold_font.setBold(True)

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = self._sorted_rows(rows)
        self.endResetModel()

    def _sort_value(self, row, column):
        value = max(0, row['maxCnt'] - row['enrollCnt']) if column == 8 else row.get(self.KEYS[column], '')
        if column in self.NUMERIC_COLUMNS:
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        return str(value) if value is not None else ''

    def _sorted_rows(self, rows):
        if self._sort_column < 0:
            return list(rows)
        return sorted(rows, key=lambda row: self._sort_value(row, self._sort_column),
                      reverse=self._sort_order == Qt.DescendingOrder)

    def sort(self, column, order=Qt.AscendingOrder):
        if not 0 <= column < len(self.KEYS):
            return
        self._sort_column, self._sort_order = column, order
        # Sort in Python once instead of Qt calling back into Python for every comparison.
        order_indices = sorted(range(len(self.rows)),
                               key=lambda i: self._sort_value(self.rows[i], column),
                               reverse=order == Qt.DescendingOrder)
        self.layoutAboutToBeChanged.emit()
        previous = self.persistentIndexList()
        positions = {old: new for new, old in enumerate(order_indices)}
        self.rows = [self.rows[i] for i in order_indices]
        self.changePersistentIndexList(previous, [self.index(positions[i.row()], i.column()) for i in previous])
        self.layoutChanged.emit()

    def set_dark_mode(self, dark):
        self.available_color = QColor("#69d7ad" if dark else "#16724f")
        self.full_color = QColor("#e997a0" if dark else "#a93246")
        if self.rows:
            self.dataChanged.emit(self.index(0, 8), self.index(len(self.rows) - 1, 8), [Qt.ForegroundRole])

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return self.HEADERS[section] if orientation == Qt.Horizontal else section + 1

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, column = self.rows[index.row()], index.column()
        if role in (Qt.DisplayRole, Qt.ToolTipRole, Qt.UserRole):
            value = max(0, row['maxCnt'] - row['enrollCnt']) if column == 8 else row.get(self.KEYS[column], '')
            if role == Qt.UserRole and column in self.NUMERIC_COLUMNS:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0.0
            return str(value) if value is not None else ""
        if role == Qt.TextAlignmentRole:
            return int((Qt.AlignLeft if column in (2, 9, 11) else Qt.AlignHCenter) | Qt.AlignVCenter)
        if column == 8:
            available = row['maxCnt'] > row['enrollCnt']
            if role == Qt.ForegroundRole:
                return self.available_color if available else self.full_color
            if role == Qt.FontRole and available:
                return self.bold_font
        return None
