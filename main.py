'''
06.05.2016
CSE-A1121 Ohjelmoinnin peruskurssi Y2
Python 3.4
PyQt 5.6
'''
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import os
import math
import pickle
import datetime
from random import randint


    #The constants below are the starting constants.

#Constants for drawing the walls and the character.
WALL_LENGTH=60                          #min: 35 max:200
DRAW_WIDTH= round(WALL_LENGTH/15)       #Acceptable range: [1, WALL_LENGTH/2]    (is 4 atm)
UPPER_BAR_HEIGHT=32*2

#Buffers that are used to get everyting drawn aligned.
X_DRAW_BUFFER= DRAW_WIDTH*2                     #RIGHT AND LEFT
Y_DRAW_BUFFER= UPPER_BAR_HEIGHT + DRAW_WIDTH*2  #ABOVE
Y_DRAW_BUFFER_UNDER= DRAW_WIDTH*2 + 40          #UNDER            menubar=20px, statusbar=20px

#Directions for walls. (In an axis direction.)    (looking from above)
XDIR=0  #left wall
YDIR=1  #top wall
ZDIR=2  #floor

#Walls observed from inside a square. POS=positive, NEG=negative
XPOS=0
XNEG=1
YPOS=2
YNEG=3
ZPOS=4
ZNEG=5

#Constants for the timer in class Field.
FPS=500                         #how often the scene is updated per second
TIMER_INTERVAL= 1000/FPS        #in ms
CHARACTER_MOVEMENT_SPEED=5      #in squares per second
CHARACTER_SIZE_MODIFIER=0.5     #just modifier times the size that is as big as a square in the labyrinth

#How many squares are scrolled at a time.
SCROLL_LEN=5


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setSettingsVariables()
        
        self.setMinimumSize(576, 324)   #(36*16, 36*9)
        self.screenGeometry=QApplication.desktop().screenGeometry()
        self.setWindowTitle('Labyrinth')
        
        self.labyrinth=None
        self.character=None
        self.saveread=SaveRead(self)
        
        self.UseCharacter=True
        self.HideInfobar=False
        self.ShowSolution=False
        self.SolutionFound=False
        
        self.ALGCreateList=["Recursive bakctracker", "2nd placeholder for algorithm"]
        self.CreateIndex=0
        
        self.ALGSolveList=["Recursive bakctracker", "2nd placeholder for algorithm"]
        self.ALGSolve=None  #An algorithm
        self.SolveIndex=None
        
        self.pressedKeys=set() #For moving the character.
        
        self.statusBar=QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.setTopMenuBar()
        
        self.setMenuCentral()
    
    def setSettingsVariables(self):
        #We store the constants here, so we can manipulate them on runtime.
        self.WALL_LENGTH=WALL_LENGTH
        
        self.DRAW_WIDTH=round(self.WALL_LENGTH/15)
        
        self.CHARACTER_MOVEMENT_SPEED=CHARACTER_MOVEMENT_SPEED
        
        self.CHARACTER_SIZE_MODIFIER=CHARACTER_SIZE_MODIFIER
        
        self.X_DRAW_BUFFER=self.DRAW_WIDTH*2
        self.X_L_EDGE=self.X_DRAW_BUFFER
        
        self.Y_DRAW_BUFFER=UPPER_BAR_HEIGHT + self.DRAW_WIDTH*2
        self.Y_U_EDGE=self.Y_DRAW_BUFFER
        
        self.SCROLL_LEN=SCROLL_LEN
        
        self.SCLEN=self.WALL_LENGTH *self.SCROLL_LEN
    
    def setEDGEsAndBUFFERsAndSCLEN(self):
        #Constants are set so we have the character and the labyrinth on the screen.
        self.X_DRAW_BUFFER=self.DRAW_WIDTH*2
        self.X_L_EDGE=self.X_DRAW_BUFFER
        
        self.Y_DRAW_BUFFER=UPPER_BAR_HEIGHT + self.DRAW_WIDTH*2
        self.Y_U_EDGE=self.Y_DRAW_BUFFER
        
        self.SCLEN=self.WALL_LENGTH *self.SCROLL_LEN
    
    def setTopMenuBar(self):
        menubar=QMenuBar()
        
        exitMenu=menubar.addMenu("&Menu")
        
        saveAction=QAction("Save", self)
        saveAction.setStatusTip("Save labyrinth")
        saveAction.triggered.connect(self.SaveFunc)
        exitMenu.addAction(saveAction)
        
        backAction=QAction("Back", self)
        backAction.triggered.connect(self.BackFunc)
        exitMenu.addAction(backAction)
        
        exitAction = QAction("Exit", self)
        exitAction.setStatusTip("Exit application")
        exitAction.triggered.connect(self.close)
        exitMenu.addAction(exitAction)
        
        
        solveMenu=menubar.addMenu("&Solve")
        
        for sol in self.ALGSolveList:
            solveAction=QAction(sol, self)
            solveAction.setStatusTip("Solve Labyrinth with " + sol)
            solveAction.triggered.connect(self.solveLabyrinth)
            solveMenu.addAction(solveAction)
        
        hideAction=QAction("Hide/Show solution", self)
        hideAction.setStatusTip("Hide or show the solution.")
        hideAction.triggered.connect(self.ShowSolutionSwitch)
        solveMenu.addAction(hideAction)
        
        self.setMenuBar(menubar)
    
    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            e.ignore()
            return
        if self.centralWidget() == self.menu:
            
            #Back
            if e.key() == Qt.Key_Escape:
                self.menu.Stack.setCurrentIndex(0)
            
            if e.key() == Qt.Key_Enter:     #Numpad Enter (for faster labyrinth creation)
                if self.menu.Stack.currentIndex() == 1:     #NewLabMenu
                    self.menu.CreateButton.click()
                
                if self.menu.Stack.currentIndex() == 0:     #MainMenu
                    self.menu.Stack.setCurrentIndex(1)
        
        else:   # == self.field
            
            #Back
            if e.key() == Qt.Key_Escape:
                self.setMenuCentral()
            
            #Move up
            if e.key() == Qt.Key_R or e.key() == Qt.Key_Space or e.key() == Qt.Key_E:
                x, y, z = self.character.getChaSQCoord()
                if self.character.SqIsPassable(x, y, z+1, 2):
                    if self.field.ZVisible != self.labyrinth.ZDim -1:
                        self.field.ZVisible +=1
                        self.field.update()
            
            #Move down
            if e.key() == Qt.Key_F or e.key() == Qt.Key_Shift or e.key() == Qt.Key_Q:
                x, y, z = self.character.getChaSQCoord()
                if self.character.SqIsPassable(x, y, z, 2):
                    if self.field.ZVisible !=0:
                        self.field.ZVisible -=1
                        self.field.update()
            
            size=self.size()    #Size of window in pixels.
            #Scrolling
            if e.key() == Qt.Key_Up: #Scroll Up
                if self.UseCharacter:
                    if self.character.y     +  self.SCLEN +Y_DRAW_BUFFER_UNDER < size.height():
                        self.character.y    += self.SCLEN
                        self.Y_DRAW_BUFFER  += self.SCLEN
                else:
                    self.Y_DRAW_BUFFER      += self.SCLEN
            
            if e.key() == Qt.Key_Down: #Scroll Down
                if self.UseCharacter:
                    if self.character.y     -  self.SCLEN > self.Y_U_EDGE:
                        self.character.y    -= self.SCLEN
                        self.Y_DRAW_BUFFER  -= self.SCLEN
                else:
                    self.Y_DRAW_BUFFER      -= self.SCLEN
            
            if e.key() == Qt.Key_Right: #Scroll Right
                if self.UseCharacter:
                    if self.character.x     -  self.SCLEN > self.X_L_EDGE:
                        self.character.x    -= self.SCLEN
                        self.X_DRAW_BUFFER  -= self.SCLEN
                else:
                    self.X_DRAW_BUFFER      -= self.SCLEN
            
            if e.key() == Qt.Key_Left: #Scroll Left
                if self.UseCharacter:
                    if self.character.x     +  self.SCLEN < size.width():
                        self.character.x    += self.SCLEN
                        self.X_DRAW_BUFFER  += self.SCLEN
                else:
                    self.X_DRAW_BUFFER      += self.SCLEN
            
            self.pressedKeys.add(e.key())
    
    def keyReleaseEvent(self, e):
        if e.isAutoRepeat():
            e.ignore()
            return
        
        if self.centralWidget() != self.menu:
            try:
                self.pressedKeys.remove(e.key())
            except KeyError:
                print("\tKey is not in pressedKeys-set. [{}]".format(e.key()))
    
    def setMenuCentral(self):
        self.menu=Menu(self)
        self.setCentralWidget(self.menu)
        
        self.ShowSolution=False
        self.SolutionFound=False
    
    def setFieldCentral(self):
        self.field=Field(self)
        self.setCentralWidget(self.field)
    
    def ShowSolutionSwitch(self):
        if self.ShowSolution == True:
            self.ShowSolution = False
        else:
            self.ShowSolution = True
    
    def solveLabyrinth(self):
        sender=self.sender()
        SIndex=self.ALGSolveList.index(sender.text())
        
        if self.centralWidget() != self.menu:
            if self.setSolveAlgorithm(SIndex):
                
                print("solveWalls START")
                self.ALGSolve.SolveLabyrinth()
                print("solveWalls DONE")
                
                self.ShowSolution=True
                self.SolutionFound=True
        else:
            self.statusBar.showMessage("You can not solve anyting in the menu.")
    
    def setSolveAlgorithm(self,SIndex):
        self.SolveIndex=SIndex
        if self.SolveIndex == 0:
            self.ALGSolve=RBSolve(self)
        else:
            print("Could not set undefined Solve Algorithm: [{}]".format(self.ALGSolveList[self.SolveIndex]))
            self.statusBar.showMessage("Could not set undefined Solve Algorithm: [{}]".format(self.ALGSolveList[self.SolveIndex]))
            return False
        
        print("Solve Algorithm set to: [{}]".format(self.ALGSolveList[self.SolveIndex]))
        return True
    
    def BackFunc(self):
        if self.centralWidget() == self.menu:
            self.menu.Stack.setCurrentIndex(0)
        else:
            self.setMenuCentral()
    
    def SaveFunc(self):
        if self.centralWidget() == self.menu:
            self.statusBar.showMessage("There is no savable labyrinth in the menu.")
        else:
            self.saveread.SaveWalls()


