# Cluster 21

class TkSelect:

    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title('Load PlayBack File')
        w_w = self.window.winfo_screenwidth()
        w_h = self.window.winfo_screenheight()
        tk_w = 350
        tk_h = 200
        self.window.geometry(f'{tk_w}x{tk_h}+{int((w_w - tk_w) / 2)}+{int((w_h - tk_h) / 2)}')
        btn = tkinter.Button(self.window, text='Load PlayBack File', pady=10, command=self.on_load_clicked)
        btn.pack()
        self.window.mainloop()

    def on_load_clicked(self):
        my_filetypes = [('playback files', '.pb')]
        self.pb_path = filedialog.askopenfilename(initialdir=os.getcwd(), title='Please select a playback file:', filetypes=my_filetypes)
        self.window.destroy()

def on_load_clicked(self):
    my_filetypes = [('playback files', '.pb')]
    self.pb_path = filedialog.askopenfilename(initialdir=os.getcwd(), title='Please select a playback file:', filetypes=my_filetypes)
    self.window.destroy()

