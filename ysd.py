# from tkinter import *
from tkinter import Tk, Text, Frame, Button, Entry, StringVar, BOTH, DISABLED, HORIZONTAL, INSERT, END
from tkinter.ttk import Progressbar, Combobox
from tkinter.filedialog import askdirectory
import os.path
import threading

from yt_dlp import YoutubeDL


class MyButton(Button):
    def __init__(self, master, text, com, color, bw):
        super().__init__(master=master)
        self.color = color
        self.config(text=text, height=1, width=1, font=('Arial', 12), command=com,
                    relief="flat", bg=color, activebackground=color, borderwidth=bw)

        self.bind("<Enter>", self.enter)
        self.bind("<Leave>", self.leave)

    def enter(self, event):
        event.widget.config(bg="#e5f1fb")

    def leave(self, event):
        event.widget.config(bg=self.color)


class Logger:
    # custom Logger to catch and send to log yt-dlp msg
    def error(self):
        print(self)
        if str(self).endswith("--list-formats for a list of available formats"):
            w.set_log("ERROR", "Format error. Try different one for this video.", "red_color")
        elif str(self).endswith("YouTube said: The playlist does not exist."):
            w.set_log("ERROR", "Playlist is not available or does not exists", "red_color")
        else:
            w.set_log("ERROR", "Something went wrong.", "red_color")

    def warning(self):
        if str(self).startswith("[youtube:tab] YouTube said:  The playlist"):
            w.set_log("WARNNING", self)

    def debug(self):
        if str(self).startswith(tuple(info_msg)):
            w.set_log("INFO", self)


class Main_Window(Tk):
    def __init__(self):
        super().__init__()
        self.minsize(200, 100)
        self.title("  Yt Simple Download")
        self.iconbitmap("ysd.ico")
        self.geometry("{0}x{1}+{2}+{3}".format(*res))

        self.path = StringVar()
        self.path.set(folder)
        # layout
        self.f = Frame(self)
        self.f.pack(fill=BOTH, expand=True)
        # elements
        self.inp = Text(self.f, border=2, height=1, width=1, font=('Arial', 12), pady=1)  # url input
        self.log = Text(self.f, border=2, height=1, width=1, state=DISABLED)
        self.d_path = Entry(self.f, state="readonly", textvariable=self.path, readonlybackground="white")
        self.browse_bt = MyButton(self.f, ". . .", self.browse, "#E9E9E9", 1)
        self.cb = Combobox(self.f, values=form, width=1, state='readonly')
        self.pb = Progressbar(self.f, orient=HORIZONTAL, mode='determinate')
        self.download_bt = MyButton(self.f, "Download", self.run_thread, "#F1FFEC", 0)

        # setup grid, some default ui
        self.setup_ui()

    def setup_ui(self):

        # grid
        self.f.grid_rowconfigure(0, weight=1, pad=0)
        for y in range(4):
            if y == 0 or y == 3:  # to make 2d and 3d colum as small as possible
                self.f.grid_columnconfigure(y, weight=1, minsize=20)
            else:
                self.f.grid_columnconfigure(y, minsize=60)

        self.inp.grid(row=0, column=0, columnspan=3, sticky="news")
        self.log.grid(row=0, column=3, rowspan=3, sticky="news")
        self.d_path.grid(row=1, column=0, sticky="news")
        self.browse_bt.grid(row=1, column=1, sticky="news")
        self.cb.grid(row=1, column=2, sticky="news")
        self.pb.grid(row=2, column=1, columnspan=2, sticky="news")
        self.download_bt.grid(row=2, column=0, sticky="news")

        # ui
        self.d_path.insert(0, folder)
        self.cb.current(2)

        self.log.tag_configure("red_color", foreground="red")
        self.log.tag_configure("blue_color", foreground="blue")
        self.set_log("INFO", "This is log")

    def set_log(self, code, text, color=""):
        self.log.config(state="normal")
        self.log.insert(INSERT, "[{}]".format(code), color)
        self.log.insert(INSERT, " " + text + "\n")
        self.log.config(state="disabled")
        self.log.see(END)

    def browse(self):
        p = askdirectory()
        if p:
            self.path.set(p)
            with open("config.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open("config.txt", "w", encoding="utf-8") as f:
                f.write(lines[0] + p + "\n" + lines[2])

    def run_thread(self):

        self.url = self.inp.get(0.0, END).strip()
        if not self.url.startswith("https://www.youtube.com/"):
            self.set_log("ERROR", "Enter correct url!", "red_color")
            return
        # there is a codec problem when making exe pyinstaller. Haven't found solution in net, so path must be english only
        if not os.path.exists(self.d_path.get()):
            self.set_log("ERROR", "Enter correct path!", "red_color")
            return
        t = threading.Thread(target=self.download)
        t.start()

    def download(self):
        def my_hook(d):
            # to get download progress from yt_dlp
            if d['status'] == 'finished':
                out_of = ""
                if "playlist_count" in d["info_dict"].keys():
                    out_of = " " + str(d["info_dict"]["playlist_index"]) + " out of " + str(
                        d["info_dict"]["playlist_count"]) + " "
                self.set_log("INFO", "Done downloading " + d["filename"] + out_of)
            self.pb['value'] = float(d['_percent_str'][:-1].strip())

        ydl_opts = {"format": self.cb.get(),
                    'progress_hooks': [my_hook],
                    "quiet": True,
                    "outtmpl": self.d_path.get() + '\\%(title)s.%(ext)s',
                    'ignoreerrors': True,
                    "logger": Logger
                    }

        self.set_log("START", "Download starts...", "blue_color")
        ydl = YoutubeDL(ydl_opts)

        # use string below to get list of available formats
        # print(ydl.list_formats(ydl.extract_info(self.url, download=False)))

        ydl.download(self.url)
        self.set_log("END", "Finished", "blue_color")


if __name__ == "__main__":
    # for custom Logger
    info_msg = ["[download] Downloading playlist",
                "[youtube: tab] playlist",
                "[download] Downloading video",
                "[download] Finished downloading",
                "[download] Destination:"]
    # params
    with open("config.txt", "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    res = lines[0].rstrip().split(" ")
    folder = lines[1].rstrip()
    form = lines[2].rstrip().split(" ")

    w = Main_Window()
    w.mainloop()