class Menu(QWidget):
    def __init__(self, MWindow):
        super().__init__()
        self.MWindow=MWindow
        
        self.setMenuWindow()
        
        self.Stack=QStackedWidget() #Handle pages in the Menu.
        self.setStack()
        
        #add the StackedWidgets to the Menu-QWidget
        TOPLayout=QHBoxLayout(self)
        TOPLayout.addWidget(self.Stack)
        self.setLayout(TOPLayout)
    
    def setMenuWindow(self):
        SCW=self.MWindow.screenGeometry.width()
        SCH=self.MWindow.screenGeometry.height()
        
        w=800   #50*16
        h=450   #50*9
        x=SCW/2 - w/2
        y=SCH/2 - h/2
        
        self.MWindow.setWindowState(Qt.WindowNoState)    #bordered normal window
        self.MWindow.setGeometry(x, y, w, h)
    
    def setStack(self):
        #define Widgets "pages"
        self.MainMenu=QWidget()
        self.NewLabMenu=QWidget()
        self.LoadLabMenu=QWidget()
        self.SettingsMenu=QWidget()
        self.ControllsMenu=QWidget()
        
        #setup layout for Widgets
        self.setupMainMenu()
        self.setupNewLabMenu()
        self.setupLoadLabMenu()
        self.setupSettigsMenu()
        self.setupControllsMenu()
        
        #add Widgets to StackedWidget            self.Stack.setCurrentIndex(i)
        self.Stack.addWidget(self.MainMenu)     #0    index for changing the Widgets
        self.Stack.addWidget(self.NewLabMenu)   #1
        self.Stack.addWidget(self.LoadLabMenu)  #2
        self.Stack.addWidget(self.SettingsMenu) #3
        self.Stack.addWidget(self.ControllsMenu) #4
    
    def MainButtonClicked(self):
        sender=self.sender()
        
        if sender.text() == "Back":
            self.Stack.setCurrentIndex(0)
        elif sender.text() == "New Labyrinth":
            self.Stack.setCurrentIndex(1)
        elif sender.text() == "Load Labyrinth":
            self.Stack.setCurrentIndex(2)
        elif sender.text() == "Settings":
            self.RefreshSettingsMenu()
            self.Stack.setCurrentIndex(3)
        elif sender.text() == "View Controlls":
            self.Stack.setCurrentIndex(4)
        elif sender.text() == "Exit":
            self.parentWidget.close()
    
    def CentralizeStartsquare(self):
        size=self.size()    #Size of window in pixels.
        xSQ=self.MWindow.labyrinth.StartSquare.x
        ySQ=self.MWindow.labyrinth.StartSquare.y
        
        xC=self.MWindow.X_DRAW_BUFFER + xSQ*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2     #Upper left corner x-coordinate of Startsquare
        yC=self.MWindow.Y_DRAW_BUFFER + ySQ*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2     #Upper left corner y-coordinate of Startsquare
        
        if yC + Y_DRAW_BUFFER_UNDER > size.height():
            print("Startsquare TOO LOW")
            self.MWindow.Y_DRAW_BUFFER  -= yC
            self.MWindow.character.y    -= yC
        if xC > size.width():
            print("Startsquare TOO RIGHT")
            self.MWindow.X_DRAW_BUFFER  -= xC
            self.MWindow.character.x    -= xC
    
    def CreateLabyrinthButtonClicked(self):
        self.MWindow.setEDGEsAndBUFFERsAndSCLEN()
        
        try:
            x=int(self.lex.text())
            y=int(self.ley.text())
            z=int(self.lez.text())
            
            if self.CrUseChaCB.checkState() == Qt.Checked:
                self.MWindow.UseCharacter=True
            else:
                self.MWindow.UseCharacter=False
            
            if self.CrHideInfoCB.checkState() == Qt.Checked:
                self.MWindow.HideInfobar=True
            else:
                self.MWindow.HideInfobar=False
            
            if x<1 or y<1 or z<1 or 999<x or 999<y or 999<z:
                self.MWindow.statusBar.showMessage("X, Y and Z must be integers and in the closed range [1, 999]!")
            elif x*y*z==1:
                self.MWindow.statusBar.showMessage("That is not a labyrinth. That is just a square.")
            else:
                self.MWindow.statusBar.clearMessage()
                
                self.MWindow.labyrinth=self.CreateLabyrinth(x, y, z, self.MWindow.CreateIndex)
                
                if self.MWindow.labyrinth:
                    if self.MWindow.UseCharacter == True:
                        self.MWindow.character=Character(self.MWindow)
                        print("Character set")
                    
                    self.MWindow.setFieldCentral()
                    self.CentralizeStartsquare()
            
        except ValueError:
            self.MWindow.statusBar.showMessage("X, Y and Z must be integers and in the closed range [1, 999]!")
    
    def CreateLabyrinth(self, x, y, z, CreateIndex):
        print("CreateLabyrinth Menu-function")
        Lab=Labyrinth(self.MWindow)
        Lab.setWalls(x,y,z)
        if not Lab.setCreateAlgorithm(CreateIndex):
            return False
        
        Lab.MODIFY()
        return Lab
    
    def RefreshFileComboBox(self):
        self.MWindow.statusBar.clearMessage()
        i=self.FileComboBox.count()
        while i>0:
            self.FileComboBox.removeItem(0)
            i-=1
        
        self.FileComboBox.addItem("from dropdown menu")
        SaveFiles = os.listdir("Saves")
        self.FileComboBox.addItems(SaveFiles)
    
    def LoadLabyrinthButtonClicked(self):
        self.MWindow.setEDGEsAndBUFFERsAndSCLEN()
        
        filename=None
        if self.FileComboBox.currentText() == 'Files in "Saves" folder':
            self.MWindow.statusBar.showMessage("Nothing is choosen.")
        else:
            filename=self.FileComboBox.currentText()
        
        if filename != None:
            #Filename format: "LAB_(11x10x10)_Recursive bakctracker-2016_4_26--10_43_42_688416.pickle"
            filename = "Saves\\" + filename
            print('File: "'+ filename + '" will be loaded.')
            
            if self.LoUseChaCB.checkState() == Qt.Checked:
                self.MWindow.UseCharacter=True
            else:
                self.MWindow.UseCharacter=False
            
            if self.LoHideInfoCB.checkState() == Qt.Checked:
                self.MWindow.HideInfobar=True
            else:
                self.MWindow.HideInfobar=False
            
            
            self.MWindow.statusBar.clearMessage()
            
            self.MWindow.labyrinth=self.LoadLabyrinth(filename)
            
            if self.MWindow.labyrinth!=-1:
                if self.MWindow.UseCharacter == True:
                    self.MWindow.character=Character(self.MWindow)
                    print("Character set")
                
                self.MWindow.setFieldCentral()
        
        self.CentralizeStartsquare()
    
    def LoadLabyrinth(self, filename):
        print("LoadLabyrinth Menu-function")
        Lab=Labyrinth(self.MWindow)
        saveread=self.MWindow.saveread
        wallsInt = saveread.ReadWallsInt(filename)
        
        if wallsInt != -1:
            x, y, z = saveread.FirstWallIntToXYZ(wallsInt[0])
            Lab.setWalls(x, y, z)
            saveread.ReadWalls(Lab, wallsInt) #start and finish squares are also here
            return Lab
        else:
            return -1
    
    def SaveSettingsButtonClicked(self):
        #Change constants
        self.MWindow.WALL_LENGTH=self.WallLengthBox.value()
        self.MWindow.DRAW_WIDTH=round(self.MWindow.WALL_LENGTH/15)
        self.MWindow.CHARACTER_MOVEMENT_SPEED=self.ChaMovSpeedBox.value()
        self.MWindow.CHARACTER_SIZE_MODIFIER=self.ChaSizeModBox.value() /100
        self.MWindow.SCROLL_LEN=self.ScrollLenBox.value()
        self.MWindow.CreateIndex=self.ALGCreateComboBox.currentIndex()
        #Show constants
        print("------------\nSettings Changed To:\nWALL_LENGTH:\t\t\t%d" % self.MWindow.WALL_LENGTH)
        print("DRAW_WIDTH:\t\t\t%d" % self.MWindow.DRAW_WIDTH)
        print("CHARACTER_MOVEMENT_SPEED:\t%d" % self.MWindow.CHARACTER_MOVEMENT_SPEED)
        print("CHARACTER_SIZE_MODIFIER:\t%f" % self.MWindow.CHARACTER_SIZE_MODIFIER)
        print("SCROLL_LEN:\t\t\t%d" % self.MWindow.SCROLL_LEN)
        print("CreateIndex:\t\t\t%d\n------------" % self.MWindow.CreateIndex)
    
    def DefaultSettingsClicked(self):
        self.WallLengthBox.setValue(WALL_LENGTH)
        self.ChaMovSpeedBox.setValue(CHARACTER_MOVEMENT_SPEED)
        self.ChaSizeModBox.setValue(CHARACTER_SIZE_MODIFIER*100)
        self.ScrollLenBox.setValue(SCROLL_LEN)
        self.ALGCreateComboBox.setCurrentIndex(0)
    
    def RefreshSettingsMenu(self):
        self.WallLengthBox.setValue(self.MWindow.WALL_LENGTH)
        self.ChaMovSpeedBox.setValue(self.MWindow.CHARACTER_MOVEMENT_SPEED)
        self.ChaSizeModBox.setValue(self.MWindow.CHARACTER_SIZE_MODIFIER*100)
        self.ScrollLenBox.setValue(self.MWindow.SCROLL_LEN)
        self.ALGCreateComboBox.setCurrentIndex(self.MWindow.CreateIndex)
    
    
    def setupMainMenu(self):
        NewLabButton    =QPushButton("New Labyrinth")
        LoadLabButton   =QPushButton("Load Labyrinth")
        SettingsButton  =QPushButton("Settings")
        ControllsButton =QPushButton("View Controlls")
        ExitButton      =QPushButton("Exit")
        
        NewLabButton.clicked.connect(self.MainButtonClicked)
        LoadLabButton.clicked.connect(self.MainButtonClicked)
        SettingsButton.clicked.connect(self.MainButtonClicked)
        ControllsButton.clicked.connect(self.MainButtonClicked)
        ExitButton.clicked.connect(self.MainButtonClicked)
        
        vbox=QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(NewLabButton)
        vbox.addWidget(LoadLabButton)
        vbox.addWidget(SettingsButton)
        vbox.addWidget(ControllsButton)
        vbox.addWidget(ExitButton)
        vbox.addStretch(1)
        
        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        hbox.addStretch(1)
        
        self.MainMenu.setLayout(hbox)
    
    def setupNewLabMenu(self):
        lbl1=QLabel("Choose labyrinth size")
        
        lblx=QLabel("X")
        self.lex=QLineEdit(self)
        hbox1=QHBoxLayout()
        hbox1.addWidget(lblx)
        hbox1.addWidget(self.lex)
        
        lbly=QLabel("Y")
        self.ley=QLineEdit(self)
        hbox2=QHBoxLayout()
        hbox2.addWidget(lbly)
        hbox2.addWidget(self.ley)
        
        lblz=QLabel("Z")
        self.lez=QLineEdit(self)
        hbox3=QHBoxLayout()
        hbox3.addWidget(lblz)
        hbox3.addWidget(self.lez)
        
        self.CrUseChaCB=QCheckBox("Use Character")
        self.CrUseChaCB.setCheckState(Qt.Checked)
        
        self.CrHideInfoCB=QCheckBox("Hide Infobar")
        self.CrHideInfoCB.setCheckState(Qt.Unchecked)
        
        DS="10" #Default size
        self.lex.setText(DS)
        self.ley.setText(DS)
        self.lez.setText(DS)
        
        self.lex.setToolTip("Integer from 1 to 999")
        self.ley.setToolTip("Integer from 1 to 999")
        self.lez.setToolTip("Integer from 1 to 999")
        
        self.CreateButton=QPushButton("Create Labyrinth")
        self.CreateButton.clicked.connect(self.CreateLabyrinthButtonClicked)
        
        BackButton=QPushButton("Back")
        BackButton.clicked.connect(self.MainButtonClicked)
        
        vbox=QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(lbl1)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addWidget(self.CrUseChaCB)
        vbox.addWidget(self.CrHideInfoCB)
        vbox.addWidget(self.CreateButton)
        vbox.addWidget(BackButton)
        vbox.addStretch(1)
        
        tophbox=QHBoxLayout()
        tophbox.addStretch(1)
        tophbox.addLayout(vbox)
        tophbox.addStretch(1)
        
        self.NewLabMenu.setLayout(tophbox)
    
    def setupLoadLabMenu(self):
        self.FileComboBox=QComboBox()
        lbl1=QLabel("Choose labyrinth to load")
        
        self.FileComboBox=QComboBox()
        self.FileComboBox.addItem('Files in "Saves" folder')
        SaveFiles = os.listdir("Saves")
        self.FileComboBox.addItems(SaveFiles)
        
        self.RefreshButton=QPushButton("Refresh")
        self.RefreshButton.clicked.connect(self.RefreshFileComboBox)
        
        hboxRF=QHBoxLayout()
        hboxRF.addWidget(self.FileComboBox)
        hboxRF.addWidget(self.RefreshButton)
        
        self.LoUseChaCB=QCheckBox("Use Character")
        self.LoUseChaCB.setCheckState(Qt.Checked)
        
        self.LoHideInfoCB=QCheckBox("Hide Infobar")
        self.LoHideInfoCB.setCheckState(Qt.Unchecked)
        
        self.LoadButton=QPushButton("Load Labyrinth")
        self.LoadButton.clicked.connect(self.LoadLabyrinthButtonClicked)
        
        BackButton=QPushButton("Back")
        BackButton.clicked.connect(self.MainButtonClicked)
        
        vbox=QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(lbl1)
        vbox.addLayout(hboxRF)
        vbox.addWidget(self.LoUseChaCB)
        vbox.addWidget(self.LoHideInfoCB)
        vbox.addWidget(self.LoadButton)
        vbox.addWidget(BackButton)
        vbox.addStretch(1)
        
        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        hbox.addStretch(1)
        
        self.LoadLabMenu.setLayout(hbox)
    
    def setupSettigsMenu(self):
        hbox0=QHBoxLayout()
        lbl1=QLabel("Settings")
        DefaultButton=QPushButton("Default")
        DefaultButton.clicked.connect(self.DefaultSettingsClicked)
        hbox0.addWidget(lbl1)
        hbox0.addWidget(DefaultButton)
        
        hbox1=QHBoxLayout()
        lblWL=QLabel("Wall Length")
        self.WallLengthBox=QSpinBox()
        self.WallLengthBox.setRange(35, 200)
        self.WallLengthBox.setValue(self.MWindow.WALL_LENGTH)
        self.WallLengthBox.setSuffix("px")
        self.WallLengthBox.setSingleStep(10)
        hbox1.addWidget(lblWL)
        hbox1.addWidget(self.WallLengthBox)
        
        hbox4=QHBoxLayout()
        lblCMS=QLabel("Character Movement Speed")
        self.ChaMovSpeedBox=QSpinBox()
        self.ChaMovSpeedBox.setRange(1, 60)
        self.ChaMovSpeedBox.setValue(self.MWindow.CHARACTER_MOVEMENT_SPEED)
        self.ChaMovSpeedBox.setSuffix(" squares/s")
        self.ChaMovSpeedBox.setSingleStep(10)
        hbox4.addWidget(lblCMS)
        hbox4.addWidget(self.ChaMovSpeedBox)
        
        hbox5=QHBoxLayout()
        lblCSM=QLabel("Character Size Compared to Square")
        self.ChaSizeModBox=QSpinBox()
        self.ChaSizeModBox.setRange(10, 100)
        self.ChaSizeModBox.setValue(self.MWindow.CHARACTER_SIZE_MODIFIER*100)
        self.ChaSizeModBox.setSuffix("%")
        self.ChaSizeModBox.setSingleStep(10)
        hbox5.addWidget(lblCSM)
        hbox5.addWidget(self.ChaSizeModBox)
        
        hbox6=QHBoxLayout()
        lblSCL=QLabel("Squares moved per scroll")
        self.ScrollLenBox=QSpinBox()
        self.ScrollLenBox.setRange(1,30)
        self.ScrollLenBox.setValue(self.MWindow.SCROLL_LEN)
        self.ScrollLenBox.setSuffix(" squares")
        self.ScrollLenBox.setSingleStep(10)
        hbox6.addWidget(lblSCL)
        hbox6.addWidget(self.ScrollLenBox)
        
        hboxCA=QHBoxLayout()
        lblCA=QLabel("Labyrinth Create Algorithm")
        self.ALGCreateComboBox=QComboBox()
        self.ALGCreateComboBox.addItems(self.MWindow.ALGCreateList)
        hboxCA.addWidget(lblCA)
        hboxCA.addWidget(self.ALGCreateComboBox)
        
        
        SaveButton=QPushButton("Save")
        SaveButton.clicked.connect(self.SaveSettingsButtonClicked)
        
        BackButton=QPushButton("Back")
        BackButton.clicked.connect(self.MainButtonClicked)
        
        vbox=QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox0)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox5)
        vbox.addLayout(hbox6)
        vbox.addLayout(hboxCA)
        vbox.addWidget(SaveButton)
        vbox.addWidget(BackButton)
        vbox.addStretch(1)
        
        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        hbox.addStretch(1)
        
        self.SettingsMenu.setLayout(hbox)
    
    def setupControllsMenu(self):
        lbl=QLabel("Controlls\n" +\
                   "\tMovement\nUp:\t\tW\nDown:\t\tS\nLeft:\t\tA\nRight:\t\tD\n" +\
                   "Ladder Up:\tE/R/Space\nLadder Down:\tQ/F/Shift\n\n" +\
                   "\tOther\nScroll:\t\tArrow Keys\nBack\t\tEsc")
        
        BackButton=QPushButton("Back")
        BackButton.clicked.connect(self.MainButtonClicked)
        
        vbox=QVBoxLayout()
        vbox.addStretch(1)
        vbox.addWidget(lbl)
        vbox.addWidget(BackButton)
        vbox.addStretch(1)
        
        hbox=QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(vbox)
        hbox.addStretch(1)
        
        self.ControllsMenu.setLayout(hbox)


