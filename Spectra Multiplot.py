#! python3

from PyQt5 import QtGui, QtCore
#import PySide
#from pyqtgraph import QtGui, QtCore
import pyqtgraph as pg
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt

app = QtGui.QApplication([])

class Curve():
    def __init__ (self, filename):
        self.filename = filename
        self.openit(self.filename)
    
    def openit (self, f):
        # this section was needed because .csv files depend on system settings of the computer it was saved on.
        # so far I saw separation by ; and numbers have commas, or separation by comma and numbers have dots.
        # therefore the two options are checked by reading the file and checking if the first separator is a comma or semicolon.
        checkfile = open(f, mode = 'r', encoding = "ISO-8859-1")
        filestart = checkfile.readline()
        print(filestart)
        if filestart.startswith("TITLE,"):
            self.data_raw = pd.read_csv(f, encoding = "ISO-8859-1", header = None, names =[0,1])
            print('reading csv complete! (Method 1, comma!)')
        elif filestart.startswith("TITLE;"):
            print("entering alternative mode for reading csv")
            self.data_raw = pd.read_csv(f, sep = ';', encoding = "ISO-8859-1", header = None, names =[0,1])
            self.data_raw.replace(to_replace = ",", value = ".", inplace = True, regex = True)
        else:
            print('File could not be read. Ask Philipp if he can fix it for you.')
            
        temp = self.data_raw.transpose()
        temp.columns = temp.iloc[0]
        
        self.data_framed = temp[1:][:] # this gives us the proper labels for each column
        print(self.data_framed)
        self.title = self.data_framed.index[0]
        try:
            self.firstx = float(self.data_framed.iloc[0]['FIRSTX'])
        except KeyError:
            self.data_framed.replace(to_replace = ",", value = ".", inplace = True)
            print("new dataframe:")
            print(self.data_framed)
            self.firstx = float(self.data_framed.iloc[0]['FIRSTX'])
        self.nstart = int(self.data_framed.columns.get_loc('XYDATA')+1)
        self.nstop = self.nstart + int(self.data_framed.iloc[0,self.data_framed.columns.get_loc('NPOINTS')])
        txvalues = temp.iloc[0,(self.nstart):(self.nstop)].values
        tyvalues = temp.iloc[1, (self.nstart):(self.nstop)].values.tolist()
        self.xvalues = [float(i) for i in txvalues]
        self.xvalues = np.asarray(self.xvalues, dtype=np.float32)
        self.yvalues = [float(i) for i in tyvalues]
        self.yvalues = np.asarray(self.yvalues, dtype=np.float32)
            
        self.date = self.data_framed.iloc[0]['DATE'] # God it took me ages to find this -....-
        self.time = self.data_framed.iloc[0]['TIME']
        self.maxy = self.data_framed.iloc[0]['MAXY']
        self.miny = self.data_framed.iloc[0]['MINY']
        self.deltax = self.data_framed.iloc[0]['DELTAX']
        self.lastx = float(self.data_framed.iloc[0]['LASTX'])
        self.ydatatype = self.data_framed.iloc[0]['YUNITS']
        self.xdatatype = self.data_framed.iloc[0]['XUNITS']
        
    def setmin(self):
        self.yvalues = self.yvalues - float(self.miny)
        self.miny = 0
        
    def setmin_nm(self, nm):
        self.yvalues = self.yvalues - self.yvalues[int(self.firstx) - int(nm)] # I think the values are plotted the wrong way, as in last is first and vice versa

class QColorButton(QtGui.QPushButton):
    '''
    Custom Qt Widget to show a chosen color.

    Left-clicking the button shows the color-chooser, while
    right-clicking resets the color to None (no-color).    
    '''

    colorChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(QColorButton, self).__init__(*args, **kwargs)

        self._color = None
        self.setMaximumWidth(32)
        self.pressed.connect(self.onColorPicker)

    def setColor(self, color):
        if color != self._color:
            self._color = color
            self.colorChanged.emit()

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        '''
        Show color-picker dialog to select color.

        Qt will use the native dialog by default.

        '''
        dlg = QtGui.QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QtGui.QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.RightButton:
            self.setColor(None)

        return super(QColorButton, self).mousePressEvent(e)
		
