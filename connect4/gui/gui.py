import Tkinter as Tk
from connect4.logic import game
import logging
import Queue
import time
import threading

LOGGER = logging.getLogger("connect4-gui")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)
LOGGER.addHandler(sh)
LOGGER.setLevel(logging.WARN)


def show_pre_game_menu(old, root):
    if old:
        old.destroy()
    frame = PreGameMenu(root)

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    frame.pack(side="top", fill="both", expand="true", padx=4, pady=4)


def start_game(old, root, game):
    old.message_queue.put("stop")

    old.destroy()
    game_board = GameBoard(root, game)
    game_board.pack(side="top", fill="both", expand="true", padx=4, pady=4)


class IntSelectionWidget(Tk.Frame):

    def __init__(
            self, parent, label="", start_val=0, min_val=None, max_val=None,
            max_error_message="maximal value reached", min_error_message="minimal value reached", on_error=None
    ):
        Tk.Frame.__init__(self, parent)
        self.error_function = on_error
        self.max_error_message = max_error_message
        self.min_error_message = min_error_message
        self.min_val = min_val
        self.max_val = max_val
        self.top_label = Tk.Label(master=self, text=label, bg="light cyan")
        self.spin_box = Tk.Spinbox(self, from_=min_val, to=max_val, command=self.value_changed)
        self.spin_box.delete(0, Tk.END)
        self.spin_box.insert(0, start_val)
        # track values to respond to increase/decrease
        self.old_val = start_val
        self.top_label.pack()
        self.spin_box.pack()

    def get(self):
        return int(self.spin_box.get())

    def value_changed(self):
        if self.old_val == self.spin_box.get():
            if int(self.old_val) == self.min_val:
                self.__error(self.min_error_message)
            else:
                self.__error(self.max_error_message)
        self.old_val = self.spin_box.get()

    def __error(self, message):
        if self.error_function:
            self.error_function(message)


class PreGameMenu(Tk.Frame):

    def __init__(self, parent):

        self.parent = parent

        self.message_rate = 2
        #gracefully stop thread
        # self.protocol("WM_DELETE_WINDOW", op"))

        Tk.Frame.__init__(self, parent)

        # run a thread to iterate the queue of messages and display them for a short time
        self.message = Tk.StringVar()
        self.message_label = Tk.Label(master=self, textvariable=self.message, fg="red")
        self.message_queue = Queue.Queue(2)
        self.messenger_thread = threading.Thread(target=self.messenger)
        self.messenger_thread.start()

        self.human_players_widget = IntSelectionWidget(
            self,
            label="Number of human players",
            start_val=1,
            min_val=0,
            max_val=3,
            max_error_message="Maximal players -> 3",
            min_error_message="Minimal players -> 2",
            on_error=self.display_message
        )
        self.human_players_widget.pack()

        self.computer_players_widget = IntSelectionWidget(
            self,
            label="Number of computer players",
            start_val=1,
            min_val=0,
            max_val=3,
            max_error_message="Maximal players -> 3",
            min_error_message="Minimal players -> 2",
            on_error=self.display_message
        )
        self.computer_players_widget.pack()

        self.difficulty_widget = IntSelectionWidget(
            self,
            label="Difficulty",
            start_val=3,
            min_val=1,
            max_val=8,
            max_error_message="Maximal difficulty -> 8 (over 5 may take a long time for PC to play)",
            min_error_message="Minimal difficulty -> 1",
            on_error=self.display_message
        )
        self.difficulty_widget.pack()

        self.rows_widget = IntSelectionWidget(
            self,
            label="Number of rows",
            start_val=6,
            min_val=3,
            max_val=15,
            max_error_message="Maximal rows -> 15",
            min_error_message="Minimal rows -> 3",
            on_error=self.display_message
        )
        self.rows_widget.pack()

        self.columns_widget = IntSelectionWidget(
            self,
            label="Number of columns",
            start_val=7,
            min_val=3,
            max_val=15,
            max_error_message="Maximal columns -> 15",
            min_error_message="Minimal columns -> 3",
            on_error=self.display_message
        )
        self.columns_widget.pack()

        self.goal_widget = IntSelectionWidget(
            self,
            label="Sequence goal",
            start_val=4,
            min_val=3,
            max_val=10,
            max_error_message="Maximal goal is 10",
            min_error_message="Minimal goal is 3",
            on_error=self.display_message
        )
        self.goal_widget.pack()

        self.start_button = Tk.Button(
            master=self, text="Start logic!", command=threading.Thread(target=self.start_game).start
        )
        self.start_button.pack()
        self.message_label.pack()

    def start_game(self):
        self.message_rate = 0
        self.message_queue.put("stop")

        # add gui menu to select players
        LOGGER.info("difficulty: %d" % self.difficulty_widget.get())
        players = [
            game.HumanPlayer("name %d" % i) for i in range(self.human_players_widget.get())
        ] + [
            game.ComputerMinMaxPlayer(
                game.AvailableVictoriesHeuristic,
                self.difficulty_widget.get()
            ) for _ in range(self.computer_players_widget.get())
        ]
        start_game(
            self,
            self.parent,
            game.Game(
                players,
                rows=self.rows_widget.get(),
                columns=self.columns_widget.get(),
                goal=self.goal_widget.get()
            )
        )

    def destroy(self):
        self.message_queue.put("stop")
        Tk.Frame.destroy(self)

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
                time.sleep(self.message_rate)
                self.message.set("")
            else:
                # stop thread
                LOGGER.debug("thread stopped")
                break