class Field(QWidget):
    def __init__(self, MWindow):
        super().__init__()
        self.MWindow=MWindow
        
        self.xlen=MWindow.labyrinth.XDim
        self.ylen=MWindow.labyrinth.YDim
        self.zlen=MWindow.labyrinth.ZDim
        
        self.ZVisible=self.MWindow.labyrinth.StartSquare.z         #whitch 2D-slice of the 3D-labyrinth is drawn.
        
        self.setFieldWindow()
        
        self.timer=QTimer()
        self.timer.timeout.connect(self.timerEvent)
        self.timer.start(TIMER_INTERVAL)
    
    def timerEvent(self):
        if self.MWindow.UseCharacter == True:
            self.MWindow.character.update()
        self.update()
    
    def setFieldWindow(self):
        SCW=self.MWindow.screenGeometry.width()
        SCH=self.MWindow.screenGeometry.height()
        
        w=(self.xlen)*self.MWindow.WALL_LENGTH + 2*self.MWindow.X_DRAW_BUFFER
        h=(self.ylen)*self.MWindow.WALL_LENGTH + self.MWindow.Y_DRAW_BUFFER + Y_DRAW_BUFFER_UNDER
        
        if w>SCW:
            w=SCW
        if h>SCH-100:
            h=SCH-100
        
        x=SCW/2 - w/2
        y=SCH/2 - h/2
        
        self.MWindow.setWindowState(Qt.WindowNoState)    #bordered normal window
        self.MWindow.setGeometry(x, y, w, h)
    
    def paintEvent(self, e):
        painter=QPainter()
        painter.begin(self)
        
        self.drawWalls(painter)
        self.drawStartAndFinish(painter)
        if not self.MWindow.HideInfobar:
            self.drawInfobar(painter)
        if self.MWindow.UseCharacter:
            self.MWindow.character.draw(painter)
        if self.MWindow.ShowSolution and self.MWindow.SolutionFound:
            self.drawSolveDots(painter)
        
        painter.end()
    
    def drawWalls(self, painter):       #THE LADDERS ARE ALSO CONSIDERED AS WALLS
        pen=QPen(Qt.black, self.MWindow.DRAW_WIDTH, Qt.SolidLine)
        painter.setPen(pen)
        
        z=self.ZVisible
        walls=self.MWindow.labyrinth.walls
        
        #Draw the "normal" walls.
        for i in range(self.xlen):
            for j in range(self.ylen):
                walls[i][j][z][0].draw(painter)     #horisontal
                walls[i][j][z][1].draw(painter)     #vertical
        
        #Draw the rightmost, bottommost and topmost walls.
        for i in range(self.xlen):      #bottommost, horisontal
            walls[i][self.ylen][z][0].draw(painter)
        for j in range(self.ylen):      #rightmost, vertical
            walls[self.xlen][j][z][1].draw(painter)
        
        #Draw the ladders.
        for i in range(self.xlen):
            for j in range(self.ylen):
                #print("{}, {}".format(i,j))
                walls[i][j][z][2].drawLadder(painter, z)     #floor
                walls[i][j][z+1][2].drawLadder(painter, z)   #ceiling
    
    def drawInfobar(self, painter):
        #Infobar on top of the labyrinth.
        GU=UPPER_BAR_HEIGHT/2   #GridUnit = 32
        
        pen=QPen(Qt.black, 1)
        painter.setPen(pen)
        font=QFont()
        font.setPixelSize(GU/2)
        painter.setFont(font)
        
        #Border
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 18*GU, 2*GU, 10, 15)
        
        ZStr=str(self.ZVisible+1)
        Line1="Current level\tLabyrinth size\t\tSTART: Red"
        coordStr="({}, {}, {})".format(self.xlen, self.ylen, self.zlen)
        Line2="%-3s\t\t(X, Y, Z)=%-15s\tFINISH: Blue" % (ZStr, coordStr)
        
        painter.drawText(1*GU,   1*GU, Line1)
        painter.drawText(1*GU, 1.5*GU, Line2)
    
    def drawStartAndFinish(self, painter):
        painter.setBrush(QBrush())
        
        StSq=self.MWindow.labyrinth.StartSquare
        FiSq=self.MWindow.labyrinth.FinishSquare
        
        CLW=math.ceil( (self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH)/15 )   #Circle Line Width
        
        if StSq.z == self.ZVisible:       #Startsquare
            pen=QPen(Qt.red, CLW, Qt.SolidLine)
            painter.setPen(pen)
            
            x=self.MWindow.X_DRAW_BUFFER + StSq.x*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW
            y=self.MWindow.Y_DRAW_BUFFER + StSq.y*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW
            hw=self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH - CLW*2
            
            painter.drawEllipse(x, y, hw, hw)
        
        if FiSq.z == self.ZVisible:       #Finishsquare
            pen=QPen(Qt.blue, CLW, Qt.SolidLine)
            painter.setPen(pen)
            
            x=self.MWindow.X_DRAW_BUFFER + FiSq.x*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW
            y=self.MWindow.Y_DRAW_BUFFER + FiSq.y*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW
            hw=self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH - CLW*2
            
            painter.drawEllipse(x, y, hw, hw)
    
    def drawSolveDots(self, painter):
        CLW=math.ceil( (self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH)/15 )   #Circle Line Width
        
        sq=Square(0,0,0)
        for SqInt in self.MWindow.ALGSolve.Stack:
            x, y, z = sq.IntToXYZ(SqInt)
            if z == self.ZVisible:
                pen=QPen(Qt.magenta, CLW, Qt.SolidLine)
                painter.setPen(pen)
                
                x=self.MWindow.X_DRAW_BUFFER + x*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW   + self.MWindow.WALL_LENGTH/2
                y=self.MWindow.Y_DRAW_BUFFER + y*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + CLW   + self.MWindow.WALL_LENGTH/2
                hw= (self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH - CLW*2) /10
                
                painter.drawEllipse(x, y, hw, hw)


