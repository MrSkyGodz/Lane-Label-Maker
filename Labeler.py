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
		self.max = len(self.images)

		self.top, self.left, self.width, self.height = 400, 400, 800, 600
		self.setWindowTitle("MyPainter")
		self.setGeometry(self.top, self.left, self.width, self.height)

		self.image = QImage(self.size(), QImage.Format_ARGB32)
		self.image.fill(Qt.white)
		self.imageDraw = QImage(self.size(), QImage.Format_ARGB32)
		self.imageDraw.fill(Qt.transparent)
		self.imageDot = QImage(self.size(), QImage.Format_ARGB32)
		self.imageDot.fill(Qt.transparent)


		self.drawing = False
		self.brushSize = 10
		self.brushColor = QColor(Qt.black)
		self.lastPoint = QPoint()
		
		self.backimg = []
		
		self.points = QPolygon()

		self.change = False
		self.drawType = 1

		self.nextImg()

		
	def nextImg(self):
		if(self.idx >= self.max):
			self.idx = self.max -1
			return
		print(self.dots)
		self.setWindowTitle(self.images[self.idx])
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
			
			
			if(self.drawType == 1):
				if(len(self.dots) > 2):
					print(len(self.dots))
					self.buildPath()
					self.paintPolygon()
			else:

				self.polynomFit()
				self.paintPolynom()
					
			if(self.drawType == 2 or (len(self.dots) > 2)):
				self.imageDot.fill(Qt.transparent)
				self.dots = []
				self.points = QPolygon()
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

		if event.key() == Qt.Key_1:
			self.drawType = 1	

		if event.key() == Qt.Key_2:
			self.drawType = 2


		self.update()

	def clearAll(self):
		self.lane = 0
		self.dots = []
		self.points = QPolygon()
		self.imageDot.fill(Qt.transparent)
		self.imageDraw.fill(Qt.transparent)

	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			
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
		gray2 = np.zeros((height,width))
		gray[:,:] = arr[:,:,0]
		gray2 = arr[:,:,0] >= 1

		if(flag == 1):
			plt.imshow(gray, interpolation='nearest')
			plt.show()

		plt.imsave(os.path.join(self.labelPath,"PolyGrandtruth",str(self.idx) + ".png"), gray, cmap='gray')
		plt.imsave(os.path.join(self.labelPath,"BinaryGrandtruth",str(self.idx) + ".png"), gray2, cmap='gray')
		shutil.copyfile(os.path.join(self.imgPath,self.images[self.idx]), os.path.join(self.labelPath,"images",str(self.idx) + ".jpg"))
		# print(self.backimg)

	def paintDot(self, event):
		painter = QPainter(self.imageDot)
		painter.setPen(QPen(Qt.green,  5, Qt.SolidLine))
		painter.drawEllipse(event.pos(),2,2)
		


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
		
		self.p = np.poly1d(z)
		
	
	def paintPolynom(self):
		painter = QPainter(self.imageDraw)
		
		pen = QPen(QColor(self.lane+1,0,0))
		
		
		pen.setWidth(self.brushSize)
		painter.setPen(pen)
		painter.setRenderHint(QPainter.Antialiasing, True)

		for i,pos in enumerate([self.p(i) for i in range(600)]):
			painter.drawPoint(int(pos),i)
	
	def buildPath(self):
		factor = 0.25
		self.path = QPainterPath(self.points[0])
		for p, current in enumerate(self.points[1:-1], 1):
			# previous segment
			source = QLineF(self.points[p - 1], current)
			# next segment
			target = QLineF(current, self.points[p + 1])
			targetAngle = target.angleTo(source)
			if targetAngle > 180:
				angle = (source.angle() + source.angleTo(target) / 2) % 360
			else:
				angle = (target.angle() + target.angleTo(source) / 2) % 360

			revTarget = QLineF.fromPolar(source.length() * factor, angle + 180).translated(current)
			cp2 = revTarget.p2()

			if p == 1:
				self.path.quadTo(cp2, current)
			else:
				# use the control point "cp1" set in the *previous* cycle
				self.path.cubicTo(cp1, cp2, current)

			revSource = QLineF.fromPolar(target.length() * factor, angle).translated(current)
			cp1 = revSource.p2()

		# the final curve, that joins to the last point
		self.path.quadTo(cp1, self.points[-1])

	def paintPolygon(self):
		painter = QPainter(self.imageDraw)
		
		pen = QPen(QColor(self.lane+1,0,0))
		
		pen.setWidth(self.brushSize)
		painter.setPen(pen)
		painter.setRenderHint(QPainter.Antialiasing, True)

		painter.drawPath(self.path)

	def cutHorizon(self,event):
		painter = QPainter(self.imageDraw)
		r = QRect(0,0, self.width,event.pos().y())
		painter.save()
		painter.setCompositionMode(QPainter.CompositionMode_Clear)
		painter.eraseRect(r)
		painter.restore()

if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = Window("images","label")
	window.show()
	sys.exit(app.exec())