class GameBoard(Tk.Frame):

    def __init__(self, parent, _game):
        self.parent = parent

        self.game = _game
        self.board = _game.board
        self.rows, self.columns = self.board.get_size()
        self.cell_size = 40
        canvas_width = self.columns * self.cell_size
        canvas_height = self.rows * self.cell_size

        Tk.Frame.__init__(self, parent)
        self.player_indicator = Tk.StringVar(self)
        self.player_indicator.set("%s players starts." % self.board.current_player.get_color())
        self.player_indicator_label = Tk.Label(self, background="bisque", textvariable=self.player_indicator)
        self.player_indicator_label.pack()
        self.canvas = Tk.Canvas(self, borderwidth=0, highlightthickness=0,
                                width=canvas_width, height=canvas_height, background="bisque")
        self.canvas.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        self.canvas.bind("<Configure>", self.resize_event)
        # if isinstance(self.game.board.current_player, game.HumanPlayer):
        self.canvas.bind("<Button-1>", self.put_one_event)
        # else:
        #     self.canvas.bind("<Button-1>", lambda x: self.put_one(self.board.current_player.get_move(self.board, None)))

        self.undo_button = Tk.Button(self, text="Undo", fg="red", bg="black", command=self.undo)
        self.undo_button.pack()
        self.tip = Tk.StringVar(self)
        self.tip_label = Tk.Label(self, background="bisque", textvariable=self.tip)
        self.tip_label.pack()

        self.win_button = None

        # self.game.start()

    def undo(self):
        if self.win_button:
            self.win_button.destroy()
        try:
            # remove two pieces and put one back to re-do all logic of last put event
            removed = self.board.undo()
            removed_and_returned = self.board.undo()
            self.put_one(removed_and_returned[1])
        except game.NoMovesPlayedError:
            self.player_indicator.set("Nothing happened, so... Undoing nothing.")
            self.refresh()
            return
        self.player_indicator.set("%s cheats! removes piece from %s" % (self.board.current_player.get_color(), removed))
        self.refresh()

    def resize_event(self, event):
        x_size = int((event.width-1) / self.columns)
        y_size = int((event.height-1) / self.rows)
        self.cell_size = min(x_size, y_size)
        self.refresh()

    def put_one(self, column):
        try:
            LOGGER.debug("Putting: %s" % str(column))
            self.board.put_one(column)
            if isinstance(self.board.current_player, game.HumanPlayer):
                # pass control to mouse button
                self.canvas.bind("<Button-1>", self.put_one_event)
            else:
                self.canvas.bind(
                    "<Button-1>", lambda x: self.put_one(self.board.current_player.get_move(self.board, column))
                )
        except game.NotYourTurnError as e:
            raise e
        except game.LocationTakenError as e:
            self.player_indicator.set("Column already full!")
            raise e
        self.refresh()

    def refresh(self):
        self.configure(bg=self.board.current_player.get_color())
        self.canvas.delete("pieces")
        for row in range(self.rows):
            for col in range(self.columns):
                x1 = (col * self.cell_size)
                y1 = (row * self.cell_size)
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                color = (self.board.get_piece(row, col) and self.board.get_piece(row, col).owner.get_color()) or "white"
                self.canvas.create_oval(x1, y1, x2, y2, outline="black", fill=color, tags="pieces")
        self.canvas.tag_raise("pieces")
        if self.board.get_winner():
            self.tip.set("Game over - %s won." % self.board.current_player)
        else:
            # self.tip.set("%(score)d, %(moves)s" % self.board.tip_strategy(self.board.current_player))
            self.tip.set("%s" % str(self.board.tip_strategy(self.board.current_player).moves[len(self.board.moves):][0][2]))
        # estimated scores:
        print "scores: %s" % '\n'.join(str(player) for player in self.board.players)
        # for player in self.board.players:
        #     print "%s: %s" % (player.get_color(), player.open_ended_run_heuristic({'board': self.board}))
        LOGGER.debug("redrew canvas")

    def get_normalized_coords(self, event):
        return event.x / self.cell_size, event.y / self.cell_size

    def put_one_event(self, event):
        self.canvas.unbind("<Button-1>")
        player = self.board.current_player
        pressed_column = self.get_normalized_coords(event)[0]
        column = self.board.current_player.get_move(self.board, pressed_column)
        if column != 0 and not column: # 0 is falsy
            self.canvas.bind("<Button-1>", self.put_one_event)
            LOGGER.debug("Couldn't find column")
            return
        self.player_indicator.set("%s player plays column %s" % (player.get_color(), str(column)))
        LOGGER.debug("put one event: %s" % str(column))
        self.put_one(column)
        if self.board.get_winner():
            self.announce_winner(self.board.get_winner())
            self.player_indicator.set("%s player won the game!" % self.board.get_winner().get_color())

    def restart_game(self):
        show_pre_game_menu(self, self.parent)

    def announce_winner(self, player):
        self.win_button = Tk.Button(
            self, text="%s player wins!" % str(player.get_color()), command=self.restart_game
        )
        self.win_button.pack()


def main():
    root = Tk.Tk()
    show_pre_game_menu(None, root)
    root.mainloop()

# if "__main__" == __name__:
#     print "main"
#     main()
#     print "maindone"