class Labyrinth:
    def __init__(self, MWindow):
        self.MWindow=MWindow
        
        self.XDim=None
        self.YDim=None
        self.ZDim=None
        
        self.StartSquare=None
        self.FinishSquare=None
        
        self.walls=None     #self.walls[i][j][k][m]=Wall(MW, i, j, k, m)
        
        self.ALGCreate=None #An algorithm.
    
    def setWalls(self, x, y, z):
        self.XDim=x
        self.YDim=y
        self.ZDim=z
        
        self.walls=[]
        #We create walls origin points for a labyrinth of (n+1)^3 size, when we set dimensions for a n^3 labyrinth.
        for i in range(self.XDim+1):                    #X
            self.walls.append([])
            for j in range(self.YDim+1):                #Y
                self.walls[i].append([])
                for k in range(self.ZDim+1):            #Z
                    self.walls[i][j].append([])
                    for m in range(3):                  #Direction (3 alternatives)
                        self.walls[i][j][k].append([])
                        #Fill labyrinth with walls.
                        self.walls[i][j][k][m]=Wall(self.MWindow, i, j, k, m)
    
    def setCreateAlgorithm(self, CreateIndex):
        if CreateIndex == 0:
            self.ALGCreate=RBCreate(self)
        else:
            print("Could not set undefined Create Algorithm: [{}]".format(self.MWindow.ALGCreateList[CreateIndex]))
            self.MWindow.statusBar.showMessage("Could not set undefined Create Algorithm: [{}]".format(self.MWindow.ALGCreateList[CreateIndex]))
            return False
        
        print("Create Algorithm set to: [{}]".format(self.MWindow.ALGCreateList[CreateIndex]))
        return True
    
    def MODIFY(self):
        print("modifyWalls START")
        self.ALGCreate.ModifyLabyrinth()
        print("modifyWalls DONE")


