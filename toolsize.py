import sys

import cv2
import ezdxf
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QLabel, QMainWindow,\
    QVBoxLayout, QSlider, QFileDialog

hiddenimports = ['numpy.core.multiarray']


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("ADS easysim")
        central_widget = QWidget()

        self.src = None
        self.dst = None
        self.cnt = None
        self.scaling = 1.0

        central_widget.setLayout(QVBoxLayout())

        wdg_slider_thresh = QWidget()
        wdg_slider_thresh.setLayout(QHBoxLayout())

        slider_label_thresh = QLabel('Threshold')

        self.slider_thresh = QSlider(Qt.Horizontal)
        self.slider_thresh.setMaximum(255)
        self.slider_thresh.setValue(150)
        self.slider_thresh.valueChanged.connect(self.on_slider_changed)
        wdg_slider_thresh.layout().addWidget(slider_label_thresh)
        wdg_slider_thresh.layout().addWidget(self.slider_thresh)

        wdg_slider_kernel = QWidget()
        wdg_slider_kernel.setLayout(QHBoxLayout())

        slider_label_kernel = QLabel('Kernel')

        self.slider_kernel = QSlider(Qt.Horizontal)
        self.slider_kernel.setMaximum(65)
        self.slider_kernel.setMinimum(1)
        self.slider_kernel.setValue(11)
        self.slider_kernel.valueChanged.connect(self.on_slider_changed)
        wdg_slider_kernel.layout().addWidget(slider_label_kernel)
        wdg_slider_kernel.layout().addWidget(self.slider_kernel)

        self.image_widget = DisplayImageWidget()

        btn_widget = QWidget()
        btn_widget.setLayout(QHBoxLayout())

        self.btn_save = QPushButton('Save as DXF')
        self.btn_save.clicked.connect(self.on_save_pressed)

        self.btn_load = QPushButton('Load image')
        self.btn_load.clicked.connect(self.on_load_pressed)

        btn_widget.layout().addWidget(self.btn_load)
        btn_widget.layout().addWidget(self.btn_save)

        central_widget.layout().addWidget(btn_widget)
        central_widget.layout().addWidget(wdg_slider_thresh)
        central_widget.layout().addWidget(wdg_slider_kernel)
        central_widget.layout().addWidget(self.image_widget)
        self.setCentralWidget(central_widget)

    def on_load_pressed(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select shadow board image", "",
                                                  "Image files (*.jpg *.jpeg *.png *.gif)", options=options)
        if filename:
            self.process(filename)
            self.image_widget.update_image(self.dst, QImage.Format_RGB888)

    def on_save_pressed(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Save contour to DXF file", "",
                                                  "DXF File (*.dxf)", options=options)
        if filename:
            doc = ezdxf.new('R2000')
            msp = doc.modelspace()

            points = []
            for p in self.cnt.tolist():
                points.append((p[0][0] / self.scaling, p[0][1] / self.scaling))
            msp.add_lwpolyline(points)
            doc.saveas(filename)

    def on_slider_changed(self):
        self.process()
        self.image_widget.update_image(self.dst, QImage.Format_RGB888)

    def process(self, filename=None):
        if filename is not None:
            self.src = cv2.imread(filename)

        gray = cv2.cvtColor(self.src, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 3)

        [_, threshed] = cv2.threshold(blur, self.slider_thresh.value(), 255, cv2.THRESH_BINARY)

        # (2) Morph-op to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.slider_kernel.value(), self.slider_kernel.value()))
        morphed = cv2.morphologyEx(threshed, cv2.MORPH_CLOSE, kernel)

        # (3) Find the max-area contour
        [_, cnts, _] = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # assert landscape orientation
        if len(cnts) > 0:
            cnt = sorted(cnts, key=cv2.contourArea)[-1]
            (x, y), (w, h), a = cv2.minAreaRect(cnt)
            if h > w:
                morphed = cv2.rotate(morphed, cv2.ROTATE_90_CLOCKWISE)

        # (3) Find the max-area contour
        [_, cnts, _] = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(cnts) > 0:
            cnt = sorted(cnts, key=cv2.contourArea)[-1]

            # (4) Crop and save it
            (x, y), (w, h), a = cv2.minAreaRect(cnt)
            rotation_matrix = cv2.getRotationMatrix2D((x, y), a, 1)
            rotated_image = cv2.warpAffine(morphed, rotation_matrix, (int(w + x), int(h + y)))

            # (3) Find the max-area contour
            cnts = cv2.findContours(rotated_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
            if len(cnts) > 0:
                # (4) Crop and save it
                cnt = sorted(cnts, key=cv2.contourArea)[-1]
                epsilon = 0.1 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                x, y, w, h = cv2.boundingRect(approx)
                rotated_image = rotated_image[y:y + h, x:x + w].copy()

                # find the tool
                # invert
                inv = ~rotated_image
                # (3) Find the max-area contour
                (_, cnts, _) = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
                if len(cnts) > 0:
                    # (4) Crop and save it
                    cnt = sorted(cnts, key=cv2.contourArea)[-1]

                    rect = cv2.minAreaRect(cnt)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)

                    fin = cv2.cvtColor(inv, cv2.COLOR_GRAY2BGR)
                    cv2.drawContours(fin, [cnt], 0, (255, 255, 0), 2)
                    cv2.drawContours(fin, [box], 0, (0, 0, 255), 1)
                    self.dst = fin.copy()
                    self.cnt = cnt
                    shadowboard_width_px = fin.shape[1]
                    shadowboard_width_mm = 380

                    px2mm = shadowboard_width_px / shadowboard_width_mm

                    self.scaling = px2mm


class DisplayImageWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DisplayImageWidget, self).__init__(parent)

        self.image_frame = QtWidgets.QLabel()
        self.image_frame.setFixedWidth(1600)
        self.image_frame.setFixedHeight(900)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.image_frame)
        self.setLayout(self.layout)

    def update_image(self, image, image_format):
        qimage = QImage(image.data, image.shape[1], image.shape[0], image.strides[0],
                        image_format)
        qimage = qimage.rgbSwapped()
        w = self.image_frame.width()
        self.image_frame.setPixmap(QPixmap.fromImage(qimage).scaledToWidth(w))


if __name__ == '__main__':
    sys._excepthook = sys.excepthook


    def exception_hook(exctype, value, traceback):
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)


    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
