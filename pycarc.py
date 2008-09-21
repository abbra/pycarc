from ocempgui import *
from ocempgui.draw import Image
from ocempgui.widgets import *
from ocempgui.widgets.Constants import *

import pygame
import pygame.surfarray
import Numeric
import random

NORTH = "NORTH"
SOUTH = "SOUTH"
EAST = "EAST"
WEST = "WEST"

CITY = "CITY"
FARM = "FARM"
ROAD = "ROAD"
STREAM = "STREAM" #not implemented yet

global tiles

gui = ocempgui.widgets.Renderer()
gui.create_screen(1024, 768, pygame.RESIZABLE)
gui.title = "PyCarc - Carcassonne in Python"

blankimage = pygame.image.load("data/blank.png").convert_alpha()
playableimage = pygame.image.load("data/playable.png").convert_alpha()
meeplered = pygame.image.load("data/meeple_red.png").convert_alpha()
meeplered = pygame.transform.scale(meeplered, (30,30))
meeplegreen = pygame.image.load("data/meeple_green.png").convert_alpha()
meeplegreen = pygame.transform.scale(meeplegreen, (30,30))
meepleblue = pygame.image.load("data/meeple_blue.png").convert_alpha()
meepleblue = pygame.transform.scale(meepleblue, (30,30))

class Tile(pygame.sprite.Sprite):
    size = 90

    def __init__(self, picture = None, row=0, column=0):
        pygame.sprite.Sprite.__init__(self)
        self.edges = ((None,),(None,),(None,),(None,))
        self.blank = False
        self.image = picture
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column
        self.meeplelocs = []
        self.features = []

    def rotate(self):
        self.edges = (self.edges[3], self.edges[0], self.edges[1], self.edges[2])
        self.image = pygame.transform.rotate(self.image, -90)
        #move meeplelocs
        for i in xrange(len(self.meeplelocs)):
            self.meeplelocs[i] = ((-(self.meeplelocs[i][1]-0.5)+0.5,(self.meeplelocs[i][0]-0.5)+0.5))


    def test_edge(self, this, other):
        if this == None or other == None or None in this or None in other:
            return True
        elif len(this) != len(other):
            return False
        elif this == other:
            return True
        else:
            return False

    def update(self):
        self.rect.topleft = ((self.row-tiles.rows[0])*self.size, (self.column-tiles.columns[0])*self.size)

class PotentialTile(Tile):
    def __init__(self, row, column):
        pygame.sprite.Sprite.__init__(self)
        self.image = playableimage
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

class BlankTile(Tile):
    def __init__(self):
        Tile.__init__(self, picture = blankimage)
        self.blank = True
        self.rect = self.image.get_rect()

class NextTile(ImageLabel):
    def __init__(self, deck, tile=BlankTile()):
        ImageLabel.__init__(self, tile.image)
        self.deck = deck

    def set_tile(self, tile):
        self.tile = tile
        self.set_picture(tile.image)

    def rotate(self, tiles):
        if tiles.mode == "tile":
            self.tile.rotate()
            self.set_tile(self.tile)
            self.update_next_tile()

    def update_next_tile(self):
        tiles.test_tile(self.tile)

    def get_next(self):
        if len(self.deck) > 0:
            self.set_tile(self.deck.pop())
        else:
            self.set_tile(BlankTile())
        self.update_next_tile()

class Meeple(pygame.sprite.Sprite):
    def __init__(self, tile, loc, feature):
        pygame.sprite.Sprite.__init__(self)
        self.tile = tile
        self.loc = loc
        self.feature = feature
        self.feature.set_occupied(self)
        self.image = meeplered
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.left = self.tile.rect.left+(self.tile.rect.width*self.loc[0])-(self.rect.width/2)
        self.rect.top = self.tile.rect.top+(self.tile.rect.height*self.loc[1])-(self.rect.height/2)