class Wall:
    def __init__(self, MWindow, x, y, z, d):
        self.MWindow=MWindow
        
        self.passable=False
        
        self.x=x
        self.y=y
        self.z=z
        self.d=d    #Direction: XDIR/YDIR/ZDIR <==> 0/1/2
        
        if self.d==XDIR:
            self.h=0
            self.w=self.MWindow.WALL_LENGTH
            self.in2D=True
        elif self.d==YDIR:
            self.h=self.MWindow.WALL_LENGTH
            self.w=0
            self.in2D=True
        else:
            self.h=0
            self.w=0
            self.in2D=False
    
    def draw(self, painter):
        if self.in2D and not self.passable:
            x=(self.x)*self.MWindow.WALL_LENGTH + self.MWindow.X_DRAW_BUFFER
            y=(self.y)*self.MWindow.WALL_LENGTH + self.MWindow.Y_DRAW_BUFFER
            
            painter.drawLine(x, y, x+self.w, y+self.h)
    
    def drawLadder(self, painter, z):   #z is the plane we are drawing in
        if self.passable:
            x0=self.MWindow.X_DRAW_BUFFER + self.x*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2
            y0=self.MWindow.Y_DRAW_BUFFER + self.y*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2
            space=self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH
            
            x=x0+(space/2)
            y=y0+(space/2)
            
            xd=x+10
            xu=x-10
            
            if self.z==z:
                painter.drawText(xd, y, "D")     #Down
            else:       #self.z == z+1
                painter.drawText(xu, y, "U")    #Up


