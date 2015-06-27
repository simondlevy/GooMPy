#!/usr/bin/env python

import math
import PIL.Image
import cStringIO
import urllib
import os
import time
import sys

try:
    from key import _KEY
except:
    _KEY = ''

_EARTHPIX = 268435456  # Number of pixels in half the earth's circumference at zoom = 21
_DEGREE_PRECISION = 4  # Number of decimal places for rounding coordinates
_TILESIZE = 640        # Larget tile we can grab without paying
_GRABRATE = 4          # Fastest rate at which we can download tiles without paying

_pixrad = _EARTHPIX / math.pi
 
def _new_image(width, height):

    return PIL.Image.new('RGB', (width, height))

def _roundto(value, digits):

    return int(value * 10**digits) / 10.**digits

def _pixels_to_degrees(pixels, zoom):
    return pixels * 2 ** (21 - zoom)

def _grab_tile(lat, lon, zoom, maptype, _TILESIZE, sleeptime):

    urlbase = 'https://maps.googleapis.com/maps/api/staticmap?center=%f,%f&zoom=%d&maptype=%s&size=%dx%d&format=jpg'
    urlbase += _KEY

    specs = lat, lon, zoom, maptype, _TILESIZE, _TILESIZE

    filename = 'mapscache/' + ('%f_%f_%d_%s_%d_%d' % specs) + '.jpg'

    tile = None

    if os.path.isfile(filename):
        tile = PIL.Image.open(filename)

    else:
        url = urlbase % specs

        result = urllib.urlopen(url).read()
        tile = PIL.Image.open(cStringIO.StringIO(result))
        if not os.path.exists('mapscache'):
            os.mkdir('mapscache')
        tile.save(filename)
        time.sleep(sleeptime) # Choke back speed to avoid maxing out limit

    return tile


def _pix_to_lon(j, lonpix, ntiles, _TILESIZE, zoom):

    return math.degrees((lonpix + _pixels_to_degrees(((j)-ntiles/2)*_TILESIZE, zoom) - _EARTHPIX) / _pixrad)

def _pix_to_lat(k, latpix, ntiles, _TILESIZE, zoom):

    return math.degrees(math.pi/2 - 2 * math.atan(math.exp(((latpix + _pixels_to_degrees((k-ntiles/2)*_TILESIZE, zoom)) - _EARTHPIX) / _pixrad))) 

def fetchTiles(latitude, longitude, zoom, maptype, radius_meters, reporter=None):
    '''
    Fetches tiles from GoogleMaps at the specified coordinates, zoom level (0-22), and map type ('roadmap', 
    'terrain', 'satellite', or 'hybrid').  The value of radius_meters deteremines the number of tiles that will be 
    fetched.  Tiles are stored as JPEG images in the mapscache folder.
    '''
 
    latitude = _roundto(latitude, _DEGREE_PRECISION)
    longitude = _roundto(longitude, _DEGREE_PRECISION)

    # https://groups.google.com/forum/#!topic/google-maps-js-api-v3/hDRO4oHVSeM
    pixels_per_meter = 2**zoom / (156543.03392 * math.cos(math.radians(latitude)))

    # number of tiles required to go from center latitude to desired radius in meters
    ntiles = int(round(2 * pixels_per_meter / (_TILESIZE /2./ radius_meters)))

    lonpix = _EARTHPIX + longitude * math.radians(_pixrad)

    sinlat = math.sin(math.radians(latitude))
    latpix = _EARTHPIX - _pixrad * math.log((1 + sinlat)/(1 - sinlat)) / 2

    bigsize = ntiles * _TILESIZE
    bigimage = _new_image(bigsize, bigsize)

    sys.stdout.flush()

    if reporter != None:
        reporter.start(ntiles*ntiles)

    for j in range(ntiles):
        lon = _pix_to_lon(j, lonpix, ntiles, _TILESIZE, zoom)
        for k in range(ntiles):
            lat = _pix_to_lat(k, latpix, ntiles, _TILESIZE, zoom)
            tile = _grab_tile(lat, lon, zoom, maptype, _TILESIZE, 1./_GRABRATE)
            if reporter != None:
                reporter.update(j*ntiles+k+1)
            bigimage.paste(tile, (j*_TILESIZE,k*_TILESIZE))

    if reporter != None:
        reporter.stop()

    west = _pix_to_lon(0, lonpix, ntiles, _TILESIZE, zoom)
    east = _pix_to_lon(ntiles-1, lonpix, ntiles, _TILESIZE, zoom)

    north = _pix_to_lat(0, latpix, ntiles, _TILESIZE, zoom)
    south = _pix_to_lat(ntiles-1, latpix, ntiles, _TILESIZE, zoom)

    return bigimage, (north,west), (south,east)