class PotentialMeeple(Meeple):
    def __init__(self, tile, loc, feature):
        pygame.sprite.Sprite.__init__(self)
        self.tile = tile
        self.loc = loc
        self.feature = feature
        
        self.image = meeplered
        self.rect = self.image.get_rect()
        
        #probably should make this semi-transparent
        #self.image.set_alpha(128)
        #array = Numeric.array(pygame.surfarray.pixels_alpha(self.image))
        #array /= 2

class Feature():
    def __init__(self, tile):
        self.occupied = [False]
        self.linkedto = [self]
        self.tile = tile

    def incorporate(self, other):
        if not self == other:
            return
        self.linkedto = other.linkedto
        other.linkedto.append(self)
        self.occupied = other.occupied
        if self.occupied[0]!= False and self.is_closed():
            #ADD SCORE TO PLAYER WHO OWNS OCCUPYING MEEPLE
            #NOT IMPLEMENTED
            print self.get_score()
            meeple = self.occupied[0]
            meeple.kill()
            self.occupied[0] = False

    def __eq__(self, other):
        if isinstance(other, Feature):
            if self.name == other.name:
                return True
            else:
                return False
        return self.name == other

    def is_closed(self):
        #see of any of the edges that have this are next to a blank tile
        for i in xrange(len(self.tile.edges)):
            if self in self.tile.edges[i]:
                #north
                if i == 0:
                    if tiles.get_neighbor("north", self.tile.row, self.tile.column).blank:
                        return False
                #east
                elif i == 1:
                    if tiles.get_neighbor("east", self.tile.row, self.tile.column).blank:
                        return False
                #south
                elif i == 2:
                    if tiles.get_neighbor("south", self.tile.row, self.tile.column).blank:
                        return False
                #west
                elif i == 3:
                    if tiles.get_neighbor("west", self.tile.row, self.tile.column).blank:
                        return False
        return True

    def get_score(self):
        total = 0
        for thing in self.linkedto:
            total += thing.get_value()
        return total

    def get_value(self):
        return self.value
        
    def set_occupied(self, meeple):
        self.occupied[0] = meeple

class Farm(Feature):
    name = "Farm"
    def __init__(self, tile):
        Feature.__init__(self, tile)

class Road(Feature):
    name = "Road"
    value = 1
    def __init__(self, tile):
        Feature.__init__(self, tile)

class City(Feature):
    name = "City"
    value = 1
    def __init__(self, tile):
        Feature.__init__(self, tile)

    def get_score(self):
        total = 0
        for thing in self.linkedto:
            total += thing.get_value()
        if self.is_closed():
            total *= 2
        return total

class CityPendant(City):
    value = 2
    def __init__(self, tile):
        City.__init__(self, tile)

class Cloister(Feature):
    name = "Cloister"
    def __init__(self, tile):
        Feature.__init__(self, tile)

    #can never join anything else
    def incorporate(self, other):
        raise TypeError, "Cloisters cannot be incorporated"

    #value is based on neighbour occupancy
    def get_value(self):
        self.value = 0
        for row in (self.tile.row-1, self.tile.row, self.tile.row+1):
            for column in (self.column.row-1, self.column.row, self.column.row+1):
                if not tiles.get_tile(row, column).blank:
                    self.value += 1
        return self.value

    def closed(self):
        for row in (self.tile.row-1, self.tile.row, self.tile.row+1):
            for column in (self.column.row-1, self.column.row, self.column.row+1):
                if tiles.get_tile(row, column).blank:
                    return False
        return True