class GUI (QtGui.QWidget):
    def __init__ (self):
        """Initializes fancy GUI class"""
        super(QtGui.QWidget, self).__init__()
        
        self.path = False
        self.curves = []
        
        # It is better having a separate function
        # to initialize your UI
        self.initUI()
                
        
    def initUI (self):    
        # Do fancy Grid Layout!
        self.setGridLayout()
        
        # Set window     x   y   w   h
        self.setGeometry(100,100,1000,600)
        
        # Set window title
        self.setWindowTitle("Spectra measurements - Multiplot")
        
        # Show GUI
        self.show()
        
        
        
    def setGridLayout (self):
        # Create a GridLayout
        self.l = QtGui.QGridLayout()
        
        # Tell our GUI to use that Grid Layout!
        self.setLayout(self.l)
        
        
        button = QtGui.QPushButton("Open a file")
        button.clicked.connect(self.openfile) # if clicked, the openfile function should be executed.
        button.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        
        button2 = QtGui.QPushButton("Close")
        button2.clicked.connect(self.close) # if clicked, the widget should be destroyed.
        
        button3 = QtGui.QPushButton("Create PDF output")
        button3.clicked.connect(self.output)
        button3.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        
        button4 = QtGui.QPushButton("Update graph")
        button4.clicked.connect(self.doplot)
        button4.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        
        buttonmin = QtGui.QPushButton("Set zero")
        buttonmin.clicked.connect(self.setmins)
        buttonmin.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        
        self.nm_checkbox = QtGui.QCheckBox("nm: ")
        self.nm_checkbox.setFixedWidth(40)
        self.nm_entry = QtGui.QLineEdit()
        self.nm_entry.setInputMask("d999") # allow only integer numbers, no leading 0
        self.nm_entry.setFixedWidth(35)
        
        buttonc1 = QColorButton()
        buttonc1.setColor('#050505')
        buttonc2 = QColorButton()
        buttonc2.setColor('#9400D3')
        buttonc3 = QColorButton()
        buttonc3.setColor('#4169E1')
        buttonc4 = QColorButton()
        buttonc4.setColor('#999999')
        buttonc5 = QColorButton()
        buttonc5.setColor('#662244')
        buttonc6 = QColorButton()
        buttonc6.setColor('#22AA66')
        
        self.buttonclist = [buttonc1, buttonc2, buttonc3, buttonc4, buttonc5, buttonc6]
        
        curve1_l = QtGui.QLabel("Curve 1: ")
        self.curve1 = QtGui.QLineEdit()
        self.curve1.setText("1")
        
        curve2_l = QtGui.QLabel("Curve 2: ")
        self.curve2 = QtGui.QLineEdit()
        self.curve2.setText("2")
        
        curve3_l = QtGui.QLabel("Curve 3: ")
        self.curve3 = QtGui.QLineEdit()
        self.curve3.setText("3")
        
        curve4_l = QtGui.QLabel("Curve 4: ")
        self.curve4 = QtGui.QLineEdit()
        self.curve4.setText("4")
        
        curve5_l = QtGui.QLabel("Curve 5: ")
        self.curve5 = QtGui.QLineEdit()
        self.curve5.setText("5")
        
        curve6_l = QtGui.QLabel("Curve 6: ")
        self.curve6 = QtGui.QLineEdit()
        self.curve6.setText("6")
        
        self.rangebox = QtGui.QCheckBox("plot range:")
        self.rangelower = QtGui.QLineEdit()
        self.rangehigher = QtGui.QLineEdit()
        self.rangelower.setInputMask("d999") # allow only integer numbers, no leading 0
        self.rangelower.setFixedWidth(35)
        self.rangehigher.setInputMask("d999") # allow only integer numbers, no leading 0
        self.rangehigher.setFixedWidth(35)
        self.range_l = QtGui.QLabel("to")
        
        #add a field for entering clip values for Y (min and max)
        self.clip_upper = QtGui.QLineEdit()
        self.clip_upper.setInputMask("##0.000")
        self.clip_upper.setFixedWidth(45)
        self.clip_lower = QtGui.QLineEdit()
        self.clip_lower.setInputMask("##0.000")
        self.clip_lower.setFixedWidth(45)
        self.clip_label = QtGui.QLabel("lower Y / upper Y")
        self.clip_button_reset = QtGui.QPushButton("reset Y")
        self.clip_button_reset.clicked.connect(self.resetY)
        
        
        pg.setConfigOption('background', 'w') # change pyqtgraph to normal color scheme
        pg.setConfigOption('foreground', 'k')
        self.p = pg.PlotWidget() # Create plot widget
                
        self.curve = self.p.plot(pen=QtGui.QPen(QtGui.QColor(0, 0, 255))) # Plot a curve with no content
        
        # Add the buttons and LineEdits etc.
        self.l.addWidget(button,  0, 0, 2, 3)
        self.l.addWidget(button3, 4, 0, 2, 3)
        self.l.addWidget(curve1_l, 0, 3)
        self.l.addWidget(self.curve1, 0, 4)
        self.l.addWidget(curve2_l, 1, 3)
        self.l.addWidget(self.curve2, 1, 4)
        self.l.addWidget(curve3_l, 2, 3)
        self.l.addWidget(self.curve3, 2, 4)  
        self.l.addWidget(curve4_l, 3, 3 )
        self.l.addWidget(self.curve4, 3, 4)
        self.l.addWidget(curve5_l,4, 3)
        self.l.addWidget(self.curve5, 4, 4 )
        self.l.addWidget(curve6_l, 5, 3)
        self.l.addWidget(self.curve6, 5, 4)
        self.l.addWidget(button2, 5, 6, 1, 2)
        self.l.addWidget(buttonc1, 0, 5)
        self.l.addWidget(buttonc2, 1, 5)
        self.l.addWidget(buttonc3, 2, 5)
        self.l.addWidget(buttonc4, 3, 5)
        self.l.addWidget(buttonc5, 4, 5)
        self.l.addWidget(buttonc6, 5, 5)
        self.l.addWidget(button4, 0, 6, 2, 2)
        self.l.addWidget(buttonmin, 3, 6, 2, 2)
        self.l.addWidget(self.nm_checkbox, 2, 6, 1, 1)
        self.l.addWidget(self.nm_entry, 2, 7, 1, 1)
        
        self.l.addWidget(self.rangebox, 2, 0, 1, 2 )
        self.l.addWidget(self.rangelower, 3, 0, 1, 1)
        self.l.addWidget(self.rangehigher, 3, 2, 1, 1)
        self.l.addWidget(self.range_l, 3, 1)
        
        # Y clipping module here
        self.l.addWidget(self.clip_label, 0, 8, 1, 2)
        self.l.addWidget(self.clip_lower, 1, 8)
        self.l.addWidget(self.clip_upper, 1, 9)
        self.l.addWidget(self.clip_button_reset, 2, 8, 1, 2)
        
        
        # Add the plot Widget below, span the whole columns
        #                        Row Col Row Span, Col Span
        self.l.addWidget(self.p, 6,  0,  1,        -1)
    
    
    def openfile (self):
        """Open a file using a FileDialog and only show csv files."""
        if self.path:
            f = QtGui.QFileDialog.getOpenFileName(directory= self.path, filter="CSV data (*.csv)")[0]
        else:
            import os.path
            if os.path.exists("X:\Spectrophotometer Jasco V-650"):
                self.path = os.path.normpath('X:/Spectrophotometer Jasco V-650')
            else:
                self.path = os.path.normpath('C:/')
            f = QtGui.QFileDialog.getOpenFileName(directory= self.path, filter="CSV data (*.csv)")[0]
               
        print(f) # Print it to the IPython console!
        self.path = QtCore.QFileInfo(f).path() # store path for next time
        
        # If there's a file, load it using Pandas!
        if (f and len(self.curves)<len(self.buttonclist)):
            new = Curve(f)
            self.curves.append(new)
            self.changelabel(f)
            #print(len(self.curves))
            self.doplot()

    def isfloat(self,value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    
        
    def doplot (self):
        self.p.clear()

        if self.rangebox.isChecked() == True and int(self.rangelower.text()) < int(self.rangehigher.text()):
            self.p.setXRange(int(self.rangelower.text()), int(self.rangehigher.text()))
            # set Y range properly if x is limited
            ymax = 0
            ymin = 50000
            if self.curves[-1].ydatatype == "ABSORBANCE":
                for curve in self.curves:
                    curve_max = np.amax(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))], axis = 0)
                    curve_min = np.amin(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))], axis = 0)
                    #print(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))])
                    if curve_max > ymax:
                        ymax = curve_max
                    if curve_min < ymin:
                        ymin = curve_min
            # case 2: any other datatype, meaning that x[-1] is the highest value
            else:
                for curve in self.curves:
                    curve_max = np.amax(curve.yvalues[int(self.rangelower.text()):int(self.rangehigher.text())], axis = 0)
                    curve_min = np.amin(curve.yvalues[int(self.rangelower.text()):int(self.rangehigher.text())], axis = 0)

                    if curve_max > ymax:
                        ymax = curve_max
                    if curve_min < ymin:
                        ymin = curve_min
            self.p.setYRange(ymin, ymax)
            
        # check if lower/upper Y-Limit are set and apply them accordingly        
        if self.isfloat(self.clip_lower.text()) and self.isfloat(self.clip_upper.text()):
            self.p.setYRange(float(self.clip_lower.text()), float(self.clip_upper.text()))
        # missing is a method to undo and go back to autoscale if you screwed up the Y-limits

        else:
            self.p.setXRange(self.curves[0].lastx, self.curves[0].firstx)
            

            
        for counter, item in enumerate(self.curves):
            self.p.plot(item.xvalues, item.yvalues, pen = self.buttonclist[counter].color())

    def resetY (self):
        self.clip_lower.clear()
        self.clip_upper.clear()
        self.p.autoRange()
        self.doplot()
            
    def setmins (self):
        if self.nm_checkbox.isChecked():
            for item in self.curves:
                item.setmin_nm(self.nm_entry.text())
        else:
            for item in self.curves:
                item.setmin()

    def changelabel(self, filename):
        filename = filename.split("/")
        filename = filename[-1]
        if filename.endswith('.csv'):
            filename = filename[:-4]
        if len(self.curves) == 1:
            self.curve1.setText(filename)
        elif len(self.curves) == 2:
            self.curve2.setText(filename)
        elif len(self.curves) == 3:
            self.curve3.setText(filename)
        elif len(self.curves) == 4:
            self.curve4.setText(filename)
        elif len(self.curves) == 5:
            self.curve5.setText(filename)
        elif len(self.curves) == 6:
            self.curve6.setText(filename)


            
    def output(self):
        from cycler import cycler

        plt.figure(figsize=(16,8))
        plt.rcParams['axes.prop_cycle'] = cycler('color', [self.buttonclist[x].color() for x in range(len(self.curves))])
        plt.title(str(len(self.curves)) + ' Curves', size = 16)
               
        labels = [self.curve1.text(), self.curve2.text(), self.curve3.text(), self.curve4.text(), self.curve5.text(), self.curve6.text()]
        
        for position, item in enumerate(self.curves):
            plt.plot(item.xvalues, item.yvalues, label = labels[position])        
        
        plt.legend(loc=0)
        plt.ylabel('Absorption')
        if self.curves[-1].ydatatype != "ABSORBANCE":
            plt.ylabel(str(self.curves[-1].ydatatype))
            plt.axhline(0, color = 'gray', linestyle = 'dashed')
        elif self.curves[-1].xdatatype == "SEC":
            plt.xlim(xmin = self.curves[-1].firstx)
            plt.xlabel('Time in seconds')
        else:
            plt.xlabel('Wavelength in nm')
            
        if self.rangebox.isChecked():
            plt.xlim((int(self.rangelower.text()), int(self.rangehigher.text())))
            # now make sure that y-range is appropriate
            ymax = 0
            ymin = 50000
            #case 1 : normal Absorption data, meaning x[0] is the highest wavelength measured
            if self.curves[-1].ydatatype == "ABSORBANCE":
                for curve in self.curves:
                    curve_max = np.amax(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))], axis = 0)
                    curve_min = np.amin(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))], axis = 0)
                    #print(curve.yvalues[(int(curve.xvalues[0]) - int(self.rangehigher.text())):(int(curve.xvalues[0])-int(self.rangelower.text()))])
                    if curve_max > ymax:
                        plt.ylim(ymax = curve_max + abs(0.05*(curve_max-curve_min)))
                        ymax = curve_max
                    if curve_min < ymin:
                        plt.ylim(ymin = curve_min - abs(0.05*(curve_max-curve_min)))
                        ymin = curve_min
            # case 2: any other datatype, meaning that x[-1] is the highest value
            else:
                for curve in self.curves:
                    curve_max = np.amax(curve.yvalues[int(self.rangelower.text()):int(self.rangehigher.text())], axis = 0)
                    curve_min = np.amin(curve.yvalues[int(self.rangelower.text()):int(self.rangehigher.text())], axis = 0)

                    if curve_max > ymax:
                        plt.ylim(ymax = curve_max + abs(0.05*(curve_max-curve_min)))
                        ymax = curve_max
                    if curve_min < ymin:
                        plt.ylim(ymin = curve_min - abs(0.05*(curve_max-curve_min)))
                        ymin = curve_min
                        
        else:
            if self.curves[-1].ydatatype == "ABSORBANCE" and self.curves[-1].xdatatype != "SEC":
                plt.xlim(xmin = self.curves[0].lastx)
        
        if self.isfloat(self.clip_lower.text()) and self.isfloat(self.clip_upper.text()):
            plt.ylim(ymin = float(self.clip_lower.text()), ymax = float(self.clip_upper.text()))
        
        fig = plt.gcf()
        fig.savefig(self.path + '\\' + str(self.curves[0].title)+'.jpg', dpi = 600, bbox_inches='tight')
        plt.show()
        plt.close(fig)
        
       
            
        #put all the functions for pdf generation and saving here
        from fpdf import FPDF
        from time import strftime
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Courier', 'B', 11)
        pdf.cell(40, 10, "Spectra measurements on " + str(self.curves[0].date[6:8]) + "." + str(self.curves[0].date[3:5]) + ".20" + str(self.curves[0].date[0:2]) + ", " + self.curves[0].time, 0)
        pdf.ln()
        pdf.image(self.path + '\\' + str(self.curves[0].title)+'.jpg', x = 10, w = 185)
        
        pdf.output(self.path + '\\' + strftime("%y%m%d-%H.%M ") + 'Spectra - ' + str(self.curve1.text()) + ' ' + str(self.curve2.text()) + ' ' + str(self.curve3.text())+'.pdf', 'F')
        print(self.path)

w = GUI() # Create Widget eq. Window
app.exec_() # Start Application