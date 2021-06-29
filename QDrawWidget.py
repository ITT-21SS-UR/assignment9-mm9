"""
Original draw widget from GRIPS was slightly adjusted: constructor call updated so it could be promoted, some setters
and getters defined for cleaner access to the data.
"""

import sys
from PyQt5 import QtCore, QtWidgets, QtGui


class QDrawWidget(QtWidgets.QWidget):

    # constructor and super call had to be slightly adjusted so this widget could be used as a "Promote to" - option
    def __init__(self, *args, **kwargs):
        super(QDrawWidget, self).__init__(*args, **kwargs)
        # self.resize(800, 800)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.custom_filter = None
        self.drawing = False
        self.grid = True
        self.points = []
        self.setMouseTracking(True)  # only get events when button is pressed
        self.setWindowTitle('Drawable')

    def set_custom_filter(self, point_filter):
        self.custom_filter = point_filter

    def get_current_points(self):
        return self.points

    def reset_current_points(self):
        self.points = []

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.drawing = True
            self.points = []
            self.update()
        elif ev.button() == QtCore.Qt.RightButton:
            try:
                if self.custom_filter:
                    # custom_filter needs to be implemented outside!
                    self.points = self.custom_filter(self.points)
                else:
                    sys.stderr.write("\nCustom filter for the draw widget isn't set!")
            except NameError:
                pass

            self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.drawing = False
            self.update()

    def mouseMoveEvent(self, ev):
        if self.drawing:
            self.points.append((ev.x(), ev.y()))
            self.update()

    def poly(self, pts):
        return QtGui.QPolygonF(map(lambda p: QtCore.QPointF(*p), pts))

    def paintEvent(self, ev):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setBrush(QtGui.QColor(0, 0, 0))
        qp.drawRect(ev.rect())
        qp.setBrush(QtGui.QColor(20, 255, 190))
        qp.setPen(QtGui.QColor(0, 155, 0))
        qp.drawPolyline(self.poly(self.points))

        for point in self.points:
            qp.drawEllipse(point[0]-1, point[1] - 1, 2, 2)
        if self.grid:
            qp.setPen(QtGui.QColor(255, 100, 100, 20))  # semi-transparent

            for x in range(0, self.width(), 20):
                qp.drawLine(x, 0, x, self.height())

            for y in range(0, self.height(), 20):
                qp.drawLine(0, y, self.width(), y)

        qp.end()
