import Tkinter as Tk
import logging
from ninarow import logic
import Queue
import time
import threading

LOGGER = logging.getLogger("ninarow GUI")
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)


class IntSelectionWidget(Tk.Frame):
    def __init__(self, parent, label="", lower_label="down", increase_label="up",
                 start_val=0, min_val=None, max_val=None, max_error_message="maximal value reached",
                 min_error_message="minimal value reached", on_error=None):
        Tk.Frame.__init__(self, parent)
        # TODO: type checking?
        self.error_function = on_error
        self.max_error_message = max_error_message
        self.min_error_message = min_error_message
        self.min_val = min_val
        self.max_val = max_val
        self.up_button = Tk.Button(master=self, text=increase_label, command=self.more)
        self.down_button = Tk.Button(master=self, text=lower_label, command=self.less)
        self.count = Tk.IntVar()
        self.count.set(start_val)
        self.players_count_label = Tk.Label(master=self, textvariable=self.count)

        self.up_button.pack()
        self.down_button.pack()
        self.players_count_label.pack()

    def more(self):
        new_val = self.count.get() + 1
        if self.max_val is not None and self.max_val < new_val:
            self.__error(self.max_error_message)
            return
        self.count.set(new_val)

    def less(self):
        new_val = self.count.get() - 1
        if self.min_val is not None and self.min_val > new_val:
            self.__error(self.min_error_message)
            return
        self.count.set(new_val)

    def __error(self, message):
        if self.error_function:
            self.error_function(message)


class PreGameMenu(Tk.Frame):

    def __init__(self, parent):
        Tk.Frame.__init__(self, parent, width=400, height=400)

        self.pack_propagate(0)

        # run a thread to iterate the queue of messages and display them for a short time
        self.message = Tk.StringVar()
        self.message_label = Tk.Label(master=self, textvariable=self.message)
        self.message_queue = Queue.Queue(2)
        self.messenger_thread = threading.Thread(target=self.messenger)
        self.messenger_thread.start()

        self.players_widget = IntSelectionWidget(
            self,
            label="Number of players",
            lower_label="Less players",
            increase_label="More players",
            start_val=2,
            min_val=2,
            max_val=6,
            max_error_message="Maximal number of players is 6",
            min_error_message="Minimal number of players is 2",
            on_error=self.display_message
        )
        self.players_widget.pack()
        # self.players_up_button = Tk.Button(master=self, text="More players!", command=self.more_players)
        # self.players_down_button = Tk.Button(master=self, text="Less players!", command=self.less_players)
        # self.players_count = Tk.IntVar()
        # self.players_count.set(2)
        # self.players_count_label = Tk.Label(master=self, textvariable=self.players_count)

        # self.players_up_button.pack()
        # self.players_down_button.pack()
        # self.players_count_label.pack()

    def more_players(self):
        print self.players_count.set(self.players_count.get()+1)

    def less_players(self):
        current_count = self.players_count.get()
        if not current_count > 2:
            self.display_message("Players count has to be at least 2!")
        else:
            self.players_count.set(self.players_count.get()-1)

    def display_message(self, message):
        if self.message_queue.full():
            # block for one element
            self.message.set("STOP CLICKING STUFF!")
        else:
            self.message_queue.put(message)

    def messenger(self):
        while True:
            message = self.message_queue.get()
            if not message == "stop":
                self.message.set(message)
                self.message_label.pack()
                time.sleep(2)
                self.message.set("")


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
        self.cell_size = min(x_size, y_size)
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
    frame = PreGameMenu(root)
    frame.pack(side="top", fill="both", expand="true", padx=4, pady=4)
    root.mainloop()

if "__main__" == __name__:
    main()
