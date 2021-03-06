from collections import defaultdict
import json
from pathlib import Path

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QDate
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QTreeWidgetItemIterator

_ui_path = Path(__file__).parent

# Work around removal of PyQt5/uic/widget-plugins/qgis_customwidgets.py
# which breaks QT Designer UI files
from .widget_daterange import WIDGET_DATE_RANGE, BASE_DATE_RANGE
# WIDGET_DATE_RANGE, BASE_DATE_RANGE = uic.loadUiType(Path(_ui_path, 'widget_daterange.ui'))
WIDGET_PRODUCT, BASE_PRODUCT = uic.loadUiType(Path(_ui_path, 'widget_product.ui'))


class WidgetDateRange(BASE_DATE_RANGE, WIDGET_DATE_RANGE):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.setupUi(self)

        self._dateformat = 'yyyy-MM-dd'

        self._start = self.date_start.dateTime().toString(self._dateformat)
        self._end = self.date_end.dateTime().toString(self._dateformat)

        self.date_start.valueChanged.connect(self.update_start)
        self.date_end.valueChanged.connect(self.update_end)

    def set_value(self, data):
        data = data if data else None
        data = json.loads(data) if isinstance(data, str) else data

        if data is None:
            self.date_start.clear()
            self.date_end.clear()

            self._start = None
            self._end = None
        else:
            # data[-1] is in case a single value is passed. Set both dates to that value
            self.date_start.setDate(QDate.fromString(data[0], self._dateformat))
            self.date_end.setDate(QDate.fromString(data[-1], self._dateformat))

            self._start = data[0]
            self._end = data[-1]

    def update_start(self, qdatetime):
        self._start = qdatetime.toString(self._dateformat)

    def update_end(self, qdatetime):
        self._end = qdatetime.toString(self._dateformat)

    def value(self):
        retval = [self._start, self._end]
        return json.dumps(retval)


class WidgetProducts(BASE_PRODUCT, WIDGET_PRODUCT):

    def __init__(self, items=None, *args, **kwargs):
        super().__init__()
        self.setupUi(self)

        self._data = None
        self.set_items(items)

    def get_checked(self):
        return self.get_items(flags=QTreeWidgetItemIterator.Checked)

    def get_items(self, flags=QTreeWidgetItemIterator.All):
        """ Returns an iterator over the tree items. """

        # noinspection PyTypeChecker
        twit = QTreeWidgetItemIterator(self.tree_products, flags)

        while twit.value() is not None: #This 'orrible iteration style offends me greatly
            yield twit.value()
            twit += 1

    def get_value(self):
        """ Return checked """
        data = defaultdict(list)

        for item in self.get_checked():
            value = item.text(0)
            parent = item.parent()
            if parent is None:
                _ = data[value]
            else:
                data[parent.text(0)].append(value)

        return data

    def set_items(self, data=None):
        """" Build the tree afresh with no selections """
        self.tree_products.clear()

        data = data if data else {}
        self._data = json.loads(data) if isinstance(data, str) else data

        for product, measurements in self._data.items():
            parent = QTreeWidgetItem(self.tree_products)
            parent.setText(0, product)
            # noinspection PyTypeChecker
            parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)

            for measurement in measurements:
                child = QTreeWidgetItem(parent)
                # noinspection PyTypeChecker
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setText(0, measurement)
                child.setCheckState(0, Qt.Unchecked)

    def set_value(self, data=None):
        """" Select items in the tree
             This is mostly used when running alg from history so the dialog loads all products
             and reselects original prod/measurement selections"""

        data = data if data else {}
        data = json.loads(data) if isinstance(data, str) else data

        for item in self.get_items():
            value = item.text(0)
            parent = item.parent()
            if parent is None:
                if value in data:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)
            else:
                parent_value = parent.text(0)
                if parent_value in data and value in data[parent_value]:
                    item.setCheckState(0, Qt.Checked)
                else:
                    item.setCheckState(0, Qt.Unchecked)

    def value(self):
        return json.dumps(self.get_value())


# # Stub for alternative TreeView widget using Model-View-Controller (MVC) design pattern
# WIDGET_PRODUCTS, BASE_PRODUCTS = uic.loadUiType(
#     os.path.join(_ui_path, 'widget_products.ui')) # This is a QTreeView, not a QTreeWidget
#
# class WidgetProducts(BASE_PRODUCTS, WIDGET_PRODUCTS):
#
#     def __init__(self, data=None, *args, **kwargs):
#         super().__init__()
#         self.setupUi(self)
#
#         self._data = None

#         self._model = QStandardItemModel()
#
#         self.set_data(data)
#
#     def set_data(self, data=None):
#         self._data = data if data else {}
#         self._model = QStandardItemModel()
#         self.tree_products.setModel(self._model)
#         root = self._model.invisibleRootItem()
#
#         for product, measurements in self._data.items():
#             parent = QStandardItem(product)
#             parent.setFlags(parent.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
#             parent.setCheckState(Qt.Unchecked)
#             root.appendRow(parent)
#
#             for measurement in measurements:
#                 child = QStandardItem(measurement)
#                 child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
#                 #child.setText(0, measurement)
#                 child.setCheckState(Qt.Unchecked)
#                 parent.appendRow(child)