class Square:
    def __init__(self, x, y, z):
        self.x=x
        self.y=y
        self.z=z
    
    def asInt(self):
        return self.x*1000000 + self.y*1000 + self.z     #Max size of labyrinth-coordinates: 999
    
    def printSq(self):
        print("Square: ({}, {}, {})".format(self.x, self.y, self.z))
    
    def IntToXYZ(self, i):
        x=int( i/1000000 )
        y=int( (i/1000)%1000 )
        z=int( i%1000 )
        return x, y, z


class AlgorithmCreate:
    #Parent-class for all classes that create labyrinths.
    def __init__(self, Labyrinth):
        self.labyrinth=Labyrinth
        self.walls=self.labyrinth.walls
        
        self.xlen=self.labyrinth.XDim
        self.ylen=self.labyrinth.YDim
        self.zlen=self.labyrinth.ZDim
        
        #Find the start and finish squares. Range for x,y and z is [0, len-1].
        self.labyrinth.StartSquare=self.RandomSquareInLabyrinth()
        self.labyrinth.FinishSquare=self.RandomSquareInLabyrinth()
        while self.labyrinth.StartSquare.asInt() == self.labyrinth.FinishSquare.asInt():
            self.labyrinth.FinishSquare=self.RandomSquareInLabyrinth()
        
        self.AllSqCount=self.xlen*self.ylen*self.zlen
    
    def ModifyLabyrinth(self):
        pass
    
    def RandomSquareInLabyrinth(self):
        x=randint(0, self.xlen-1)
        y=randint(0, self.ylen-1)
        z=randint(0, self.zlen-1)
        square=Square(x, y, z)
        return square
    
    def RemoveWall(self, referenceSq, d):   #d=direction
        x=referenceSq.x
        y=referenceSq.y
        z=referenceSq.z
        
        if d==XPOS:
            self.walls[x+1][y][z][1].passable=True
        elif d==XNEG:
            self.walls[x][y][z][1].passable=True
        elif d==YPOS:
            self.walls[x][y+1][z][0].passable=True
        elif d==YNEG:
            self.walls[x][y][z][0].passable=True
        elif d==ZPOS:
            self.walls[x][y][z+1][2].passable=True
        else:   #ZNEG
            self.walls[x][y][z][2].passable=True
    
    def SquareIsLegal(self, sq):
        x=sq.x
        y=sq.y
        z=sq.z
        
        if x<0 or y<0 or z<0 or self.xlen-1<x or self.ylen-1<y or self.zlen-1<z:
            return False
        else:
            return True
    
    def RandomAdjacentSquare(self, referenceSq):
        d=randint(0,5)
        
        x=referenceSq.x
        y=referenceSq.y
        z=referenceSq.z
        
        if d==XPOS:
            newSquare=Square(x+1,y,z)
        elif d==XNEG:
            newSquare=Square(x-1,y,z)
        elif d==YPOS:
            newSquare=Square(x,y+1,z)
        elif d==YNEG:
            newSquare=Square(x,y-1,z)
        elif d==ZPOS:
            newSquare=Square(x,y,z+1)
        else:   #ZNEG
            newSquare=Square(x,y,z-1)
        
        return newSquare, d


class RBCreate(AlgorithmCreate):   #RB = Recursive bakctracker
    def __init__(self, Labyrinth):
        AlgorithmCreate.__init__(self, Labyrinth)
        self.Stack=[]       #Current route that is developing
        self.Wisited=[]
    
    def ModifyLabyrinth(self):
        self.CurrentSq=self.labyrinth.StartSquare
        self.Wisited.append(self.CurrentSq.asInt())
        self.Stack.append(self.CurrentSq.asInt())
        
        while len(self.Wisited)<self.AllSqCount:                                    #All squares are in the labyrinth.
            
            while not self.AllVisited():                                            #We have come to a square that does not have any fresh squeres nearby.
                newSq, d=self.RandomAdjacentSquare(self.CurrentSq)
                while self.SquareIsVisited(newSq) or not self.SquareIsLegal(newSq): #We get a square that is not wisited and is legal.
                    newSq, d=self.RandomAdjacentSquare(self.CurrentSq)
                #newSq is now acceptable, so we remowe the wall between the current and the new square.
                self.RemoveWall(self.CurrentSq, d)
                
                self.CurrentSq=newSq
                self.Wisited.append(self.CurrentSq.asInt())
                self.Stack.append(self.CurrentSq.asInt())
            
            #When we reach a square that does  not lead to any new squares, we move back in the Stack
            CSqInt=self.Stack.pop()
            x, y, z = self.CurrentSq.IntToXYZ(CSqInt)
            self.CurrentSq=Square(x, y, z)
    
    def AllVisited(self):
        x=self.CurrentSq.x
        y=self.CurrentSq.y
        z=self.CurrentSq.z
        
        if   not ( x==self.xlen-1 or self.SquareIsVisited(Square(x+1,y,z)) ):
            return False
        elif not ( x==0           or self.SquareIsVisited(Square(x-1,y,z)) ):
            return False
        elif not ( y==self.ylen-1 or self.SquareIsVisited(Square(x,y+1,z)) ):
            return False
        elif not ( y==0           or self.SquareIsVisited(Square(x,y-1,z)) ):
            return False
        elif not ( z==self.zlen-1 or self.SquareIsVisited(Square(x,y,z+1)) ):
            return False
        elif not ( z==0           or self.SquareIsVisited(Square(x,y,z-1)) ):
            return False
        else:
            return True
    
    def SquareIsVisited(self, sq):
        sqInt=sq.asInt()
        return sqInt in self.Wisited


class AlgorithmSolve:
    #Parent-class for all classes that solve labyrinths.
    def __init__(self, MWindow):
        self.MWindow=MWindow
        
        self.labyrinth=self.MWindow.labyrinth
        self.walls=self.labyrinth.walls
        self.character=self.MWindow.character
        
        if self.MWindow.UseCharacter:
            x, y, z = self.character.getChaSQCoord()
            self.SolvingStartSQ=Square(x, y, z)
        else:
            self.SolvingStartSQ=self.MWindow.labyrinth.StartSquare
        
        self.SolvingFinishSQ=self.labyrinth.FinishSquare
        
        self.xlen=self.labyrinth.XDim
        self.ylen=self.labyrinth.YDim
        self.zlen=self.labyrinth.ZDim
        
        self.Stack=[]  #Path to the finish as list of squares in int-form.
    
    def SolveLabyrinth(self):
        pass
    
    def RandomAdjacentSquare(self, referenceSq):
        d=randint(0,5)
        
        x=referenceSq.x
        y=referenceSq.y
        z=referenceSq.z
        
        if d==XPOS:
            newSquare=Square(x+1,y,z)
        elif d==XNEG:
            newSquare=Square(x-1,y,z)
        elif d==YPOS:
            newSquare=Square(x,y+1,z)
        elif d==YNEG:
            newSquare=Square(x,y-1,z)
        elif d==ZPOS:
            newSquare=Square(x,y,z+1)
        else:   #ZNEG
            newSquare=Square(x,y,z-1)
        
        return newSquare, d
    
    def SquareIsLegal(self, sq):
        x=sq.x
        y=sq.y
        z=sq.z
        
        if x<0 or y<0 or z<0 or self.xlen-1<x or self.ylen-1<y or self.zlen-1<z:
            return False
        else:
            return True


