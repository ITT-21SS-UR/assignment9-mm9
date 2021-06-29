#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pathlib
import sys
import pandas as pd
from enum import Enum
from PyQt5 import QtWidgets, QtGui, uic, QtCore
from dollar_one_recognizer import DollarOneRecognizer


class Mode(Enum):
    LEARN = "Learn"
    PREDICT = "Predict"


# noinspection PyAttributeOutsideInit
class GestureRecognizer(QtWidgets.QWidget):
    """
    Uses a 1$ gesture recognizer that tries to predict pre-defined gestures.
    """
    def __init__(self):
        super(GestureRecognizer, self).__init__()
        self.__log_folder = "existing_gestures"
        self.__log_file_path = pathlib.Path(self.__log_folder) / "gestures.csv"

        self.dollar_one_recognizer = DollarOneRecognizer()

        self._init_save_file()
        self._init_ui()

    def _init_save_file(self):
        folder_path = pathlib.Path(self.__log_folder)
        if not folder_path.is_dir():
            folder_path.mkdir()

        # check if the file already exists
        if self.__log_file_path.exists():
            # load existing gestures
            self.existing_gestures = pd.read_csv(self.__log_file_path, sep=",")
        else:
            # or create a new csv if it doesn't exist
            self.existing_gestures = pd.DataFrame(columns=['gesture_name', 'gesture_data'])

    def _save_to_file(self, gesture_name):
        current_points = self.ui.draw_widget.get_current_points()
        # TODO for now if a gesture already exists, it is simply replaced with the new one -> ask user if he wants that
        if gesture_name in self.existing_gestures['gesture_name'].unique():
            # replace the existing data for this gesture_name with the new data
            # current_points needs to be wrapped into a list otherwise replacing the np.array directly would lead to a
            # crash: "ValueError: cannot copy sequence with size ... to array axis with dimension 1"
            self.existing_gestures.loc[self.existing_gestures['gesture_name'] == gesture_name,
                                       "gesture_data"] = [current_points]
        else:
            # save the new points as list instead of a numpy array for the same reason as above
            new_gesture = {'gesture_name': gesture_name, 'gesture_data': [current_points]}
            self.existing_gestures = self.existing_gestures.append(new_gesture, ignore_index=True)

        self.existing_gestures.to_csv(self.__log_file_path, sep=",", index=False)

    def _init_ui(self):
        self.ui = uic.loadUi("gesture_recognizer.ui", self)
        self.ui.mode_selection.setFocusPolicy(QtCore.Qt.NoFocus)  # prevent auto-focus

        self._setup_draw_widget()
        self._setup_learn_ui()
        self._setup_predict_ui()

        # connect the dropdown menu to switch between adding and prediction gestures
        self.ui.mode_selection.currentIndexChanged.connect(self.mode_changed)
        self.ui.mode_selection.setCurrentIndex(0)  # set the first item in the dropdown box as selected at the start
        self.ui.predict_ui.hide()
        self.ui.learn_ui.show()

    def _setup_learn_ui(self):
        self.ui.btn_save.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.btn_save.clicked.connect(self._save_template)

    def _setup_predict_ui(self):
        self.ui.btn_predict.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ui.btn_predict.clicked.connect(self._predict_gesture)

    def mode_changed(self, index):
        self.current_mode = self.mode_selection.currentText()
        print(f"Current index {index}; selection changed to {self.current_mode}")

        if self.current_mode == Mode.LEARN.value:
            # reset data when switching from learn to predict and vice versa and show the correct ui
            self._show_learn_ui()
        elif self.current_mode == Mode.PREDICT.value:
            self._show_predict_ui()
        else:
            print(f"Mode {self.current_mode} not known!")

    def _show_learn_ui(self):
        self.ui.draw_widget.reset_current_points()
        self.ui.error_label.setText("")
        self._reset_learn_ui()
        self.ui.predict_ui.hide()
        self.ui.learn_ui.show()

    def _show_predict_ui(self):
        self.ui.error_label.setText("")
        self._reset_predict_ui()
        # TODO show which gestures were already recorded:
        # existing_activities = self.existing_activity_data.activity.unique()
        # self.predict_text_field.setHtml(f"Existing recorded activities: {existing_activities}")
        self.ui.learn_ui.hide()
        self.ui.predict_ui.show()

    def custom_filter(self, points):
        return self.dollar_one_recognizer.normalize(points)

    def transpose_points(self, points):
        return list(map(list, zip(*points)))

    def _setup_draw_widget(self):
        # set the draw widgets custom filter variable to the function of the same way which applies our transformation stack
        self.ui.draw_widget.set_custom_filter(self.custom_filter)

    def _save_template(self):
        # check if a name for this gesture has been entered
        if not self.ui.gesture_name_input.text():
            self.ui.error_label.setText("You have to enter a name for the drawn gesture to save it!")
            return
        elif len(self.ui.draw_widget.get_current_points()) < 1:  # TODO at least 32 points?
            self.ui.error_label.setText("You have to draw more to save this as a gesture!")
            return

        self.ui.error_label.setText("")  # hide error label
        gesture_name = self.ui.gesture_name_input.text()
        self._save_to_file(gesture_name)
        self._reset_canvas()  # reset the current gesture data on the canvas!

    def _reset_learn_ui(self):
        self.gesture_name_input.setText("")
        self._reset_canvas()

    def _reset_predict_ui(self):
        self.ui.prediction_result.setText("No gesture found!")
        self._reset_canvas()

    def _reset_canvas(self):
        self.ui.draw_widget.reset_current_points()
        self.ui.draw_widget.update()  # update the draw widget immediately so it will be redrawn without the points

    def _predict_gesture(self):
        if len(self.ui.draw_widget.get_current_points()) < 1:  # TODO ?
            self.ui.error_label.setText("You have to draw a gesture on the canvas to predict it!")
            return

        self.ui.error_label.setText("")
        """
        # TODO call recognize for template and sample
        if not len(self.ui.draw_widget.points) < 1:
            # plot(self.transpose_points(dw.points)[0], self.transpose_points(dw.points)[1])
            s1 = self.dollar_one_recognizer.normalize([(-1, 0), (0, -1), (1, 0), (0, 1)])

            sim = self.dollar_one_recognizer.recognize(s1, self.dollar_one_recognizer.normalize(dw.points))
            print("similarity:", sim)
        """

    def paintEvent(self, event: QtGui.QPaintEvent):
        # TODO
        pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    recognizer = GestureRecognizer()
    recognizer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
