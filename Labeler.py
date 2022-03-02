from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import shutil

 
class Window(QMainWindow):
	def __init__(self, imgPath, labelPath):
		super().__init__()
		self.imgPath = imgPath
		self.labelPath = labelPath
		self.images = os.listdir(imgPath)
		self.idx = 0
		self.lane = 0
		self.dots = []

		top, left, width, height = 400, 400, 800, 600
		self.setWindowTitle("MyPainter")
		self.setGeometry(top, left, width, height)

		self.image = QImage(self.size(), QImage.Format_ARGB32)
		self.image.fill(Qt.white)
		self.imageDraw = QImage(self.size(), QImage.Format_ARGB32)
		self.imageDraw.fill(Qt.transparent)
		self.imageDot = QImage(self.size(), QImage.Format_ARGB32)
		self.imageDot.fill(Qt.transparent)


		self.drawing = False
		self.brushSize = 2
		self.brushColor = QColor(Qt.black)
		self.lastPoint = QPoint()
		
		self.backimg = []
		
		self.points = QPolygon()

		self.change = False
		self.nextImg()
		
	def nextImg(self):
		print(self.dots)

		with open(os.path.join(self.imgPath,self.images[self.idx]), 'rb') as f:
			content = f.read()
			self.image.loadFromData(content)
			self.backimg = content
		self.update()

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return:
			self.convertQImageToMat(0)
			self.idx += 1
			self.nextImg()
			self.clearAll()

		if event.key() == Qt.Key_Space:
			
			if(self.lane != 2):
				self.polynomFit()
				self.paintPoly()
				
				self.imageDot.fill(Qt.transparent)
				self.dots = []
				self.lane += 1
			

		if event.key() == Qt.Key_Q:
			print(self.dots)
			self.clearAll()

		if event.key() == Qt.Key_D:
			self.idx += 1
			self.nextImg()
			self.clearAll()

		if event.key() == Qt.Key_A:
			if(self.idx != 0):
				self.idx -= 1
				self.nextImg()
				self.clearAll()

		if event.key() == Qt.Key_S:
			try:
				self.idx = int(input("Fotografi gir"))
			except:
				self.idx = 0		
			self.nextImg()
			self.clearAll()
			

		self.update()

	def clearAll(self):
		self.lane = 0
		self.dots = []
		self.imageDot.fill(Qt.transparent)
		self.imageDraw.fill(Qt.transparent)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			if(self.lane != 2):
				self.lastPoint = event.pos()

				self.points << event.pos()

				self.dots.append(self.lastPoint)
				self.paintDot(event)

		if event.button() == Qt.RightButton:
			self.cutHorizon(event)

		if event.button() == Qt.MidButton:
			self.convertQImageToMat(1)

		self.update()

	def convertQImageToMat(self,flag):

		incomingImage = self.imageDraw.convertToFormat(QImage.Format_RGB888)
		# incomingImage = self.imageDraw.convertToFormat(QImage.Format_Grayscale8)
		width = incomingImage.width()
		height = incomingImage.height()

		ptr = incomingImage.bits()
		ptr.setsize(incomingImage.byteCount())
		arr = np.array(ptr).reshape(height, width, 3)  #  Copies the data
		gray = np.zeros((height,width))
		gray[:,:] = arr[:,:,0]
		if(flag == 1):
			plt.imshow(gray, interpolation='nearest')
			plt.show()
		
		plt.imsave(os.path.join(self.labelPath,"Grandtruth",str(self.idx) + ".png"), gray, cmap='gray')
		
		shutil.copyfile(os.path.join(self.imgPath,self.images[self.idx]), os.path.join(self.labelPath,"images",str(self.idx) + ".jpg"))
		# print(self.backimg)

	def paintDot(self, event):
		painter = QPainter(self.imageDot)
		painter.setPen(QPen(Qt.green,  5, Qt.SolidLine))
		painter.drawEllipse(event.pos(),10,10)
		


	def paintEvent(self, event):
		canvasPainter = QPainter(self)
		
		canvasPainter.drawImage(self.rect(), self.image, self.image.rect())
		canvasPainter.drawImage(self.rect(), self.imageDraw, self.imageDraw.rect())
		canvasPainter.drawImage(self.rect(), self.imageDot, self.imageDot.rect())

	def polynomFit(self):
		x = []
		y = []
		for i,_ in enumerate(self.dots):
			x.append(self.dots[i].x())
			y.append(self.dots[i].y())
		z = np.polyfit(y, x, 3)
		print(z)
		self.p = np.poly1d(z)
	
	def paintPoly(self):
		painter = QPainter(self.imageDraw)
		if(self.lane == 0):
			pen = QPen(QColor(1,0,0))
		else:
			pen = QPen(QColor(2,0,0))
		pen.setWidth(10)
		painter.setPen(pen)
		painter.setRenderHint(QPainter.Antialiasing, True)

		for i,pos in enumerate([self.p(i) for i in range(600)]):
			painter.drawPoint(pos,i)

	def cutHorizon(self,event):
		painter = QPainter(self.imageDraw)
		r = QRect(0,0, 800,event.pos().y())
		painter.save()
		painter.setCompositionMode(QPainter.CompositionMode_Clear)
		painter.eraseRect(r)
		painter.restore()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Window("images","label")
	window.show()
	sys.exit(app.exec())


