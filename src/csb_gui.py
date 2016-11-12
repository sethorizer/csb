import tkinter as tk
import threading, queue
import sys, math, cmath

board = (16000, 9000)
cp_size = 600
pod_size = 400

resolution = 0.06
canvas = (960, 540)

color_bg = 'black'
color_cp = 'gray'
color_pods = ('yellow', 'orange', 'red', 'magenta')


def to_canvas(z):
    return (round(z.real*resolution), round(z.imag*resolution))

def to_board(x, y):
    #return (round(x/resolution), round(y/resolution))
    return round(x/resolution) + round(y/resolution) * 1j


class Checkpoint():
    def __init__(self, canvas, idx):
        self.canvas = canvas
        self.idx = idx
        self.__p = 0j

        x1, y1 = to_canvas(self.p - (1 + 1j) * cp_size)
        x2, y2 = to_canvas(self.p + (1 + 1j) * cp_size)
        x, y = to_canvas(self.p + (cp_size * 0.15) * 1j)
        self._c_circ = self.canvas.create_oval(x1, y1, x2, y2,
                outline=color_cp, tags=('cp', 'cp%s' % idx), width=3)
        self._c_text = self.canvas.create_text(x, y, text=str(idx),
                fill=color_cp, tags=('cp', 'cp%s' % idx),
                font=('Nimbus Sans', round(cp_size * 0.75 * resolution)), anchor='center')

    def _get_p(self):
        return self.__p
    def _set_p(self, p):
        self.canvas.coords(self._c_circ, *(to_canvas(p - (1 + 1j) * cp_size) + to_canvas(p + (1 + 1j) * cp_size)))
        self.canvas.coords(self._c_text, *(to_canvas(p + (cp_size * 0.15) * 1j)))
        self.__p = p
    p = property(_get_p, _set_p)

class Pod():
    def __init__(self, canvas, idx):
        self.canvas = canvas
        self.idx = idx
        self.__p = 0j
        self.__v = 0j
        self.__a = 0

        x1, y1 = to_canvas(self.p - (1 + 1j) * pod_size)
        x2, y2 = to_canvas(self.p + (1 + 1j) * pod_size)
        x, y = to_canvas(self.p)
        xa, ya = to_canvas(self.p + cmath.exp(1j * self.a * math.pi / 180) * pod_size)
        xv, yv = to_canvas(self.p + self.v)

        self._c_vec = canvas.create_line(x, y, xv, yv,
                width=3, fill='lightblue', tags=('pod', 'pod_%s' % idx))
        self._c_circ = canvas.create_oval(x1, y1, x2, y2, 
                outline=color_pods[idx], width=3, tags=('pod', 'pod_%s' % idx))
        self._c_ang = canvas.create_line(x, y, xa, ya,
                width=3, fill=color_pods[idx], tags=('pod', 'pod_%s' % idx))

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
        self.canvas.coords(self._c_circ, *(to_canvas(p - (1 + 1j) * pod_size) + to_canvas(p + (1 + 1j) * pod_size)))
        self.canvas.coords(self._c_vec, *(to_canvas(p) + to_canvas(p+self.__v)))
        self.canvas.coords(self._c_ang, *(to_canvas(p) + to_canvas(p + cmath.exp(1j * self.__a * math.pi / 180) * pod_size)))
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
        self.canvas.coords(self._c_ang, *(to_canvas(self.__p) + to_canvas(self.__p + cmath.exp(1j * self.__a * math.pi / 180) * pod_size)))
    a = property(_get_a, _set_a)


class GUI(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = queue.Queue()
        self.daemon = True
        self.start()

    def cb_quit(self):
        self.root.quit()

    def show_position(self, positions):
        self.q.put(positions)
        self.root.event_generate('<<show:pos>>', when='tail')

    def _show_position(self, event):
        pos = self.q.get()
        for i, p in enumerate(pos):
            self.pods[i].p = complex(float(p[0]), float(p[1]))
            self.pods[i].v = complex(float(p[2]), float(p[3]))
            self.pods[i].a = int(p[4])

    def set_checkpoints(self, checkpoints):
        self.q.put(checkpoints)
        self.root.event_generate('<<set:cps>>', when='tail')

    def _set_checkpoints(self, event):
        checkpoints = self.q.get()
        i=0
        for i, p in enumerate(checkpoints):
            if i == len(self.cps):
                self.cps.append(Checkpoint(self.canvas, i))
                self.canvas.tag_lower('cp%s' % i)
            self.cps[i].p = int(p[0]) + int(p[1]) * 1j
            self.canvas.itemconfig('cp%s' % i, state='normal')
        for j in range(i+1, len(self.cps)):
            self.canvas.itemconfig('cp%s' % j, state='hidden')
            

    def run(self):
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.cb_quit)
        self.root.title("Coders Strike Back - Replay")
        self.canvas = tk.Canvas(self.root, width=canvas[0], height=canvas[1], background='black')
        self.canvas.pack(padx=8, pady=8)
        self.root.bind('<<show:pos>>', self._show_position)
        self.root.bind('<<set:cps>>', self._set_checkpoints)

        self.pods = []
        for i in range(4):
            self.pods.append(Pod(self.canvas, i))
        self.cps = []

        self.root.mainloop()

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