class Tiles(ImageMap):
    def __init__(self):
        ImageMap.__init__(self, pygame.Surface((1,1)))
        self.group = pygame.sprite.Group()

        self.potential = pygame.sprite.Group()
        self.meeples = pygame.sprite.Group()
        self.grid = {}
        self.rows = [0,0]
        self.columns = [0,0]
        self.mode = "tile"

    def set_mode_tile(self):
        nexttile.get_next()
        self.test_tile(nexttile.tile)
        self.mode = "tile"

    def set_mode_meeple(self):
        self.test_meeple(nexttile.tile)
        self.mode = "meeple"
        #skip if unable to play
        if len(self.potential) == 0:
            self.set_mode_tile()

    def location_picked(self, event):
        loc = ((self.relative_position[0]/Tile.size)+self.rows[0], (self.relative_position[1]/Tile.size)+self.columns[0])
        for sprite in self.potential.sprites():
            if sprite.rect.collidepoint(self.relative_position):
                if self.mode == "tile":
                    nexttile.tile.row = loc[0]
                    nexttile.tile.column = loc[1]
                    self.set_tile(nexttile.tile)
                    self.set_mode_meeple()
                    return
                elif self.mode == "meeple":
                    self.add_meeple(sprite)
                    self.set_mode_tile()
                    return

    def set_tile(self, tile):
        row = tile.row
        column = tile.column
        self.grid[(row,column)] = tile
        changed = False


        if row >= self.rows[1]:
            self.rows[1] = row+1
            changed = True
        if row <= self.rows[0]:
            self.rows[0] = row-1
            changed = True

        if column >= self.columns[1]:
            self.columns[1] = column+1
            changed = True
        if column <= self.columns[0]:
            self.columns[0] = column-1
            changed = True

        if changed:
            pixelheight = (self.columns[1]-self.columns[0]+1)*Tile.size
            pixelwidth = (self.rows[1]-self.rows[0]+1)*Tile.size
            self.background = pygame.surface.Surface((pixelwidth, pixelheight))
            self.set_picture(pygame.surface.Surface((pixelwidth, pixelheight)))

        #link the features on the tile to external features
        self.merge_edges(tile)

        self.group.add(tile)

        self.redraw()

    def get_tile(self, row, column):
        if (row,column) in self.grid:
            return self.grid[(row, column)]
        else:
            return BlankTile()

    def redraw(self):
        self.potential.clear(self.picture, self.background)
        self.meeples.clear(self.picture, self.background)
        self.group.update()
        self.potential.update()
        self.meeples.update()
        self.group.draw(self.picture)
        self.potential.draw(self.picture)
        self.meeples.draw(self.picture)
        self.set_dirty(True)

    def test_tile(self, testtile):
        self.potential.empty()
        if not testtile.blank:
            for row in xrange(self.rows[0],self.rows[1]+1):
                for column in xrange(self.columns[0],self.columns[1]+1):
                    tile = self.get_tile(row,column)
                    if tile.blank:
                        if self.test_edges(testtile, row, column):
                            self.potential.add(PotentialTile(row, column))
        self.redraw()

    def test_edges(self, tile, row, column):
        north = self.get_neighbor("north", row, column)
        south = self.get_neighbor("south", row, column)
        east = self.get_neighbor("east", row, column)
        west = self.get_neighbor("west", row, column)
        #no neighbours
        if north.blank and south.blank and east.blank and west.blank:
            return False
        #to the north
        elif not tile.test_edge(tile.edges[0], north.edges[2]):
            return False
        #to the south
        elif not tile.test_edge(tile.edges[2], south.edges[0]):
            return False
        #to the east
        elif not tile.test_edge(tile.edges[1], east.edges[3]):
            return False
        #to the west
        elif not tile.test_edge(tile.edges[3], west.edges[1]):
            return False
        return True

    def merge_edges(self, tile):
        if tile.blank:
            return
        north = self.get_neighbor("north", tile.row, tile.column)
        south = self.get_neighbor("south", tile.row, tile.column)
        east = self.get_neighbor("east", tile.row, tile.column)
        west = self.get_neighbor("west", tile.row, tile.column)
        #to the north
        if not north.blank:
            for i in xrange(len(tile.edges[0])):
                tile.edges[0][i].incorporate(north.edges[2][len(tile.edges[0])-1-i])
        #to the south
        if not south.blank:
            for i in xrange(len(tile.edges[2])):
                tile.edges[2][i].incorporate(south.edges[0][len(tile.edges[2])-1-i])
        #to the east
        if not east.blank:
            for i in xrange(len(tile.edges[1])):
                tile.edges[1][i].incorporate(east.edges[3][len(tile.edges[1])-1-i])
        #to the west
        if not west.blank:
            for i in xrange(len(tile.edges[3])):
                tile.edges[3][i].incorporate(west.edges[1][len(tile.edges[3])-1-i])

    def get_neighbor(self, direction, row, column):
        if direction == "north":
            return self.get_tile(row, column-1)
        elif direction == "south":
            return self.get_tile(row, column+1)
        elif direction == "east":
            return self.get_tile(row+1, column)
        elif direction == "west":
            return self.get_tile(row-1, column)

    def test_meeple(self, tile):
        self.potential.empty()
        for i in xrange(len(tile.meeplelocs)):
            if not tile.features[i].occupied[0] and not tile.features[i].is_closed():
                self.potential.add(PotentialMeeple(tile, tile.meeplelocs[i], tile.features[i]))
        self.redraw()

    def add_meeple(self, tempmeeple):
        self.meeples.add(Meeple(tempmeeple.tile, tempmeeple.loc, tempmeeple.feature))
        self.redraw()


