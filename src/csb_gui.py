import tkinter as tk
import sys, math, cmath

board = (16000, 9000)
resolution = 0.06
canvas = (960, 540)

color_bg = 'black'
color_cp = 'white'
color_pods = ('yellow', 'orange', 'red', 'magenta')

cps = [(2000, 2000), (3000, 7000)]


def to_canvas(z):
    return (round(z.real*resolution), round(z.imag*resolution))

def to_board(x, y):
    #return (round(x/resolution), round(y/resolution))
    return round(x/resolution) + round(y/resolution) * 1j


def create_checkpoint(cvs, loc, idx):
    p = loc[0] + loc[1] * 1j
    x1, y1 = to_canvas(p-600-600j)
    x2, y2 = to_canvas(p+600+600j)
    x, y = to_canvas(p+90j)

    cvs.create_oval(x1, y1, x2, y2,
            outline='white', tags=('cp', 'cp%s' % idx), width=3)
    cvs.create_text(x, y, text=str(idx),
            fill='white', tags=('cp', 'cp%s' % idx),
            font=('Nimbus Sans', round(450*resolution)), anchor='center')

class Pod():
    def __init__(self, canvas, idx):
        self.canvas = canvas
        self.idx = idx
        self.__p = 0j
        self.__v = 0j
        self.__a = 0

        x1, y1 = to_canvas(self.p - 400 - 400j)
        x2, y2 = to_canvas(self.p + 400 + 400j)
        x, y = to_canvas(self.p)
        xa, ya = to_canvas(self.p + cmath.exp(1j * self.a * math.pi / 180) * 400)
        xv, yv = to_canvas(self.p + self.v)

        self._c_vec = canvas.create_line(x, y, xv, yv,
                width=2, fill='lightblue', tags=('pod', 'pod_%s' % idx))
        self._c_circ = canvas.create_oval(x1, y1, x2, y2, 
                outline=color_pods[idx], width=2, tags=('pod', 'pod_%s' % idx))
        self._c_ang = canvas.create_line(x, y, xa, ya,
                width=2, fill=color_pods[idx], tags=('pod', 'pod_%s' % idx))

    def _get_x(self):
        return self.__p.real
    def _set_x(self, x):
        self.p = x + self.__p.imag * 1j
    x = property(_get_x, _set_x)

    def _get_y(self):
        return self.__p.imag
    def _set_y(self, y):
        self.p = self.__p.real + y * 1j
    y = property(_get_y, _set_y)

    def _get_p(self):
        return self.__p
    def _set_p(self, p):
        #dx, dy = to_canvas(p - self.__p)
        #self.canvas.move('pod_%s' % self.idx, dx, dy)
        self.canvas.coords(self._c_circ, *(to_canvas(p-400-400j) + to_canvas(p+400+400j)))
        self.canvas.coords(self._c_vec, *(to_canvas(p) + to_canvas(p+self.__v)))
        self.canvas.coords(self._c_ang, *(to_canvas(p) + to_canvas(p + cmath.exp(1j * self.__a * math.pi/180)*400)))
        self.__p = p
    p = property(_get_p, _set_p)

    def _get_vx(self):
        return self.__v.real
    def _set_vx(self, vx):
        self.v = vx + self.__v.imag * 1j
    vx = property(_get_vx, _set_vx)

    def _get_vy(self):
        return self.__v.imag
    def _set_vy(self, vy):
        self.v = self.__v.real + vy * 1j
    vy = property(_get_vy, _set_vy)

    def _get_v(self):
        return self.__v
    def _set_v(self, v):
        self.__v = v
        self.canvas.coords(self._c_vec, *(to_canvas(self.__p) + to_canvas(self.__p + self.__v)))
    v = property(_get_v, _set_v)

    def _get_a(self):
        return self.__a
    def _set_a(self, a):
        self.__a = a
        self.canvas.coords(self._c_ang, *(to_canvas(self.__p) + to_canvas(self.__p + cmath.exp(1j * self.__a * math.pi / 180) * 400)))
    a = property(_get_a, _set_a)


class GUI():
    def __init__(self, parent):
        self.parent = parent
        self.canvas = tk.Canvas(parent, width=canvas[0], height=canvas[1], background='black')
        self.canvas.pack(padx=8, pady=8)
        #self.draw_arena()

    def draw_arena(self, cps):
        for i, cp in enumerate(cps):
            create_checkpoint(self.canvas, cp, i)

def main():
    root = tk.Tk()
    root.title("Coders Strike Back")
    gui = GUI(root)
    p = Pod(gui.canvas, 0)
    p.x = 2500
    p.y = 3000
    p = Pod(gui.canvas, 1)
    p.x = 4500
    p.y = 2500
    p.a = 113
    p = Pod(gui.canvas, 2)
    p.x = 5000
    p.y = 6000
    p.a = 78
    p.vx = 400
    p.vy = -100
    p = Pod(gui.canvas, 3)
    p.x = 2500
    p.y = 5500
    p.a = 68
    root.mainloop()
if __name__ == '__main__':
    main()

