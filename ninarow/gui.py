import Tkinter as Tk
import logging
from ninarow import logic

LOGGER = logging.getLogger("ninarow GUI")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class GameBoard(Tk.Frame):
    def __init__(self, parent, board):

        self.board = board
        self.rows, self.columns = board.get_size()
        self.cell_size = 40
        canvas_width = self.columns * self.cell_size
        canvas_height = self.rows * self.cell_size

        Tk.Frame.__init__(self, parent)
        self.canvas = Tk.Canvas(self, borderwidth=0, highlightthickness=0,
                                width=canvas_width, height=canvas_height, background="bisque")
        self.canvas.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        self.canvas.bind("<Configure>", self.resize_event)
        self.canvas.bind("<Button-1>", self.put_one_event)

        self.win_button = None

    def resize_event(self, event):
        x_size = int((event.width-1) / self.columns)
        y_size = int((event.height-1) / self.rows)
        self.size = min(x_size, y_size)
        self.refresh()

    def put_one(self, column, player):
        try:
            self.board.put_one(column, player)
        except logic.NotYourTurnError as e:
            raise e
        except logic.LocationTakenError as e:
            raise e
        self.refresh()

    def refresh(self):
        self.canvas.delete("pieces")
        for row in range(self.rows):
            for col in range(self.columns):
                x1 = (col * self.cell_size)
                y1 = (row * self.cell_size)
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = self.board.get_piece(row, col).owner.get_color()
                self.canvas.create_oval(x1, y1, x2, y2, outline="black", fill=color, tags="pieces")
        self.canvas.tag_raise("pieces")
        LOGGER.debug("redrew canvas")

    def get_normalized_coords(self, event):
        return event.x / self.cell_size, event.y / self.cell_size

    def put_one_event(self, event):
        self.put_one(self.get_normalized_coords(event)[0], self.board.current_player)
        if self.board.board_won():
            self.announce_winner(self.board.board_won())

    def restart_game(self):
        self.win_button.destroy()
        self.board = logic.Board(len(self.board.get_players()))
        self.refresh()

    def announce_winner(self, player):
        self.win_button = Tk.Button(
            self, text="Player %s wins!" % str(player), command=self.restart_game
        )
        self.win_button.pack()


# image comes from the silk icon set which is under a Creative Commons
# license. For more information see http://www.famfamfam.com/lab/icons/silk/
imagedata = '''
    R0lGODlhEAAQAOeSAKx7Fqx8F61/G62CILCJKriIHM+HALKNMNCIANKKANOMALuRK7WOVLWPV9eR
    ANiSANuXAN2ZAN6aAN+bAOCcAOKeANCjKOShANKnK+imAOyrAN6qSNaxPfCwAOKyJOKyJvKyANW0
    R/S1APW2APW3APa4APe5APm7APm8APq8AO28Ke29LO2/LO2/L+7BM+7BNO6+Re7CMu7BOe7DNPHA
    P+/FOO/FO+jGS+/FQO/GO/DHPOjBdfDIPPDJQPDISPDKQPDKRPDIUPHLQ/HLRerMV/HMR/LNSOvH
    fvLOS/rNP/LPTvLOVe/LdfPRUfPRU/PSU/LPaPPTVPPUVfTUVvLPe/LScPTWWfTXW/TXXPTXX/XY
    Xu/SkvXZYPfVdfXaY/TYcfXaZPXaZvbWfvTYe/XbbvHWl/bdaPbeavvadffea/bebvffbfbdfPvb
    e/fgb/Pam/fgcvfgePTbnfbcl/bfivfjdvfjePbemfjelPXeoPjkePbfmvffnvbfofjlgffjkvfh
    nvjio/nnhvfjovjmlvzlmvrmpvrrmfzpp/zqq/vqr/zssvvvp/vvqfvvuPvvuvvwvfzzwP//////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    /////////////////////////////////////////////////////yH+FUNyZWF0ZWQgd2l0aCBU
    aGUgR0lNUAAh+QQBCgD/ACwAAAAAEAAQAAAIzAD/CRxIsKDBfydMlBhxcGAKNIkgPTLUpcPBJIUa
    +VEThswfPDQKokB0yE4aMFiiOPnCJ8PAE20Y6VnTQMsUBkWAjKFyQaCJRYLcmOFipYmRHzV89Kkg
    kESkOme8XHmCREiOGC/2TBAowhGcAyGkKBnCwwKAFnciCAShKA4RAhyK9MAQwIMMOQ8EdhBDKMuN
    BQMEFPigAsoRBQM1BGLjRIiOGSxWBCmToCCMOXSW2HCBo8qWDQcvMMkzCNCbHQga/qMgAYIDBQZU
    yxYYEAA7
'''


def main():
    root = Tk.Tk()
    logic_board = logic.Board(2)
    board = GameBoard(root, logic_board)
    board.pack(side="top", fill="both", expand="true", padx=4, pady=4)
    root.mainloop()
if __name__ == "__main__":
    main()
