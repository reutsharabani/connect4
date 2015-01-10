import logic
import logging
import Tkinter as tk

LOGGER = logging.getLogger("ninarow GUI")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class GameBoard(tk.Frame):
    def __init__(self, parent, board, rows=8, columns=8, size=32, bg_color="white"):
        '''size is the size of a square, in pixels'''

        self.board = board

        self.rows, self.columns = board.get_size()
        self.size = size
        self.bg_color = bg_color
        self.pieces = {}

        canvas_width = columns * size
        canvas_height = rows * size

        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0,
                                width=canvas_width, height=canvas_height, background="bisque")
        self.canvas.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        # this binding will cause a refresh if the user interactively
        # changes the window size
        self.canvas.bind("<Configure>", self.refresh)

    def put_one(self, , row=0, column=0):
        '''Add a piece to the playing board'''
        self.canvas.create_image(0,0, image=image, tags=(name, "piece"), anchor="c")
        self.placepiece(name, row, column)

    def placepiece(self, name, row, column):
        '''Place a piece at the given row/column'''
        self.pieces[name] = (row, column)
        x0 = (column * self.size) + int(self.size/2)
        y0 = (row * self.size) + int(self.size/2)
        self.canvas.coords(name, x0, y0)

    def refresh(self, event):
        '''Redraw the board, possibly in response to window being resized'''
        xsize = int((event.width-1) / self.columns)
        ysize = int((event.height-1) / self.rows)
        self.size = min(xsize, ysize)
        self.canvas.delete("square")
        for row in range(self.rows):
            for col in range(self.columns):
                x1 = (col * self.size)
                y1 = (row * self.size)
                x2 = x1 + self.size
                y2 = y1 + self.size
                piece = self.board.get_piece(row, col)
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill=piece.owner.get_color(), tags="square")
        for name in self.pieces:
            self.placepiece(name, self.pieces[name][0], self.pieces[name][1])
        self.canvas.tag_raise("piece")
        self.canvas.tag_lower("square")


if __name__ == "__main__":
    root = tk.Tk()
    board = logic.Board()
    board_gui = GameBoard(root, board)

    board_gui.pack(side="top", fill="both", expand="true", padx=4, pady=4)
    root.mainloop()
