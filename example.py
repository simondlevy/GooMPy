#!/usr/bin/env python
'''
Example of using GooMPy with Tkinter

Copyright (C) 2015 Alec Singer and Simon D. Levy

This code is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.
This code is distributed in the hope that it will be useful,     
but WITHOUT ANY WARRANTY without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU Lesser General Public License 
along with this code.  If not, see <http://www.gnu.org/licenses/>.
'''

from Tkinter import Tk, Canvas, Label, Frame, IntVar, Radiobutton, Button
from PIL import ImageTk

from goompy import GooMPy

WIDTH = 800
HEIGHT = 500

LATITUDE  =  37.7913838
LONGITUDE = -79.44398934
ZOOM = 15
MAPTYPE = 'roadmap'

class UI(Tk):

    def __init__(self):

        Tk.__init__(self)

        self.geometry('%dx%d+500+500' % (WIDTH,HEIGHT))
        self.title('GooMPy')

        self.canvas = Canvas(self, width=WIDTH, height=HEIGHT)

        self.canvas.pack()

        self.bind("<Key>", self.check_quit)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<Button-1>', self.click)

        self.label = Label(self.canvas)

        self.radiogroup = Frame(self.canvas)
        self.radiovar = IntVar()
        self.maptypes = ['roadmap', 'terrain', 'satellite', 'hybrid']
        self.add_radio_button('Road Map',  0)
        self.add_radio_button('Terrain',   1)
        self.add_radio_button('Satellite', 2)
        self.add_radio_button('Hybrid',    3)

        self.zoom_in_button  = self.add_zoom_button('+', +1)
        self.zoom_out_button = self.add_zoom_button('-', -1)

        self.zoomlevel = ZOOM

        maptype_index = 0
        self.radiovar.set(maptype_index)

        self.goompy = GooMPy(WIDTH, HEIGHT, LATITUDE, LONGITUDE, ZOOM, MAPTYPE)

        self.restart()

    def add_zoom_button(self, text, sign):

        button = Button(self.canvas, text=text, width=1, command=lambda:self.zoom(sign))
        return button

    def reload(self):

        self.coords = None
        self.redraw()

        self['cursor']  = ''


    def restart(self):

        # A little trick to get a watch cursor along with loading
        self['cursor']  = 'watch'
        self.after(1, self.reload)

    def add_radio_button(self, text, index):

        maptype = self.maptypes[index]
        Radiobutton(self.radiogroup, text=maptype, variable=self.radiovar, value=index, 
                command=lambda:self.usemap(maptype)).grid(row=0, column=index)

    def click(self, event):

        self.coords = event.x, event.y

    def drag(self, event):

        self.goompy.move(self.coords[0]-event.x, self.coords[1]-event.y)
        self.image = self.goompy.getImage()
        self.redraw()
        self.coords = event.x, event.y

    def redraw(self):

        self.image = self.goompy.getImage()
        self.image_tk = ImageTk.PhotoImage(self.image)
        self.label['image'] = self.image_tk

        self.label.place(x=0, y=0, width=WIDTH, height=HEIGHT) 

        self.radiogroup.place(x=0,y=0)

        x = int(self.canvas['width']) - 50
        y = int(self.canvas['height']) - 80

        self.zoom_in_button.place(x= x, y=y)
        self.zoom_out_button.place(x= x, y=y+30)

    def usemap(self, maptype):

        self.goompy.useMaptype(maptype)
        self.restart()

    def zoom(self, sign):

        newlevel = self.zoomlevel + sign
        if newlevel > 0 and newlevel < 22:
            self.zoomlevel = newlevel
            self.goompy.useZoom(newlevel)
            self.restart()

    def check_quit(self, event):

        if ord(event.char) == 27: # ESC
            exit(0)

UI().mainloop()