class RBSolve(AlgorithmSolve):   #RB = Recursive bakctracker
    def __init__(self, MWindow):
        AlgorithmSolve.__init__(self, MWindow)
        self.Stack=[]       #Current route that is developing
        self.Wisited=[]
    
    def SolveLabyrinth(self):
        self.CurrentSq=self.SolvingStartSQ
        self.Stack.append(self.CurrentSq.asInt())
        self.Wisited.append(self.CurrentSq.asInt())
        
        while self.CurrentSq.asInt() != self.SolvingFinishSQ.asInt():   #Compearing int:s because the square object representing the same square are different.
            
            while self.CanMoveToSomeAdjacentSQ(self.CurrentSq):         #Can move to a square from current square that is not wisited.
                newSq, d=self.RandomAdjacentSquare(self.CurrentSq)
                while self.SquareIsVisited(newSq) or not self.CanMoveInDirection(self.CurrentSq, d) or not self.SquareIsLegal(newSq):
                    newSq, d=self.RandomAdjacentSquare(self.CurrentSq)
                #newSq is acceptable, so we move to the newSq.
                self.CurrentSq=newSq
                self.Stack.append(self.CurrentSq.asInt())
                self.Wisited.append(self.CurrentSq.asInt())
            
            #When we reach a square that does  not lead to any new squares, we move back in the Stack.
            CSqInt=self.Stack.pop()
            x, y, z = self.CurrentSq.IntToXYZ(CSqInt)
            self.CurrentSq=Square(x, y, z)
        self.Stack.append(self.CurrentSq.asInt())
    
    def SquareIsVisited(self, sq):
        sqInt=sq.asInt()
        return sqInt in self.Wisited
    
    def CanMoveInDirection(self, referenceSq, d):
        x=referenceSq.x
        y=referenceSq.y
        z=referenceSq.z
        
        if d==XPOS:
            if self.walls[x+1][y][z][1].passable==True:
                return True
            else:
                return False
        elif d==XNEG:
            if self.walls[x][y][z][1].passable==True:
                return True
            else:
                return False
        elif d==YPOS:
            if self.walls[x][y+1][z][0].passable==True:
                return True
            else:
                return False
        elif d==YNEG:
            if self.walls[x][y][z][0].passable==True:
                return True
            else:
                return False
        elif d==ZPOS:
            if self.walls[x][y][z+1][2].passable==True:
                return True
            else:
                return False
        else:   #ZNEG
            if self.walls[x][y][z][2].passable==True:
                return True
            else:
                return False
    
    def CanMoveToSomeAdjacentSQ(self, referenceSq):
        x=referenceSq.x
        y=referenceSq.y
        z=referenceSq.z
        
        for d in range(6):
            if self.CanMoveInDirection(referenceSq, d):
                if d==XPOS:
                    newSquare=Square(x+1,y,z)
                elif d==XNEG:
                    newSquare=Square(x-1,y,z)
                elif d==YPOS:
                    newSquare=Square(x,y+1,z)
                elif d==YNEG:
                    newSquare=Square(x,y-1,z)
                elif d==ZPOS:
                    newSquare=Square(x,y,z+1)
                else:   #ZNEG
                    newSquare=Square(x,y,z-1)
                
                if not self.SquareIsVisited(newSquare):
                    return True
        return False