def loadtiles():
    tiledeck = []
    
    pic_city1rwe =  pygame.image.load("data/city1rwe.png"). convert_alpha()
    pic_city1rswe = pygame.image.load("data/city1rswe.png").convert_alpha()
    pic_city1rse =  pygame.image.load("data/city1rse.png"). convert_alpha()
    pic_city1rsw =  pygame.image.load("data/city1rsw.png"). convert_alpha()
    pic_city2nw =   pygame.image.load("data/city2nw.png").  convert_alpha()
    pic_city2nwr =  pygame.image.load("data/city2nwr.png"). convert_alpha()
    pic_city2nws =  pygame.image.load("data/city2nws.png"). convert_alpha()
    pic_city2nwsr = pygame.image.load("data/city2nwsr.png").convert_alpha()
    pic_city2we =   pygame.image.load("data/city2we.png").  convert_alpha()
    pic_city2wes =  pygame.image.load("data/city2wes.png"). convert_alpha()
    pic_city3 =     pygame.image.load("data/city3.png").    convert_alpha()
    pic_city3r =    pygame.image.load("data/city3r.png").   convert_alpha()
    pic_city3s =    pygame.image.load("data/city3s.png").   convert_alpha()
    pic_city3sr =   pygame.image.load("data/city3sr.png").  convert_alpha()
    pic_city4 =     pygame.image.load("data/city4.png").    convert_alpha()
    pic_city11ne =  pygame.image.load("data/city11ne.png"). convert_alpha()
    pic_city11we =  pygame.image.load("data/city11we.png"). convert_alpha()
    pic_cloister =  pygame.image.load("data/cloister.png"). convert_alpha()
    pic_cloisterr = pygame.image.load("data/cloisterr.png").convert_alpha()
    pic_road2ns =   pygame.image.load("data/road2ns.png").  convert_alpha()
    pic_road2sw =   pygame.image.load("data/road2sw.png").  convert_alpha()
    pic_road3 =     pygame.image.load("data/road3.png").    convert_alpha()
    pic_road4 =     pygame.image.load("data/road4.png").    convert_alpha()

    #coordinate system has origin in topright going right then down

    tile = Tile(pic_city1rwe)
    tile.meeplelocs = [(0.5,0.0),(0.5,0.5),(0.5,1.0),(0.15,0.25)]
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2],), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rwe)
    tile.meeplelocs = [(0.5,0.0),(0.5,0.5),(0.5,1.0),(0.15,0.25)]
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2],), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rwe)
    tile.meeplelocs = [(0.5,0.0),(0.5,0.5),(0.5,1.0),(0.15,0.25)]
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2],), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rswe)
    #                  N      E        S      W      NE NE     SE     SW
    tile.features = (City(tile), Road(tile), Road(tile), Road(tile), Farm(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(1.0,0.5),(0.5,1.0),(0.0,0.5),(0.15,0.25), (1.0,1.0), (0.0, 1.0)]
    tile.edges = ((tile.features[0],), (tile.features[4], tile.features[1], tile.features[5]), (tile.features[5], tile.features[2], tile.features[6]), (tile.features[6], tile.features[3], tile.features[5]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rswe)
    #                  N      E        S      W      NE NE     SE     SW
    tile.features = (City(tile), Road(tile), Road(tile), Road(tile), Farm(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(1.0,0.5),(0.5,1.0),(0.0,0.5),(0.15,0.25), (1.0,1.0), (0.0, 1.0)]
    tile.edges = ((tile.features[0],), (tile.features[4], tile.features[1], tile.features[5]), (tile.features[5], tile.features[2], tile.features[6]), (tile.features[6], tile.features[3], tile.features[5]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rswe)
    #                  N      E        S      W      NE NE     SE     SW
    tile.features = (City(tile), Road(tile), Road(tile), Road(tile), Farm(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(1.0,0.5),(0.5,1.0),(0.0,0.5),(0.15,0.25), (1.0,1.0), (0.0, 1.0)]
    tile.edges = ((tile.features[0],), (tile.features[4], tile.features[1], tile.features[5]), (tile.features[5], tile.features[2], tile.features[6]), (tile.features[6], tile.features[3], tile.features[5]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rse)
    #                  N      E S    SE       NW
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.6,0.6),(0.9,0.9),(0.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]), (tile.features[3],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rse)
    #                  N      E S    SE       NW
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.6,0.6),(0.9,0.9),(0.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]), (tile.features[3],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rse)
    #                  N      E S    SE       NW
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.6,0.6),(0.9,0.9),(0.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]), (tile.features[3],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rsw)
    #                  N      W S    SW       NE
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.4,0.6),(0.1,0.9),(1.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rsw)
    #                  N      W S    SW       NE
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.4,0.6),(0.1,0.9),(1.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city1rsw)
    #                  N      W S    SW       NE
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.0),(0.4,0.6),(0.1,0.9),(1.0,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[3],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nw)
    #                  NW      SE
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[1],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nw)
    #                  NW      SE
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[1],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nw)
    #                  NW      SE
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[1],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nwr)
    #                  NW      C     S E     SE
    tile.features = (City(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],tile.features[2],tile.features[3]), (tile.features[3],tile.features[2],tile.features[1]), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nwr)
    #                  NW      C     S E     SE
    tile.features = (City(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],tile.features[2],tile.features[3]), (tile.features[3],tile.features[2],tile.features[1]), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nwr)
    #                  NW      C     S E     SE
    tile.features = (City(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],tile.features[2],tile.features[3]), (tile.features[3],tile.features[2],tile.features[1]), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nws)
    #                  NW      SE
    tile.features = (CityPendant(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[1],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nws)
    #                  NW      SE
    tile.features = (CityPendant(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[1],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nwsr)
    #                  NW      C     S E     SE
    tile.features = (CityPendant(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],tile.features[2],tile.features[3]), (tile.features[3],tile.features[2],tile.features[1]), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2nwsr)
    #                  NW      C     S E     SE
    tile.features = (CityPendant(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0),(0.5, 0.5), (0.7, 0.7), (1.0,1.0)]
    tile.edges = ((tile.features[0],), (tile.features[1],tile.features[2],tile.features[3]), (tile.features[3],tile.features[2],tile.features[1]), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2we)
    #                  EW           N             S
    tile.features = (City(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 1.0), (0.5, 0.0)]
    tile.edges = ((tile.features[1],), (tile.features[0],),(tile.features[2],),(tile.features[0],))
    #add to the deck
    
    tiledeck += [tile]

    tile = Tile(pic_city2wes)
    #                  EW           N             S
    tile.features = (CityPendant(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 1.0), (0.5, 0.0)]
    tile.edges = ((tile.features[1],), (tile.features[0],),(tile.features[2],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city2wes)
    #                  EW           N             S
    tile.features = (CityPendant(tile), Farm(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 1.0), (0.5, 0.0)]
    tile.edges = ((tile.features[1],), (tile.features[0],),(tile.features[2],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city3)
    #                  EW           S             S
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[1],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city3)
    #                  EW           S             S
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[1],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city3)
    #                  EW           S             S
    tile.features = (City(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[1],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city3r)
    #                  EW                  SE             S         SW
    tile.features = (City(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.0, 0.0), (0.5,0.0), (1.0,0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[3],tile.features[2],tile.features[1]),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]

    tile = Tile(pic_city3s)
    #                  EW           S             S
    tile.features = (CityPendant(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.5, 0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[1],),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city3sr)
    #                  EW                  SE             S         SW
    tile.features = (CityPendant(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.0, 0.0), (0.5,0.0), (1.0,0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[3],tile.features[2],tile.features[1]),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city3sr)
    #                  EW                  SE             S         SW
    tile.features = (CityPendant(tile), Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.5,0.5),(0.0, 0.0), (0.5,0.0), (1.0,0.0)]
    tile.edges = ((tile.features[0],), (tile.features[0],),(tile.features[3],tile.features[2],tile.features[1]),(tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city4)
    #                  EW                  SE             S         SW
    tile.features = (CityPendant(tile),)
    tile.meeplelocs = [(0.5,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[0],), (tile.features[0],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city11ne)
    #                  
    tile.features = (City(tile),City(tile),Farm(tile))
    tile.meeplelocs = [(0.5,1.0), (1.0,0.5), (0.5,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[2],), (tile.features[2],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city11ne)
    #                  
    tile.features = (City(tile),City(tile),Farm(tile))
    tile.meeplelocs = [(0.5,1.0), (1.0,0.5), (0.5,0.5)]
    tile.edges = ((tile.features[0],), (tile.features[1],), (tile.features[2],), (tile.features[2],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city11we)
    #                  
    tile.features = (City(tile),City(tile),Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (1.0,0.5), (0.5,0.5)]
    tile.edges = ((tile.features[2],), (tile.features[1],), (tile.features[2],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city11we)
    #                  
    tile.features = (City(tile),City(tile),Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (1.0,0.5), (0.5,0.5)]
    tile.edges = ((tile.features[2],), (tile.features[1],), (tile.features[2],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_city11we)
    #                  
    tile.features = (City(tile),City(tile),Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (1.0,0.5), (0.5,0.5)]
    tile.edges = ((tile.features[2],), (tile.features[1],), (tile.features[2],), (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_cloister)
    #                  
    tile.features = (Cloister(tile),Farm(tile))
    tile.meeplelocs = [(0.5,0.5), (0.25,0.25)]
    tile.edges = ((tile.features[1],), (tile.features[1],), (tile.features[1],), (tile.features[1],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_cloister)
    #                  
    tile.features = (Cloister(tile),Farm(tile))
    tile.meeplelocs = [(0.5,0.5), (0.25,0.25)]
    tile.edges = ((tile.features[1],), (tile.features[1],), (tile.features[1],), (tile.features[1],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_cloister)
    #                  
    tile.features = (Cloister(tile),Farm(tile))
    tile.meeplelocs = [(0.5,0.5), (0.25,0.25)]
    tile.edges = ((tile.features[1],), (tile.features[1],), (tile.features[1],), (tile.features[1],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_cloister)
    #                  
    tile.features = (Cloister(tile),Farm(tile))
    tile.meeplelocs = [(0.5,0.5), (0.25,0.25)]
    tile.edges = ((tile.features[1],), (tile.features[1],), (tile.features[1],), (tile.features[1],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_cloisterr)
    #                  
    tile.features = (Cloister(tile),Farm(tile), Road(tile))
    tile.meeplelocs = [(0.5,0.5), (0.25,0.25), (1.0, 0.5)]
    tile.edges = ((tile.features[1],), (tile.features[1],tile.features[2],tile.features[1]), (tile.features[1],), (tile.features[1],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2ns)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.5), (0.5,0.5), (1.0, 0.5)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road2sw)
    #                  
    tile.features = (Farm(tile), Road(tile), Farm(tile))
    tile.meeplelocs = [(0.0,0.0), (0.5,0.5), (0.0, 1.0)]
    tile.edges = ((tile.features[2],), (tile.features[2],), (tile.features[2],tile.features[1],tile.features[0]),  (tile.features[0],tile.features[1],tile.features[2]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road3)
    #                  N             E          SE        S              SW        W
    tile.features = (Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile))
    tile.meeplelocs = [(0.5,0.0), (1.0,0.5), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (0.0, 0.5)]
    tile.edges = ((tile.features[0],), (tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],tile.features[3],tile.features[4]), (tile.features[4],tile.features[5],tile.features[0]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road3)
    #                  N             E          SE        S              SW        W
    tile.features = (Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile))
    tile.meeplelocs = [(0.5,0.0), (1.0,0.5), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (0.0, 0.5)]
    tile.edges = ((tile.features[0],), (tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],tile.features[3],tile.features[4]), (tile.features[4],tile.features[5],tile.features[0]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road3)
    #                  N             E          SE        S              SW        W
    tile.features = (Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile))
    tile.meeplelocs = [(0.5,0.0), (1.0,0.5), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (0.0, 0.5)]
    tile.edges = ((tile.features[0],), (tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],tile.features[3],tile.features[4]), (tile.features[4],tile.features[5],tile.features[0]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road3)
    #                  N             E          SE        S              SW        W
    tile.features = (Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile))
    tile.meeplelocs = [(0.5,0.0), (1.0,0.5), (1.0, 1.0), (0.5, 1.0), (0.0, 1.0), (0.0, 0.5)]
    tile.edges = ((tile.features[0],), (tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],tile.features[3],tile.features[4]), (tile.features[4],tile.features[5],tile.features[0]))
    #add to the deck
    tiledeck += [tile]
    
    tile = Tile(pic_road4)
    #                  NW           N           NE             E          SE        S              SW        W
    tile.features = (Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile), Farm(tile), Road(tile))
    tile.meeplelocs = [(0.0, 0.0), (0.0, 0.5), (0.0, 1.0), (0.5, 1.0), (1.0, 1.0), (1.0, 0.5), (1.0, 0.0), (0.5, 0.0)]
    tile.edges = ((tile.features[0],tile.features[1],tile.features[2]), (tile.features[2],tile.features[3],tile.features[4]), (tile.features[4],tile.features[5],tile.features[6]), (tile.features[6],tile.features[7],tile.features[0]))
    #add to the deck
    tiledeck += [tile]
    
    #end of standard tiles
    random.shuffle(tiledeck)
    #add river tiles if using
    #otherwise add start tile

    tile = Tile(pic_city1rwe)
    tile.meeplelocs = [(0.5,0.0),(0.5,0.5),(0.5,1.0),(0.15,0.25)]
    tile.features = (City(tile), Road(tile), Farm(tile), Farm(tile))
    tile.edges = ((tile.features[0],), (tile.features[3], tile.features[1], tile.features[2]), (tile.features[2],), (tile.features[2], tile.features[1], tile.features[3]))
    #add to the deck
    tiledeck += [tile]
    
    return tiledeck

scrolledwindow = ScrolledWindow(768,768)

tiles = Tiles()

tiledeck = loadtiles()

#lay the starting tile
tiles.set_tile(tiledeck.pop())

#draw the first one
nexttile = NextTile(tiledeck)
rotatebutton = Button("Rotate")
rotatebutton.connect_signal(SIG_CLICKED, nexttile.rotate, tiles)

baseframe = HFrame()
sidebar = VFrame()
baseframe.add_child(scrolledwindow)
baseframe.add_child(sidebar)
sidebar.add_child(nexttile)
sidebar.add_child(rotatebutton)
gui.add_widget(baseframe)
scrolledwindow.set_child(tiles)
scrolledwindow.connect_signal(SIG_MOUSEDOWN, tiles.location_picked)
nexttile.get_next()

gui.start()