class GooMPy(object):

    def __init__(self, width, height, latitude, longitude, zoom, maptype, radius_meters, reporter=None):
        '''
        Creates a GooMPy object for specified display widthan and height at the specified coordinates,
        zoom level (0-22), and map type ('roadmap', 'terrain', 'satellite', or 'hybrid').
        The value of radius_meters deteremines the number of tiles that will be used to create
        the map image.  The reporter is an optional reporting object that should provide the methods
        start(self,tiles_total), update(self, tiles_so_far), and stop(self).  Tiles will be fetched using
        the fetchTiles() method (q.v.) as needed.
        '''

        self.lat = latitude
        self.lon = longitude

        self.width = width
        self.height = height

        self.zoom = zoom
        self.maptype = maptype

        self.winimage = _new_image(self.width, self.height)

        self.bigimage, self.northwest, self.southeast = fetchTiles(latitude, longitude,  zoom, maptype, radius_meters, reporter)

        self.leftx  = self._center(self.width)
        self.uppery = self._center(self.height)

        self._update()

    def _center(self, dim):

        return (self.bigimage.size[0] - dim) / 2

    def _update(self):
       
        self.winimage.paste(self.bigimage, (-self.leftx, -self.uppery))

    def getImage(self):
        '''
        Returns the current image as a PIL.Image object.
        '''

        return self.winimage

    def _constrain(self, oldval, diff, dimsize):

        newval = oldval + diff
        return newval if newval > 0 and newval < self.bigimage.size[0]-dimsize else oldval

    def move(self, dx, dy):
        '''
        Moves the view by the specified pixels dx, dy.
        '''

        self.leftx = self._constrain(self.leftx, dx, self.width)
        self.uppery = self._constrain(self.uppery, dy, self.height)
        self._update()

     
# Example ---------------------------------------------------------------------------------

if __name__ == '__main__':

    from Tkinter import Tk, Canvas, Label, Frame, IntVar, Radiobutton, Button
    from ttk import Progressbar
    from PIL import ImageTk
    from threading import Thread

    LATITUDE  =  37.7913838
    LONGITUDE = -79.44398934
 
    WIDTH = 800
    HEIGHT = 500

    RADIUS_METERS = 2000

    class Progbar(Progressbar):

        def __init__(self, canvas):

            cw = int(canvas['width'])
            ch = int(canvas['height'])

            self.x = 100
            self.y = ch / 2

            self.progbar = Progressbar( canvas, orient="horizontal", length=cw-2*self.x, mode="determinate")

            self.label = Label(canvas, text='Loading tiles ...', font=('Helvetica', 18))

        def start(self, maxval):

            self.progbar.place(x=self.x, y=self.y)
            self.label.place(x=self.x, y=self.y-50)
 
            self.maxval = maxval

        def stop(self):

            self._hide(self.progbar)
            self._hide(self.label)

        def update(self, value):

            self.progbar['value'] = 100 * value/self.maxval

        def _hide(self, widget):

            widget.place(x=-9999)


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

            self.radiogroup = Frame(self.label)
            self.radiovar = IntVar()
            self.maptypes = ['roadmap', 'terrain', 'satellite', 'hybrid']
            self.add_radio_button('Road Map',  0)
            self.add_radio_button('Terrain',   1)
            self.add_radio_button('Satellite', 2)
            self.add_radio_button('Hybrid',    3)

            self.zoom_in_button  = self.add_zoom_button('+', +1)
            self.zoom_out_button = self.add_zoom_button('-', -1)

            maptype_index = 0
            self.radiovar.set(maptype_index)
            self.maptype = self.maptypes[maptype_index]

            self.zoomlevel = 15

            self.restart()

        def add_zoom_button(self, text, sign):

            button = Button(self.label, text=text, width=1, command=lambda:self.zoom(sign))
            return button

        def zoom(self, sign):

            newlevel = self.zoomlevel + sign
            if newlevel > 0 and newlevel < 22:
                self.zoomlevel += sign
                self.restart()

        def restart(self):

            self.thread = Thread(target=self.launch)
            self.thread.start()

        def add_radio_button(self, text, index):

            maptype = self.maptypes[index]
            Radiobutton(self.radiogroup, text=maptype, variable=self.radiovar, value=index, command=lambda:self.usemap(maptype)).grid(row=0, column=index)

        def launch(self):

            self.progbar = Progbar(self.canvas)
            self.goompy = GooMPy(WIDTH, HEIGHT, LATITUDE, LONGITUDE, self.zoomlevel, self.maptype, RADIUS_METERS, reporter=self.progbar)
            self.coords = None
            self.redraw()

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

            self.label.place(x=0, y=0, width=WIDTH, height=HEIGHT) # make room for widgets at top

            self.radiogroup.place(x=0,y=0)

            x = int(self.canvas['width']) - 50
            y = int(self.canvas['height']) - 80

            self.zoom_in_button.place(x= x, y=y)
            self.zoom_out_button.place(x= x, y=y+30)

        def usemap(self, maptype):

            self.maptype = maptype
            self.restart()

        def check_quit(self, event):

            if ord(event.char) == 27: # ESC
                exit(0)

    UI().mainloop()