class Character:
    def __init__(self, MWindow):
        self.MWindow=MWindow
        #These are in square-coordinates for the characther WHEN starting.
        self.xSQ=MWindow.labyrinth.StartSquare.x
        self.ySQ=MWindow.labyrinth.StartSquare.y
        self.zSQ=MWindow.labyrinth.StartSquare.z
        
        #The coordinates we use for the character are in pixels.
        self.RLW=math.ceil( (self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH)/15 )   #Rectangle Line Width
        
        self.x=self.MWindow.X_DRAW_BUFFER + self.xSQ*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + self.RLW*1.0    #Upper left corner x-coordinate
        self.y=self.MWindow.Y_DRAW_BUFFER + self.ySQ*self.MWindow.WALL_LENGTH + self.MWindow.DRAW_WIDTH/2 + self.RLW*1.0    #Upper left corner y-coordinate
        self.hw=self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH - self.RLW*2*1.0                                         #Height and Width
        
        self.MovementPerFrame= self.MWindow.CHARACTER_MOVEMENT_SPEED * ( self.MWindow.WALL_LENGTH / FPS )
        #We modify the characters size.
        self.x+=0.5*(1-self.MWindow.CHARACTER_SIZE_MODIFIER)*self.hw
        self.y+=0.5*(1-self.MWindow.CHARACTER_SIZE_MODIFIER)*self.hw
        self.hw*=self.MWindow.CHARACTER_SIZE_MODIFIER
    
    def draw(self, painter):
        painter.setBrush(QBrush())
        
        RLW=math.ceil( (self.MWindow.WALL_LENGTH - self.MWindow.DRAW_WIDTH)/15 )   #Rectangle Line Width
        
        pen=QPen(Qt.green, RLW, Qt.SolidLine)
        painter.setPen(pen)
        
        painter.drawRect(self.x, self.y, self.hw, self.hw)
    
    def update(self):
        x, y , z = self.getChaSQCoord()
        xL = self.x - self.MWindow.X_DRAW_BUFFER - self.MWindow.DRAW_WIDTH/2    #x Left
        xR = xL + self.hw                                                       #x Right
        yU = self.y - self.MWindow.Y_DRAW_BUFFER - self.MWindow.DRAW_WIDTH/2    #y Up
        yD = yU + self.hw                                                       #y Down
        
        for key in self.MWindow.pressedKeys:
            if key == Qt.Key_W: #Up
                dW = yU - self.MWindow.WALL_LENGTH*y - self.MWindow.DRAW_WIDTH  -self.MovementPerFrame    #Difference W(button)
                
                if self.SqIsPassable(x, y, z, 0):
                    if not self.SqIsPassable(x+1, y, z, 0) or not self.SqIsPassable(x+1, y-1, z, 1):
                        #Checking if the square right has a wall that is horisontal, and if the square up right has a wall that is vertical.
                        dD = self.MWindow.WALL_LENGTH*(x+1) - self.MWindow.DRAW_WIDTH*2 - xR  +self.MovementPerFrame      #+ so you dont get stuck on the flat.
                        if dD>0:
                            self.y-=self.MovementPerFrame
                        else:
                            if dW>0:
                                self.y-=self.MovementPerFrame
                    else:
                        self.y-=self.MovementPerFrame
                else:
                    if dW>0:
                        self.y-=self.MovementPerFrame
            
            if key == Qt.Key_A: #Left
                dA = xL - self.MWindow.WALL_LENGTH*x - self.MWindow.DRAW_WIDTH  -self.MovementPerFrame
                
                if self.SqIsPassable(x, y, z, 1):
                    if not self.SqIsPassable(x, y+1, z, 1) or not self.SqIsPassable(x-1, y+1, z, 0):
                        #Checking if the square down has a wall that is vertical., and if the square down left has a wall that is horisontal.
                        dS = self.MWindow.WALL_LENGTH*(y+1) - self.MWindow.DRAW_WIDTH*2 - yD  +self.MovementPerFrame      #+ so you dont get stuck on the flat.
                        if dS>0:
                            self.x-=self.MovementPerFrame
                        else:
                            if dA>0:
                                self.x-=self.MovementPerFrame
                    else:
                        self.x-=self.MovementPerFrame
                else:
                    if dA>0:
                        self.x-=self.MovementPerFrame
            
            if key == Qt.Key_S: #Down
                dS = self.MWindow.WALL_LENGTH*(y+1) - self.MWindow.DRAW_WIDTH*2 - yD  -self.MovementPerFrame
                
                if self.SqIsPassable(x, y+1, z, 0):
                    if not self.SqIsPassable(x+1, y+1, z, 0) or not self.SqIsPassable(x+1, y+1, z, 1):
                        #Checking if the square down right has a wall that is horisontal, and if the square down right has a wall that is vertical.
                        dD = self.MWindow.WALL_LENGTH*(x+1) - self.MWindow.DRAW_WIDTH*2 - xR  +self.MovementPerFrame      #+ so you dont get stuck on the flat.
                        if dD>0:
                            self.y+=self.MovementPerFrame
                        else:
                            if dS>0:
                                self.y+=self.MovementPerFrame
                    else:
                        self.y+=self.MovementPerFrame
                else:
                    if dS>0:
                        self.y+=self.MovementPerFrame
            
            if key == Qt.Key_D: #Right
                dD = self.MWindow.WALL_LENGTH*(x+1) - self.MWindow.DRAW_WIDTH*2 - xR  -self.MovementPerFrame
                
                if self.SqIsPassable(x+1, y, z, 1):
                    if not self.SqIsPassable(x+1, y+1, z, 1) or not self.SqIsPassable(x+1, y+1, z, 0):
                        #Checking if the square down right has a wall that is vertical, and if the square down right has a wall that is horisontal.
                        dS = self.MWindow.WALL_LENGTH*(y+1) - self.MWindow.DRAW_WIDTH*2 - yD  +self.MovementPerFrame      #+ so you dont get stuck on the flat.
                        if dS>0:
                            self.x+=self.MovementPerFrame
                        else:
                            if dD>0:
                                self.x+=self.MovementPerFrame
                    else:
                        self.x+=self.MovementPerFrame
                else:
                    if dD>0:
                        self.x+=self.MovementPerFrame
    
    def getChaSQCoord(self):
        xSQ = math.floor( ( self.x - self.MWindow.X_DRAW_BUFFER - self.MWindow.DRAW_WIDTH/2 ) / self.MWindow.WALL_LENGTH )
        ySQ = math.floor( ( self.y - self.MWindow.Y_DRAW_BUFFER - self.MWindow.DRAW_WIDTH/2 ) / self.MWindow.WALL_LENGTH )
        zSQ = self.MWindow.field.ZVisible
        return xSQ, ySQ, zSQ
    
    def SqIsPassable(self, x, y, z, d):
        return self.MWindow.labyrinth.walls[x][y][z][d].passable


class SaveRead:
    def __init__(self, MWindow):
        self.MWindow=MWindow
    
    def WallAsInt(self, wall):  #WallInt looks like: PDXXXYYYZZZ
        # passable: 0-1 direction: 0-2  coordinates: 0-999
        return int(wall.passable)*10000000000 + wall.d*1000000000 + wall.x*1000000 + wall.y*1000 + wall.z
    
    def WallIntToPDXYZ(self, i):
        p=int( i/10000000000 )
        d=int( (i/1000000000)%10 )
        x=int( (i/1000000)%1000 )
        y=int( (i/1000)%1000 )
        z=int( i%1000 )
        return p, d, x, y, z
    
    def FirstWallIntToXYZ(self, i):
        x=int( i/1000000 )
        y=int( (i/1000)%1000 )
        z=int( i%1000 )
        return x, y, z
    
    def SaveWalls(self):
        #The walls are stored as ints in a list.
        self.xlen=self.MWindow.labyrinth.XDim
        self.ylen=self.MWindow.labyrinth.YDim
        self.zlen=self.MWindow.labyrinth.ZDim
        
        self.walls=self.MWindow.labyrinth.walls
        self.WallInts=[]
        
        self.WallInts.append( self.xlen*1000000 + self.ylen*1000 + self.zlen )  #Dimensions
        SqInt = self.MWindow.labyrinth.StartSquare.asInt()                      #StartSquare
        self.WallInts.append(SqInt)
        SqInt = self.MWindow.labyrinth.FinishSquare.asInt()                     #FinishSquare
        self.WallInts.append(SqInt)
        
        for i in range(self.xlen+1):
            for j in range(self.ylen+1):
                for k in range(self.zlen+1):
                    for d in range(3):
                        wallInt = self.WallAsInt( self.walls[i][j][k][d] )
                        self.WallInts.append(wallInt)
        
        dimensions = "_("+ str(self.xlen) +"x"+ str(self.ylen) +"x"+ str(self.zlen) +")_"
        
        usedCreateALG = self.MWindow.ALGCreateList[ self.MWindow.CreateIndex ]
        
        dt=datetime.datetime.today()
        dateNtime = str(dt.year) +"_"+ str(dt.month) +"_"+ str(dt.day) \
        +"--"+ str(dt.hour) +"_"+ str(dt.minute) +"_"+ str(dt.second) +"_"+ str(dt.microsecond)
        
        filename = "Saves\\LAB" + dimensions + usedCreateALG +"-"+ dateNtime + ".pickle"
        
        try:
            file=open(filename, "wb")
            pickle.dump(self.WallInts, file)
            file.close()
            self.MWindow.statusBar.showMessage("The labyrinth has been saved.")
        except:
            self.MWindow.statusBar.showMessage("An error occured during the writing. " +\
            "Check that you have a file named \"Saves\" in the applications map.")
    
    def ReadWallsInt(self, filename):
        try:
            file=open(filename, "rb")
            wallsInt=pickle.load(file)
            file.close()
            
            return wallsInt
        except:
            self.MWindow.statusBar.showMessage("An error occured during the reading.")
            return -1
    
    def ReadWalls(self, Lab, wallsInt):
        header=True
        hc=3    #header count
        sq=Square(0,0,0)
        for WI in wallsInt:
            if not header:
                p, d, x, y, z = self.WallIntToPDXYZ(WI)
                Lab.walls[x][y][z][d].passable=bool(p)
            else:
                if hc==2:
                    x, y, z = sq.IntToXYZ(WI)
                    Lab.StartSquare = Square(x,y,z)
                elif hc==1:
                    x, y, z = sq.IntToXYZ(WI)
                    Lab.FinishSquare = Square(x,y,z)
                hc-=1
                if hc==0:
                    header=False



if __name__ == '__main__':
    #Creates a "Saves"-folder if one does not exist.
    if not os.path.isdir("Saves"):
        os.makedirs("Saves")
        print('"Saves" folder created')
    
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())