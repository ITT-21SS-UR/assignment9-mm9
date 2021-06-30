#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import pathlib
import sys
import pandas as pd
from enum import Enum
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtWidgets import QMessageBox
from dollar_one_recognizer import DollarOneRecognizer


class Mode(Enum):
    LEARN = "Learn"
    PREDICT = "Predict"


# noinspection PyAttributeOutsideInit
class GestureRecognizer(QtWidgets.QWidget):
    """
    Uses a 1$ gesture recognizer to predict pre-defined gestures.
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
            self.existing_gestures = pd.read_csv(self.__log_file_path, sep=";")
            # use a converter to convert saved list back to a list (by default it would be a string)
            self.existing_gestures['gesture_data'] = self.existing_gestures['gesture_data'].apply(ast.literal_eval)
        else:
            # or create a new csv if it doesn't exist
            self.existing_gestures = pd.DataFrame(columns=['gesture_name', 'gesture_data'])

    def _save_to_file(self, gesture_name):
        current_points = self.ui.draw_widget.get_current_points()
        # normalize gesture before saving so it doesn't have to be done everytime again when trying to predict sth
        normalized_gesture = self.custom_filter(current_points)

        if gesture_name in self.existing_gestures['gesture_name'].unique():
            # if the gesture already exists, ask the user if he wants to overwrite it
            choice = QMessageBox.question(self, 'Overwrite gesture?',
                                          "A gesture with this name already exists! Do you want to overwrite it?",
                                          QMessageBox.Yes | QMessageBox.No)
            if choice == QMessageBox.Yes:
                # replace the existing data for this gesture_name with the new data
                # normalized_gesture needs to be wrapped into a list otherwise replacing the np.array directly would
                # lead to a crash: "ValueError: cannot copy sequence with size ... to array axis with dimension 1"
                self.existing_gestures.loc[self.existing_gestures['gesture_name'] == gesture_name,
                                           "gesture_data"] = [normalized_gesture]
                self.ui.save_label.setText(f"Old content for gesture \"{gesture_name}\" was successfully overwritten!")
            else:
                return

        else:
            # save the new points as list instead of a numpy array for the same reason as above
            new_gesture = {'gesture_name': gesture_name, 'gesture_data': [normalized_gesture]}
            self.existing_gestures = self.existing_gestures.append(new_gesture, ignore_index=True)
            self.ui.save_label.setText(f"Gesture \"{gesture_name}\" was successfully saved!")

        self.existing_gestures.to_csv(self.__log_file_path, sep=";", index=False)

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
        # TODO show which gestures were already recorded to user as well (let him delete specific ones?)
        known_gestures = self.existing_gestures.gesture_name.unique()
        print(f"Existing gestures: {known_gestures}")

        self.ui.learn_ui.hide()
        self.ui.predict_ui.show()

    def custom_filter(self, points):
        return self.dollar_one_recognizer.normalize(points)

    def _setup_draw_widget(self):
        # set the draw widgets custom filter variable to the function of the same way which applies our
        # transformation stack
        self.ui.draw_widget.set_custom_filter(self.custom_filter)

    def _save_template(self):
        # check if a name for this gesture has been entered
        if not self.ui.gesture_name_input.text():
            self.ui.error_label.setText("You have to enter a name for the drawn gesture to save it!")
            return
        elif len(self.ui.draw_widget.get_current_points()) < 1:
            self.ui.error_label.setText("You have to draw more to save this as a gesture!")
            return

        self.ui.error_label.setText("")  # hide error label
        gesture_name = self.ui.gesture_name_input.text()

        self._save_to_file(gesture_name)
        self.ui.gesture_name_input.clear()  # reset the name input field
        self._reset_canvas()  # reset the current gesture data on the canvas!

    def _reset_learn_ui(self):
        self.ui.gesture_name_input.setText("")
        self.ui.save_label.setText("")
        self._reset_canvas()

    def _reset_predict_ui(self):
        self.ui.prediction_result.setText("No gesture found!")
        self._reset_canvas()

    def _reset_canvas(self):
        self.ui.draw_widget.reset_current_points()
        self.ui.draw_widget.update()  # update the draw widget immediately so it will be redrawn without the points

    def _predict_gesture(self):
        if len(self.ui.draw_widget.get_current_points()) < 1:
            self.ui.error_label.setText("You have to draw a gesture on the canvas to predict it!")
            return

        self.ui.error_label.setText("")
        drawn_gesture = self.ui.draw_widget.get_current_points()
        normalized_gesture = self.custom_filter(drawn_gesture)

        template_dict = dict(self.existing_gestures.values)
        recognition_result = self.dollar_one_recognizer.recognize(normalized_gesture, template_dict)
        if recognition_result is not None:
            best_template, score = recognition_result
            self.ui.prediction_result.setText(f"{best_template}   (score: {score})")
        else:
            self.ui.prediction_result.setText(f"Couldn't predict a gesture!")


def main():
    app = QtWidgets.QApplication(sys.argv)
    recognizer = GestureRecognizer()
    recognizer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
