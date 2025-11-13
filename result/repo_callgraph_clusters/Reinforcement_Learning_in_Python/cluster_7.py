# Cluster 7

class Environment(tk.Tk, object):

    def __init__(self):
        super(Environment, self).__init__()
        self.action_space = ['up', 'down', 'left', 'right']
        self.n_actions = len(self.action_space)
        self.title('RL Q-learning. Sichkar Valentyn')
        self.geometry('{0}x{1}'.format(env_height * pixels, env_height * pixels))
        self.build_environment()
        self.d = {}
        self.f = {}
        self.i = 0
        self.c = True
        self.longest = 0
        self.shortest = 0

    def build_environment(self):
        self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
        img_background = Image.open('images/bg.png')
        self.background = ImageTk.PhotoImage(img_background)
        self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
        for column in range(0, env_width * pixels, pixels):
            x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        for row in range(0, env_height * pixels, pixels):
            x0, y0, x1, y1 = (0, row, env_height * pixels, row)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        self.o = np.array([pixels / 2, pixels / 2])
        obstacle1_center = self.o + np.array([pixels, pixels * 2])
        self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
        obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
        self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
        obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
        self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
        obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
        self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
        obstacle5_center = self.o + np.array([pixels * 23, pixels])
        self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
        obstacle6_center = self.o + np.array([pixels * 6, pixels])
        self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
        obstacle7_center = self.o + np.array([pixels * 6, pixels * 2])
        self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
        obstacle8_center = self.o + np.array([pixels * 7, pixels * 2])
        self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
        obstacle9_center = self.o + np.array([pixels * 8, pixels * 2])
        self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
        obstacle10_center = self.o + np.array([pixels * 10, pixels * 4])
        self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
        obstacle11_center = self.o + np.array([pixels * 10, pixels * 5])
        self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
        obstacle12_center = self.o + np.array([pixels * 10, pixels * 6])
        self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
        obstacle13_center = self.o + np.array([pixels * 11, pixels * 5])
        self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
        obstacle14_center = self.o + np.array([pixels * 12, pixels * 5])
        self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
        obstacle15_center = self.o + np.array([pixels * 13, pixels * 5])
        self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
        obstacle16_center = self.o + np.array([pixels * 14, pixels * 5])
        self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
        obstacle17_center = self.o + np.array([pixels * 15, pixels * 4])
        self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
        obstacle18_center = self.o + np.array([pixels * 15, pixels * 5])
        self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
        obstacle19_center = self.o + np.array([pixels * 15, pixels * 6])
        self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
        obstacle20_center = self.o + np.array([pixels * 16, pixels * 1])
        self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
        obstacle21_center = self.o + np.array([pixels * 17, pixels * 1])
        self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
        obstacle22_center = self.o + np.array([pixels * 18, pixels * 1])
        self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
        obstacle23_center = self.o + np.array([pixels * 18, pixels * 2])
        self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
        obstacle24_center = self.o + np.array([pixels * 18, pixels * 3])
        self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
        obstacle25_center = self.o + np.array([pixels * 18, pixels * 7])
        self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
        obstacle26_center = self.o + np.array([pixels * 18, pixels * 8])
        self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
        obstacle27_center = self.o + np.array([pixels * 19, pixels * 8])
        self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
        obstacle28_center = self.o + np.array([pixels * 20, pixels * 8])
        self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
        obstacle29_center = self.o + np.array([pixels * 21, pixels * 8])
        self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
        obstacle30_center = self.o + np.array([pixels * 22, pixels * 8])
        self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
        obstacle31_center = self.o + np.array([pixels * 22, pixels * 7])
        self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
        obstacle32_center = self.o + np.array([pixels * 22, pixels * 6])
        self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
        obstacle33_center = self.o + np.array([pixels * 23, pixels * 2])
        self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
        obstacle34_center = self.o + np.array([pixels * 24, pixels * 2])
        self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
        obstacle35_center = self.o + np.array([pixels * 25, pixels * 2])
        self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
        obstacle36_center = self.o + np.array([pixels * 26, pixels * 2])
        self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
        obstacle37_center = self.o + np.array([pixels * 26, pixels * 3])
        self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
        obstacle38_center = self.o + np.array([pixels * 26, pixels * 4])
        self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
        obstacle39_center = self.o + np.array([pixels * 26, pixels * 5])
        self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
        obstacle40_center = self.o + np.array([pixels * 27, pixels * 5])
        self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
        obstacle41_center = self.o + np.array([pixels * 27, pixels * 7])
        self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
        obstacle42_center = self.o + np.array([pixels * 28, pixels * 7])
        self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
        obstacle43_center = self.o + np.array([pixels * 26, pixels * 7])
        self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
        obstacle44_center = self.o + np.array([pixels * 27, pixels * 8])
        self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
        obstacle45_center = self.o + np.array([pixels * 27, pixels * 9])
        self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
        obstacle46_center = self.o + np.array([pixels * 27, pixels * 10])
        self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
        obstacle47_center = self.o + np.array([pixels * 27, pixels * 11])
        self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
        obstacle48_center = self.o + np.array([pixels * 26, pixels * 11])
        self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
        obstacle49_center = self.o + np.array([pixels * 28, pixels * 11])
        self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
        obstacle50_center = self.o + np.array([pixels * 23, pixels * 10])
        self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
        obstacle51_center = self.o + np.array([pixels * 22, pixels * 10])
        self.obstacle51 = self.canvas_widget.create_rectangle(obstacle51_center[0] - 10, obstacle51_center[1] - 10, obstacle51_center[0] + 10, obstacle51_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle51 = [self.canvas_widget.coords(self.obstacle51)[0] + 3, self.canvas_widget.coords(self.obstacle51)[1] + 3, self.canvas_widget.coords(self.obstacle51)[2] - 3, self.canvas_widget.coords(self.obstacle51)[3] - 3]
        obstacle52_center = self.o + np.array([pixels * 21, pixels * 10])
        self.obstacle52 = self.canvas_widget.create_rectangle(obstacle52_center[0] - 10, obstacle52_center[1] - 10, obstacle52_center[0] + 10, obstacle52_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle52 = [self.canvas_widget.coords(self.obstacle52)[0] + 3, self.canvas_widget.coords(self.obstacle52)[1] + 3, self.canvas_widget.coords(self.obstacle52)[2] - 3, self.canvas_widget.coords(self.obstacle52)[3] - 3]
        obstacle53_center = self.o + np.array([pixels * 21, pixels * 11])
        self.obstacle53 = self.canvas_widget.create_rectangle(obstacle53_center[0] - 10, obstacle53_center[1] - 10, obstacle53_center[0] + 10, obstacle53_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle53 = [self.canvas_widget.coords(self.obstacle53)[0] + 3, self.canvas_widget.coords(self.obstacle53)[1] + 3, self.canvas_widget.coords(self.obstacle53)[2] - 3, self.canvas_widget.coords(self.obstacle53)[3] - 3]
        obstacle54_center = self.o + np.array([pixels * 21, pixels * 12])
        self.obstacle54 = self.canvas_widget.create_rectangle(obstacle54_center[0] - 10, obstacle54_center[1] - 10, obstacle54_center[0] + 10, obstacle54_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle54 = [self.canvas_widget.coords(self.obstacle54)[0] + 3, self.canvas_widget.coords(self.obstacle54)[1] + 3, self.canvas_widget.coords(self.obstacle54)[2] - 3, self.canvas_widget.coords(self.obstacle54)[3] - 3]
        obstacle55_center = self.o + np.array([pixels * 21, pixels * 13])
        self.obstacle55 = self.canvas_widget.create_rectangle(obstacle55_center[0] - 10, obstacle55_center[1] - 10, obstacle55_center[0] + 10, obstacle55_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle55 = [self.canvas_widget.coords(self.obstacle55)[0] + 3, self.canvas_widget.coords(self.obstacle55)[1] + 3, self.canvas_widget.coords(self.obstacle55)[2] - 3, self.canvas_widget.coords(self.obstacle55)[3] - 3]
        obstacle56_center = self.o + np.array([pixels * 18, pixels * 11])
        self.obstacle56 = self.canvas_widget.create_rectangle(obstacle56_center[0] - 10, obstacle56_center[1] - 10, obstacle56_center[0] + 10, obstacle56_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle56 = [self.canvas_widget.coords(self.obstacle56)[0] + 3, self.canvas_widget.coords(self.obstacle56)[1] + 3, self.canvas_widget.coords(self.obstacle56)[2] - 3, self.canvas_widget.coords(self.obstacle56)[3] - 3]
        obstacle57_center = self.o + np.array([pixels * 17, pixels * 11])
        self.obstacle57 = self.canvas_widget.create_rectangle(obstacle57_center[0] - 10, obstacle57_center[1] - 10, obstacle57_center[0] + 10, obstacle57_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle57 = [self.canvas_widget.coords(self.obstacle57)[0] + 3, self.canvas_widget.coords(self.obstacle57)[1] + 3, self.canvas_widget.coords(self.obstacle57)[2] - 3, self.canvas_widget.coords(self.obstacle57)[3] - 3]
        obstacle58_center = self.o + np.array([pixels * 16, pixels * 11])
        self.obstacle58 = self.canvas_widget.create_rectangle(obstacle58_center[0] - 10, obstacle58_center[1] - 10, obstacle58_center[0] + 10, obstacle58_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle58 = [self.canvas_widget.coords(self.obstacle58)[0] + 3, self.canvas_widget.coords(self.obstacle58)[1] + 3, self.canvas_widget.coords(self.obstacle58)[2] - 3, self.canvas_widget.coords(self.obstacle58)[3] - 3]
        obstacle59_center = self.o + np.array([pixels * 15, pixels * 11])
        self.obstacle59 = self.canvas_widget.create_rectangle(obstacle59_center[0] - 10, obstacle59_center[1] - 10, obstacle59_center[0] + 10, obstacle59_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle59 = [self.canvas_widget.coords(self.obstacle59)[0] + 3, self.canvas_widget.coords(self.obstacle59)[1] + 3, self.canvas_widget.coords(self.obstacle59)[2] - 3, self.canvas_widget.coords(self.obstacle59)[3] - 3]
        obstacle60_center = self.o + np.array([pixels * 14, pixels * 11])
        self.obstacle60 = self.canvas_widget.create_rectangle(obstacle60_center[0] - 10, obstacle60_center[1] - 10, obstacle60_center[0] + 10, obstacle60_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle60 = [self.canvas_widget.coords(self.obstacle60)[0] + 3, self.canvas_widget.coords(self.obstacle60)[1] + 3, self.canvas_widget.coords(self.obstacle60)[2] - 3, self.canvas_widget.coords(self.obstacle60)[3] - 3]
        obstacle61_center = self.o + np.array([pixels * 14, pixels * 10])
        self.obstacle61 = self.canvas_widget.create_rectangle(obstacle61_center[0] - 10, obstacle61_center[1] - 10, obstacle61_center[0] + 10, obstacle61_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle61 = [self.canvas_widget.coords(self.obstacle61)[0] + 3, self.canvas_widget.coords(self.obstacle61)[1] + 3, self.canvas_widget.coords(self.obstacle61)[2] - 3, self.canvas_widget.coords(self.obstacle61)[3] - 3]
        obstacle62_center = self.o + np.array([pixels * 10, pixels * 9])
        self.obstacle62 = self.canvas_widget.create_rectangle(obstacle62_center[0] - 10, obstacle62_center[1] - 10, obstacle62_center[0] + 10, obstacle62_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle62 = [self.canvas_widget.coords(self.obstacle62)[0] + 3, self.canvas_widget.coords(self.obstacle62)[1] + 3, self.canvas_widget.coords(self.obstacle62)[2] - 3, self.canvas_widget.coords(self.obstacle62)[3] - 3]
        obstacle63_center = self.o + np.array([pixels * 9, pixels * 9])
        self.obstacle63 = self.canvas_widget.create_rectangle(obstacle63_center[0] - 10, obstacle63_center[1] - 10, obstacle63_center[0] + 10, obstacle63_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle63 = [self.canvas_widget.coords(self.obstacle63)[0] + 3, self.canvas_widget.coords(self.obstacle63)[1] + 3, self.canvas_widget.coords(self.obstacle63)[2] - 3, self.canvas_widget.coords(self.obstacle63)[3] - 3]
        obstacle64_center = self.o + np.array([pixels * 8, pixels * 9])
        self.obstacle64 = self.canvas_widget.create_rectangle(obstacle64_center[0] - 10, obstacle64_center[1] - 10, obstacle64_center[0] + 10, obstacle64_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle64 = [self.canvas_widget.coords(self.obstacle64)[0] + 3, self.canvas_widget.coords(self.obstacle64)[1] + 3, self.canvas_widget.coords(self.obstacle64)[2] - 3, self.canvas_widget.coords(self.obstacle64)[3] - 3]
        obstacle65_center = self.o + np.array([pixels * 7, pixels * 9])
        self.obstacle65 = self.canvas_widget.create_rectangle(obstacle65_center[0] - 10, obstacle65_center[1] - 10, obstacle65_center[0] + 10, obstacle65_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle65 = [self.canvas_widget.coords(self.obstacle65)[0] + 3, self.canvas_widget.coords(self.obstacle65)[1] + 3, self.canvas_widget.coords(self.obstacle65)[2] - 3, self.canvas_widget.coords(self.obstacle65)[3] - 3]
        obstacle66_center = self.o + np.array([pixels * 7, pixels * 8])
        self.obstacle66 = self.canvas_widget.create_rectangle(obstacle66_center[0] - 10, obstacle66_center[1] - 10, obstacle66_center[0] + 10, obstacle66_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle66 = [self.canvas_widget.coords(self.obstacle66)[0] + 3, self.canvas_widget.coords(self.obstacle66)[1] + 3, self.canvas_widget.coords(self.obstacle66)[2] - 3, self.canvas_widget.coords(self.obstacle66)[3] - 3]
        obstacle67_center = self.o + np.array([pixels * 7, pixels * 7])
        self.obstacle67 = self.canvas_widget.create_rectangle(obstacle67_center[0] - 10, obstacle67_center[1] - 10, obstacle67_center[0] + 10, obstacle67_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle67 = [self.canvas_widget.coords(self.obstacle67)[0] + 3, self.canvas_widget.coords(self.obstacle67)[1] + 3, self.canvas_widget.coords(self.obstacle67)[2] - 3, self.canvas_widget.coords(self.obstacle67)[3] - 3]
        obstacle68_center = self.o + np.array([pixels * 6, pixels * 7])
        self.obstacle68 = self.canvas_widget.create_rectangle(obstacle68_center[0] - 10, obstacle68_center[1] - 10, obstacle68_center[0] + 10, obstacle68_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle68 = [self.canvas_widget.coords(self.obstacle68)[0] + 3, self.canvas_widget.coords(self.obstacle68)[1] + 3, self.canvas_widget.coords(self.obstacle68)[2] - 3, self.canvas_widget.coords(self.obstacle68)[3] - 3]
        obstacle69_center = self.o + np.array([pixels * 5, pixels * 7])
        self.obstacle69 = self.canvas_widget.create_rectangle(obstacle69_center[0] - 10, obstacle69_center[1] - 10, obstacle69_center[0] + 10, obstacle69_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle69 = [self.canvas_widget.coords(self.obstacle69)[0] + 3, self.canvas_widget.coords(self.obstacle69)[1] + 3, self.canvas_widget.coords(self.obstacle69)[2] - 3, self.canvas_widget.coords(self.obstacle69)[3] - 3]
        obstacle70_center = self.o + np.array([pixels * 5, pixels * 5])
        self.obstacle70 = self.canvas_widget.create_rectangle(obstacle70_center[0] - 10, obstacle70_center[1] - 10, obstacle70_center[0] + 10, obstacle70_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle70 = [self.canvas_widget.coords(self.obstacle70)[0] + 3, self.canvas_widget.coords(self.obstacle70)[1] + 3, self.canvas_widget.coords(self.obstacle70)[2] - 3, self.canvas_widget.coords(self.obstacle70)[3] - 3]
        obstacle71_center = self.o + np.array([pixels * 5, pixels * 6])
        self.obstacle71 = self.canvas_widget.create_rectangle(obstacle71_center[0] - 10, obstacle71_center[1] - 10, obstacle71_center[0] + 10, obstacle71_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle71 = [self.canvas_widget.coords(self.obstacle71)[0] + 3, self.canvas_widget.coords(self.obstacle71)[1] + 3, self.canvas_widget.coords(self.obstacle71)[2] - 3, self.canvas_widget.coords(self.obstacle71)[3] - 3]
        obstacle72_center = self.o + np.array([pixels, pixels * 7])
        self.obstacle72 = self.canvas_widget.create_rectangle(obstacle72_center[0] - 10, obstacle72_center[1] - 10, obstacle72_center[0] + 10, obstacle72_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle72 = [self.canvas_widget.coords(self.obstacle72)[0] + 3, self.canvas_widget.coords(self.obstacle72)[1] + 3, self.canvas_widget.coords(self.obstacle72)[2] - 3, self.canvas_widget.coords(self.obstacle72)[3] - 3]
        obstacle73_center = self.o + np.array([pixels, pixels * 6])
        self.obstacle73 = self.canvas_widget.create_rectangle(obstacle73_center[0] - 10, obstacle73_center[1] - 10, obstacle73_center[0] + 10, obstacle73_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle73 = [self.canvas_widget.coords(self.obstacle73)[0] + 3, self.canvas_widget.coords(self.obstacle73)[1] + 3, self.canvas_widget.coords(self.obstacle73)[2] - 3, self.canvas_widget.coords(self.obstacle73)[3] - 3]
        obstacle74_center = self.o + np.array([pixels * 2, pixels * 6])
        self.obstacle74 = self.canvas_widget.create_rectangle(obstacle74_center[0] - 10, obstacle74_center[1] - 10, obstacle74_center[0] + 10, obstacle74_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle74 = [self.canvas_widget.coords(self.obstacle74)[0] + 3, self.canvas_widget.coords(self.obstacle74)[1] + 3, self.canvas_widget.coords(self.obstacle74)[2] - 3, self.canvas_widget.coords(self.obstacle74)[3] - 3]
        obstacle75_center = self.o + np.array([pixels, pixels * 8])
        self.obstacle75 = self.canvas_widget.create_rectangle(obstacle75_center[0] - 10, obstacle75_center[1] - 10, obstacle75_center[0] + 10, obstacle75_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle75 = [self.canvas_widget.coords(self.obstacle75)[0] + 3, self.canvas_widget.coords(self.obstacle75)[1] + 3, self.canvas_widget.coords(self.obstacle75)[2] - 3, self.canvas_widget.coords(self.obstacle75)[3] - 3]
        obstacle76_center = self.o + np.array([pixels, pixels * 9])
        self.obstacle76 = self.canvas_widget.create_rectangle(obstacle76_center[0] - 10, obstacle76_center[1] - 10, obstacle76_center[0] + 10, obstacle76_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle76 = [self.canvas_widget.coords(self.obstacle76)[0] + 3, self.canvas_widget.coords(self.obstacle76)[1] + 3, self.canvas_widget.coords(self.obstacle76)[2] - 3, self.canvas_widget.coords(self.obstacle76)[3] - 3]
        obstacle77_center = self.o + np.array([pixels, pixels * 10])
        self.obstacle77 = self.canvas_widget.create_rectangle(obstacle77_center[0] - 10, obstacle77_center[1] - 10, obstacle77_center[0] + 10, obstacle77_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle77 = [self.canvas_widget.coords(self.obstacle77)[0] + 3, self.canvas_widget.coords(self.obstacle77)[1] + 3, self.canvas_widget.coords(self.obstacle77)[2] - 3, self.canvas_widget.coords(self.obstacle77)[3] - 3]
        obstacle78_center = self.o + np.array([pixels, pixels * 11])
        self.obstacle78 = self.canvas_widget.create_rectangle(obstacle78_center[0] - 10, obstacle78_center[1] - 10, obstacle78_center[0] + 10, obstacle78_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle78 = [self.canvas_widget.coords(self.obstacle78)[0] + 3, self.canvas_widget.coords(self.obstacle78)[1] + 3, self.canvas_widget.coords(self.obstacle78)[2] - 3, self.canvas_widget.coords(self.obstacle78)[3] - 3]
        obstacle79_center = self.o + np.array([pixels * 3, pixels * 9])
        self.obstacle79 = self.canvas_widget.create_rectangle(obstacle79_center[0] - 10, obstacle79_center[1] - 10, obstacle79_center[0] + 10, obstacle79_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle79 = [self.canvas_widget.coords(self.obstacle79)[0] + 3, self.canvas_widget.coords(self.obstacle79)[1] + 3, self.canvas_widget.coords(self.obstacle79)[2] - 3, self.canvas_widget.coords(self.obstacle79)[3] - 3]
        obstacle80_center = self.o + np.array([pixels * 3, pixels * 10])
        self.obstacle80 = self.canvas_widget.create_rectangle(obstacle80_center[0] - 10, obstacle80_center[1] - 10, obstacle80_center[0] + 10, obstacle80_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle80 = [self.canvas_widget.coords(self.obstacle80)[0] + 3, self.canvas_widget.coords(self.obstacle80)[1] + 3, self.canvas_widget.coords(self.obstacle80)[2] - 3, self.canvas_widget.coords(self.obstacle80)[3] - 3]
        obstacle81_center = self.o + np.array([pixels * 3, pixels * 11])
        self.obstacle81 = self.canvas_widget.create_rectangle(obstacle81_center[0] - 10, obstacle81_center[1] - 10, obstacle81_center[0] + 10, obstacle81_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle81 = [self.canvas_widget.coords(self.obstacle81)[0] + 3, self.canvas_widget.coords(self.obstacle81)[1] + 3, self.canvas_widget.coords(self.obstacle81)[2] - 3, self.canvas_widget.coords(self.obstacle81)[3] - 3]
        obstacle82_center = self.o + np.array([pixels * 3, pixels * 12])
        self.obstacle82 = self.canvas_widget.create_rectangle(obstacle82_center[0] - 10, obstacle82_center[1] - 10, obstacle82_center[0] + 10, obstacle82_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle82 = [self.canvas_widget.coords(self.obstacle82)[0] + 3, self.canvas_widget.coords(self.obstacle82)[1] + 3, self.canvas_widget.coords(self.obstacle82)[2] - 3, self.canvas_widget.coords(self.obstacle82)[3] - 3]
        obstacle83_center = self.o + np.array([pixels * 3, pixels * 13])
        self.obstacle83 = self.canvas_widget.create_rectangle(obstacle83_center[0] - 10, obstacle83_center[1] - 10, obstacle83_center[0] + 10, obstacle83_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle83 = [self.canvas_widget.coords(self.obstacle83)[0] + 3, self.canvas_widget.coords(self.obstacle83)[1] + 3, self.canvas_widget.coords(self.obstacle83)[2] - 3, self.canvas_widget.coords(self.obstacle83)[3] - 3]
        obstacle84_center = self.o + np.array([pixels * 4, pixels * 13])
        self.obstacle84 = self.canvas_widget.create_rectangle(obstacle84_center[0] - 10, obstacle84_center[1] - 10, obstacle84_center[0] + 10, obstacle84_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle84 = [self.canvas_widget.coords(self.obstacle84)[0] + 3, self.canvas_widget.coords(self.obstacle84)[1] + 3, self.canvas_widget.coords(self.obstacle84)[2] - 3, self.canvas_widget.coords(self.obstacle84)[3] - 3]
        obstacle85_center = self.o + np.array([pixels * 5, pixels * 13])
        self.obstacle85 = self.canvas_widget.create_rectangle(obstacle85_center[0] - 10, obstacle85_center[1] - 10, obstacle85_center[0] + 10, obstacle85_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle85 = [self.canvas_widget.coords(self.obstacle85)[0] + 3, self.canvas_widget.coords(self.obstacle85)[1] + 3, self.canvas_widget.coords(self.obstacle85)[2] - 3, self.canvas_widget.coords(self.obstacle85)[3] - 3]
        obstacle86_center = self.o + np.array([pixels * 6, pixels * 13])
        self.obstacle86 = self.canvas_widget.create_rectangle(obstacle86_center[0] - 10, obstacle86_center[1] - 10, obstacle86_center[0] + 10, obstacle86_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle86 = [self.canvas_widget.coords(self.obstacle86)[0] + 3, self.canvas_widget.coords(self.obstacle86)[1] + 3, self.canvas_widget.coords(self.obstacle86)[2] - 3, self.canvas_widget.coords(self.obstacle86)[3] - 3]
        obstacle87_center = self.o + np.array([pixels * 6, pixels * 12])
        self.obstacle87 = self.canvas_widget.create_rectangle(obstacle87_center[0] - 10, obstacle87_center[1] - 10, obstacle87_center[0] + 10, obstacle87_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle87 = [self.canvas_widget.coords(self.obstacle87)[0] + 3, self.canvas_widget.coords(self.obstacle87)[1] + 3, self.canvas_widget.coords(self.obstacle87)[2] - 3, self.canvas_widget.coords(self.obstacle87)[3] - 3]
        obstacle88_center = self.o + np.array([pixels * 2, pixels * 15])
        self.obstacle88 = self.canvas_widget.create_rectangle(obstacle88_center[0] - 10, obstacle88_center[1] - 10, obstacle88_center[0] + 10, obstacle88_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle88 = [self.canvas_widget.coords(self.obstacle88)[0] + 3, self.canvas_widget.coords(self.obstacle88)[1] + 3, self.canvas_widget.coords(self.obstacle88)[2] - 3, self.canvas_widget.coords(self.obstacle88)[3] - 3]
        obstacle89_center = self.o + np.array([pixels * 2, pixels * 16])
        self.obstacle89 = self.canvas_widget.create_rectangle(obstacle89_center[0] - 10, obstacle89_center[1] - 10, obstacle89_center[0] + 10, obstacle89_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle89 = [self.canvas_widget.coords(self.obstacle89)[0] + 3, self.canvas_widget.coords(self.obstacle89)[1] + 3, self.canvas_widget.coords(self.obstacle89)[2] - 3, self.canvas_widget.coords(self.obstacle89)[3] - 3]
        obstacle90_center = self.o + np.array([pixels * 2, pixels * 17])
        self.obstacle90 = self.canvas_widget.create_rectangle(obstacle90_center[0] - 10, obstacle90_center[1] - 10, obstacle90_center[0] + 10, obstacle90_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle90 = [self.canvas_widget.coords(self.obstacle90)[0] + 3, self.canvas_widget.coords(self.obstacle90)[1] + 3, self.canvas_widget.coords(self.obstacle90)[2] - 3, self.canvas_widget.coords(self.obstacle90)[3] - 3]
        obstacle91_center = self.o + np.array([pixels * 2, pixels * 18])
        self.obstacle91 = self.canvas_widget.create_rectangle(obstacle91_center[0] - 10, obstacle91_center[1] - 10, obstacle91_center[0] + 10, obstacle91_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle91 = [self.canvas_widget.coords(self.obstacle91)[0] + 3, self.canvas_widget.coords(self.obstacle91)[1] + 3, self.canvas_widget.coords(self.obstacle91)[2] - 3, self.canvas_widget.coords(self.obstacle91)[3] - 3]
        obstacle92_center = self.o + np.array([pixels * 2, pixels * 19])
        self.obstacle92 = self.canvas_widget.create_rectangle(obstacle92_center[0] - 10, obstacle92_center[1] - 10, obstacle92_center[0] + 10, obstacle92_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle92 = [self.canvas_widget.coords(self.obstacle92)[0] + 3, self.canvas_widget.coords(self.obstacle92)[1] + 3, self.canvas_widget.coords(self.obstacle92)[2] - 3, self.canvas_widget.coords(self.obstacle92)[3] - 3]
        obstacle93_center = self.o + np.array([pixels, pixels * 16])
        self.obstacle93 = self.canvas_widget.create_rectangle(obstacle93_center[0] - 10, obstacle93_center[1] - 10, obstacle93_center[0] + 10, obstacle93_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle93 = [self.canvas_widget.coords(self.obstacle93)[0] + 3, self.canvas_widget.coords(self.obstacle93)[1] + 3, self.canvas_widget.coords(self.obstacle93)[2] - 3, self.canvas_widget.coords(self.obstacle93)[3] - 3]
        obstacle94_center = self.o + np.array([pixels * 2, pixels * 21])
        self.obstacle94 = self.canvas_widget.create_rectangle(obstacle94_center[0] - 10, obstacle94_center[1] - 10, obstacle94_center[0] + 10, obstacle94_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle94 = [self.canvas_widget.coords(self.obstacle94)[0] + 3, self.canvas_widget.coords(self.obstacle94)[1] + 3, self.canvas_widget.coords(self.obstacle94)[2] - 3, self.canvas_widget.coords(self.obstacle94)[3] - 3]
        obstacle95_center = self.o + np.array([pixels * 3, pixels * 21])
        self.obstacle95 = self.canvas_widget.create_rectangle(obstacle95_center[0] - 10, obstacle95_center[1] - 10, obstacle95_center[0] + 10, obstacle95_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle95 = [self.canvas_widget.coords(self.obstacle95)[0] + 3, self.canvas_widget.coords(self.obstacle95)[1] + 3, self.canvas_widget.coords(self.obstacle95)[2] - 3, self.canvas_widget.coords(self.obstacle95)[3] - 3]
        obstacle96_center = self.o + np.array([pixels * 4, pixels * 21])
        self.obstacle96 = self.canvas_widget.create_rectangle(obstacle96_center[0] - 10, obstacle96_center[1] - 10, obstacle96_center[0] + 10, obstacle96_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle96 = [self.canvas_widget.coords(self.obstacle96)[0] + 3, self.canvas_widget.coords(self.obstacle96)[1] + 3, self.canvas_widget.coords(self.obstacle96)[2] - 3, self.canvas_widget.coords(self.obstacle96)[3] - 3]
        obstacle97_center = self.o + np.array([pixels * 4, pixels * 22])
        self.obstacle97 = self.canvas_widget.create_rectangle(obstacle97_center[0] - 10, obstacle97_center[1] - 10, obstacle97_center[0] + 10, obstacle97_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle97 = [self.canvas_widget.coords(self.obstacle97)[0] + 3, self.canvas_widget.coords(self.obstacle97)[1] + 3, self.canvas_widget.coords(self.obstacle97)[2] - 3, self.canvas_widget.coords(self.obstacle97)[3] - 3]
        obstacle98_center = self.o + np.array([pixels * 4, pixels * 23])
        self.obstacle98 = self.canvas_widget.create_rectangle(obstacle98_center[0] - 10, obstacle98_center[1] - 10, obstacle98_center[0] + 10, obstacle98_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle98 = [self.canvas_widget.coords(self.obstacle98)[0] + 3, self.canvas_widget.coords(self.obstacle98)[1] + 3, self.canvas_widget.coords(self.obstacle98)[2] - 3, self.canvas_widget.coords(self.obstacle98)[3] - 3]
        obstacle99_center = self.o + np.array([pixels * 4, pixels * 24])
        self.obstacle99 = self.canvas_widget.create_rectangle(obstacle99_center[0] - 10, obstacle99_center[1] - 10, obstacle99_center[0] + 10, obstacle99_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle99 = [self.canvas_widget.coords(self.obstacle99)[0] + 3, self.canvas_widget.coords(self.obstacle99)[1] + 3, self.canvas_widget.coords(self.obstacle99)[2] - 3, self.canvas_widget.coords(self.obstacle99)[3] - 3]
        obstacle100_center = self.o + np.array([pixels * 4, pixels * 25])
        self.obstacle100 = self.canvas_widget.create_rectangle(obstacle100_center[0] - 10, obstacle100_center[1] - 10, obstacle100_center[0] + 10, obstacle100_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle100 = [self.canvas_widget.coords(self.obstacle100)[0] + 3, self.canvas_widget.coords(self.obstacle100)[1] + 3, self.canvas_widget.coords(self.obstacle100)[2] - 3, self.canvas_widget.coords(self.obstacle100)[3] - 3]
        obstacle101_center = self.o + np.array([pixels * 3, pixels * 25])
        self.obstacle101 = self.canvas_widget.create_rectangle(obstacle101_center[0] - 10, obstacle101_center[1] - 10, obstacle101_center[0] + 10, obstacle101_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle101 = [self.canvas_widget.coords(self.obstacle101)[0] + 3, self.canvas_widget.coords(self.obstacle101)[1] + 3, self.canvas_widget.coords(self.obstacle101)[2] - 3, self.canvas_widget.coords(self.obstacle101)[3] - 3]
        obstacle102_center = self.o + np.array([pixels * 2, pixels * 25])
        self.obstacle102 = self.canvas_widget.create_rectangle(obstacle102_center[0] - 10, obstacle102_center[1] - 10, obstacle102_center[0] + 10, obstacle102_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle102 = [self.canvas_widget.coords(self.obstacle102)[0] + 3, self.canvas_widget.coords(self.obstacle102)[1] + 3, self.canvas_widget.coords(self.obstacle102)[2] - 3, self.canvas_widget.coords(self.obstacle102)[3] - 3]
        obstacle103_center = self.o + np.array([pixels, pixels * 25])
        self.obstacle103 = self.canvas_widget.create_rectangle(obstacle103_center[0] - 10, obstacle103_center[1] - 10, obstacle103_center[0] + 10, obstacle103_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle103 = [self.canvas_widget.coords(self.obstacle103)[0] + 3, self.canvas_widget.coords(self.obstacle103)[1] + 3, self.canvas_widget.coords(self.obstacle103)[2] - 3, self.canvas_widget.coords(self.obstacle103)[3] - 3]
        obstacle104_center = self.o + np.array([pixels * 3, pixels * 16])
        self.obstacle104 = self.canvas_widget.create_rectangle(obstacle104_center[0] - 10, obstacle104_center[1] - 10, obstacle104_center[0] + 10, obstacle104_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle104 = [self.canvas_widget.coords(self.obstacle104)[0] + 3, self.canvas_widget.coords(self.obstacle104)[1] + 3, self.canvas_widget.coords(self.obstacle104)[2] - 3, self.canvas_widget.coords(self.obstacle104)[3] - 3]
        obstacle105_center = self.o + np.array([pixels * 4, pixels * 16])
        self.obstacle105 = self.canvas_widget.create_rectangle(obstacle105_center[0] - 10, obstacle105_center[1] - 10, obstacle105_center[0] + 10, obstacle105_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle105 = [self.canvas_widget.coords(self.obstacle105)[0] + 3, self.canvas_widget.coords(self.obstacle105)[1] + 3, self.canvas_widget.coords(self.obstacle105)[2] - 3, self.canvas_widget.coords(self.obstacle105)[3] - 3]
        obstacle106_center = self.o + np.array([pixels * 5, pixels * 16])
        self.obstacle106 = self.canvas_widget.create_rectangle(obstacle106_center[0] - 10, obstacle106_center[1] - 10, obstacle106_center[0] + 10, obstacle106_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle106 = [self.canvas_widget.coords(self.obstacle106)[0] + 3, self.canvas_widget.coords(self.obstacle106)[1] + 3, self.canvas_widget.coords(self.obstacle106)[2] - 3, self.canvas_widget.coords(self.obstacle106)[3] - 3]
        obstacle107_center = self.o + np.array([pixels * 2, pixels * 27])
        self.obstacle107 = self.canvas_widget.create_rectangle(obstacle107_center[0] - 10, obstacle107_center[1] - 10, obstacle107_center[0] + 10, obstacle107_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle107 = [self.canvas_widget.coords(self.obstacle107)[0] + 3, self.canvas_widget.coords(self.obstacle107)[1] + 3, self.canvas_widget.coords(self.obstacle107)[2] - 3, self.canvas_widget.coords(self.obstacle107)[3] - 3]
        obstacle108_center = self.o + np.array([pixels * 2, pixels * 28])
        self.obstacle108 = self.canvas_widget.create_rectangle(obstacle108_center[0] - 10, obstacle108_center[1] - 10, obstacle108_center[0] + 10, obstacle108_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle108 = [self.canvas_widget.coords(self.obstacle108)[0] + 3, self.canvas_widget.coords(self.obstacle108)[1] + 3, self.canvas_widget.coords(self.obstacle108)[2] - 3, self.canvas_widget.coords(self.obstacle108)[3] - 3]
        obstacle109_center = self.o + np.array([pixels * 3, pixels * 28])
        self.obstacle109 = self.canvas_widget.create_rectangle(obstacle109_center[0] - 10, obstacle109_center[1] - 10, obstacle109_center[0] + 10, obstacle109_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle109 = [self.canvas_widget.coords(self.obstacle109)[0] + 3, self.canvas_widget.coords(self.obstacle109)[1] + 3, self.canvas_widget.coords(self.obstacle109)[2] - 3, self.canvas_widget.coords(self.obstacle109)[3] - 3]
        obstacle110_center = self.o + np.array([pixels * 4, pixels * 28])
        self.obstacle110 = self.canvas_widget.create_rectangle(obstacle110_center[0] - 10, obstacle110_center[1] - 10, obstacle110_center[0] + 10, obstacle110_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle110 = [self.canvas_widget.coords(self.obstacle110)[0] + 3, self.canvas_widget.coords(self.obstacle110)[1] + 3, self.canvas_widget.coords(self.obstacle110)[2] - 3, self.canvas_widget.coords(self.obstacle110)[3] - 3]
        obstacle111_center = self.o + np.array([pixels * 5, pixels * 28])
        self.obstacle111 = self.canvas_widget.create_rectangle(obstacle111_center[0] - 10, obstacle111_center[1] - 10, obstacle111_center[0] + 10, obstacle111_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle111 = [self.canvas_widget.coords(self.obstacle111)[0] + 3, self.canvas_widget.coords(self.obstacle111)[1] + 3, self.canvas_widget.coords(self.obstacle111)[2] - 3, self.canvas_widget.coords(self.obstacle111)[3] - 3]
        obstacle112_center = self.o + np.array([pixels * 6, pixels * 28])
        self.obstacle112 = self.canvas_widget.create_rectangle(obstacle112_center[0] - 10, obstacle112_center[1] - 10, obstacle112_center[0] + 10, obstacle112_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle112 = [self.canvas_widget.coords(self.obstacle112)[0] + 3, self.canvas_widget.coords(self.obstacle112)[1] + 3, self.canvas_widget.coords(self.obstacle112)[2] - 3, self.canvas_widget.coords(self.obstacle112)[3] - 3]
        obstacle113_center = self.o + np.array([pixels * 7, pixels * 28])
        self.obstacle113 = self.canvas_widget.create_rectangle(obstacle113_center[0] - 10, obstacle113_center[1] - 10, obstacle113_center[0] + 10, obstacle113_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle113 = [self.canvas_widget.coords(self.obstacle113)[0] + 3, self.canvas_widget.coords(self.obstacle113)[1] + 3, self.canvas_widget.coords(self.obstacle113)[2] - 3, self.canvas_widget.coords(self.obstacle113)[3] - 3]
        obstacle114_center = self.o + np.array([pixels * 7, pixels * 27])
        self.obstacle114 = self.canvas_widget.create_rectangle(obstacle114_center[0] - 10, obstacle114_center[1] - 10, obstacle114_center[0] + 10, obstacle114_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle114 = [self.canvas_widget.coords(self.obstacle114)[0] + 3, self.canvas_widget.coords(self.obstacle114)[1] + 3, self.canvas_widget.coords(self.obstacle114)[2] - 3, self.canvas_widget.coords(self.obstacle114)[3] - 3]
        obstacle115_center = self.o + np.array([pixels * 7, pixels * 26])
        self.obstacle115 = self.canvas_widget.create_rectangle(obstacle115_center[0] - 10, obstacle115_center[1] - 10, obstacle115_center[0] + 10, obstacle115_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle115 = [self.canvas_widget.coords(self.obstacle115)[0] + 3, self.canvas_widget.coords(self.obstacle115)[1] + 3, self.canvas_widget.coords(self.obstacle115)[2] - 3, self.canvas_widget.coords(self.obstacle115)[3] - 3]
        obstacle116_center = self.o + np.array([pixels * 7, pixels * 25])
        self.obstacle116 = self.canvas_widget.create_rectangle(obstacle116_center[0] - 10, obstacle116_center[1] - 10, obstacle116_center[0] + 10, obstacle116_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle116 = [self.canvas_widget.coords(self.obstacle116)[0] + 3, self.canvas_widget.coords(self.obstacle116)[1] + 3, self.canvas_widget.coords(self.obstacle116)[2] - 3, self.canvas_widget.coords(self.obstacle116)[3] - 3]
        obstacle117_center = self.o + np.array([pixels * 7, pixels * 24])
        self.obstacle117 = self.canvas_widget.create_rectangle(obstacle117_center[0] - 10, obstacle117_center[1] - 10, obstacle117_center[0] + 10, obstacle117_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle117 = [self.canvas_widget.coords(self.obstacle117)[0] + 3, self.canvas_widget.coords(self.obstacle117)[1] + 3, self.canvas_widget.coords(self.obstacle117)[2] - 3, self.canvas_widget.coords(self.obstacle117)[3] - 3]
        obstacle118_center = self.o + np.array([pixels * 9, pixels * 22])
        self.obstacle118 = self.canvas_widget.create_rectangle(obstacle118_center[0] - 10, obstacle118_center[1] - 10, obstacle118_center[0] + 10, obstacle118_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle118 = [self.canvas_widget.coords(self.obstacle118)[0] + 3, self.canvas_widget.coords(self.obstacle118)[1] + 3, self.canvas_widget.coords(self.obstacle118)[2] - 3, self.canvas_widget.coords(self.obstacle118)[3] - 3]
        obstacle119_center = self.o + np.array([pixels * 9, pixels * 21])
        self.obstacle119 = self.canvas_widget.create_rectangle(obstacle119_center[0] - 10, obstacle119_center[1] - 10, obstacle119_center[0] + 10, obstacle119_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle119 = [self.canvas_widget.coords(self.obstacle119)[0] + 3, self.canvas_widget.coords(self.obstacle119)[1] + 3, self.canvas_widget.coords(self.obstacle119)[2] - 3, self.canvas_widget.coords(self.obstacle119)[3] - 3]
        obstacle120_center = self.o + np.array([pixels * 9, pixels * 20])
        self.obstacle120 = self.canvas_widget.create_rectangle(obstacle120_center[0] - 10, obstacle120_center[1] - 10, obstacle120_center[0] + 10, obstacle120_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle120 = [self.canvas_widget.coords(self.obstacle120)[0] + 3, self.canvas_widget.coords(self.obstacle120)[1] + 3, self.canvas_widget.coords(self.obstacle120)[2] - 3, self.canvas_widget.coords(self.obstacle120)[3] - 3]
        obstacle121_center = self.o + np.array([pixels * 9, pixels * 19])
        self.obstacle121 = self.canvas_widget.create_rectangle(obstacle121_center[0] - 10, obstacle121_center[1] - 10, obstacle121_center[0] + 10, obstacle121_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle121 = [self.canvas_widget.coords(self.obstacle121)[0] + 3, self.canvas_widget.coords(self.obstacle121)[1] + 3, self.canvas_widget.coords(self.obstacle121)[2] - 3, self.canvas_widget.coords(self.obstacle121)[3] - 3]
        obstacle122_center = self.o + np.array([pixels * 9, pixels * 18])
        self.obstacle122 = self.canvas_widget.create_rectangle(obstacle122_center[0] - 10, obstacle122_center[1] - 10, obstacle122_center[0] + 10, obstacle122_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle122 = [self.canvas_widget.coords(self.obstacle122)[0] + 3, self.canvas_widget.coords(self.obstacle122)[1] + 3, self.canvas_widget.coords(self.obstacle122)[2] - 3, self.canvas_widget.coords(self.obstacle122)[3] - 3]
        obstacle123_center = self.o + np.array([pixels * 8, pixels * 18])
        self.obstacle123 = self.canvas_widget.create_rectangle(obstacle123_center[0] - 10, obstacle123_center[1] - 10, obstacle123_center[0] + 10, obstacle123_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle123 = [self.canvas_widget.coords(self.obstacle123)[0] + 3, self.canvas_widget.coords(self.obstacle123)[1] + 3, self.canvas_widget.coords(self.obstacle123)[2] - 3, self.canvas_widget.coords(self.obstacle123)[3] - 3]
        obstacle124_center = self.o + np.array([pixels * 7, pixels * 18])
        self.obstacle124 = self.canvas_widget.create_rectangle(obstacle124_center[0] - 10, obstacle124_center[1] - 10, obstacle124_center[0] + 10, obstacle124_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle124 = [self.canvas_widget.coords(self.obstacle124)[0] + 3, self.canvas_widget.coords(self.obstacle124)[1] + 3, self.canvas_widget.coords(self.obstacle124)[2] - 3, self.canvas_widget.coords(self.obstacle124)[3] - 3]
        obstacle125_center = self.o + np.array([pixels * 7, pixels * 16])
        self.obstacle125 = self.canvas_widget.create_rectangle(obstacle125_center[0] - 10, obstacle125_center[1] - 10, obstacle125_center[0] + 10, obstacle125_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle125 = [self.canvas_widget.coords(self.obstacle125)[0] + 3, self.canvas_widget.coords(self.obstacle125)[1] + 3, self.canvas_widget.coords(self.obstacle125)[2] - 3, self.canvas_widget.coords(self.obstacle125)[3] - 3]
        obstacle126_center = self.o + np.array([pixels * 7, pixels * 15])
        self.obstacle126 = self.canvas_widget.create_rectangle(obstacle126_center[0] - 10, obstacle126_center[1] - 10, obstacle126_center[0] + 10, obstacle126_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle126 = [self.canvas_widget.coords(self.obstacle126)[0] + 3, self.canvas_widget.coords(self.obstacle126)[1] + 3, self.canvas_widget.coords(self.obstacle126)[2] - 3, self.canvas_widget.coords(self.obstacle126)[3] - 3]
        obstacle127_center = self.o + np.array([pixels * 7, pixels * 17])
        self.obstacle127 = self.canvas_widget.create_rectangle(obstacle127_center[0] - 10, obstacle127_center[1] - 10, obstacle127_center[0] + 10, obstacle127_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle127 = [self.canvas_widget.coords(self.obstacle127)[0] + 3, self.canvas_widget.coords(self.obstacle127)[1] + 3, self.canvas_widget.coords(self.obstacle127)[2] - 3, self.canvas_widget.coords(self.obstacle127)[3] - 3]
        obstacle128_center = self.o + np.array([pixels * 8, pixels * 15])
        self.obstacle128 = self.canvas_widget.create_rectangle(obstacle128_center[0] - 10, obstacle128_center[1] - 10, obstacle128_center[0] + 10, obstacle128_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle128 = [self.canvas_widget.coords(self.obstacle128)[0] + 3, self.canvas_widget.coords(self.obstacle128)[1] + 3, self.canvas_widget.coords(self.obstacle128)[2] - 3, self.canvas_widget.coords(self.obstacle128)[3] - 3]
        obstacle129_center = self.o + np.array([pixels * 9, pixels * 15])
        self.obstacle129 = self.canvas_widget.create_rectangle(obstacle129_center[0] - 10, obstacle129_center[1] - 10, obstacle129_center[0] + 10, obstacle129_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle129 = [self.canvas_widget.coords(self.obstacle129)[0] + 3, self.canvas_widget.coords(self.obstacle129)[1] + 3, self.canvas_widget.coords(self.obstacle129)[2] - 3, self.canvas_widget.coords(self.obstacle129)[3] - 3]
        obstacle130_center = self.o + np.array([pixels * 10, pixels * 15])
        self.obstacle130 = self.canvas_widget.create_rectangle(obstacle130_center[0] - 10, obstacle130_center[1] - 10, obstacle130_center[0] + 10, obstacle130_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle130 = [self.canvas_widget.coords(self.obstacle130)[0] + 3, self.canvas_widget.coords(self.obstacle130)[1] + 3, self.canvas_widget.coords(self.obstacle130)[2] - 3, self.canvas_widget.coords(self.obstacle130)[3] - 3]
        obstacle131_center = self.o + np.array([pixels * 11, pixels * 12])
        self.obstacle131 = self.canvas_widget.create_rectangle(obstacle131_center[0] - 10, obstacle131_center[1] - 10, obstacle131_center[0] + 10, obstacle131_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle131 = [self.canvas_widget.coords(self.obstacle131)[0] + 3, self.canvas_widget.coords(self.obstacle131)[1] + 3, self.canvas_widget.coords(self.obstacle131)[2] - 3, self.canvas_widget.coords(self.obstacle131)[3] - 3]
        obstacle132_center = self.o + np.array([pixels * 10, pixels * 12])
        self.obstacle132 = self.canvas_widget.create_rectangle(obstacle132_center[0] - 10, obstacle132_center[1] - 10, obstacle132_center[0] + 10, obstacle132_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle132 = [self.canvas_widget.coords(self.obstacle132)[0] + 3, self.canvas_widget.coords(self.obstacle132)[1] + 3, self.canvas_widget.coords(self.obstacle132)[2] - 3, self.canvas_widget.coords(self.obstacle132)[3] - 3]
        obstacle133_center = self.o + np.array([pixels * 11, pixels * 13])
        self.obstacle133 = self.canvas_widget.create_rectangle(obstacle133_center[0] - 10, obstacle133_center[1] - 10, obstacle133_center[0] + 10, obstacle133_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle133 = [self.canvas_widget.coords(self.obstacle133)[0] + 3, self.canvas_widget.coords(self.obstacle133)[1] + 3, self.canvas_widget.coords(self.obstacle133)[2] - 3, self.canvas_widget.coords(self.obstacle133)[3] - 3]
        obstacle134_center = self.o + np.array([pixels * 12, pixels * 13])
        self.obstacle134 = self.canvas_widget.create_rectangle(obstacle134_center[0] - 10, obstacle134_center[1] - 10, obstacle134_center[0] + 10, obstacle134_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle134 = [self.canvas_widget.coords(self.obstacle134)[0] + 3, self.canvas_widget.coords(self.obstacle134)[1] + 3, self.canvas_widget.coords(self.obstacle134)[2] - 3, self.canvas_widget.coords(self.obstacle134)[3] - 3]
        obstacle135_center = self.o + np.array([pixels * 13, pixels * 13])
        self.obstacle135 = self.canvas_widget.create_rectangle(obstacle135_center[0] - 10, obstacle135_center[1] - 10, obstacle135_center[0] + 10, obstacle135_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle135 = [self.canvas_widget.coords(self.obstacle135)[0] + 3, self.canvas_widget.coords(self.obstacle135)[1] + 3, self.canvas_widget.coords(self.obstacle135)[2] - 3, self.canvas_widget.coords(self.obstacle135)[3] - 3]
        obstacle136_center = self.o + np.array([pixels * 13, pixels * 14])
        self.obstacle136 = self.canvas_widget.create_rectangle(obstacle136_center[0] - 10, obstacle136_center[1] - 10, obstacle136_center[0] + 10, obstacle136_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle136 = [self.canvas_widget.coords(self.obstacle136)[0] + 3, self.canvas_widget.coords(self.obstacle136)[1] + 3, self.canvas_widget.coords(self.obstacle136)[2] - 3, self.canvas_widget.coords(self.obstacle136)[3] - 3]
        obstacle137_center = self.o + np.array([pixels * 13, pixels * 15])
        self.obstacle137 = self.canvas_widget.create_rectangle(obstacle137_center[0] - 10, obstacle137_center[1] - 10, obstacle137_center[0] + 10, obstacle137_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle137 = [self.canvas_widget.coords(self.obstacle137)[0] + 3, self.canvas_widget.coords(self.obstacle137)[1] + 3, self.canvas_widget.coords(self.obstacle137)[2] - 3, self.canvas_widget.coords(self.obstacle137)[3] - 3]
        obstacle138_center = self.o + np.array([pixels * 14, pixels * 15])
        self.obstacle138 = self.canvas_widget.create_rectangle(obstacle138_center[0] - 10, obstacle138_center[1] - 10, obstacle138_center[0] + 10, obstacle138_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle138 = [self.canvas_widget.coords(self.obstacle138)[0] + 3, self.canvas_widget.coords(self.obstacle138)[1] + 3, self.canvas_widget.coords(self.obstacle138)[2] - 3, self.canvas_widget.coords(self.obstacle138)[3] - 3]
        obstacle139_center = self.o + np.array([pixels * 15, pixels * 15])
        self.obstacle139 = self.canvas_widget.create_rectangle(obstacle139_center[0] - 10, obstacle139_center[1] - 10, obstacle139_center[0] + 10, obstacle139_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle139 = [self.canvas_widget.coords(self.obstacle139)[0] + 3, self.canvas_widget.coords(self.obstacle139)[1] + 3, self.canvas_widget.coords(self.obstacle139)[2] - 3, self.canvas_widget.coords(self.obstacle139)[3] - 3]
        obstacle140_center = self.o + np.array([pixels * 16, pixels * 15])
        self.obstacle140 = self.canvas_widget.create_rectangle(obstacle140_center[0] - 10, obstacle140_center[1] - 10, obstacle140_center[0] + 10, obstacle140_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle140 = [self.canvas_widget.coords(self.obstacle140)[0] + 3, self.canvas_widget.coords(self.obstacle140)[1] + 3, self.canvas_widget.coords(self.obstacle140)[2] - 3, self.canvas_widget.coords(self.obstacle140)[3] - 3]
        obstacle141_center = self.o + np.array([pixels * 17, pixels * 15])
        self.obstacle141 = self.canvas_widget.create_rectangle(obstacle141_center[0] - 10, obstacle141_center[1] - 10, obstacle141_center[0] + 10, obstacle141_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle141 = [self.canvas_widget.coords(self.obstacle141)[0] + 3, self.canvas_widget.coords(self.obstacle141)[1] + 3, self.canvas_widget.coords(self.obstacle141)[2] - 3, self.canvas_widget.coords(self.obstacle141)[3] - 3]
        obstacle142_center = self.o + np.array([pixels * 18, pixels * 15])
        self.obstacle142 = self.canvas_widget.create_rectangle(obstacle142_center[0] - 10, obstacle142_center[1] - 10, obstacle142_center[0] + 10, obstacle142_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle142 = [self.canvas_widget.coords(self.obstacle142)[0] + 3, self.canvas_widget.coords(self.obstacle142)[1] + 3, self.canvas_widget.coords(self.obstacle142)[2] - 3, self.canvas_widget.coords(self.obstacle142)[3] - 3]
        obstacle143_center = self.o + np.array([pixels * 18, pixels * 14])
        self.obstacle143 = self.canvas_widget.create_rectangle(obstacle143_center[0] - 10, obstacle143_center[1] - 10, obstacle143_center[0] + 10, obstacle143_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle143 = [self.canvas_widget.coords(self.obstacle143)[0] + 3, self.canvas_widget.coords(self.obstacle143)[1] + 3, self.canvas_widget.coords(self.obstacle143)[2] - 3, self.canvas_widget.coords(self.obstacle143)[3] - 3]
        obstacle144_center = self.o + np.array([pixels * 18, pixels * 13])
        self.obstacle144 = self.canvas_widget.create_rectangle(obstacle144_center[0] - 10, obstacle144_center[1] - 10, obstacle144_center[0] + 10, obstacle144_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle144 = [self.canvas_widget.coords(self.obstacle144)[0] + 3, self.canvas_widget.coords(self.obstacle144)[1] + 3, self.canvas_widget.coords(self.obstacle144)[2] - 3, self.canvas_widget.coords(self.obstacle144)[3] - 3]
        obstacle145_center = self.o + np.array([pixels * 15, pixels * 17])
        self.obstacle145 = self.canvas_widget.create_rectangle(obstacle145_center[0] - 10, obstacle145_center[1] - 10, obstacle145_center[0] + 10, obstacle145_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle145 = [self.canvas_widget.coords(self.obstacle145)[0] + 3, self.canvas_widget.coords(self.obstacle145)[1] + 3, self.canvas_widget.coords(self.obstacle145)[2] - 3, self.canvas_widget.coords(self.obstacle145)[3] - 3]
        obstacle146_center = self.o + np.array([pixels * 14, pixels * 17])
        self.obstacle146 = self.canvas_widget.create_rectangle(obstacle146_center[0] - 10, obstacle146_center[1] - 10, obstacle146_center[0] + 10, obstacle146_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle146 = [self.canvas_widget.coords(self.obstacle146)[0] + 3, self.canvas_widget.coords(self.obstacle146)[1] + 3, self.canvas_widget.coords(self.obstacle146)[2] - 3, self.canvas_widget.coords(self.obstacle146)[3] - 3]
        obstacle147_center = self.o + np.array([pixels * 13, pixels * 17])
        self.obstacle147 = self.canvas_widget.create_rectangle(obstacle147_center[0] - 10, obstacle147_center[1] - 10, obstacle147_center[0] + 10, obstacle147_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle147 = [self.canvas_widget.coords(self.obstacle147)[0] + 3, self.canvas_widget.coords(self.obstacle147)[1] + 3, self.canvas_widget.coords(self.obstacle147)[2] - 3, self.canvas_widget.coords(self.obstacle147)[3] - 3]
        obstacle148_center = self.o + np.array([pixels * 12, pixels * 17])
        self.obstacle148 = self.canvas_widget.create_rectangle(obstacle148_center[0] - 10, obstacle148_center[1] - 10, obstacle148_center[0] + 10, obstacle148_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle148 = [self.canvas_widget.coords(self.obstacle148)[0] + 3, self.canvas_widget.coords(self.obstacle148)[1] + 3, self.canvas_widget.coords(self.obstacle148)[2] - 3, self.canvas_widget.coords(self.obstacle148)[3] - 3]
        obstacle149_center = self.o + np.array([pixels * 12, pixels * 18])
        self.obstacle149 = self.canvas_widget.create_rectangle(obstacle149_center[0] - 10, obstacle149_center[1] - 10, obstacle149_center[0] + 10, obstacle149_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle149 = [self.canvas_widget.coords(self.obstacle149)[0] + 3, self.canvas_widget.coords(self.obstacle149)[1] + 3, self.canvas_widget.coords(self.obstacle149)[2] - 3, self.canvas_widget.coords(self.obstacle149)[3] - 3]
        obstacle150_center = self.o + np.array([pixels * 12, pixels * 19])
        self.obstacle150 = self.canvas_widget.create_rectangle(obstacle150_center[0] - 10, obstacle150_center[1] - 10, obstacle150_center[0] + 10, obstacle150_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle150 = [self.canvas_widget.coords(self.obstacle150)[0] + 3, self.canvas_widget.coords(self.obstacle150)[1] + 3, self.canvas_widget.coords(self.obstacle150)[2] - 3, self.canvas_widget.coords(self.obstacle150)[3] - 3]
        obstacle151_center = self.o + np.array([pixels * 12, pixels * 20])
        self.obstacle151 = self.canvas_widget.create_rectangle(obstacle151_center[0] - 10, obstacle151_center[1] - 10, obstacle151_center[0] + 10, obstacle151_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle151 = [self.canvas_widget.coords(self.obstacle151)[0] + 3, self.canvas_widget.coords(self.obstacle151)[1] + 3, self.canvas_widget.coords(self.obstacle151)[2] - 3, self.canvas_widget.coords(self.obstacle151)[3] - 3]
        obstacle152_center = self.o + np.array([pixels * 12, pixels * 21])
        self.obstacle152 = self.canvas_widget.create_rectangle(obstacle152_center[0] - 10, obstacle152_center[1] - 10, obstacle152_center[0] + 10, obstacle152_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle152 = [self.canvas_widget.coords(self.obstacle152)[0] + 3, self.canvas_widget.coords(self.obstacle152)[1] + 3, self.canvas_widget.coords(self.obstacle152)[2] - 3, self.canvas_widget.coords(self.obstacle152)[3] - 3]
        obstacle153_center = self.o + np.array([pixels * 12, pixels * 22])
        self.obstacle153 = self.canvas_widget.create_rectangle(obstacle153_center[0] - 10, obstacle153_center[1] - 10, obstacle153_center[0] + 10, obstacle153_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle153 = [self.canvas_widget.coords(self.obstacle153)[0] + 3, self.canvas_widget.coords(self.obstacle153)[1] + 3, self.canvas_widget.coords(self.obstacle153)[2] - 3, self.canvas_widget.coords(self.obstacle153)[3] - 3]
        obstacle154_center = self.o + np.array([pixels * 12, pixels * 23])
        self.obstacle154 = self.canvas_widget.create_rectangle(obstacle154_center[0] - 10, obstacle154_center[1] - 10, obstacle154_center[0] + 10, obstacle154_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle154 = [self.canvas_widget.coords(self.obstacle154)[0] + 3, self.canvas_widget.coords(self.obstacle154)[1] + 3, self.canvas_widget.coords(self.obstacle154)[2] - 3, self.canvas_widget.coords(self.obstacle154)[3] - 3]
        obstacle155_center = self.o + np.array([pixels * 12, pixels * 24])
        self.obstacle155 = self.canvas_widget.create_rectangle(obstacle155_center[0] - 10, obstacle155_center[1] - 10, obstacle155_center[0] + 10, obstacle155_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle155 = [self.canvas_widget.coords(self.obstacle155)[0] + 3, self.canvas_widget.coords(self.obstacle155)[1] + 3, self.canvas_widget.coords(self.obstacle155)[2] - 3, self.canvas_widget.coords(self.obstacle155)[3] - 3]
        obstacle156_center = self.o + np.array([pixels * 12, pixels * 25])
        self.obstacle156 = self.canvas_widget.create_rectangle(obstacle156_center[0] - 10, obstacle156_center[1] - 10, obstacle156_center[0] + 10, obstacle156_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle156 = [self.canvas_widget.coords(self.obstacle156)[0] + 3, self.canvas_widget.coords(self.obstacle156)[1] + 3, self.canvas_widget.coords(self.obstacle156)[2] - 3, self.canvas_widget.coords(self.obstacle156)[3] - 3]
        obstacle157_center = self.o + np.array([pixels * 11, pixels * 25])
        self.obstacle157 = self.canvas_widget.create_rectangle(obstacle157_center[0] - 10, obstacle157_center[1] - 10, obstacle157_center[0] + 10, obstacle157_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle157 = [self.canvas_widget.coords(self.obstacle157)[0] + 3, self.canvas_widget.coords(self.obstacle157)[1] + 3, self.canvas_widget.coords(self.obstacle157)[2] - 3, self.canvas_widget.coords(self.obstacle157)[3] - 3]
        obstacle158_center = self.o + np.array([pixels * 10, pixels * 25])
        self.obstacle158 = self.canvas_widget.create_rectangle(obstacle158_center[0] - 10, obstacle158_center[1] - 10, obstacle158_center[0] + 10, obstacle158_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle158 = [self.canvas_widget.coords(self.obstacle158)[0] + 3, self.canvas_widget.coords(self.obstacle158)[1] + 3, self.canvas_widget.coords(self.obstacle158)[2] - 3, self.canvas_widget.coords(self.obstacle158)[3] - 3]
        obstacle159_center = self.o + np.array([pixels * 9, pixels * 25])
        self.obstacle159 = self.canvas_widget.create_rectangle(obstacle159_center[0] - 10, obstacle159_center[1] - 10, obstacle159_center[0] + 10, obstacle159_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle159 = [self.canvas_widget.coords(self.obstacle159)[0] + 3, self.canvas_widget.coords(self.obstacle159)[1] + 3, self.canvas_widget.coords(self.obstacle159)[2] - 3, self.canvas_widget.coords(self.obstacle159)[3] - 3]
        obstacle160_center = self.o + np.array([pixels * 21, pixels * 27])
        self.obstacle160 = self.canvas_widget.create_rectangle(obstacle160_center[0] - 10, obstacle160_center[1] - 10, obstacle160_center[0] + 10, obstacle160_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle160 = [self.canvas_widget.coords(self.obstacle160)[0] + 3, self.canvas_widget.coords(self.obstacle160)[1] + 3, self.canvas_widget.coords(self.obstacle160)[2] - 3, self.canvas_widget.coords(self.obstacle160)[3] - 3]
        obstacle161_center = self.o + np.array([pixels * 10, pixels * 28])
        self.obstacle161 = self.canvas_widget.create_rectangle(obstacle161_center[0] - 10, obstacle161_center[1] - 10, obstacle161_center[0] + 10, obstacle161_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle161 = [self.canvas_widget.coords(self.obstacle161)[0] + 3, self.canvas_widget.coords(self.obstacle161)[1] + 3, self.canvas_widget.coords(self.obstacle161)[2] - 3, self.canvas_widget.coords(self.obstacle161)[3] - 3]
        obstacle162_center = self.o + np.array([pixels * 10, pixels * 27])
        self.obstacle162 = self.canvas_widget.create_rectangle(obstacle162_center[0] - 10, obstacle162_center[1] - 10, obstacle162_center[0] + 10, obstacle162_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle162 = [self.canvas_widget.coords(self.obstacle162)[0] + 3, self.canvas_widget.coords(self.obstacle162)[1] + 3, self.canvas_widget.coords(self.obstacle162)[2] - 3, self.canvas_widget.coords(self.obstacle162)[3] - 3]
        obstacle163_center = self.o + np.array([pixels * 11, pixels * 27])
        self.obstacle163 = self.canvas_widget.create_rectangle(obstacle163_center[0] - 10, obstacle163_center[1] - 10, obstacle163_center[0] + 10, obstacle163_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle163 = [self.canvas_widget.coords(self.obstacle163)[0] + 3, self.canvas_widget.coords(self.obstacle163)[1] + 3, self.canvas_widget.coords(self.obstacle163)[2] - 3, self.canvas_widget.coords(self.obstacle163)[3] - 3]
        obstacle164_center = self.o + np.array([pixels * 12, pixels * 27])
        self.obstacle164 = self.canvas_widget.create_rectangle(obstacle164_center[0] - 10, obstacle164_center[1] - 10, obstacle164_center[0] + 10, obstacle164_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle164 = [self.canvas_widget.coords(self.obstacle164)[0] + 3, self.canvas_widget.coords(self.obstacle164)[1] + 3, self.canvas_widget.coords(self.obstacle164)[2] - 3, self.canvas_widget.coords(self.obstacle164)[3] - 3]
        obstacle165_center = self.o + np.array([pixels * 13, pixels * 27])
        self.obstacle165 = self.canvas_widget.create_rectangle(obstacle165_center[0] - 10, obstacle165_center[1] - 10, obstacle165_center[0] + 10, obstacle165_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle165 = [self.canvas_widget.coords(self.obstacle165)[0] + 3, self.canvas_widget.coords(self.obstacle165)[1] + 3, self.canvas_widget.coords(self.obstacle165)[2] - 3, self.canvas_widget.coords(self.obstacle165)[3] - 3]
        obstacle166_center = self.o + np.array([pixels * 14, pixels * 27])
        self.obstacle166 = self.canvas_widget.create_rectangle(obstacle166_center[0] - 10, obstacle166_center[1] - 10, obstacle166_center[0] + 10, obstacle166_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle166 = [self.canvas_widget.coords(self.obstacle166)[0] + 3, self.canvas_widget.coords(self.obstacle166)[1] + 3, self.canvas_widget.coords(self.obstacle166)[2] - 3, self.canvas_widget.coords(self.obstacle166)[3] - 3]
        obstacle167_center = self.o + np.array([pixels * 15, pixels * 27])
        self.obstacle167 = self.canvas_widget.create_rectangle(obstacle167_center[0] - 10, obstacle167_center[1] - 10, obstacle167_center[0] + 10, obstacle167_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle167 = [self.canvas_widget.coords(self.obstacle167)[0] + 3, self.canvas_widget.coords(self.obstacle167)[1] + 3, self.canvas_widget.coords(self.obstacle167)[2] - 3, self.canvas_widget.coords(self.obstacle167)[3] - 3]
        obstacle168_center = self.o + np.array([pixels * 16, pixels * 27])
        self.obstacle168 = self.canvas_widget.create_rectangle(obstacle168_center[0] - 10, obstacle168_center[1] - 10, obstacle168_center[0] + 10, obstacle168_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle168 = [self.canvas_widget.coords(self.obstacle168)[0] + 3, self.canvas_widget.coords(self.obstacle168)[1] + 3, self.canvas_widget.coords(self.obstacle168)[2] - 3, self.canvas_widget.coords(self.obstacle168)[3] - 3]
        obstacle169_center = self.o + np.array([pixels * 16, pixels * 28])
        self.obstacle169 = self.canvas_widget.create_rectangle(obstacle169_center[0] - 10, obstacle169_center[1] - 10, obstacle169_center[0] + 10, obstacle169_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle169 = [self.canvas_widget.coords(self.obstacle169)[0] + 3, self.canvas_widget.coords(self.obstacle169)[1] + 3, self.canvas_widget.coords(self.obstacle169)[2] - 3, self.canvas_widget.coords(self.obstacle169)[3] - 3]
        obstacle170_center = self.o + np.array([pixels * 14, pixels * 24])
        self.obstacle170 = self.canvas_widget.create_rectangle(obstacle170_center[0] - 10, obstacle170_center[1] - 10, obstacle170_center[0] + 10, obstacle170_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle170 = [self.canvas_widget.coords(self.obstacle170)[0] + 3, self.canvas_widget.coords(self.obstacle170)[1] + 3, self.canvas_widget.coords(self.obstacle170)[2] - 3, self.canvas_widget.coords(self.obstacle170)[3] - 3]
        obstacle171_center = self.o + np.array([pixels * 15, pixels * 24])
        self.obstacle171 = self.canvas_widget.create_rectangle(obstacle171_center[0] - 10, obstacle171_center[1] - 10, obstacle171_center[0] + 10, obstacle171_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle171 = [self.canvas_widget.coords(self.obstacle171)[0] + 3, self.canvas_widget.coords(self.obstacle171)[1] + 3, self.canvas_widget.coords(self.obstacle171)[2] - 3, self.canvas_widget.coords(self.obstacle171)[3] - 3]
        obstacle172_center = self.o + np.array([pixels * 16, pixels * 24])
        self.obstacle172 = self.canvas_widget.create_rectangle(obstacle172_center[0] - 10, obstacle172_center[1] - 10, obstacle172_center[0] + 10, obstacle172_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle172 = [self.canvas_widget.coords(self.obstacle172)[0] + 3, self.canvas_widget.coords(self.obstacle172)[1] + 3, self.canvas_widget.coords(self.obstacle172)[2] - 3, self.canvas_widget.coords(self.obstacle172)[3] - 3]
        obstacle173_center = self.o + np.array([pixels * 17, pixels * 24])
        self.obstacle173 = self.canvas_widget.create_rectangle(obstacle173_center[0] - 10, obstacle173_center[1] - 10, obstacle173_center[0] + 10, obstacle173_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle173 = [self.canvas_widget.coords(self.obstacle173)[0] + 3, self.canvas_widget.coords(self.obstacle173)[1] + 3, self.canvas_widget.coords(self.obstacle173)[2] - 3, self.canvas_widget.coords(self.obstacle173)[3] - 3]
        obstacle174_center = self.o + np.array([pixels * 17, pixels * 23])
        self.obstacle174 = self.canvas_widget.create_rectangle(obstacle174_center[0] - 10, obstacle174_center[1] - 10, obstacle174_center[0] + 10, obstacle174_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle174 = [self.canvas_widget.coords(self.obstacle174)[0] + 3, self.canvas_widget.coords(self.obstacle174)[1] + 3, self.canvas_widget.coords(self.obstacle174)[2] - 3, self.canvas_widget.coords(self.obstacle174)[3] - 3]
        obstacle175_center = self.o + np.array([pixels * 17, pixels * 22])
        self.obstacle175 = self.canvas_widget.create_rectangle(obstacle175_center[0] - 10, obstacle175_center[1] - 10, obstacle175_center[0] + 10, obstacle175_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle175 = [self.canvas_widget.coords(self.obstacle175)[0] + 3, self.canvas_widget.coords(self.obstacle175)[1] + 3, self.canvas_widget.coords(self.obstacle175)[2] - 3, self.canvas_widget.coords(self.obstacle175)[3] - 3]
        obstacle176_center = self.o + np.array([pixels * 17, pixels * 21])
        self.obstacle176 = self.canvas_widget.create_rectangle(obstacle176_center[0] - 10, obstacle176_center[1] - 10, obstacle176_center[0] + 10, obstacle176_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle176 = [self.canvas_widget.coords(self.obstacle176)[0] + 3, self.canvas_widget.coords(self.obstacle176)[1] + 3, self.canvas_widget.coords(self.obstacle176)[2] - 3, self.canvas_widget.coords(self.obstacle176)[3] - 3]
        obstacle177_center = self.o + np.array([pixels * 17, pixels * 20])
        self.obstacle177 = self.canvas_widget.create_rectangle(obstacle177_center[0] - 10, obstacle177_center[1] - 10, obstacle177_center[0] + 10, obstacle177_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle177 = [self.canvas_widget.coords(self.obstacle177)[0] + 3, self.canvas_widget.coords(self.obstacle177)[1] + 3, self.canvas_widget.coords(self.obstacle177)[2] - 3, self.canvas_widget.coords(self.obstacle177)[3] - 3]
        obstacle178_center = self.o + np.array([pixels * 17, pixels * 19])
        self.obstacle178 = self.canvas_widget.create_rectangle(obstacle178_center[0] - 10, obstacle178_center[1] - 10, obstacle178_center[0] + 10, obstacle178_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle178 = [self.canvas_widget.coords(self.obstacle178)[0] + 3, self.canvas_widget.coords(self.obstacle178)[1] + 3, self.canvas_widget.coords(self.obstacle178)[2] - 3, self.canvas_widget.coords(self.obstacle178)[3] - 3]
        obstacle179_center = self.o + np.array([pixels * 17, pixels * 18])
        self.obstacle179 = self.canvas_widget.create_rectangle(obstacle179_center[0] - 10, obstacle179_center[1] - 10, obstacle179_center[0] + 10, obstacle179_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle179 = [self.canvas_widget.coords(self.obstacle179)[0] + 3, self.canvas_widget.coords(self.obstacle179)[1] + 3, self.canvas_widget.coords(self.obstacle179)[2] - 3, self.canvas_widget.coords(self.obstacle179)[3] - 3]
        obstacle180_center = self.o + np.array([pixels * 18, pixels * 18])
        self.obstacle180 = self.canvas_widget.create_rectangle(obstacle180_center[0] - 10, obstacle180_center[1] - 10, obstacle180_center[0] + 10, obstacle180_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle180 = [self.canvas_widget.coords(self.obstacle180)[0] + 3, self.canvas_widget.coords(self.obstacle180)[1] + 3, self.canvas_widget.coords(self.obstacle180)[2] - 3, self.canvas_widget.coords(self.obstacle180)[3] - 3]
        obstacle181_center = self.o + np.array([pixels * 19, pixels * 18])
        self.obstacle181 = self.canvas_widget.create_rectangle(obstacle181_center[0] - 10, obstacle181_center[1] - 10, obstacle181_center[0] + 10, obstacle181_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle181 = [self.canvas_widget.coords(self.obstacle181)[0] + 3, self.canvas_widget.coords(self.obstacle181)[1] + 3, self.canvas_widget.coords(self.obstacle181)[2] - 3, self.canvas_widget.coords(self.obstacle181)[3] - 3]
        obstacle182_center = self.o + np.array([pixels * 20, pixels * 18])
        self.obstacle182 = self.canvas_widget.create_rectangle(obstacle182_center[0] - 10, obstacle182_center[1] - 10, obstacle182_center[0] + 10, obstacle182_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle182 = [self.canvas_widget.coords(self.obstacle182)[0] + 3, self.canvas_widget.coords(self.obstacle182)[1] + 3, self.canvas_widget.coords(self.obstacle182)[2] - 3, self.canvas_widget.coords(self.obstacle182)[3] - 3]
        obstacle183_center = self.o + np.array([pixels * 21, pixels * 18])
        self.obstacle183 = self.canvas_widget.create_rectangle(obstacle183_center[0] - 10, obstacle183_center[1] - 10, obstacle183_center[0] + 10, obstacle183_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle183 = [self.canvas_widget.coords(self.obstacle183)[0] + 3, self.canvas_widget.coords(self.obstacle183)[1] + 3, self.canvas_widget.coords(self.obstacle183)[2] - 3, self.canvas_widget.coords(self.obstacle183)[3] - 3]
        obstacle184_center = self.o + np.array([pixels * 22, pixels * 18])
        self.obstacle184 = self.canvas_widget.create_rectangle(obstacle184_center[0] - 10, obstacle184_center[1] - 10, obstacle184_center[0] + 10, obstacle184_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle184 = [self.canvas_widget.coords(self.obstacle184)[0] + 3, self.canvas_widget.coords(self.obstacle184)[1] + 3, self.canvas_widget.coords(self.obstacle184)[2] - 3, self.canvas_widget.coords(self.obstacle184)[3] - 3]
        obstacle185_center = self.o + np.array([pixels * 23, pixels * 18])
        self.obstacle185 = self.canvas_widget.create_rectangle(obstacle185_center[0] - 10, obstacle185_center[1] - 10, obstacle185_center[0] + 10, obstacle185_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle185 = [self.canvas_widget.coords(self.obstacle185)[0] + 3, self.canvas_widget.coords(self.obstacle185)[1] + 3, self.canvas_widget.coords(self.obstacle185)[2] - 3, self.canvas_widget.coords(self.obstacle185)[3] - 3]
        obstacle186_center = self.o + np.array([pixels * 23, pixels * 18])
        self.obstacle186 = self.canvas_widget.create_rectangle(obstacle186_center[0] - 10, obstacle186_center[1] - 10, obstacle186_center[0] + 10, obstacle186_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle186 = [self.canvas_widget.coords(self.obstacle186)[0] + 3, self.canvas_widget.coords(self.obstacle186)[1] + 3, self.canvas_widget.coords(self.obstacle186)[2] - 3, self.canvas_widget.coords(self.obstacle186)[3] - 3]
        obstacle187_center = self.o + np.array([pixels * 23, pixels * 19])
        self.obstacle187 = self.canvas_widget.create_rectangle(obstacle187_center[0] - 10, obstacle187_center[1] - 10, obstacle187_center[0] + 10, obstacle187_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle187 = [self.canvas_widget.coords(self.obstacle187)[0] + 3, self.canvas_widget.coords(self.obstacle187)[1] + 3, self.canvas_widget.coords(self.obstacle187)[2] - 3, self.canvas_widget.coords(self.obstacle187)[3] - 3]
        obstacle188_center = self.o + np.array([pixels * 23, pixels * 20])
        self.obstacle188 = self.canvas_widget.create_rectangle(obstacle188_center[0] - 10, obstacle188_center[1] - 10, obstacle188_center[0] + 10, obstacle188_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle188 = [self.canvas_widget.coords(self.obstacle188)[0] + 3, self.canvas_widget.coords(self.obstacle188)[1] + 3, self.canvas_widget.coords(self.obstacle188)[2] - 3, self.canvas_widget.coords(self.obstacle188)[3] - 3]
        obstacle189_center = self.o + np.array([pixels * 23, pixels * 21])
        self.obstacle189 = self.canvas_widget.create_rectangle(obstacle189_center[0] - 10, obstacle189_center[1] - 10, obstacle189_center[0] + 10, obstacle189_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle189 = [self.canvas_widget.coords(self.obstacle189)[0] + 3, self.canvas_widget.coords(self.obstacle189)[1] + 3, self.canvas_widget.coords(self.obstacle189)[2] - 3, self.canvas_widget.coords(self.obstacle189)[3] - 3]
        obstacle190_center = self.o + np.array([pixels * 23, pixels * 22])
        self.obstacle190 = self.canvas_widget.create_rectangle(obstacle190_center[0] - 10, obstacle190_center[1] - 10, obstacle190_center[0] + 10, obstacle190_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle190 = [self.canvas_widget.coords(self.obstacle190)[0] + 3, self.canvas_widget.coords(self.obstacle190)[1] + 3, self.canvas_widget.coords(self.obstacle190)[2] - 3, self.canvas_widget.coords(self.obstacle190)[3] - 3]
        obstacle191_center = self.o + np.array([pixels * 23, pixels * 23])
        self.obstacle191 = self.canvas_widget.create_rectangle(obstacle191_center[0] - 10, obstacle191_center[1] - 10, obstacle191_center[0] + 10, obstacle191_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle191 = [self.canvas_widget.coords(self.obstacle191)[0] + 3, self.canvas_widget.coords(self.obstacle191)[1] + 3, self.canvas_widget.coords(self.obstacle191)[2] - 3, self.canvas_widget.coords(self.obstacle191)[3] - 3]
        obstacle192_center = self.o + np.array([pixels * 23, pixels * 24])
        self.obstacle192 = self.canvas_widget.create_rectangle(obstacle192_center[0] - 10, obstacle192_center[1] - 10, obstacle192_center[0] + 10, obstacle192_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle192 = [self.canvas_widget.coords(self.obstacle192)[0] + 3, self.canvas_widget.coords(self.obstacle192)[1] + 3, self.canvas_widget.coords(self.obstacle192)[2] - 3, self.canvas_widget.coords(self.obstacle192)[3] - 3]
        obstacle193_center = self.o + np.array([pixels * 23, pixels * 25])
        self.obstacle193 = self.canvas_widget.create_rectangle(obstacle193_center[0] - 10, obstacle193_center[1] - 10, obstacle193_center[0] + 10, obstacle193_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle193 = [self.canvas_widget.coords(self.obstacle193)[0] + 3, self.canvas_widget.coords(self.obstacle193)[1] + 3, self.canvas_widget.coords(self.obstacle193)[2] - 3, self.canvas_widget.coords(self.obstacle193)[3] - 3]
        obstacle194_center = self.o + np.array([pixels * 23, pixels * 26])
        self.obstacle194 = self.canvas_widget.create_rectangle(obstacle194_center[0] - 10, obstacle194_center[1] - 10, obstacle194_center[0] + 10, obstacle194_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle194 = [self.canvas_widget.coords(self.obstacle194)[0] + 3, self.canvas_widget.coords(self.obstacle194)[1] + 3, self.canvas_widget.coords(self.obstacle194)[2] - 3, self.canvas_widget.coords(self.obstacle194)[3] - 3]
        obstacle195_center = self.o + np.array([pixels * 23, pixels * 27])
        self.obstacle195 = self.canvas_widget.create_rectangle(obstacle195_center[0] - 10, obstacle195_center[1] - 10, obstacle195_center[0] + 10, obstacle195_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle195 = [self.canvas_widget.coords(self.obstacle195)[0] + 3, self.canvas_widget.coords(self.obstacle195)[1] + 3, self.canvas_widget.coords(self.obstacle195)[2] - 3, self.canvas_widget.coords(self.obstacle195)[3] - 3]
        obstacle196_center = self.o + np.array([pixels * 22, pixels * 27])
        self.obstacle196 = self.canvas_widget.create_rectangle(obstacle196_center[0] - 10, obstacle196_center[1] - 10, obstacle196_center[0] + 10, obstacle196_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle196 = [self.canvas_widget.coords(self.obstacle196)[0] + 3, self.canvas_widget.coords(self.obstacle196)[1] + 3, self.canvas_widget.coords(self.obstacle196)[2] - 3, self.canvas_widget.coords(self.obstacle196)[3] - 3]
        obstacle197_center = self.o + np.array([pixels * 21, pixels * 16])
        self.obstacle197 = self.canvas_widget.create_rectangle(obstacle197_center[0] - 10, obstacle197_center[1] - 10, obstacle197_center[0] + 10, obstacle197_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle197 = [self.canvas_widget.coords(self.obstacle197)[0] + 3, self.canvas_widget.coords(self.obstacle197)[1] + 3, self.canvas_widget.coords(self.obstacle197)[2] - 3, self.canvas_widget.coords(self.obstacle197)[3] - 3]
        obstacle198_center = self.o + np.array([pixels * 22, pixels * 16])
        self.obstacle198 = self.canvas_widget.create_rectangle(obstacle198_center[0] - 10, obstacle198_center[1] - 10, obstacle198_center[0] + 10, obstacle198_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle198 = [self.canvas_widget.coords(self.obstacle198)[0] + 3, self.canvas_widget.coords(self.obstacle198)[1] + 3, self.canvas_widget.coords(self.obstacle198)[2] - 3, self.canvas_widget.coords(self.obstacle198)[3] - 3]
        obstacle199_center = self.o + np.array([pixels * 23, pixels * 16])
        self.obstacle199 = self.canvas_widget.create_rectangle(obstacle199_center[0] - 10, obstacle199_center[1] - 10, obstacle199_center[0] + 10, obstacle199_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle199 = [self.canvas_widget.coords(self.obstacle199)[0] + 3, self.canvas_widget.coords(self.obstacle199)[1] + 3, self.canvas_widget.coords(self.obstacle199)[2] - 3, self.canvas_widget.coords(self.obstacle199)[3] - 3]
        obstacle200_center = self.o + np.array([pixels * 24, pixels * 16])
        self.obstacle200 = self.canvas_widget.create_rectangle(obstacle200_center[0] - 10, obstacle200_center[1] - 10, obstacle200_center[0] + 10, obstacle200_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle200 = [self.canvas_widget.coords(self.obstacle200)[0] + 3, self.canvas_widget.coords(self.obstacle200)[1] + 3, self.canvas_widget.coords(self.obstacle200)[2] - 3, self.canvas_widget.coords(self.obstacle200)[3] - 3]
        obstacle201_center = self.o + np.array([pixels * 25, pixels * 16])
        self.obstacle201 = self.canvas_widget.create_rectangle(obstacle201_center[0] - 10, obstacle201_center[1] - 10, obstacle201_center[0] + 10, obstacle201_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle201 = [self.canvas_widget.coords(self.obstacle201)[0] + 3, self.canvas_widget.coords(self.obstacle201)[1] + 3, self.canvas_widget.coords(self.obstacle201)[2] - 3, self.canvas_widget.coords(self.obstacle201)[3] - 3]
        obstacle202_center = self.o + np.array([pixels * 26, pixels * 17])
        self.obstacle202 = self.canvas_widget.create_rectangle(obstacle202_center[0] - 10, obstacle202_center[1] - 10, obstacle202_center[0] + 10, obstacle202_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle202 = [self.canvas_widget.coords(self.obstacle202)[0] + 3, self.canvas_widget.coords(self.obstacle202)[1] + 3, self.canvas_widget.coords(self.obstacle202)[2] - 3, self.canvas_widget.coords(self.obstacle202)[3] - 3]
        obstacle203_center = self.o + np.array([pixels * 26, pixels * 16])
        self.obstacle203 = self.canvas_widget.create_rectangle(obstacle203_center[0] - 10, obstacle203_center[1] - 10, obstacle203_center[0] + 10, obstacle203_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle203 = [self.canvas_widget.coords(self.obstacle203)[0] + 3, self.canvas_widget.coords(self.obstacle203)[1] + 3, self.canvas_widget.coords(self.obstacle203)[2] - 3, self.canvas_widget.coords(self.obstacle203)[3] - 3]
        obstacle204_center = self.o + np.array([pixels * 26, pixels * 18])
        self.obstacle204 = self.canvas_widget.create_rectangle(obstacle204_center[0] - 10, obstacle204_center[1] - 10, obstacle204_center[0] + 10, obstacle204_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle204 = [self.canvas_widget.coords(self.obstacle204)[0] + 3, self.canvas_widget.coords(self.obstacle204)[1] + 3, self.canvas_widget.coords(self.obstacle204)[2] - 3, self.canvas_widget.coords(self.obstacle204)[3] - 3]
        obstacle205_center = self.o + np.array([pixels * 27, pixels * 18])
        self.obstacle205 = self.canvas_widget.create_rectangle(obstacle205_center[0] - 10, obstacle205_center[1] - 10, obstacle205_center[0] + 10, obstacle205_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle205 = [self.canvas_widget.coords(self.obstacle205)[0] + 3, self.canvas_widget.coords(self.obstacle205)[1] + 3, self.canvas_widget.coords(self.obstacle205)[2] - 3, self.canvas_widget.coords(self.obstacle205)[3] - 3]
        obstacle206_center = self.o + np.array([pixels * 28, pixels * 18])
        self.obstacle206 = self.canvas_widget.create_rectangle(obstacle206_center[0] - 10, obstacle206_center[1] - 10, obstacle206_center[0] + 10, obstacle206_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle206 = [self.canvas_widget.coords(self.obstacle206)[0] + 3, self.canvas_widget.coords(self.obstacle206)[1] + 3, self.canvas_widget.coords(self.obstacle206)[2] - 3, self.canvas_widget.coords(self.obstacle206)[3] - 3]
        obstacle207_center = self.o + np.array([pixels * 27, pixels * 27])
        self.obstacle207 = self.canvas_widget.create_rectangle(obstacle207_center[0] - 10, obstacle207_center[1] - 10, obstacle207_center[0] + 10, obstacle207_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle207 = [self.canvas_widget.coords(self.obstacle207)[0] + 3, self.canvas_widget.coords(self.obstacle207)[1] + 3, self.canvas_widget.coords(self.obstacle207)[2] - 3, self.canvas_widget.coords(self.obstacle207)[3] - 3]
        obstacle208_center = self.o + np.array([pixels * 28, pixels * 27])
        self.obstacle208 = self.canvas_widget.create_rectangle(obstacle208_center[0] - 10, obstacle208_center[1] - 10, obstacle208_center[0] + 10, obstacle208_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle208 = [self.canvas_widget.coords(self.obstacle208)[0] + 3, self.canvas_widget.coords(self.obstacle208)[1] + 3, self.canvas_widget.coords(self.obstacle208)[2] - 3, self.canvas_widget.coords(self.obstacle208)[3] - 3]
        obstacle209_center = self.o + np.array([pixels * 28, pixels * 26])
        self.obstacle209 = self.canvas_widget.create_rectangle(obstacle209_center[0] - 10, obstacle209_center[1] - 10, obstacle209_center[0] + 10, obstacle209_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle209 = [self.canvas_widget.coords(self.obstacle209)[0] + 3, self.canvas_widget.coords(self.obstacle209)[1] + 3, self.canvas_widget.coords(self.obstacle209)[2] - 3, self.canvas_widget.coords(self.obstacle209)[3] - 3]
        obstacle210_center = self.o + np.array([pixels * 28, pixels * 25])
        self.obstacle210 = self.canvas_widget.create_rectangle(obstacle210_center[0] - 10, obstacle210_center[1] - 10, obstacle210_center[0] + 10, obstacle210_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle210 = [self.canvas_widget.coords(self.obstacle210)[0] + 3, self.canvas_widget.coords(self.obstacle210)[1] + 3, self.canvas_widget.coords(self.obstacle210)[2] - 3, self.canvas_widget.coords(self.obstacle210)[3] - 3]
        obstacle211_center = self.o + np.array([pixels * 28, pixels * 24])
        self.obstacle211 = self.canvas_widget.create_rectangle(obstacle211_center[0] - 10, obstacle211_center[1] - 10, obstacle211_center[0] + 10, obstacle211_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle211 = [self.canvas_widget.coords(self.obstacle211)[0] + 3, self.canvas_widget.coords(self.obstacle211)[1] + 3, self.canvas_widget.coords(self.obstacle211)[2] - 3, self.canvas_widget.coords(self.obstacle211)[3] - 3]
        obstacle212_center = self.o + np.array([pixels * 27, pixels * 24])
        self.obstacle212 = self.canvas_widget.create_rectangle(obstacle212_center[0] - 10, obstacle212_center[1] - 10, obstacle212_center[0] + 10, obstacle212_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle212 = [self.canvas_widget.coords(self.obstacle212)[0] + 3, self.canvas_widget.coords(self.obstacle212)[1] + 3, self.canvas_widget.coords(self.obstacle212)[2] - 3, self.canvas_widget.coords(self.obstacle212)[3] - 3]
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
        flag_center = self.o + np.array([pixels * 20, pixels * 20])
        self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
        self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
        self.canvas_widget.pack()

    def reset(self):
        self.update()
        self.canvas_widget.delete(self.agent)
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='red', fill='red')
        self.d = {}
        self.i = 0
        return self.canvas_widget.coords(self.agent)

    def step(self, action):
        state = self.canvas_widget.coords(self.agent)
        base_action = np.array([0, 0])
        if action == 0:
            if state[1] >= pixels:
                base_action[1] -= pixels
        elif action == 1:
            if state[1] < (env_height - 1) * pixels:
                base_action[1] += pixels
        elif action == 2:
            if state[0] < (env_width - 1) * pixels:
                base_action[0] += pixels
        elif action == 3:
            if state[0] >= pixels:
                base_action[0] -= pixels
        self.canvas_widget.move(self.agent, base_action[0], base_action[1])
        self.d[self.i] = self.canvas_widget.coords(self.agent)
        next_state = self.d[self.i]
        self.i += 1
        if next_state == self.coords_flag:
            time.sleep(0.1)
            reward = 1
            done = True
            next_state = 'goal'
            if self.c == True:
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
                self.c = False
                self.longest = len(self.d)
                self.shortest = len(self.d)
            if len(self.d) < len(self.f):
                self.shortest = len(self.d)
                self.f = {}
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
            if len(self.d) > self.longest:
                self.longest = len(self.d)
        elif next_state in [self.coords_obstacle1, self.coords_obstacle2, self.coords_obstacle3, self.coords_obstacle4, self.coords_obstacle5, self.coords_obstacle6, self.coords_obstacle7, self.coords_obstacle8, self.coords_obstacle9, self.coords_obstacle10, self.coords_obstacle11, self.coords_obstacle12, self.coords_obstacle13, self.coords_obstacle14, self.coords_obstacle15, self.coords_obstacle16, self.coords_obstacle17, self.coords_obstacle18, self.coords_obstacle19, self.coords_obstacle20, self.coords_obstacle21, self.coords_obstacle22, self.coords_obstacle23, self.coords_obstacle24, self.coords_obstacle25, self.coords_obstacle26, self.coords_obstacle27, self.coords_obstacle28, self.coords_obstacle29, self.coords_obstacle30, self.coords_obstacle31, self.coords_obstacle32, self.coords_obstacle33, self.coords_obstacle34, self.coords_obstacle35, self.coords_obstacle36, self.coords_obstacle37, self.coords_obstacle38, self.coords_obstacle39, self.coords_obstacle40, self.coords_obstacle41, self.coords_obstacle42, self.coords_obstacle43, self.coords_obstacle44, self.coords_obstacle45, self.coords_obstacle46, self.coords_obstacle47, self.coords_obstacle48, self.coords_obstacle49, self.coords_obstacle50, self.coords_obstacle51, self.coords_obstacle52, self.coords_obstacle53, self.coords_obstacle54, self.coords_obstacle55, self.coords_obstacle56, self.coords_obstacle57, self.coords_obstacle58, self.coords_obstacle59, self.coords_obstacle60, self.coords_obstacle61, self.coords_obstacle62, self.coords_obstacle63, self.coords_obstacle64, self.coords_obstacle65, self.coords_obstacle66, self.coords_obstacle66, self.coords_obstacle67, self.coords_obstacle68, self.coords_obstacle69, self.coords_obstacle70, self.coords_obstacle71, self.coords_obstacle72, self.coords_obstacle73, self.coords_obstacle74, self.coords_obstacle75, self.coords_obstacle76, self.coords_obstacle77, self.coords_obstacle78, self.coords_obstacle79, self.coords_obstacle80, self.coords_obstacle81, self.coords_obstacle82, self.coords_obstacle83, self.coords_obstacle84, self.coords_obstacle85, self.coords_obstacle86, self.coords_obstacle87, self.coords_obstacle88, self.coords_obstacle89, self.coords_obstacle90, self.coords_obstacle91, self.coords_obstacle92, self.coords_obstacle93, self.coords_obstacle94, self.coords_obstacle95, self.coords_obstacle96, self.coords_obstacle97, self.coords_obstacle98, self.coords_obstacle99, self.coords_obstacle100, self.coords_obstacle101, self.coords_obstacle102, self.coords_obstacle103, self.coords_obstacle104, self.coords_obstacle105, self.coords_obstacle106, self.coords_obstacle107, self.coords_obstacle108, self.coords_obstacle109, self.coords_obstacle110, self.coords_obstacle111, self.coords_obstacle112, self.coords_obstacle113, self.coords_obstacle114, self.coords_obstacle115, self.coords_obstacle116, self.coords_obstacle117, self.coords_obstacle118, self.coords_obstacle119, self.coords_obstacle120, self.coords_obstacle121, self.coords_obstacle122, self.coords_obstacle123, self.coords_obstacle124, self.coords_obstacle125, self.coords_obstacle126, self.coords_obstacle127, self.coords_obstacle128, self.coords_obstacle129, self.coords_obstacle130, self.coords_obstacle131, self.coords_obstacle132, self.coords_obstacle133, self.coords_obstacle134, self.coords_obstacle135, self.coords_obstacle136, self.coords_obstacle137, self.coords_obstacle138, self.coords_obstacle139, self.coords_obstacle140, self.coords_obstacle141, self.coords_obstacle142, self.coords_obstacle143, self.coords_obstacle144, self.coords_obstacle145, self.coords_obstacle146, self.coords_obstacle147, self.coords_obstacle148, self.coords_obstacle149, self.coords_obstacle150, self.coords_obstacle151, self.coords_obstacle152, self.coords_obstacle153, self.coords_obstacle154, self.coords_obstacle155, self.coords_obstacle156, self.coords_obstacle157, self.coords_obstacle158, self.coords_obstacle159, self.coords_obstacle160, self.coords_obstacle161, self.coords_obstacle162, self.coords_obstacle163, self.coords_obstacle164, self.coords_obstacle165, self.coords_obstacle166, self.coords_obstacle167, self.coords_obstacle168, self.coords_obstacle169, self.coords_obstacle170, self.coords_obstacle171, self.coords_obstacle172, self.coords_obstacle173, self.coords_obstacle174, self.coords_obstacle175, self.coords_obstacle176, self.coords_obstacle177, self.coords_obstacle178, self.coords_obstacle179, self.coords_obstacle180, self.coords_obstacle181, self.coords_obstacle182, self.coords_obstacle183, self.coords_obstacle184, self.coords_obstacle185, self.coords_obstacle186, self.coords_obstacle187, self.coords_obstacle188, self.coords_obstacle189, self.coords_obstacle190, self.coords_obstacle191, self.coords_obstacle192, self.coords_obstacle193, self.coords_obstacle194, self.coords_obstacle195, self.coords_obstacle196, self.coords_obstacle197, self.coords_obstacle198, self.coords_obstacle199, self.coords_obstacle200, self.coords_obstacle201, self.coords_obstacle202, self.coords_obstacle203, self.coords_obstacle204, self.coords_obstacle205, self.coords_obstacle206, self.coords_obstacle207, self.coords_obstacle208, self.coords_obstacle209, self.coords_obstacle210, self.coords_obstacle211, self.coords_obstacle212]:
            reward = -1
            done = True
            next_state = 'obstacle'
            self.d = {}
            self.i = 0
        else:
            reward = 0
            done = False
        return (next_state, reward, done)

    def render(self):
        self.update()

    def final(self):
        self.canvas_widget.delete(self.agent)
        print('The shortest route:', self.shortest)
        print('The longest route:', self.longest)
        self.initial_point = self.canvas_widget.create_oval(self.o[0] - 4, self.o[1] - 4, self.o[0] + 4, self.o[1] + 4, fill='blue', outline='blue')
        for j in range(len(self.f)):
            print(self.f[j])
            self.track = self.canvas_widget.create_oval(self.f[j][0] - 3 + self.o[0] - 4, self.f[j][1] - 3 + self.o[1] - 4, self.f[j][0] - 3 + self.o[0] + 4, self.f[j][1] - 3 + self.o[1] + 4, fill='blue', outline='blue')
            a[j] = self.f[j]

def build_environment(self):
    self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
    img_background = Image.open('images/bg.png')
    self.background = ImageTk.PhotoImage(img_background)
    self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
    for column in range(0, env_width * pixels, pixels):
        x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    for row in range(0, env_height * pixels, pixels):
        x0, y0, x1, y1 = (0, row, env_height * pixels, row)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    self.o = np.array([pixels / 2, pixels / 2])
    obstacle1_center = self.o + np.array([pixels, pixels * 2])
    self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
    obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
    self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
    obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
    self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
    obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
    self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
    obstacle5_center = self.o + np.array([pixels * 23, pixels])
    self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
    obstacle6_center = self.o + np.array([pixels * 6, pixels])
    self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
    obstacle7_center = self.o + np.array([pixels * 6, pixels * 2])
    self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
    obstacle8_center = self.o + np.array([pixels * 7, pixels * 2])
    self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
    obstacle9_center = self.o + np.array([pixels * 8, pixels * 2])
    self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
    obstacle10_center = self.o + np.array([pixels * 10, pixels * 4])
    self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
    obstacle11_center = self.o + np.array([pixels * 10, pixels * 5])
    self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
    obstacle12_center = self.o + np.array([pixels * 10, pixels * 6])
    self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
    obstacle13_center = self.o + np.array([pixels * 11, pixels * 5])
    self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
    obstacle14_center = self.o + np.array([pixels * 12, pixels * 5])
    self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
    obstacle15_center = self.o + np.array([pixels * 13, pixels * 5])
    self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
    obstacle16_center = self.o + np.array([pixels * 14, pixels * 5])
    self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
    obstacle17_center = self.o + np.array([pixels * 15, pixels * 4])
    self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
    obstacle18_center = self.o + np.array([pixels * 15, pixels * 5])
    self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
    obstacle19_center = self.o + np.array([pixels * 15, pixels * 6])
    self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
    obstacle20_center = self.o + np.array([pixels * 16, pixels * 1])
    self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
    obstacle21_center = self.o + np.array([pixels * 17, pixels * 1])
    self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
    obstacle22_center = self.o + np.array([pixels * 18, pixels * 1])
    self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
    obstacle23_center = self.o + np.array([pixels * 18, pixels * 2])
    self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
    obstacle24_center = self.o + np.array([pixels * 18, pixels * 3])
    self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
    obstacle25_center = self.o + np.array([pixels * 18, pixels * 7])
    self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
    obstacle26_center = self.o + np.array([pixels * 18, pixels * 8])
    self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
    obstacle27_center = self.o + np.array([pixels * 19, pixels * 8])
    self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
    obstacle28_center = self.o + np.array([pixels * 20, pixels * 8])
    self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
    obstacle29_center = self.o + np.array([pixels * 21, pixels * 8])
    self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
    obstacle30_center = self.o + np.array([pixels * 22, pixels * 8])
    self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
    obstacle31_center = self.o + np.array([pixels * 22, pixels * 7])
    self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
    obstacle32_center = self.o + np.array([pixels * 22, pixels * 6])
    self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
    obstacle33_center = self.o + np.array([pixels * 23, pixels * 2])
    self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
    obstacle34_center = self.o + np.array([pixels * 24, pixels * 2])
    self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
    obstacle35_center = self.o + np.array([pixels * 25, pixels * 2])
    self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
    obstacle36_center = self.o + np.array([pixels * 26, pixels * 2])
    self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
    obstacle37_center = self.o + np.array([pixels * 26, pixels * 3])
    self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
    obstacle38_center = self.o + np.array([pixels * 26, pixels * 4])
    self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
    obstacle39_center = self.o + np.array([pixels * 26, pixels * 5])
    self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
    obstacle40_center = self.o + np.array([pixels * 27, pixels * 5])
    self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
    obstacle41_center = self.o + np.array([pixels * 27, pixels * 7])
    self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
    obstacle42_center = self.o + np.array([pixels * 28, pixels * 7])
    self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
    obstacle43_center = self.o + np.array([pixels * 26, pixels * 7])
    self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
    obstacle44_center = self.o + np.array([pixels * 27, pixels * 8])
    self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
    obstacle45_center = self.o + np.array([pixels * 27, pixels * 9])
    self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
    obstacle46_center = self.o + np.array([pixels * 27, pixels * 10])
    self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
    obstacle47_center = self.o + np.array([pixels * 27, pixels * 11])
    self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
    obstacle48_center = self.o + np.array([pixels * 26, pixels * 11])
    self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
    obstacle49_center = self.o + np.array([pixels * 28, pixels * 11])
    self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
    obstacle50_center = self.o + np.array([pixels * 23, pixels * 10])
    self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
    obstacle51_center = self.o + np.array([pixels * 22, pixels * 10])
    self.obstacle51 = self.canvas_widget.create_rectangle(obstacle51_center[0] - 10, obstacle51_center[1] - 10, obstacle51_center[0] + 10, obstacle51_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle51 = [self.canvas_widget.coords(self.obstacle51)[0] + 3, self.canvas_widget.coords(self.obstacle51)[1] + 3, self.canvas_widget.coords(self.obstacle51)[2] - 3, self.canvas_widget.coords(self.obstacle51)[3] - 3]
    obstacle52_center = self.o + np.array([pixels * 21, pixels * 10])
    self.obstacle52 = self.canvas_widget.create_rectangle(obstacle52_center[0] - 10, obstacle52_center[1] - 10, obstacle52_center[0] + 10, obstacle52_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle52 = [self.canvas_widget.coords(self.obstacle52)[0] + 3, self.canvas_widget.coords(self.obstacle52)[1] + 3, self.canvas_widget.coords(self.obstacle52)[2] - 3, self.canvas_widget.coords(self.obstacle52)[3] - 3]
    obstacle53_center = self.o + np.array([pixels * 21, pixels * 11])
    self.obstacle53 = self.canvas_widget.create_rectangle(obstacle53_center[0] - 10, obstacle53_center[1] - 10, obstacle53_center[0] + 10, obstacle53_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle53 = [self.canvas_widget.coords(self.obstacle53)[0] + 3, self.canvas_widget.coords(self.obstacle53)[1] + 3, self.canvas_widget.coords(self.obstacle53)[2] - 3, self.canvas_widget.coords(self.obstacle53)[3] - 3]
    obstacle54_center = self.o + np.array([pixels * 21, pixels * 12])
    self.obstacle54 = self.canvas_widget.create_rectangle(obstacle54_center[0] - 10, obstacle54_center[1] - 10, obstacle54_center[0] + 10, obstacle54_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle54 = [self.canvas_widget.coords(self.obstacle54)[0] + 3, self.canvas_widget.coords(self.obstacle54)[1] + 3, self.canvas_widget.coords(self.obstacle54)[2] - 3, self.canvas_widget.coords(self.obstacle54)[3] - 3]
    obstacle55_center = self.o + np.array([pixels * 21, pixels * 13])
    self.obstacle55 = self.canvas_widget.create_rectangle(obstacle55_center[0] - 10, obstacle55_center[1] - 10, obstacle55_center[0] + 10, obstacle55_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle55 = [self.canvas_widget.coords(self.obstacle55)[0] + 3, self.canvas_widget.coords(self.obstacle55)[1] + 3, self.canvas_widget.coords(self.obstacle55)[2] - 3, self.canvas_widget.coords(self.obstacle55)[3] - 3]
    obstacle56_center = self.o + np.array([pixels * 18, pixels * 11])
    self.obstacle56 = self.canvas_widget.create_rectangle(obstacle56_center[0] - 10, obstacle56_center[1] - 10, obstacle56_center[0] + 10, obstacle56_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle56 = [self.canvas_widget.coords(self.obstacle56)[0] + 3, self.canvas_widget.coords(self.obstacle56)[1] + 3, self.canvas_widget.coords(self.obstacle56)[2] - 3, self.canvas_widget.coords(self.obstacle56)[3] - 3]
    obstacle57_center = self.o + np.array([pixels * 17, pixels * 11])
    self.obstacle57 = self.canvas_widget.create_rectangle(obstacle57_center[0] - 10, obstacle57_center[1] - 10, obstacle57_center[0] + 10, obstacle57_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle57 = [self.canvas_widget.coords(self.obstacle57)[0] + 3, self.canvas_widget.coords(self.obstacle57)[1] + 3, self.canvas_widget.coords(self.obstacle57)[2] - 3, self.canvas_widget.coords(self.obstacle57)[3] - 3]
    obstacle58_center = self.o + np.array([pixels * 16, pixels * 11])
    self.obstacle58 = self.canvas_widget.create_rectangle(obstacle58_center[0] - 10, obstacle58_center[1] - 10, obstacle58_center[0] + 10, obstacle58_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle58 = [self.canvas_widget.coords(self.obstacle58)[0] + 3, self.canvas_widget.coords(self.obstacle58)[1] + 3, self.canvas_widget.coords(self.obstacle58)[2] - 3, self.canvas_widget.coords(self.obstacle58)[3] - 3]
    obstacle59_center = self.o + np.array([pixels * 15, pixels * 11])
    self.obstacle59 = self.canvas_widget.create_rectangle(obstacle59_center[0] - 10, obstacle59_center[1] - 10, obstacle59_center[0] + 10, obstacle59_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle59 = [self.canvas_widget.coords(self.obstacle59)[0] + 3, self.canvas_widget.coords(self.obstacle59)[1] + 3, self.canvas_widget.coords(self.obstacle59)[2] - 3, self.canvas_widget.coords(self.obstacle59)[3] - 3]
    obstacle60_center = self.o + np.array([pixels * 14, pixels * 11])
    self.obstacle60 = self.canvas_widget.create_rectangle(obstacle60_center[0] - 10, obstacle60_center[1] - 10, obstacle60_center[0] + 10, obstacle60_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle60 = [self.canvas_widget.coords(self.obstacle60)[0] + 3, self.canvas_widget.coords(self.obstacle60)[1] + 3, self.canvas_widget.coords(self.obstacle60)[2] - 3, self.canvas_widget.coords(self.obstacle60)[3] - 3]
    obstacle61_center = self.o + np.array([pixels * 14, pixels * 10])
    self.obstacle61 = self.canvas_widget.create_rectangle(obstacle61_center[0] - 10, obstacle61_center[1] - 10, obstacle61_center[0] + 10, obstacle61_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle61 = [self.canvas_widget.coords(self.obstacle61)[0] + 3, self.canvas_widget.coords(self.obstacle61)[1] + 3, self.canvas_widget.coords(self.obstacle61)[2] - 3, self.canvas_widget.coords(self.obstacle61)[3] - 3]
    obstacle62_center = self.o + np.array([pixels * 10, pixels * 9])
    self.obstacle62 = self.canvas_widget.create_rectangle(obstacle62_center[0] - 10, obstacle62_center[1] - 10, obstacle62_center[0] + 10, obstacle62_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle62 = [self.canvas_widget.coords(self.obstacle62)[0] + 3, self.canvas_widget.coords(self.obstacle62)[1] + 3, self.canvas_widget.coords(self.obstacle62)[2] - 3, self.canvas_widget.coords(self.obstacle62)[3] - 3]
    obstacle63_center = self.o + np.array([pixels * 9, pixels * 9])
    self.obstacle63 = self.canvas_widget.create_rectangle(obstacle63_center[0] - 10, obstacle63_center[1] - 10, obstacle63_center[0] + 10, obstacle63_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle63 = [self.canvas_widget.coords(self.obstacle63)[0] + 3, self.canvas_widget.coords(self.obstacle63)[1] + 3, self.canvas_widget.coords(self.obstacle63)[2] - 3, self.canvas_widget.coords(self.obstacle63)[3] - 3]
    obstacle64_center = self.o + np.array([pixels * 8, pixels * 9])
    self.obstacle64 = self.canvas_widget.create_rectangle(obstacle64_center[0] - 10, obstacle64_center[1] - 10, obstacle64_center[0] + 10, obstacle64_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle64 = [self.canvas_widget.coords(self.obstacle64)[0] + 3, self.canvas_widget.coords(self.obstacle64)[1] + 3, self.canvas_widget.coords(self.obstacle64)[2] - 3, self.canvas_widget.coords(self.obstacle64)[3] - 3]
    obstacle65_center = self.o + np.array([pixels * 7, pixels * 9])
    self.obstacle65 = self.canvas_widget.create_rectangle(obstacle65_center[0] - 10, obstacle65_center[1] - 10, obstacle65_center[0] + 10, obstacle65_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle65 = [self.canvas_widget.coords(self.obstacle65)[0] + 3, self.canvas_widget.coords(self.obstacle65)[1] + 3, self.canvas_widget.coords(self.obstacle65)[2] - 3, self.canvas_widget.coords(self.obstacle65)[3] - 3]
    obstacle66_center = self.o + np.array([pixels * 7, pixels * 8])
    self.obstacle66 = self.canvas_widget.create_rectangle(obstacle66_center[0] - 10, obstacle66_center[1] - 10, obstacle66_center[0] + 10, obstacle66_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle66 = [self.canvas_widget.coords(self.obstacle66)[0] + 3, self.canvas_widget.coords(self.obstacle66)[1] + 3, self.canvas_widget.coords(self.obstacle66)[2] - 3, self.canvas_widget.coords(self.obstacle66)[3] - 3]
    obstacle67_center = self.o + np.array([pixels * 7, pixels * 7])
    self.obstacle67 = self.canvas_widget.create_rectangle(obstacle67_center[0] - 10, obstacle67_center[1] - 10, obstacle67_center[0] + 10, obstacle67_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle67 = [self.canvas_widget.coords(self.obstacle67)[0] + 3, self.canvas_widget.coords(self.obstacle67)[1] + 3, self.canvas_widget.coords(self.obstacle67)[2] - 3, self.canvas_widget.coords(self.obstacle67)[3] - 3]
    obstacle68_center = self.o + np.array([pixels * 6, pixels * 7])
    self.obstacle68 = self.canvas_widget.create_rectangle(obstacle68_center[0] - 10, obstacle68_center[1] - 10, obstacle68_center[0] + 10, obstacle68_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle68 = [self.canvas_widget.coords(self.obstacle68)[0] + 3, self.canvas_widget.coords(self.obstacle68)[1] + 3, self.canvas_widget.coords(self.obstacle68)[2] - 3, self.canvas_widget.coords(self.obstacle68)[3] - 3]
    obstacle69_center = self.o + np.array([pixels * 5, pixels * 7])
    self.obstacle69 = self.canvas_widget.create_rectangle(obstacle69_center[0] - 10, obstacle69_center[1] - 10, obstacle69_center[0] + 10, obstacle69_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle69 = [self.canvas_widget.coords(self.obstacle69)[0] + 3, self.canvas_widget.coords(self.obstacle69)[1] + 3, self.canvas_widget.coords(self.obstacle69)[2] - 3, self.canvas_widget.coords(self.obstacle69)[3] - 3]
    obstacle70_center = self.o + np.array([pixels * 5, pixels * 5])
    self.obstacle70 = self.canvas_widget.create_rectangle(obstacle70_center[0] - 10, obstacle70_center[1] - 10, obstacle70_center[0] + 10, obstacle70_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle70 = [self.canvas_widget.coords(self.obstacle70)[0] + 3, self.canvas_widget.coords(self.obstacle70)[1] + 3, self.canvas_widget.coords(self.obstacle70)[2] - 3, self.canvas_widget.coords(self.obstacle70)[3] - 3]
    obstacle71_center = self.o + np.array([pixels * 5, pixels * 6])
    self.obstacle71 = self.canvas_widget.create_rectangle(obstacle71_center[0] - 10, obstacle71_center[1] - 10, obstacle71_center[0] + 10, obstacle71_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle71 = [self.canvas_widget.coords(self.obstacle71)[0] + 3, self.canvas_widget.coords(self.obstacle71)[1] + 3, self.canvas_widget.coords(self.obstacle71)[2] - 3, self.canvas_widget.coords(self.obstacle71)[3] - 3]
    obstacle72_center = self.o + np.array([pixels, pixels * 7])
    self.obstacle72 = self.canvas_widget.create_rectangle(obstacle72_center[0] - 10, obstacle72_center[1] - 10, obstacle72_center[0] + 10, obstacle72_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle72 = [self.canvas_widget.coords(self.obstacle72)[0] + 3, self.canvas_widget.coords(self.obstacle72)[1] + 3, self.canvas_widget.coords(self.obstacle72)[2] - 3, self.canvas_widget.coords(self.obstacle72)[3] - 3]
    obstacle73_center = self.o + np.array([pixels, pixels * 6])
    self.obstacle73 = self.canvas_widget.create_rectangle(obstacle73_center[0] - 10, obstacle73_center[1] - 10, obstacle73_center[0] + 10, obstacle73_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle73 = [self.canvas_widget.coords(self.obstacle73)[0] + 3, self.canvas_widget.coords(self.obstacle73)[1] + 3, self.canvas_widget.coords(self.obstacle73)[2] - 3, self.canvas_widget.coords(self.obstacle73)[3] - 3]
    obstacle74_center = self.o + np.array([pixels * 2, pixels * 6])
    self.obstacle74 = self.canvas_widget.create_rectangle(obstacle74_center[0] - 10, obstacle74_center[1] - 10, obstacle74_center[0] + 10, obstacle74_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle74 = [self.canvas_widget.coords(self.obstacle74)[0] + 3, self.canvas_widget.coords(self.obstacle74)[1] + 3, self.canvas_widget.coords(self.obstacle74)[2] - 3, self.canvas_widget.coords(self.obstacle74)[3] - 3]
    obstacle75_center = self.o + np.array([pixels, pixels * 8])
    self.obstacle75 = self.canvas_widget.create_rectangle(obstacle75_center[0] - 10, obstacle75_center[1] - 10, obstacle75_center[0] + 10, obstacle75_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle75 = [self.canvas_widget.coords(self.obstacle75)[0] + 3, self.canvas_widget.coords(self.obstacle75)[1] + 3, self.canvas_widget.coords(self.obstacle75)[2] - 3, self.canvas_widget.coords(self.obstacle75)[3] - 3]
    obstacle76_center = self.o + np.array([pixels, pixels * 9])
    self.obstacle76 = self.canvas_widget.create_rectangle(obstacle76_center[0] - 10, obstacle76_center[1] - 10, obstacle76_center[0] + 10, obstacle76_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle76 = [self.canvas_widget.coords(self.obstacle76)[0] + 3, self.canvas_widget.coords(self.obstacle76)[1] + 3, self.canvas_widget.coords(self.obstacle76)[2] - 3, self.canvas_widget.coords(self.obstacle76)[3] - 3]
    obstacle77_center = self.o + np.array([pixels, pixels * 10])
    self.obstacle77 = self.canvas_widget.create_rectangle(obstacle77_center[0] - 10, obstacle77_center[1] - 10, obstacle77_center[0] + 10, obstacle77_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle77 = [self.canvas_widget.coords(self.obstacle77)[0] + 3, self.canvas_widget.coords(self.obstacle77)[1] + 3, self.canvas_widget.coords(self.obstacle77)[2] - 3, self.canvas_widget.coords(self.obstacle77)[3] - 3]
    obstacle78_center = self.o + np.array([pixels, pixels * 11])
    self.obstacle78 = self.canvas_widget.create_rectangle(obstacle78_center[0] - 10, obstacle78_center[1] - 10, obstacle78_center[0] + 10, obstacle78_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle78 = [self.canvas_widget.coords(self.obstacle78)[0] + 3, self.canvas_widget.coords(self.obstacle78)[1] + 3, self.canvas_widget.coords(self.obstacle78)[2] - 3, self.canvas_widget.coords(self.obstacle78)[3] - 3]
    obstacle79_center = self.o + np.array([pixels * 3, pixels * 9])
    self.obstacle79 = self.canvas_widget.create_rectangle(obstacle79_center[0] - 10, obstacle79_center[1] - 10, obstacle79_center[0] + 10, obstacle79_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle79 = [self.canvas_widget.coords(self.obstacle79)[0] + 3, self.canvas_widget.coords(self.obstacle79)[1] + 3, self.canvas_widget.coords(self.obstacle79)[2] - 3, self.canvas_widget.coords(self.obstacle79)[3] - 3]
    obstacle80_center = self.o + np.array([pixels * 3, pixels * 10])
    self.obstacle80 = self.canvas_widget.create_rectangle(obstacle80_center[0] - 10, obstacle80_center[1] - 10, obstacle80_center[0] + 10, obstacle80_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle80 = [self.canvas_widget.coords(self.obstacle80)[0] + 3, self.canvas_widget.coords(self.obstacle80)[1] + 3, self.canvas_widget.coords(self.obstacle80)[2] - 3, self.canvas_widget.coords(self.obstacle80)[3] - 3]
    obstacle81_center = self.o + np.array([pixels * 3, pixels * 11])
    self.obstacle81 = self.canvas_widget.create_rectangle(obstacle81_center[0] - 10, obstacle81_center[1] - 10, obstacle81_center[0] + 10, obstacle81_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle81 = [self.canvas_widget.coords(self.obstacle81)[0] + 3, self.canvas_widget.coords(self.obstacle81)[1] + 3, self.canvas_widget.coords(self.obstacle81)[2] - 3, self.canvas_widget.coords(self.obstacle81)[3] - 3]
    obstacle82_center = self.o + np.array([pixels * 3, pixels * 12])
    self.obstacle82 = self.canvas_widget.create_rectangle(obstacle82_center[0] - 10, obstacle82_center[1] - 10, obstacle82_center[0] + 10, obstacle82_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle82 = [self.canvas_widget.coords(self.obstacle82)[0] + 3, self.canvas_widget.coords(self.obstacle82)[1] + 3, self.canvas_widget.coords(self.obstacle82)[2] - 3, self.canvas_widget.coords(self.obstacle82)[3] - 3]
    obstacle83_center = self.o + np.array([pixels * 3, pixels * 13])
    self.obstacle83 = self.canvas_widget.create_rectangle(obstacle83_center[0] - 10, obstacle83_center[1] - 10, obstacle83_center[0] + 10, obstacle83_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle83 = [self.canvas_widget.coords(self.obstacle83)[0] + 3, self.canvas_widget.coords(self.obstacle83)[1] + 3, self.canvas_widget.coords(self.obstacle83)[2] - 3, self.canvas_widget.coords(self.obstacle83)[3] - 3]
    obstacle84_center = self.o + np.array([pixels * 4, pixels * 13])
    self.obstacle84 = self.canvas_widget.create_rectangle(obstacle84_center[0] - 10, obstacle84_center[1] - 10, obstacle84_center[0] + 10, obstacle84_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle84 = [self.canvas_widget.coords(self.obstacle84)[0] + 3, self.canvas_widget.coords(self.obstacle84)[1] + 3, self.canvas_widget.coords(self.obstacle84)[2] - 3, self.canvas_widget.coords(self.obstacle84)[3] - 3]
    obstacle85_center = self.o + np.array([pixels * 5, pixels * 13])
    self.obstacle85 = self.canvas_widget.create_rectangle(obstacle85_center[0] - 10, obstacle85_center[1] - 10, obstacle85_center[0] + 10, obstacle85_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle85 = [self.canvas_widget.coords(self.obstacle85)[0] + 3, self.canvas_widget.coords(self.obstacle85)[1] + 3, self.canvas_widget.coords(self.obstacle85)[2] - 3, self.canvas_widget.coords(self.obstacle85)[3] - 3]
    obstacle86_center = self.o + np.array([pixels * 6, pixels * 13])
    self.obstacle86 = self.canvas_widget.create_rectangle(obstacle86_center[0] - 10, obstacle86_center[1] - 10, obstacle86_center[0] + 10, obstacle86_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle86 = [self.canvas_widget.coords(self.obstacle86)[0] + 3, self.canvas_widget.coords(self.obstacle86)[1] + 3, self.canvas_widget.coords(self.obstacle86)[2] - 3, self.canvas_widget.coords(self.obstacle86)[3] - 3]
    obstacle87_center = self.o + np.array([pixels * 6, pixels * 12])
    self.obstacle87 = self.canvas_widget.create_rectangle(obstacle87_center[0] - 10, obstacle87_center[1] - 10, obstacle87_center[0] + 10, obstacle87_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle87 = [self.canvas_widget.coords(self.obstacle87)[0] + 3, self.canvas_widget.coords(self.obstacle87)[1] + 3, self.canvas_widget.coords(self.obstacle87)[2] - 3, self.canvas_widget.coords(self.obstacle87)[3] - 3]
    obstacle88_center = self.o + np.array([pixels * 2, pixels * 15])
    self.obstacle88 = self.canvas_widget.create_rectangle(obstacle88_center[0] - 10, obstacle88_center[1] - 10, obstacle88_center[0] + 10, obstacle88_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle88 = [self.canvas_widget.coords(self.obstacle88)[0] + 3, self.canvas_widget.coords(self.obstacle88)[1] + 3, self.canvas_widget.coords(self.obstacle88)[2] - 3, self.canvas_widget.coords(self.obstacle88)[3] - 3]
    obstacle89_center = self.o + np.array([pixels * 2, pixels * 16])
    self.obstacle89 = self.canvas_widget.create_rectangle(obstacle89_center[0] - 10, obstacle89_center[1] - 10, obstacle89_center[0] + 10, obstacle89_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle89 = [self.canvas_widget.coords(self.obstacle89)[0] + 3, self.canvas_widget.coords(self.obstacle89)[1] + 3, self.canvas_widget.coords(self.obstacle89)[2] - 3, self.canvas_widget.coords(self.obstacle89)[3] - 3]
    obstacle90_center = self.o + np.array([pixels * 2, pixels * 17])
    self.obstacle90 = self.canvas_widget.create_rectangle(obstacle90_center[0] - 10, obstacle90_center[1] - 10, obstacle90_center[0] + 10, obstacle90_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle90 = [self.canvas_widget.coords(self.obstacle90)[0] + 3, self.canvas_widget.coords(self.obstacle90)[1] + 3, self.canvas_widget.coords(self.obstacle90)[2] - 3, self.canvas_widget.coords(self.obstacle90)[3] - 3]
    obstacle91_center = self.o + np.array([pixels * 2, pixels * 18])
    self.obstacle91 = self.canvas_widget.create_rectangle(obstacle91_center[0] - 10, obstacle91_center[1] - 10, obstacle91_center[0] + 10, obstacle91_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle91 = [self.canvas_widget.coords(self.obstacle91)[0] + 3, self.canvas_widget.coords(self.obstacle91)[1] + 3, self.canvas_widget.coords(self.obstacle91)[2] - 3, self.canvas_widget.coords(self.obstacle91)[3] - 3]
    obstacle92_center = self.o + np.array([pixels * 2, pixels * 19])
    self.obstacle92 = self.canvas_widget.create_rectangle(obstacle92_center[0] - 10, obstacle92_center[1] - 10, obstacle92_center[0] + 10, obstacle92_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle92 = [self.canvas_widget.coords(self.obstacle92)[0] + 3, self.canvas_widget.coords(self.obstacle92)[1] + 3, self.canvas_widget.coords(self.obstacle92)[2] - 3, self.canvas_widget.coords(self.obstacle92)[3] - 3]
    obstacle93_center = self.o + np.array([pixels, pixels * 16])
    self.obstacle93 = self.canvas_widget.create_rectangle(obstacle93_center[0] - 10, obstacle93_center[1] - 10, obstacle93_center[0] + 10, obstacle93_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle93 = [self.canvas_widget.coords(self.obstacle93)[0] + 3, self.canvas_widget.coords(self.obstacle93)[1] + 3, self.canvas_widget.coords(self.obstacle93)[2] - 3, self.canvas_widget.coords(self.obstacle93)[3] - 3]
    obstacle94_center = self.o + np.array([pixels * 2, pixels * 21])
    self.obstacle94 = self.canvas_widget.create_rectangle(obstacle94_center[0] - 10, obstacle94_center[1] - 10, obstacle94_center[0] + 10, obstacle94_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle94 = [self.canvas_widget.coords(self.obstacle94)[0] + 3, self.canvas_widget.coords(self.obstacle94)[1] + 3, self.canvas_widget.coords(self.obstacle94)[2] - 3, self.canvas_widget.coords(self.obstacle94)[3] - 3]
    obstacle95_center = self.o + np.array([pixels * 3, pixels * 21])
    self.obstacle95 = self.canvas_widget.create_rectangle(obstacle95_center[0] - 10, obstacle95_center[1] - 10, obstacle95_center[0] + 10, obstacle95_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle95 = [self.canvas_widget.coords(self.obstacle95)[0] + 3, self.canvas_widget.coords(self.obstacle95)[1] + 3, self.canvas_widget.coords(self.obstacle95)[2] - 3, self.canvas_widget.coords(self.obstacle95)[3] - 3]
    obstacle96_center = self.o + np.array([pixels * 4, pixels * 21])
    self.obstacle96 = self.canvas_widget.create_rectangle(obstacle96_center[0] - 10, obstacle96_center[1] - 10, obstacle96_center[0] + 10, obstacle96_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle96 = [self.canvas_widget.coords(self.obstacle96)[0] + 3, self.canvas_widget.coords(self.obstacle96)[1] + 3, self.canvas_widget.coords(self.obstacle96)[2] - 3, self.canvas_widget.coords(self.obstacle96)[3] - 3]
    obstacle97_center = self.o + np.array([pixels * 4, pixels * 22])
    self.obstacle97 = self.canvas_widget.create_rectangle(obstacle97_center[0] - 10, obstacle97_center[1] - 10, obstacle97_center[0] + 10, obstacle97_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle97 = [self.canvas_widget.coords(self.obstacle97)[0] + 3, self.canvas_widget.coords(self.obstacle97)[1] + 3, self.canvas_widget.coords(self.obstacle97)[2] - 3, self.canvas_widget.coords(self.obstacle97)[3] - 3]
    obstacle98_center = self.o + np.array([pixels * 4, pixels * 23])
    self.obstacle98 = self.canvas_widget.create_rectangle(obstacle98_center[0] - 10, obstacle98_center[1] - 10, obstacle98_center[0] + 10, obstacle98_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle98 = [self.canvas_widget.coords(self.obstacle98)[0] + 3, self.canvas_widget.coords(self.obstacle98)[1] + 3, self.canvas_widget.coords(self.obstacle98)[2] - 3, self.canvas_widget.coords(self.obstacle98)[3] - 3]
    obstacle99_center = self.o + np.array([pixels * 4, pixels * 24])
    self.obstacle99 = self.canvas_widget.create_rectangle(obstacle99_center[0] - 10, obstacle99_center[1] - 10, obstacle99_center[0] + 10, obstacle99_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle99 = [self.canvas_widget.coords(self.obstacle99)[0] + 3, self.canvas_widget.coords(self.obstacle99)[1] + 3, self.canvas_widget.coords(self.obstacle99)[2] - 3, self.canvas_widget.coords(self.obstacle99)[3] - 3]
    obstacle100_center = self.o + np.array([pixels * 4, pixels * 25])
    self.obstacle100 = self.canvas_widget.create_rectangle(obstacle100_center[0] - 10, obstacle100_center[1] - 10, obstacle100_center[0] + 10, obstacle100_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle100 = [self.canvas_widget.coords(self.obstacle100)[0] + 3, self.canvas_widget.coords(self.obstacle100)[1] + 3, self.canvas_widget.coords(self.obstacle100)[2] - 3, self.canvas_widget.coords(self.obstacle100)[3] - 3]
    obstacle101_center = self.o + np.array([pixels * 3, pixels * 25])
    self.obstacle101 = self.canvas_widget.create_rectangle(obstacle101_center[0] - 10, obstacle101_center[1] - 10, obstacle101_center[0] + 10, obstacle101_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle101 = [self.canvas_widget.coords(self.obstacle101)[0] + 3, self.canvas_widget.coords(self.obstacle101)[1] + 3, self.canvas_widget.coords(self.obstacle101)[2] - 3, self.canvas_widget.coords(self.obstacle101)[3] - 3]
    obstacle102_center = self.o + np.array([pixels * 2, pixels * 25])
    self.obstacle102 = self.canvas_widget.create_rectangle(obstacle102_center[0] - 10, obstacle102_center[1] - 10, obstacle102_center[0] + 10, obstacle102_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle102 = [self.canvas_widget.coords(self.obstacle102)[0] + 3, self.canvas_widget.coords(self.obstacle102)[1] + 3, self.canvas_widget.coords(self.obstacle102)[2] - 3, self.canvas_widget.coords(self.obstacle102)[3] - 3]
    obstacle103_center = self.o + np.array([pixels, pixels * 25])
    self.obstacle103 = self.canvas_widget.create_rectangle(obstacle103_center[0] - 10, obstacle103_center[1] - 10, obstacle103_center[0] + 10, obstacle103_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle103 = [self.canvas_widget.coords(self.obstacle103)[0] + 3, self.canvas_widget.coords(self.obstacle103)[1] + 3, self.canvas_widget.coords(self.obstacle103)[2] - 3, self.canvas_widget.coords(self.obstacle103)[3] - 3]
    obstacle104_center = self.o + np.array([pixels * 3, pixels * 16])
    self.obstacle104 = self.canvas_widget.create_rectangle(obstacle104_center[0] - 10, obstacle104_center[1] - 10, obstacle104_center[0] + 10, obstacle104_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle104 = [self.canvas_widget.coords(self.obstacle104)[0] + 3, self.canvas_widget.coords(self.obstacle104)[1] + 3, self.canvas_widget.coords(self.obstacle104)[2] - 3, self.canvas_widget.coords(self.obstacle104)[3] - 3]
    obstacle105_center = self.o + np.array([pixels * 4, pixels * 16])
    self.obstacle105 = self.canvas_widget.create_rectangle(obstacle105_center[0] - 10, obstacle105_center[1] - 10, obstacle105_center[0] + 10, obstacle105_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle105 = [self.canvas_widget.coords(self.obstacle105)[0] + 3, self.canvas_widget.coords(self.obstacle105)[1] + 3, self.canvas_widget.coords(self.obstacle105)[2] - 3, self.canvas_widget.coords(self.obstacle105)[3] - 3]
    obstacle106_center = self.o + np.array([pixels * 5, pixels * 16])
    self.obstacle106 = self.canvas_widget.create_rectangle(obstacle106_center[0] - 10, obstacle106_center[1] - 10, obstacle106_center[0] + 10, obstacle106_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle106 = [self.canvas_widget.coords(self.obstacle106)[0] + 3, self.canvas_widget.coords(self.obstacle106)[1] + 3, self.canvas_widget.coords(self.obstacle106)[2] - 3, self.canvas_widget.coords(self.obstacle106)[3] - 3]
    obstacle107_center = self.o + np.array([pixels * 2, pixels * 27])
    self.obstacle107 = self.canvas_widget.create_rectangle(obstacle107_center[0] - 10, obstacle107_center[1] - 10, obstacle107_center[0] + 10, obstacle107_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle107 = [self.canvas_widget.coords(self.obstacle107)[0] + 3, self.canvas_widget.coords(self.obstacle107)[1] + 3, self.canvas_widget.coords(self.obstacle107)[2] - 3, self.canvas_widget.coords(self.obstacle107)[3] - 3]
    obstacle108_center = self.o + np.array([pixels * 2, pixels * 28])
    self.obstacle108 = self.canvas_widget.create_rectangle(obstacle108_center[0] - 10, obstacle108_center[1] - 10, obstacle108_center[0] + 10, obstacle108_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle108 = [self.canvas_widget.coords(self.obstacle108)[0] + 3, self.canvas_widget.coords(self.obstacle108)[1] + 3, self.canvas_widget.coords(self.obstacle108)[2] - 3, self.canvas_widget.coords(self.obstacle108)[3] - 3]
    obstacle109_center = self.o + np.array([pixels * 3, pixels * 28])
    self.obstacle109 = self.canvas_widget.create_rectangle(obstacle109_center[0] - 10, obstacle109_center[1] - 10, obstacle109_center[0] + 10, obstacle109_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle109 = [self.canvas_widget.coords(self.obstacle109)[0] + 3, self.canvas_widget.coords(self.obstacle109)[1] + 3, self.canvas_widget.coords(self.obstacle109)[2] - 3, self.canvas_widget.coords(self.obstacle109)[3] - 3]
    obstacle110_center = self.o + np.array([pixels * 4, pixels * 28])
    self.obstacle110 = self.canvas_widget.create_rectangle(obstacle110_center[0] - 10, obstacle110_center[1] - 10, obstacle110_center[0] + 10, obstacle110_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle110 = [self.canvas_widget.coords(self.obstacle110)[0] + 3, self.canvas_widget.coords(self.obstacle110)[1] + 3, self.canvas_widget.coords(self.obstacle110)[2] - 3, self.canvas_widget.coords(self.obstacle110)[3] - 3]
    obstacle111_center = self.o + np.array([pixels * 5, pixels * 28])
    self.obstacle111 = self.canvas_widget.create_rectangle(obstacle111_center[0] - 10, obstacle111_center[1] - 10, obstacle111_center[0] + 10, obstacle111_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle111 = [self.canvas_widget.coords(self.obstacle111)[0] + 3, self.canvas_widget.coords(self.obstacle111)[1] + 3, self.canvas_widget.coords(self.obstacle111)[2] - 3, self.canvas_widget.coords(self.obstacle111)[3] - 3]
    obstacle112_center = self.o + np.array([pixels * 6, pixels * 28])
    self.obstacle112 = self.canvas_widget.create_rectangle(obstacle112_center[0] - 10, obstacle112_center[1] - 10, obstacle112_center[0] + 10, obstacle112_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle112 = [self.canvas_widget.coords(self.obstacle112)[0] + 3, self.canvas_widget.coords(self.obstacle112)[1] + 3, self.canvas_widget.coords(self.obstacle112)[2] - 3, self.canvas_widget.coords(self.obstacle112)[3] - 3]
    obstacle113_center = self.o + np.array([pixels * 7, pixels * 28])
    self.obstacle113 = self.canvas_widget.create_rectangle(obstacle113_center[0] - 10, obstacle113_center[1] - 10, obstacle113_center[0] + 10, obstacle113_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle113 = [self.canvas_widget.coords(self.obstacle113)[0] + 3, self.canvas_widget.coords(self.obstacle113)[1] + 3, self.canvas_widget.coords(self.obstacle113)[2] - 3, self.canvas_widget.coords(self.obstacle113)[3] - 3]
    obstacle114_center = self.o + np.array([pixels * 7, pixels * 27])
    self.obstacle114 = self.canvas_widget.create_rectangle(obstacle114_center[0] - 10, obstacle114_center[1] - 10, obstacle114_center[0] + 10, obstacle114_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle114 = [self.canvas_widget.coords(self.obstacle114)[0] + 3, self.canvas_widget.coords(self.obstacle114)[1] + 3, self.canvas_widget.coords(self.obstacle114)[2] - 3, self.canvas_widget.coords(self.obstacle114)[3] - 3]
    obstacle115_center = self.o + np.array([pixels * 7, pixels * 26])
    self.obstacle115 = self.canvas_widget.create_rectangle(obstacle115_center[0] - 10, obstacle115_center[1] - 10, obstacle115_center[0] + 10, obstacle115_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle115 = [self.canvas_widget.coords(self.obstacle115)[0] + 3, self.canvas_widget.coords(self.obstacle115)[1] + 3, self.canvas_widget.coords(self.obstacle115)[2] - 3, self.canvas_widget.coords(self.obstacle115)[3] - 3]
    obstacle116_center = self.o + np.array([pixels * 7, pixels * 25])
    self.obstacle116 = self.canvas_widget.create_rectangle(obstacle116_center[0] - 10, obstacle116_center[1] - 10, obstacle116_center[0] + 10, obstacle116_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle116 = [self.canvas_widget.coords(self.obstacle116)[0] + 3, self.canvas_widget.coords(self.obstacle116)[1] + 3, self.canvas_widget.coords(self.obstacle116)[2] - 3, self.canvas_widget.coords(self.obstacle116)[3] - 3]
    obstacle117_center = self.o + np.array([pixels * 7, pixels * 24])
    self.obstacle117 = self.canvas_widget.create_rectangle(obstacle117_center[0] - 10, obstacle117_center[1] - 10, obstacle117_center[0] + 10, obstacle117_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle117 = [self.canvas_widget.coords(self.obstacle117)[0] + 3, self.canvas_widget.coords(self.obstacle117)[1] + 3, self.canvas_widget.coords(self.obstacle117)[2] - 3, self.canvas_widget.coords(self.obstacle117)[3] - 3]
    obstacle118_center = self.o + np.array([pixels * 9, pixels * 22])
    self.obstacle118 = self.canvas_widget.create_rectangle(obstacle118_center[0] - 10, obstacle118_center[1] - 10, obstacle118_center[0] + 10, obstacle118_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle118 = [self.canvas_widget.coords(self.obstacle118)[0] + 3, self.canvas_widget.coords(self.obstacle118)[1] + 3, self.canvas_widget.coords(self.obstacle118)[2] - 3, self.canvas_widget.coords(self.obstacle118)[3] - 3]
    obstacle119_center = self.o + np.array([pixels * 9, pixels * 21])
    self.obstacle119 = self.canvas_widget.create_rectangle(obstacle119_center[0] - 10, obstacle119_center[1] - 10, obstacle119_center[0] + 10, obstacle119_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle119 = [self.canvas_widget.coords(self.obstacle119)[0] + 3, self.canvas_widget.coords(self.obstacle119)[1] + 3, self.canvas_widget.coords(self.obstacle119)[2] - 3, self.canvas_widget.coords(self.obstacle119)[3] - 3]
    obstacle120_center = self.o + np.array([pixels * 9, pixels * 20])
    self.obstacle120 = self.canvas_widget.create_rectangle(obstacle120_center[0] - 10, obstacle120_center[1] - 10, obstacle120_center[0] + 10, obstacle120_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle120 = [self.canvas_widget.coords(self.obstacle120)[0] + 3, self.canvas_widget.coords(self.obstacle120)[1] + 3, self.canvas_widget.coords(self.obstacle120)[2] - 3, self.canvas_widget.coords(self.obstacle120)[3] - 3]
    obstacle121_center = self.o + np.array([pixels * 9, pixels * 19])
    self.obstacle121 = self.canvas_widget.create_rectangle(obstacle121_center[0] - 10, obstacle121_center[1] - 10, obstacle121_center[0] + 10, obstacle121_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle121 = [self.canvas_widget.coords(self.obstacle121)[0] + 3, self.canvas_widget.coords(self.obstacle121)[1] + 3, self.canvas_widget.coords(self.obstacle121)[2] - 3, self.canvas_widget.coords(self.obstacle121)[3] - 3]
    obstacle122_center = self.o + np.array([pixels * 9, pixels * 18])
    self.obstacle122 = self.canvas_widget.create_rectangle(obstacle122_center[0] - 10, obstacle122_center[1] - 10, obstacle122_center[0] + 10, obstacle122_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle122 = [self.canvas_widget.coords(self.obstacle122)[0] + 3, self.canvas_widget.coords(self.obstacle122)[1] + 3, self.canvas_widget.coords(self.obstacle122)[2] - 3, self.canvas_widget.coords(self.obstacle122)[3] - 3]
    obstacle123_center = self.o + np.array([pixels * 8, pixels * 18])
    self.obstacle123 = self.canvas_widget.create_rectangle(obstacle123_center[0] - 10, obstacle123_center[1] - 10, obstacle123_center[0] + 10, obstacle123_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle123 = [self.canvas_widget.coords(self.obstacle123)[0] + 3, self.canvas_widget.coords(self.obstacle123)[1] + 3, self.canvas_widget.coords(self.obstacle123)[2] - 3, self.canvas_widget.coords(self.obstacle123)[3] - 3]
    obstacle124_center = self.o + np.array([pixels * 7, pixels * 18])
    self.obstacle124 = self.canvas_widget.create_rectangle(obstacle124_center[0] - 10, obstacle124_center[1] - 10, obstacle124_center[0] + 10, obstacle124_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle124 = [self.canvas_widget.coords(self.obstacle124)[0] + 3, self.canvas_widget.coords(self.obstacle124)[1] + 3, self.canvas_widget.coords(self.obstacle124)[2] - 3, self.canvas_widget.coords(self.obstacle124)[3] - 3]
    obstacle125_center = self.o + np.array([pixels * 7, pixels * 16])
    self.obstacle125 = self.canvas_widget.create_rectangle(obstacle125_center[0] - 10, obstacle125_center[1] - 10, obstacle125_center[0] + 10, obstacle125_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle125 = [self.canvas_widget.coords(self.obstacle125)[0] + 3, self.canvas_widget.coords(self.obstacle125)[1] + 3, self.canvas_widget.coords(self.obstacle125)[2] - 3, self.canvas_widget.coords(self.obstacle125)[3] - 3]
    obstacle126_center = self.o + np.array([pixels * 7, pixels * 15])
    self.obstacle126 = self.canvas_widget.create_rectangle(obstacle126_center[0] - 10, obstacle126_center[1] - 10, obstacle126_center[0] + 10, obstacle126_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle126 = [self.canvas_widget.coords(self.obstacle126)[0] + 3, self.canvas_widget.coords(self.obstacle126)[1] + 3, self.canvas_widget.coords(self.obstacle126)[2] - 3, self.canvas_widget.coords(self.obstacle126)[3] - 3]
    obstacle127_center = self.o + np.array([pixels * 7, pixels * 17])
    self.obstacle127 = self.canvas_widget.create_rectangle(obstacle127_center[0] - 10, obstacle127_center[1] - 10, obstacle127_center[0] + 10, obstacle127_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle127 = [self.canvas_widget.coords(self.obstacle127)[0] + 3, self.canvas_widget.coords(self.obstacle127)[1] + 3, self.canvas_widget.coords(self.obstacle127)[2] - 3, self.canvas_widget.coords(self.obstacle127)[3] - 3]
    obstacle128_center = self.o + np.array([pixels * 8, pixels * 15])
    self.obstacle128 = self.canvas_widget.create_rectangle(obstacle128_center[0] - 10, obstacle128_center[1] - 10, obstacle128_center[0] + 10, obstacle128_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle128 = [self.canvas_widget.coords(self.obstacle128)[0] + 3, self.canvas_widget.coords(self.obstacle128)[1] + 3, self.canvas_widget.coords(self.obstacle128)[2] - 3, self.canvas_widget.coords(self.obstacle128)[3] - 3]
    obstacle129_center = self.o + np.array([pixels * 9, pixels * 15])
    self.obstacle129 = self.canvas_widget.create_rectangle(obstacle129_center[0] - 10, obstacle129_center[1] - 10, obstacle129_center[0] + 10, obstacle129_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle129 = [self.canvas_widget.coords(self.obstacle129)[0] + 3, self.canvas_widget.coords(self.obstacle129)[1] + 3, self.canvas_widget.coords(self.obstacle129)[2] - 3, self.canvas_widget.coords(self.obstacle129)[3] - 3]
    obstacle130_center = self.o + np.array([pixels * 10, pixels * 15])
    self.obstacle130 = self.canvas_widget.create_rectangle(obstacle130_center[0] - 10, obstacle130_center[1] - 10, obstacle130_center[0] + 10, obstacle130_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle130 = [self.canvas_widget.coords(self.obstacle130)[0] + 3, self.canvas_widget.coords(self.obstacle130)[1] + 3, self.canvas_widget.coords(self.obstacle130)[2] - 3, self.canvas_widget.coords(self.obstacle130)[3] - 3]
    obstacle131_center = self.o + np.array([pixels * 11, pixels * 12])
    self.obstacle131 = self.canvas_widget.create_rectangle(obstacle131_center[0] - 10, obstacle131_center[1] - 10, obstacle131_center[0] + 10, obstacle131_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle131 = [self.canvas_widget.coords(self.obstacle131)[0] + 3, self.canvas_widget.coords(self.obstacle131)[1] + 3, self.canvas_widget.coords(self.obstacle131)[2] - 3, self.canvas_widget.coords(self.obstacle131)[3] - 3]
    obstacle132_center = self.o + np.array([pixels * 10, pixels * 12])
    self.obstacle132 = self.canvas_widget.create_rectangle(obstacle132_center[0] - 10, obstacle132_center[1] - 10, obstacle132_center[0] + 10, obstacle132_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle132 = [self.canvas_widget.coords(self.obstacle132)[0] + 3, self.canvas_widget.coords(self.obstacle132)[1] + 3, self.canvas_widget.coords(self.obstacle132)[2] - 3, self.canvas_widget.coords(self.obstacle132)[3] - 3]
    obstacle133_center = self.o + np.array([pixels * 11, pixels * 13])
    self.obstacle133 = self.canvas_widget.create_rectangle(obstacle133_center[0] - 10, obstacle133_center[1] - 10, obstacle133_center[0] + 10, obstacle133_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle133 = [self.canvas_widget.coords(self.obstacle133)[0] + 3, self.canvas_widget.coords(self.obstacle133)[1] + 3, self.canvas_widget.coords(self.obstacle133)[2] - 3, self.canvas_widget.coords(self.obstacle133)[3] - 3]
    obstacle134_center = self.o + np.array([pixels * 12, pixels * 13])
    self.obstacle134 = self.canvas_widget.create_rectangle(obstacle134_center[0] - 10, obstacle134_center[1] - 10, obstacle134_center[0] + 10, obstacle134_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle134 = [self.canvas_widget.coords(self.obstacle134)[0] + 3, self.canvas_widget.coords(self.obstacle134)[1] + 3, self.canvas_widget.coords(self.obstacle134)[2] - 3, self.canvas_widget.coords(self.obstacle134)[3] - 3]
    obstacle135_center = self.o + np.array([pixels * 13, pixels * 13])
    self.obstacle135 = self.canvas_widget.create_rectangle(obstacle135_center[0] - 10, obstacle135_center[1] - 10, obstacle135_center[0] + 10, obstacle135_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle135 = [self.canvas_widget.coords(self.obstacle135)[0] + 3, self.canvas_widget.coords(self.obstacle135)[1] + 3, self.canvas_widget.coords(self.obstacle135)[2] - 3, self.canvas_widget.coords(self.obstacle135)[3] - 3]
    obstacle136_center = self.o + np.array([pixels * 13, pixels * 14])
    self.obstacle136 = self.canvas_widget.create_rectangle(obstacle136_center[0] - 10, obstacle136_center[1] - 10, obstacle136_center[0] + 10, obstacle136_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle136 = [self.canvas_widget.coords(self.obstacle136)[0] + 3, self.canvas_widget.coords(self.obstacle136)[1] + 3, self.canvas_widget.coords(self.obstacle136)[2] - 3, self.canvas_widget.coords(self.obstacle136)[3] - 3]
    obstacle137_center = self.o + np.array([pixels * 13, pixels * 15])
    self.obstacle137 = self.canvas_widget.create_rectangle(obstacle137_center[0] - 10, obstacle137_center[1] - 10, obstacle137_center[0] + 10, obstacle137_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle137 = [self.canvas_widget.coords(self.obstacle137)[0] + 3, self.canvas_widget.coords(self.obstacle137)[1] + 3, self.canvas_widget.coords(self.obstacle137)[2] - 3, self.canvas_widget.coords(self.obstacle137)[3] - 3]
    obstacle138_center = self.o + np.array([pixels * 14, pixels * 15])
    self.obstacle138 = self.canvas_widget.create_rectangle(obstacle138_center[0] - 10, obstacle138_center[1] - 10, obstacle138_center[0] + 10, obstacle138_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle138 = [self.canvas_widget.coords(self.obstacle138)[0] + 3, self.canvas_widget.coords(self.obstacle138)[1] + 3, self.canvas_widget.coords(self.obstacle138)[2] - 3, self.canvas_widget.coords(self.obstacle138)[3] - 3]
    obstacle139_center = self.o + np.array([pixels * 15, pixels * 15])
    self.obstacle139 = self.canvas_widget.create_rectangle(obstacle139_center[0] - 10, obstacle139_center[1] - 10, obstacle139_center[0] + 10, obstacle139_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle139 = [self.canvas_widget.coords(self.obstacle139)[0] + 3, self.canvas_widget.coords(self.obstacle139)[1] + 3, self.canvas_widget.coords(self.obstacle139)[2] - 3, self.canvas_widget.coords(self.obstacle139)[3] - 3]
    obstacle140_center = self.o + np.array([pixels * 16, pixels * 15])
    self.obstacle140 = self.canvas_widget.create_rectangle(obstacle140_center[0] - 10, obstacle140_center[1] - 10, obstacle140_center[0] + 10, obstacle140_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle140 = [self.canvas_widget.coords(self.obstacle140)[0] + 3, self.canvas_widget.coords(self.obstacle140)[1] + 3, self.canvas_widget.coords(self.obstacle140)[2] - 3, self.canvas_widget.coords(self.obstacle140)[3] - 3]
    obstacle141_center = self.o + np.array([pixels * 17, pixels * 15])
    self.obstacle141 = self.canvas_widget.create_rectangle(obstacle141_center[0] - 10, obstacle141_center[1] - 10, obstacle141_center[0] + 10, obstacle141_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle141 = [self.canvas_widget.coords(self.obstacle141)[0] + 3, self.canvas_widget.coords(self.obstacle141)[1] + 3, self.canvas_widget.coords(self.obstacle141)[2] - 3, self.canvas_widget.coords(self.obstacle141)[3] - 3]
    obstacle142_center = self.o + np.array([pixels * 18, pixels * 15])
    self.obstacle142 = self.canvas_widget.create_rectangle(obstacle142_center[0] - 10, obstacle142_center[1] - 10, obstacle142_center[0] + 10, obstacle142_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle142 = [self.canvas_widget.coords(self.obstacle142)[0] + 3, self.canvas_widget.coords(self.obstacle142)[1] + 3, self.canvas_widget.coords(self.obstacle142)[2] - 3, self.canvas_widget.coords(self.obstacle142)[3] - 3]
    obstacle143_center = self.o + np.array([pixels * 18, pixels * 14])
    self.obstacle143 = self.canvas_widget.create_rectangle(obstacle143_center[0] - 10, obstacle143_center[1] - 10, obstacle143_center[0] + 10, obstacle143_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle143 = [self.canvas_widget.coords(self.obstacle143)[0] + 3, self.canvas_widget.coords(self.obstacle143)[1] + 3, self.canvas_widget.coords(self.obstacle143)[2] - 3, self.canvas_widget.coords(self.obstacle143)[3] - 3]
    obstacle144_center = self.o + np.array([pixels * 18, pixels * 13])
    self.obstacle144 = self.canvas_widget.create_rectangle(obstacle144_center[0] - 10, obstacle144_center[1] - 10, obstacle144_center[0] + 10, obstacle144_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle144 = [self.canvas_widget.coords(self.obstacle144)[0] + 3, self.canvas_widget.coords(self.obstacle144)[1] + 3, self.canvas_widget.coords(self.obstacle144)[2] - 3, self.canvas_widget.coords(self.obstacle144)[3] - 3]
    obstacle145_center = self.o + np.array([pixels * 15, pixels * 17])
    self.obstacle145 = self.canvas_widget.create_rectangle(obstacle145_center[0] - 10, obstacle145_center[1] - 10, obstacle145_center[0] + 10, obstacle145_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle145 = [self.canvas_widget.coords(self.obstacle145)[0] + 3, self.canvas_widget.coords(self.obstacle145)[1] + 3, self.canvas_widget.coords(self.obstacle145)[2] - 3, self.canvas_widget.coords(self.obstacle145)[3] - 3]
    obstacle146_center = self.o + np.array([pixels * 14, pixels * 17])
    self.obstacle146 = self.canvas_widget.create_rectangle(obstacle146_center[0] - 10, obstacle146_center[1] - 10, obstacle146_center[0] + 10, obstacle146_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle146 = [self.canvas_widget.coords(self.obstacle146)[0] + 3, self.canvas_widget.coords(self.obstacle146)[1] + 3, self.canvas_widget.coords(self.obstacle146)[2] - 3, self.canvas_widget.coords(self.obstacle146)[3] - 3]
    obstacle147_center = self.o + np.array([pixels * 13, pixels * 17])
    self.obstacle147 = self.canvas_widget.create_rectangle(obstacle147_center[0] - 10, obstacle147_center[1] - 10, obstacle147_center[0] + 10, obstacle147_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle147 = [self.canvas_widget.coords(self.obstacle147)[0] + 3, self.canvas_widget.coords(self.obstacle147)[1] + 3, self.canvas_widget.coords(self.obstacle147)[2] - 3, self.canvas_widget.coords(self.obstacle147)[3] - 3]
    obstacle148_center = self.o + np.array([pixels * 12, pixels * 17])
    self.obstacle148 = self.canvas_widget.create_rectangle(obstacle148_center[0] - 10, obstacle148_center[1] - 10, obstacle148_center[0] + 10, obstacle148_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle148 = [self.canvas_widget.coords(self.obstacle148)[0] + 3, self.canvas_widget.coords(self.obstacle148)[1] + 3, self.canvas_widget.coords(self.obstacle148)[2] - 3, self.canvas_widget.coords(self.obstacle148)[3] - 3]
    obstacle149_center = self.o + np.array([pixels * 12, pixels * 18])
    self.obstacle149 = self.canvas_widget.create_rectangle(obstacle149_center[0] - 10, obstacle149_center[1] - 10, obstacle149_center[0] + 10, obstacle149_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle149 = [self.canvas_widget.coords(self.obstacle149)[0] + 3, self.canvas_widget.coords(self.obstacle149)[1] + 3, self.canvas_widget.coords(self.obstacle149)[2] - 3, self.canvas_widget.coords(self.obstacle149)[3] - 3]
    obstacle150_center = self.o + np.array([pixels * 12, pixels * 19])
    self.obstacle150 = self.canvas_widget.create_rectangle(obstacle150_center[0] - 10, obstacle150_center[1] - 10, obstacle150_center[0] + 10, obstacle150_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle150 = [self.canvas_widget.coords(self.obstacle150)[0] + 3, self.canvas_widget.coords(self.obstacle150)[1] + 3, self.canvas_widget.coords(self.obstacle150)[2] - 3, self.canvas_widget.coords(self.obstacle150)[3] - 3]
    obstacle151_center = self.o + np.array([pixels * 12, pixels * 20])
    self.obstacle151 = self.canvas_widget.create_rectangle(obstacle151_center[0] - 10, obstacle151_center[1] - 10, obstacle151_center[0] + 10, obstacle151_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle151 = [self.canvas_widget.coords(self.obstacle151)[0] + 3, self.canvas_widget.coords(self.obstacle151)[1] + 3, self.canvas_widget.coords(self.obstacle151)[2] - 3, self.canvas_widget.coords(self.obstacle151)[3] - 3]
    obstacle152_center = self.o + np.array([pixels * 12, pixels * 21])
    self.obstacle152 = self.canvas_widget.create_rectangle(obstacle152_center[0] - 10, obstacle152_center[1] - 10, obstacle152_center[0] + 10, obstacle152_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle152 = [self.canvas_widget.coords(self.obstacle152)[0] + 3, self.canvas_widget.coords(self.obstacle152)[1] + 3, self.canvas_widget.coords(self.obstacle152)[2] - 3, self.canvas_widget.coords(self.obstacle152)[3] - 3]
    obstacle153_center = self.o + np.array([pixels * 12, pixels * 22])
    self.obstacle153 = self.canvas_widget.create_rectangle(obstacle153_center[0] - 10, obstacle153_center[1] - 10, obstacle153_center[0] + 10, obstacle153_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle153 = [self.canvas_widget.coords(self.obstacle153)[0] + 3, self.canvas_widget.coords(self.obstacle153)[1] + 3, self.canvas_widget.coords(self.obstacle153)[2] - 3, self.canvas_widget.coords(self.obstacle153)[3] - 3]
    obstacle154_center = self.o + np.array([pixels * 12, pixels * 23])
    self.obstacle154 = self.canvas_widget.create_rectangle(obstacle154_center[0] - 10, obstacle154_center[1] - 10, obstacle154_center[0] + 10, obstacle154_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle154 = [self.canvas_widget.coords(self.obstacle154)[0] + 3, self.canvas_widget.coords(self.obstacle154)[1] + 3, self.canvas_widget.coords(self.obstacle154)[2] - 3, self.canvas_widget.coords(self.obstacle154)[3] - 3]
    obstacle155_center = self.o + np.array([pixels * 12, pixels * 24])
    self.obstacle155 = self.canvas_widget.create_rectangle(obstacle155_center[0] - 10, obstacle155_center[1] - 10, obstacle155_center[0] + 10, obstacle155_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle155 = [self.canvas_widget.coords(self.obstacle155)[0] + 3, self.canvas_widget.coords(self.obstacle155)[1] + 3, self.canvas_widget.coords(self.obstacle155)[2] - 3, self.canvas_widget.coords(self.obstacle155)[3] - 3]
    obstacle156_center = self.o + np.array([pixels * 12, pixels * 25])
    self.obstacle156 = self.canvas_widget.create_rectangle(obstacle156_center[0] - 10, obstacle156_center[1] - 10, obstacle156_center[0] + 10, obstacle156_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle156 = [self.canvas_widget.coords(self.obstacle156)[0] + 3, self.canvas_widget.coords(self.obstacle156)[1] + 3, self.canvas_widget.coords(self.obstacle156)[2] - 3, self.canvas_widget.coords(self.obstacle156)[3] - 3]
    obstacle157_center = self.o + np.array([pixels * 11, pixels * 25])
    self.obstacle157 = self.canvas_widget.create_rectangle(obstacle157_center[0] - 10, obstacle157_center[1] - 10, obstacle157_center[0] + 10, obstacle157_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle157 = [self.canvas_widget.coords(self.obstacle157)[0] + 3, self.canvas_widget.coords(self.obstacle157)[1] + 3, self.canvas_widget.coords(self.obstacle157)[2] - 3, self.canvas_widget.coords(self.obstacle157)[3] - 3]
    obstacle158_center = self.o + np.array([pixels * 10, pixels * 25])
    self.obstacle158 = self.canvas_widget.create_rectangle(obstacle158_center[0] - 10, obstacle158_center[1] - 10, obstacle158_center[0] + 10, obstacle158_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle158 = [self.canvas_widget.coords(self.obstacle158)[0] + 3, self.canvas_widget.coords(self.obstacle158)[1] + 3, self.canvas_widget.coords(self.obstacle158)[2] - 3, self.canvas_widget.coords(self.obstacle158)[3] - 3]
    obstacle159_center = self.o + np.array([pixels * 9, pixels * 25])
    self.obstacle159 = self.canvas_widget.create_rectangle(obstacle159_center[0] - 10, obstacle159_center[1] - 10, obstacle159_center[0] + 10, obstacle159_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle159 = [self.canvas_widget.coords(self.obstacle159)[0] + 3, self.canvas_widget.coords(self.obstacle159)[1] + 3, self.canvas_widget.coords(self.obstacle159)[2] - 3, self.canvas_widget.coords(self.obstacle159)[3] - 3]
    obstacle160_center = self.o + np.array([pixels * 21, pixels * 27])
    self.obstacle160 = self.canvas_widget.create_rectangle(obstacle160_center[0] - 10, obstacle160_center[1] - 10, obstacle160_center[0] + 10, obstacle160_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle160 = [self.canvas_widget.coords(self.obstacle160)[0] + 3, self.canvas_widget.coords(self.obstacle160)[1] + 3, self.canvas_widget.coords(self.obstacle160)[2] - 3, self.canvas_widget.coords(self.obstacle160)[3] - 3]
    obstacle161_center = self.o + np.array([pixels * 10, pixels * 28])
    self.obstacle161 = self.canvas_widget.create_rectangle(obstacle161_center[0] - 10, obstacle161_center[1] - 10, obstacle161_center[0] + 10, obstacle161_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle161 = [self.canvas_widget.coords(self.obstacle161)[0] + 3, self.canvas_widget.coords(self.obstacle161)[1] + 3, self.canvas_widget.coords(self.obstacle161)[2] - 3, self.canvas_widget.coords(self.obstacle161)[3] - 3]
    obstacle162_center = self.o + np.array([pixels * 10, pixels * 27])
    self.obstacle162 = self.canvas_widget.create_rectangle(obstacle162_center[0] - 10, obstacle162_center[1] - 10, obstacle162_center[0] + 10, obstacle162_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle162 = [self.canvas_widget.coords(self.obstacle162)[0] + 3, self.canvas_widget.coords(self.obstacle162)[1] + 3, self.canvas_widget.coords(self.obstacle162)[2] - 3, self.canvas_widget.coords(self.obstacle162)[3] - 3]
    obstacle163_center = self.o + np.array([pixels * 11, pixels * 27])
    self.obstacle163 = self.canvas_widget.create_rectangle(obstacle163_center[0] - 10, obstacle163_center[1] - 10, obstacle163_center[0] + 10, obstacle163_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle163 = [self.canvas_widget.coords(self.obstacle163)[0] + 3, self.canvas_widget.coords(self.obstacle163)[1] + 3, self.canvas_widget.coords(self.obstacle163)[2] - 3, self.canvas_widget.coords(self.obstacle163)[3] - 3]
    obstacle164_center = self.o + np.array([pixels * 12, pixels * 27])
    self.obstacle164 = self.canvas_widget.create_rectangle(obstacle164_center[0] - 10, obstacle164_center[1] - 10, obstacle164_center[0] + 10, obstacle164_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle164 = [self.canvas_widget.coords(self.obstacle164)[0] + 3, self.canvas_widget.coords(self.obstacle164)[1] + 3, self.canvas_widget.coords(self.obstacle164)[2] - 3, self.canvas_widget.coords(self.obstacle164)[3] - 3]
    obstacle165_center = self.o + np.array([pixels * 13, pixels * 27])
    self.obstacle165 = self.canvas_widget.create_rectangle(obstacle165_center[0] - 10, obstacle165_center[1] - 10, obstacle165_center[0] + 10, obstacle165_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle165 = [self.canvas_widget.coords(self.obstacle165)[0] + 3, self.canvas_widget.coords(self.obstacle165)[1] + 3, self.canvas_widget.coords(self.obstacle165)[2] - 3, self.canvas_widget.coords(self.obstacle165)[3] - 3]
    obstacle166_center = self.o + np.array([pixels * 14, pixels * 27])
    self.obstacle166 = self.canvas_widget.create_rectangle(obstacle166_center[0] - 10, obstacle166_center[1] - 10, obstacle166_center[0] + 10, obstacle166_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle166 = [self.canvas_widget.coords(self.obstacle166)[0] + 3, self.canvas_widget.coords(self.obstacle166)[1] + 3, self.canvas_widget.coords(self.obstacle166)[2] - 3, self.canvas_widget.coords(self.obstacle166)[3] - 3]
    obstacle167_center = self.o + np.array([pixels * 15, pixels * 27])
    self.obstacle167 = self.canvas_widget.create_rectangle(obstacle167_center[0] - 10, obstacle167_center[1] - 10, obstacle167_center[0] + 10, obstacle167_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle167 = [self.canvas_widget.coords(self.obstacle167)[0] + 3, self.canvas_widget.coords(self.obstacle167)[1] + 3, self.canvas_widget.coords(self.obstacle167)[2] - 3, self.canvas_widget.coords(self.obstacle167)[3] - 3]
    obstacle168_center = self.o + np.array([pixels * 16, pixels * 27])
    self.obstacle168 = self.canvas_widget.create_rectangle(obstacle168_center[0] - 10, obstacle168_center[1] - 10, obstacle168_center[0] + 10, obstacle168_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle168 = [self.canvas_widget.coords(self.obstacle168)[0] + 3, self.canvas_widget.coords(self.obstacle168)[1] + 3, self.canvas_widget.coords(self.obstacle168)[2] - 3, self.canvas_widget.coords(self.obstacle168)[3] - 3]
    obstacle169_center = self.o + np.array([pixels * 16, pixels * 28])
    self.obstacle169 = self.canvas_widget.create_rectangle(obstacle169_center[0] - 10, obstacle169_center[1] - 10, obstacle169_center[0] + 10, obstacle169_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle169 = [self.canvas_widget.coords(self.obstacle169)[0] + 3, self.canvas_widget.coords(self.obstacle169)[1] + 3, self.canvas_widget.coords(self.obstacle169)[2] - 3, self.canvas_widget.coords(self.obstacle169)[3] - 3]
    obstacle170_center = self.o + np.array([pixels * 14, pixels * 24])
    self.obstacle170 = self.canvas_widget.create_rectangle(obstacle170_center[0] - 10, obstacle170_center[1] - 10, obstacle170_center[0] + 10, obstacle170_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle170 = [self.canvas_widget.coords(self.obstacle170)[0] + 3, self.canvas_widget.coords(self.obstacle170)[1] + 3, self.canvas_widget.coords(self.obstacle170)[2] - 3, self.canvas_widget.coords(self.obstacle170)[3] - 3]
    obstacle171_center = self.o + np.array([pixels * 15, pixels * 24])
    self.obstacle171 = self.canvas_widget.create_rectangle(obstacle171_center[0] - 10, obstacle171_center[1] - 10, obstacle171_center[0] + 10, obstacle171_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle171 = [self.canvas_widget.coords(self.obstacle171)[0] + 3, self.canvas_widget.coords(self.obstacle171)[1] + 3, self.canvas_widget.coords(self.obstacle171)[2] - 3, self.canvas_widget.coords(self.obstacle171)[3] - 3]
    obstacle172_center = self.o + np.array([pixels * 16, pixels * 24])
    self.obstacle172 = self.canvas_widget.create_rectangle(obstacle172_center[0] - 10, obstacle172_center[1] - 10, obstacle172_center[0] + 10, obstacle172_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle172 = [self.canvas_widget.coords(self.obstacle172)[0] + 3, self.canvas_widget.coords(self.obstacle172)[1] + 3, self.canvas_widget.coords(self.obstacle172)[2] - 3, self.canvas_widget.coords(self.obstacle172)[3] - 3]
    obstacle173_center = self.o + np.array([pixels * 17, pixels * 24])
    self.obstacle173 = self.canvas_widget.create_rectangle(obstacle173_center[0] - 10, obstacle173_center[1] - 10, obstacle173_center[0] + 10, obstacle173_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle173 = [self.canvas_widget.coords(self.obstacle173)[0] + 3, self.canvas_widget.coords(self.obstacle173)[1] + 3, self.canvas_widget.coords(self.obstacle173)[2] - 3, self.canvas_widget.coords(self.obstacle173)[3] - 3]
    obstacle174_center = self.o + np.array([pixels * 17, pixels * 23])
    self.obstacle174 = self.canvas_widget.create_rectangle(obstacle174_center[0] - 10, obstacle174_center[1] - 10, obstacle174_center[0] + 10, obstacle174_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle174 = [self.canvas_widget.coords(self.obstacle174)[0] + 3, self.canvas_widget.coords(self.obstacle174)[1] + 3, self.canvas_widget.coords(self.obstacle174)[2] - 3, self.canvas_widget.coords(self.obstacle174)[3] - 3]
    obstacle175_center = self.o + np.array([pixels * 17, pixels * 22])
    self.obstacle175 = self.canvas_widget.create_rectangle(obstacle175_center[0] - 10, obstacle175_center[1] - 10, obstacle175_center[0] + 10, obstacle175_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle175 = [self.canvas_widget.coords(self.obstacle175)[0] + 3, self.canvas_widget.coords(self.obstacle175)[1] + 3, self.canvas_widget.coords(self.obstacle175)[2] - 3, self.canvas_widget.coords(self.obstacle175)[3] - 3]
    obstacle176_center = self.o + np.array([pixels * 17, pixels * 21])
    self.obstacle176 = self.canvas_widget.create_rectangle(obstacle176_center[0] - 10, obstacle176_center[1] - 10, obstacle176_center[0] + 10, obstacle176_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle176 = [self.canvas_widget.coords(self.obstacle176)[0] + 3, self.canvas_widget.coords(self.obstacle176)[1] + 3, self.canvas_widget.coords(self.obstacle176)[2] - 3, self.canvas_widget.coords(self.obstacle176)[3] - 3]
    obstacle177_center = self.o + np.array([pixels * 17, pixels * 20])
    self.obstacle177 = self.canvas_widget.create_rectangle(obstacle177_center[0] - 10, obstacle177_center[1] - 10, obstacle177_center[0] + 10, obstacle177_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle177 = [self.canvas_widget.coords(self.obstacle177)[0] + 3, self.canvas_widget.coords(self.obstacle177)[1] + 3, self.canvas_widget.coords(self.obstacle177)[2] - 3, self.canvas_widget.coords(self.obstacle177)[3] - 3]
    obstacle178_center = self.o + np.array([pixels * 17, pixels * 19])
    self.obstacle178 = self.canvas_widget.create_rectangle(obstacle178_center[0] - 10, obstacle178_center[1] - 10, obstacle178_center[0] + 10, obstacle178_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle178 = [self.canvas_widget.coords(self.obstacle178)[0] + 3, self.canvas_widget.coords(self.obstacle178)[1] + 3, self.canvas_widget.coords(self.obstacle178)[2] - 3, self.canvas_widget.coords(self.obstacle178)[3] - 3]
    obstacle179_center = self.o + np.array([pixels * 17, pixels * 18])
    self.obstacle179 = self.canvas_widget.create_rectangle(obstacle179_center[0] - 10, obstacle179_center[1] - 10, obstacle179_center[0] + 10, obstacle179_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle179 = [self.canvas_widget.coords(self.obstacle179)[0] + 3, self.canvas_widget.coords(self.obstacle179)[1] + 3, self.canvas_widget.coords(self.obstacle179)[2] - 3, self.canvas_widget.coords(self.obstacle179)[3] - 3]
    obstacle180_center = self.o + np.array([pixels * 18, pixels * 18])
    self.obstacle180 = self.canvas_widget.create_rectangle(obstacle180_center[0] - 10, obstacle180_center[1] - 10, obstacle180_center[0] + 10, obstacle180_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle180 = [self.canvas_widget.coords(self.obstacle180)[0] + 3, self.canvas_widget.coords(self.obstacle180)[1] + 3, self.canvas_widget.coords(self.obstacle180)[2] - 3, self.canvas_widget.coords(self.obstacle180)[3] - 3]
    obstacle181_center = self.o + np.array([pixels * 19, pixels * 18])
    self.obstacle181 = self.canvas_widget.create_rectangle(obstacle181_center[0] - 10, obstacle181_center[1] - 10, obstacle181_center[0] + 10, obstacle181_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle181 = [self.canvas_widget.coords(self.obstacle181)[0] + 3, self.canvas_widget.coords(self.obstacle181)[1] + 3, self.canvas_widget.coords(self.obstacle181)[2] - 3, self.canvas_widget.coords(self.obstacle181)[3] - 3]
    obstacle182_center = self.o + np.array([pixels * 20, pixels * 18])
    self.obstacle182 = self.canvas_widget.create_rectangle(obstacle182_center[0] - 10, obstacle182_center[1] - 10, obstacle182_center[0] + 10, obstacle182_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle182 = [self.canvas_widget.coords(self.obstacle182)[0] + 3, self.canvas_widget.coords(self.obstacle182)[1] + 3, self.canvas_widget.coords(self.obstacle182)[2] - 3, self.canvas_widget.coords(self.obstacle182)[3] - 3]
    obstacle183_center = self.o + np.array([pixels * 21, pixels * 18])
    self.obstacle183 = self.canvas_widget.create_rectangle(obstacle183_center[0] - 10, obstacle183_center[1] - 10, obstacle183_center[0] + 10, obstacle183_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle183 = [self.canvas_widget.coords(self.obstacle183)[0] + 3, self.canvas_widget.coords(self.obstacle183)[1] + 3, self.canvas_widget.coords(self.obstacle183)[2] - 3, self.canvas_widget.coords(self.obstacle183)[3] - 3]
    obstacle184_center = self.o + np.array([pixels * 22, pixels * 18])
    self.obstacle184 = self.canvas_widget.create_rectangle(obstacle184_center[0] - 10, obstacle184_center[1] - 10, obstacle184_center[0] + 10, obstacle184_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle184 = [self.canvas_widget.coords(self.obstacle184)[0] + 3, self.canvas_widget.coords(self.obstacle184)[1] + 3, self.canvas_widget.coords(self.obstacle184)[2] - 3, self.canvas_widget.coords(self.obstacle184)[3] - 3]
    obstacle185_center = self.o + np.array([pixels * 23, pixels * 18])
    self.obstacle185 = self.canvas_widget.create_rectangle(obstacle185_center[0] - 10, obstacle185_center[1] - 10, obstacle185_center[0] + 10, obstacle185_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle185 = [self.canvas_widget.coords(self.obstacle185)[0] + 3, self.canvas_widget.coords(self.obstacle185)[1] + 3, self.canvas_widget.coords(self.obstacle185)[2] - 3, self.canvas_widget.coords(self.obstacle185)[3] - 3]
    obstacle186_center = self.o + np.array([pixels * 23, pixels * 18])
    self.obstacle186 = self.canvas_widget.create_rectangle(obstacle186_center[0] - 10, obstacle186_center[1] - 10, obstacle186_center[0] + 10, obstacle186_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle186 = [self.canvas_widget.coords(self.obstacle186)[0] + 3, self.canvas_widget.coords(self.obstacle186)[1] + 3, self.canvas_widget.coords(self.obstacle186)[2] - 3, self.canvas_widget.coords(self.obstacle186)[3] - 3]
    obstacle187_center = self.o + np.array([pixels * 23, pixels * 19])
    self.obstacle187 = self.canvas_widget.create_rectangle(obstacle187_center[0] - 10, obstacle187_center[1] - 10, obstacle187_center[0] + 10, obstacle187_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle187 = [self.canvas_widget.coords(self.obstacle187)[0] + 3, self.canvas_widget.coords(self.obstacle187)[1] + 3, self.canvas_widget.coords(self.obstacle187)[2] - 3, self.canvas_widget.coords(self.obstacle187)[3] - 3]
    obstacle188_center = self.o + np.array([pixels * 23, pixels * 20])
    self.obstacle188 = self.canvas_widget.create_rectangle(obstacle188_center[0] - 10, obstacle188_center[1] - 10, obstacle188_center[0] + 10, obstacle188_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle188 = [self.canvas_widget.coords(self.obstacle188)[0] + 3, self.canvas_widget.coords(self.obstacle188)[1] + 3, self.canvas_widget.coords(self.obstacle188)[2] - 3, self.canvas_widget.coords(self.obstacle188)[3] - 3]
    obstacle189_center = self.o + np.array([pixels * 23, pixels * 21])
    self.obstacle189 = self.canvas_widget.create_rectangle(obstacle189_center[0] - 10, obstacle189_center[1] - 10, obstacle189_center[0] + 10, obstacle189_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle189 = [self.canvas_widget.coords(self.obstacle189)[0] + 3, self.canvas_widget.coords(self.obstacle189)[1] + 3, self.canvas_widget.coords(self.obstacle189)[2] - 3, self.canvas_widget.coords(self.obstacle189)[3] - 3]
    obstacle190_center = self.o + np.array([pixels * 23, pixels * 22])
    self.obstacle190 = self.canvas_widget.create_rectangle(obstacle190_center[0] - 10, obstacle190_center[1] - 10, obstacle190_center[0] + 10, obstacle190_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle190 = [self.canvas_widget.coords(self.obstacle190)[0] + 3, self.canvas_widget.coords(self.obstacle190)[1] + 3, self.canvas_widget.coords(self.obstacle190)[2] - 3, self.canvas_widget.coords(self.obstacle190)[3] - 3]
    obstacle191_center = self.o + np.array([pixels * 23, pixels * 23])
    self.obstacle191 = self.canvas_widget.create_rectangle(obstacle191_center[0] - 10, obstacle191_center[1] - 10, obstacle191_center[0] + 10, obstacle191_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle191 = [self.canvas_widget.coords(self.obstacle191)[0] + 3, self.canvas_widget.coords(self.obstacle191)[1] + 3, self.canvas_widget.coords(self.obstacle191)[2] - 3, self.canvas_widget.coords(self.obstacle191)[3] - 3]
    obstacle192_center = self.o + np.array([pixels * 23, pixels * 24])
    self.obstacle192 = self.canvas_widget.create_rectangle(obstacle192_center[0] - 10, obstacle192_center[1] - 10, obstacle192_center[0] + 10, obstacle192_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle192 = [self.canvas_widget.coords(self.obstacle192)[0] + 3, self.canvas_widget.coords(self.obstacle192)[1] + 3, self.canvas_widget.coords(self.obstacle192)[2] - 3, self.canvas_widget.coords(self.obstacle192)[3] - 3]
    obstacle193_center = self.o + np.array([pixels * 23, pixels * 25])
    self.obstacle193 = self.canvas_widget.create_rectangle(obstacle193_center[0] - 10, obstacle193_center[1] - 10, obstacle193_center[0] + 10, obstacle193_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle193 = [self.canvas_widget.coords(self.obstacle193)[0] + 3, self.canvas_widget.coords(self.obstacle193)[1] + 3, self.canvas_widget.coords(self.obstacle193)[2] - 3, self.canvas_widget.coords(self.obstacle193)[3] - 3]
    obstacle194_center = self.o + np.array([pixels * 23, pixels * 26])
    self.obstacle194 = self.canvas_widget.create_rectangle(obstacle194_center[0] - 10, obstacle194_center[1] - 10, obstacle194_center[0] + 10, obstacle194_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle194 = [self.canvas_widget.coords(self.obstacle194)[0] + 3, self.canvas_widget.coords(self.obstacle194)[1] + 3, self.canvas_widget.coords(self.obstacle194)[2] - 3, self.canvas_widget.coords(self.obstacle194)[3] - 3]
    obstacle195_center = self.o + np.array([pixels * 23, pixels * 27])
    self.obstacle195 = self.canvas_widget.create_rectangle(obstacle195_center[0] - 10, obstacle195_center[1] - 10, obstacle195_center[0] + 10, obstacle195_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle195 = [self.canvas_widget.coords(self.obstacle195)[0] + 3, self.canvas_widget.coords(self.obstacle195)[1] + 3, self.canvas_widget.coords(self.obstacle195)[2] - 3, self.canvas_widget.coords(self.obstacle195)[3] - 3]
    obstacle196_center = self.o + np.array([pixels * 22, pixels * 27])
    self.obstacle196 = self.canvas_widget.create_rectangle(obstacle196_center[0] - 10, obstacle196_center[1] - 10, obstacle196_center[0] + 10, obstacle196_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle196 = [self.canvas_widget.coords(self.obstacle196)[0] + 3, self.canvas_widget.coords(self.obstacle196)[1] + 3, self.canvas_widget.coords(self.obstacle196)[2] - 3, self.canvas_widget.coords(self.obstacle196)[3] - 3]
    obstacle197_center = self.o + np.array([pixels * 21, pixels * 16])
    self.obstacle197 = self.canvas_widget.create_rectangle(obstacle197_center[0] - 10, obstacle197_center[1] - 10, obstacle197_center[0] + 10, obstacle197_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle197 = [self.canvas_widget.coords(self.obstacle197)[0] + 3, self.canvas_widget.coords(self.obstacle197)[1] + 3, self.canvas_widget.coords(self.obstacle197)[2] - 3, self.canvas_widget.coords(self.obstacle197)[3] - 3]
    obstacle198_center = self.o + np.array([pixels * 22, pixels * 16])
    self.obstacle198 = self.canvas_widget.create_rectangle(obstacle198_center[0] - 10, obstacle198_center[1] - 10, obstacle198_center[0] + 10, obstacle198_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle198 = [self.canvas_widget.coords(self.obstacle198)[0] + 3, self.canvas_widget.coords(self.obstacle198)[1] + 3, self.canvas_widget.coords(self.obstacle198)[2] - 3, self.canvas_widget.coords(self.obstacle198)[3] - 3]
    obstacle199_center = self.o + np.array([pixels * 23, pixels * 16])
    self.obstacle199 = self.canvas_widget.create_rectangle(obstacle199_center[0] - 10, obstacle199_center[1] - 10, obstacle199_center[0] + 10, obstacle199_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle199 = [self.canvas_widget.coords(self.obstacle199)[0] + 3, self.canvas_widget.coords(self.obstacle199)[1] + 3, self.canvas_widget.coords(self.obstacle199)[2] - 3, self.canvas_widget.coords(self.obstacle199)[3] - 3]
    obstacle200_center = self.o + np.array([pixels * 24, pixels * 16])
    self.obstacle200 = self.canvas_widget.create_rectangle(obstacle200_center[0] - 10, obstacle200_center[1] - 10, obstacle200_center[0] + 10, obstacle200_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle200 = [self.canvas_widget.coords(self.obstacle200)[0] + 3, self.canvas_widget.coords(self.obstacle200)[1] + 3, self.canvas_widget.coords(self.obstacle200)[2] - 3, self.canvas_widget.coords(self.obstacle200)[3] - 3]
    obstacle201_center = self.o + np.array([pixels * 25, pixels * 16])
    self.obstacle201 = self.canvas_widget.create_rectangle(obstacle201_center[0] - 10, obstacle201_center[1] - 10, obstacle201_center[0] + 10, obstacle201_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle201 = [self.canvas_widget.coords(self.obstacle201)[0] + 3, self.canvas_widget.coords(self.obstacle201)[1] + 3, self.canvas_widget.coords(self.obstacle201)[2] - 3, self.canvas_widget.coords(self.obstacle201)[3] - 3]
    obstacle202_center = self.o + np.array([pixels * 26, pixels * 17])
    self.obstacle202 = self.canvas_widget.create_rectangle(obstacle202_center[0] - 10, obstacle202_center[1] - 10, obstacle202_center[0] + 10, obstacle202_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle202 = [self.canvas_widget.coords(self.obstacle202)[0] + 3, self.canvas_widget.coords(self.obstacle202)[1] + 3, self.canvas_widget.coords(self.obstacle202)[2] - 3, self.canvas_widget.coords(self.obstacle202)[3] - 3]
    obstacle203_center = self.o + np.array([pixels * 26, pixels * 16])
    self.obstacle203 = self.canvas_widget.create_rectangle(obstacle203_center[0] - 10, obstacle203_center[1] - 10, obstacle203_center[0] + 10, obstacle203_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle203 = [self.canvas_widget.coords(self.obstacle203)[0] + 3, self.canvas_widget.coords(self.obstacle203)[1] + 3, self.canvas_widget.coords(self.obstacle203)[2] - 3, self.canvas_widget.coords(self.obstacle203)[3] - 3]
    obstacle204_center = self.o + np.array([pixels * 26, pixels * 18])
    self.obstacle204 = self.canvas_widget.create_rectangle(obstacle204_center[0] - 10, obstacle204_center[1] - 10, obstacle204_center[0] + 10, obstacle204_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle204 = [self.canvas_widget.coords(self.obstacle204)[0] + 3, self.canvas_widget.coords(self.obstacle204)[1] + 3, self.canvas_widget.coords(self.obstacle204)[2] - 3, self.canvas_widget.coords(self.obstacle204)[3] - 3]
    obstacle205_center = self.o + np.array([pixels * 27, pixels * 18])
    self.obstacle205 = self.canvas_widget.create_rectangle(obstacle205_center[0] - 10, obstacle205_center[1] - 10, obstacle205_center[0] + 10, obstacle205_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle205 = [self.canvas_widget.coords(self.obstacle205)[0] + 3, self.canvas_widget.coords(self.obstacle205)[1] + 3, self.canvas_widget.coords(self.obstacle205)[2] - 3, self.canvas_widget.coords(self.obstacle205)[3] - 3]
    obstacle206_center = self.o + np.array([pixels * 28, pixels * 18])
    self.obstacle206 = self.canvas_widget.create_rectangle(obstacle206_center[0] - 10, obstacle206_center[1] - 10, obstacle206_center[0] + 10, obstacle206_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle206 = [self.canvas_widget.coords(self.obstacle206)[0] + 3, self.canvas_widget.coords(self.obstacle206)[1] + 3, self.canvas_widget.coords(self.obstacle206)[2] - 3, self.canvas_widget.coords(self.obstacle206)[3] - 3]
    obstacle207_center = self.o + np.array([pixels * 27, pixels * 27])
    self.obstacle207 = self.canvas_widget.create_rectangle(obstacle207_center[0] - 10, obstacle207_center[1] - 10, obstacle207_center[0] + 10, obstacle207_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle207 = [self.canvas_widget.coords(self.obstacle207)[0] + 3, self.canvas_widget.coords(self.obstacle207)[1] + 3, self.canvas_widget.coords(self.obstacle207)[2] - 3, self.canvas_widget.coords(self.obstacle207)[3] - 3]
    obstacle208_center = self.o + np.array([pixels * 28, pixels * 27])
    self.obstacle208 = self.canvas_widget.create_rectangle(obstacle208_center[0] - 10, obstacle208_center[1] - 10, obstacle208_center[0] + 10, obstacle208_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle208 = [self.canvas_widget.coords(self.obstacle208)[0] + 3, self.canvas_widget.coords(self.obstacle208)[1] + 3, self.canvas_widget.coords(self.obstacle208)[2] - 3, self.canvas_widget.coords(self.obstacle208)[3] - 3]
    obstacle209_center = self.o + np.array([pixels * 28, pixels * 26])
    self.obstacle209 = self.canvas_widget.create_rectangle(obstacle209_center[0] - 10, obstacle209_center[1] - 10, obstacle209_center[0] + 10, obstacle209_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle209 = [self.canvas_widget.coords(self.obstacle209)[0] + 3, self.canvas_widget.coords(self.obstacle209)[1] + 3, self.canvas_widget.coords(self.obstacle209)[2] - 3, self.canvas_widget.coords(self.obstacle209)[3] - 3]
    obstacle210_center = self.o + np.array([pixels * 28, pixels * 25])
    self.obstacle210 = self.canvas_widget.create_rectangle(obstacle210_center[0] - 10, obstacle210_center[1] - 10, obstacle210_center[0] + 10, obstacle210_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle210 = [self.canvas_widget.coords(self.obstacle210)[0] + 3, self.canvas_widget.coords(self.obstacle210)[1] + 3, self.canvas_widget.coords(self.obstacle210)[2] - 3, self.canvas_widget.coords(self.obstacle210)[3] - 3]
    obstacle211_center = self.o + np.array([pixels * 28, pixels * 24])
    self.obstacle211 = self.canvas_widget.create_rectangle(obstacle211_center[0] - 10, obstacle211_center[1] - 10, obstacle211_center[0] + 10, obstacle211_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle211 = [self.canvas_widget.coords(self.obstacle211)[0] + 3, self.canvas_widget.coords(self.obstacle211)[1] + 3, self.canvas_widget.coords(self.obstacle211)[2] - 3, self.canvas_widget.coords(self.obstacle211)[3] - 3]
    obstacle212_center = self.o + np.array([pixels * 27, pixels * 24])
    self.obstacle212 = self.canvas_widget.create_rectangle(obstacle212_center[0] - 10, obstacle212_center[1] - 10, obstacle212_center[0] + 10, obstacle212_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle212 = [self.canvas_widget.coords(self.obstacle212)[0] + 3, self.canvas_widget.coords(self.obstacle212)[1] + 3, self.canvas_widget.coords(self.obstacle212)[2] - 3, self.canvas_widget.coords(self.obstacle212)[3] - 3]
    self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
    flag_center = self.o + np.array([pixels * 20, pixels * 20])
    self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
    self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
    self.canvas_widget.pack()

class Environment(tk.Tk, object):

    def __init__(self):
        super(Environment, self).__init__()
        self.action_space = ['up', 'down', 'left', 'right']
        self.n_actions = len(self.action_space)
        self.title('RL Sarsa. Sichkar Valentyn')
        self.geometry('{0}x{1}'.format(env_height * pixels, env_height * pixels))
        self.build_environment()
        self.d = {}
        self.f = {}
        self.i = 0
        self.c = True
        self.longest = 0
        self.shortest = 0

    def build_environment(self):
        self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
        for column in range(0, env_width * pixels, pixels):
            x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        for row in range(0, env_height * pixels, pixels):
            x0, y0, x1, y1 = (0, row, env_height * pixels, row)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        img_obstacle1 = Image.open('images/road_closed1.png')
        self.obstacle1_object = ImageTk.PhotoImage(img_obstacle1)
        img_obstacle2 = Image.open('images/tree1.png')
        self.obstacle2_object = ImageTk.PhotoImage(img_obstacle2)
        img_obstacle3 = Image.open('images/tree2.png')
        self.obstacle3_object = ImageTk.PhotoImage(img_obstacle3)
        img_obstacle4 = Image.open('images/building1.png')
        self.obstacle4_object = ImageTk.PhotoImage(img_obstacle4)
        img_obstacle5 = Image.open('images/building2.png')
        self.obstacle5_object = ImageTk.PhotoImage(img_obstacle5)
        img_obstacle6 = Image.open('images/road_closed2.png')
        self.obstacle6_object = ImageTk.PhotoImage(img_obstacle6)
        img_obstacle7 = Image.open('images/road_closed3.png')
        self.obstacle7_object = ImageTk.PhotoImage(img_obstacle7)
        img_obstacle8 = Image.open('images/traffic_lights.png')
        self.obstacle8_object = ImageTk.PhotoImage(img_obstacle8)
        img_obstacle9 = Image.open('images/pedestrian.png')
        self.obstacle9_object = ImageTk.PhotoImage(img_obstacle9)
        img_obstacle10 = Image.open('images/shop.png')
        self.obstacle10_object = ImageTk.PhotoImage(img_obstacle10)
        img_obstacle11 = Image.open('images/bank1.png')
        self.obstacle11_object = ImageTk.PhotoImage(img_obstacle11)
        img_obstacle12 = Image.open('images/bank2.png')
        self.obstacle12_object = ImageTk.PhotoImage(img_obstacle12)
        self.obstacle1 = self.canvas_widget.create_image(pixels * 3, pixels * 4, anchor='nw', image=self.obstacle2_object)
        self.obstacle2 = self.canvas_widget.create_image(0, pixels * 2, anchor='nw', image=self.obstacle6_object)
        self.obstacle3 = self.canvas_widget.create_image(pixels, 0, anchor='nw', image=self.obstacle5_object)
        self.obstacle4 = self.canvas_widget.create_image(pixels * 3, pixels * 2, anchor='nw', image=self.obstacle2_object)
        self.obstacle5 = self.canvas_widget.create_image(pixels * 4, 0, anchor='nw', image=self.obstacle12_object)
        self.obstacle6 = self.canvas_widget.create_image(pixels * 5, pixels * 3, anchor='nw', image=self.obstacle7_object)
        self.obstacle7 = self.canvas_widget.create_image(pixels * 7, pixels * 3, anchor='nw', image=self.obstacle9_object)
        self.obstacle8 = self.canvas_widget.create_image(pixels * 6, pixels, anchor='nw', image=self.obstacle10_object)
        self.obstacle9 = self.canvas_widget.create_image(pixels * 5, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle10 = self.canvas_widget.create_image(pixels * 6, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle11 = self.canvas_widget.create_image(pixels * 5, pixels * 6, anchor='nw', image=self.obstacle4_object)
        self.obstacle12 = self.canvas_widget.create_image(pixels * 5, pixels * 7, anchor='nw', image=self.obstacle4_object)
        self.obstacle13 = self.canvas_widget.create_image(0, pixels * 8, anchor='nw', image=self.obstacle3_object)
        self.obstacle14 = self.canvas_widget.create_image(pixels * 3, pixels * 7, anchor='nw', image=self.obstacle8_object)
        self.obstacle15 = self.canvas_widget.create_image(0, pixels * 4, anchor='nw', image=self.obstacle1_object)
        self.obstacle16 = self.canvas_widget.create_image(pixels * 8, 0, anchor='nw', image=self.obstacle3_object)
        self.obstacle17 = self.canvas_widget.create_image(pixels * 7, pixels * 7, anchor='nw', image=self.obstacle4_object)
        self.obstacle18 = self.canvas_widget.create_image(pixels, pixels * 6, anchor='nw', image=self.obstacle11_object)
        self.obstacle19 = self.canvas_widget.create_image(pixels * 8, pixels * 3, anchor='nw', image=self.obstacle8_object)
        self.obstacle20 = self.canvas_widget.create_image(pixels * 7, pixels * 6, anchor='nw', image=self.obstacle4_object)
        self.obstacle21 = self.canvas_widget.create_image(pixels * 7, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle22 = self.canvas_widget.create_image(pixels * 2, pixels * 3, anchor='nw', image=self.obstacle2_object)
        img_flag = Image.open('images/flag.png')
        self.flag_object = ImageTk.PhotoImage(img_flag)
        self.flag = self.canvas_widget.create_image(pixels * 6, pixels * 6, anchor='nw', image=self.flag_object)
        img_robot = Image.open('images/agent1.png')
        self.robot = ImageTk.PhotoImage(img_robot)
        self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
        self.canvas_widget.pack()

    def reset(self):
        self.update()
        self.canvas_widget.delete(self.agent)
        self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
        self.d = {}
        self.i = 0
        return self.canvas_widget.coords(self.agent)

    def step(self, action):
        state = self.canvas_widget.coords(self.agent)
        base_action = np.array([0, 0])
        if action == 0:
            if state[1] >= pixels:
                base_action[1] -= pixels
        elif action == 1:
            if state[1] < (env_height - 1) * pixels:
                base_action[1] += pixels
        elif action == 2:
            if state[0] < (env_width - 1) * pixels:
                base_action[0] += pixels
        elif action == 3:
            if state[0] >= pixels:
                base_action[0] -= pixels
        self.canvas_widget.move(self.agent, base_action[0], base_action[1])
        self.d[self.i] = self.canvas_widget.coords(self.agent)
        next_state = self.d[self.i]
        self.i += 1
        if next_state == self.canvas_widget.coords(self.flag):
            reward = 1
            done = True
            next_state = 'goal'
            if self.c == True:
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
                self.c = False
                self.longest = len(self.d)
                self.shortest = len(self.d)
            if len(self.d) < len(self.f):
                self.shortest = len(self.d)
                self.f = {}
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
            if len(self.d) > self.longest:
                self.longest = len(self.d)
        elif next_state in [self.canvas_widget.coords(self.obstacle1), self.canvas_widget.coords(self.obstacle2), self.canvas_widget.coords(self.obstacle3), self.canvas_widget.coords(self.obstacle4), self.canvas_widget.coords(self.obstacle5), self.canvas_widget.coords(self.obstacle6), self.canvas_widget.coords(self.obstacle7), self.canvas_widget.coords(self.obstacle8), self.canvas_widget.coords(self.obstacle9), self.canvas_widget.coords(self.obstacle10), self.canvas_widget.coords(self.obstacle11), self.canvas_widget.coords(self.obstacle12), self.canvas_widget.coords(self.obstacle13), self.canvas_widget.coords(self.obstacle14), self.canvas_widget.coords(self.obstacle15), self.canvas_widget.coords(self.obstacle16), self.canvas_widget.coords(self.obstacle17), self.canvas_widget.coords(self.obstacle18), self.canvas_widget.coords(self.obstacle19), self.canvas_widget.coords(self.obstacle20), self.canvas_widget.coords(self.obstacle21), self.canvas_widget.coords(self.obstacle22)]:
            reward = -1
            done = True
            next_state = 'obstacle'
            self.d = {}
            self.i = 0
        else:
            reward = 0
            done = False
        return (next_state, reward, done)

    def render(self):
        self.update()

    def final(self):
        self.canvas_widget.delete(self.agent)
        print('The shortest route:', self.shortest)
        print('The longest route:', self.longest)
        origin = np.array([20, 20])
        self.initial_point = self.canvas_widget.create_oval(origin[0] - 5, origin[1] - 5, origin[0] + 5, origin[1] + 5, fill='blue', outline='blue')
        for j in range(len(self.f)):
            print(self.f[j])
            self.track = self.canvas_widget.create_oval(self.f[j][0] + origin[0] - 5, self.f[j][1] + origin[0] - 5, self.f[j][0] + origin[0] + 5, self.f[j][1] + origin[0] + 5, fill='blue', outline='blue')
            a[j] = self.f[j]

def build_environment(self):
    self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
    for column in range(0, env_width * pixels, pixels):
        x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    for row in range(0, env_height * pixels, pixels):
        x0, y0, x1, y1 = (0, row, env_height * pixels, row)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    img_obstacle1 = Image.open('images/road_closed1.png')
    self.obstacle1_object = ImageTk.PhotoImage(img_obstacle1)
    img_obstacle2 = Image.open('images/tree1.png')
    self.obstacle2_object = ImageTk.PhotoImage(img_obstacle2)
    img_obstacle3 = Image.open('images/tree2.png')
    self.obstacle3_object = ImageTk.PhotoImage(img_obstacle3)
    img_obstacle4 = Image.open('images/building1.png')
    self.obstacle4_object = ImageTk.PhotoImage(img_obstacle4)
    img_obstacle5 = Image.open('images/building2.png')
    self.obstacle5_object = ImageTk.PhotoImage(img_obstacle5)
    img_obstacle6 = Image.open('images/road_closed2.png')
    self.obstacle6_object = ImageTk.PhotoImage(img_obstacle6)
    img_obstacle7 = Image.open('images/road_closed3.png')
    self.obstacle7_object = ImageTk.PhotoImage(img_obstacle7)
    img_obstacle8 = Image.open('images/traffic_lights.png')
    self.obstacle8_object = ImageTk.PhotoImage(img_obstacle8)
    img_obstacle9 = Image.open('images/pedestrian.png')
    self.obstacle9_object = ImageTk.PhotoImage(img_obstacle9)
    img_obstacle10 = Image.open('images/shop.png')
    self.obstacle10_object = ImageTk.PhotoImage(img_obstacle10)
    img_obstacle11 = Image.open('images/bank1.png')
    self.obstacle11_object = ImageTk.PhotoImage(img_obstacle11)
    img_obstacle12 = Image.open('images/bank2.png')
    self.obstacle12_object = ImageTk.PhotoImage(img_obstacle12)
    self.obstacle1 = self.canvas_widget.create_image(pixels * 3, pixels * 4, anchor='nw', image=self.obstacle2_object)
    self.obstacle2 = self.canvas_widget.create_image(0, pixels * 2, anchor='nw', image=self.obstacle6_object)
    self.obstacle3 = self.canvas_widget.create_image(pixels, 0, anchor='nw', image=self.obstacle5_object)
    self.obstacle4 = self.canvas_widget.create_image(pixels * 3, pixels * 2, anchor='nw', image=self.obstacle2_object)
    self.obstacle5 = self.canvas_widget.create_image(pixels * 4, 0, anchor='nw', image=self.obstacle12_object)
    self.obstacle6 = self.canvas_widget.create_image(pixels * 5, pixels * 3, anchor='nw', image=self.obstacle7_object)
    self.obstacle7 = self.canvas_widget.create_image(pixels * 7, pixels * 3, anchor='nw', image=self.obstacle9_object)
    self.obstacle8 = self.canvas_widget.create_image(pixels * 6, pixels, anchor='nw', image=self.obstacle10_object)
    self.obstacle9 = self.canvas_widget.create_image(pixels * 5, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle10 = self.canvas_widget.create_image(pixels * 6, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle11 = self.canvas_widget.create_image(pixels * 5, pixels * 6, anchor='nw', image=self.obstacle4_object)
    self.obstacle12 = self.canvas_widget.create_image(pixels * 5, pixels * 7, anchor='nw', image=self.obstacle4_object)
    self.obstacle13 = self.canvas_widget.create_image(0, pixels * 8, anchor='nw', image=self.obstacle3_object)
    self.obstacle14 = self.canvas_widget.create_image(pixels * 3, pixels * 7, anchor='nw', image=self.obstacle8_object)
    self.obstacle15 = self.canvas_widget.create_image(0, pixels * 4, anchor='nw', image=self.obstacle1_object)
    self.obstacle16 = self.canvas_widget.create_image(pixels * 8, 0, anchor='nw', image=self.obstacle3_object)
    self.obstacle17 = self.canvas_widget.create_image(pixels * 7, pixels * 7, anchor='nw', image=self.obstacle4_object)
    self.obstacle18 = self.canvas_widget.create_image(pixels, pixels * 6, anchor='nw', image=self.obstacle11_object)
    self.obstacle19 = self.canvas_widget.create_image(pixels * 8, pixels * 3, anchor='nw', image=self.obstacle8_object)
    self.obstacle20 = self.canvas_widget.create_image(pixels * 7, pixels * 6, anchor='nw', image=self.obstacle4_object)
    self.obstacle21 = self.canvas_widget.create_image(pixels * 7, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle22 = self.canvas_widget.create_image(pixels * 2, pixels * 3, anchor='nw', image=self.obstacle2_object)
    img_flag = Image.open('images/flag.png')
    self.flag_object = ImageTk.PhotoImage(img_flag)
    self.flag = self.canvas_widget.create_image(pixels * 6, pixels * 6, anchor='nw', image=self.flag_object)
    img_robot = Image.open('images/agent1.png')
    self.robot = ImageTk.PhotoImage(img_robot)
    self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
    self.canvas_widget.pack()

class Environment(tk.Tk, object):

    def __init__(self):
        super(Environment, self).__init__()
        self.action_space = ['up', 'down', 'left', 'right']
        self.n_actions = len(self.action_space)
        self.title('RL Sarsa. Sichkar Valentyn')
        self.geometry('{0}x{1}'.format(env_height * pixels, env_height * pixels))
        self.build_environment()
        self.d = {}
        self.f = {}
        self.i = 0
        self.c = True
        self.longest = 0
        self.shortest = 0

    def build_environment(self):
        self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
        img_background = Image.open('images/bg.png')
        self.background = ImageTk.PhotoImage(img_background)
        self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
        for column in range(0, env_width * pixels, pixels):
            x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        for row in range(0, env_height * pixels, pixels):
            x0, y0, x1, y1 = (0, row, env_height * pixels, row)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        self.o = np.array([pixels / 2, pixels / 2])
        obstacle1_center = self.o + np.array([pixels, pixels * 2])
        self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
        obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
        self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
        obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
        self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
        obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
        self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
        obstacle5_center = self.o + np.array([pixels * 4, pixels * 10])
        self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
        obstacle6_center = self.o + np.array([pixels * 4, pixels * 11])
        self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
        obstacle7_center = self.o + np.array([pixels * 4, pixels * 12])
        self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
        obstacle8_center = self.o + np.array([pixels * 5, pixels * 12])
        self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
        obstacle9_center = self.o + np.array([pixels * 6, pixels * 12])
        self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
        obstacle10_center = self.o + np.array([pixels * 2, pixels * 18])
        self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
        obstacle11_center = self.o + np.array([pixels * 3, pixels * 18])
        self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
        obstacle12_center = self.o + np.array([pixels * 4, pixels * 18])
        self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
        obstacle13_center = self.o + np.array([pixels * 3, pixels * 19])
        self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
        obstacle14_center = self.o + np.array([pixels * 3, pixels * 20])
        self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
        obstacle15_center = self.o + np.array([pixels * 3, pixels * 21])
        self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
        obstacle16_center = self.o + np.array([pixels * 10, pixels * 22])
        self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
        obstacle17_center = self.o + np.array([pixels * 11, pixels * 15])
        self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
        obstacle18_center = self.o + np.array([pixels * 12, pixels * 15])
        self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
        obstacle19_center = self.o + np.array([pixels * 13, pixels * 15])
        self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
        obstacle20_center = self.o + np.array([pixels * 13, pixels * 14])
        self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
        obstacle21_center = self.o + np.array([pixels * 13, pixels * 13])
        self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
        obstacle22_center = self.o + np.array([pixels * 21, pixels * 22])
        self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
        obstacle23_center = self.o + np.array([pixels * 20, pixels * 22])
        self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
        obstacle24_center = self.o + np.array([pixels * 19, pixels * 22])
        self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
        obstacle25_center = self.o + np.array([pixels * 18, pixels * 22])
        self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
        obstacle26_center = self.o + np.array([pixels * 18, pixels * 21])
        self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
        obstacle27_center = self.o + np.array([pixels * 18, pixels * 20])
        self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
        obstacle28_center = self.o + np.array([pixels * 18, pixels * 19])
        self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
        obstacle29_center = self.o + np.array([pixels * 18, pixels * 18])
        self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
        obstacle30_center = self.o + np.array([pixels * 19, pixels * 18])
        self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
        obstacle31_center = self.o + np.array([pixels * 20, pixels * 18])
        self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
        obstacle32_center = self.o + np.array([pixels * 11, pixels * 6])
        self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
        obstacle33_center = self.o + np.array([pixels * 12, pixels * 6])
        self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
        obstacle34_center = self.o + np.array([pixels * 13, pixels * 6])
        self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
        obstacle35_center = self.o + np.array([pixels * 14, pixels * 6])
        self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
        obstacle36_center = self.o + np.array([pixels * 14, pixels * 7])
        self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
        obstacle37_center = self.o + np.array([pixels * 14, pixels * 5])
        self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
        obstacle38_center = self.o + np.array([pixels * 20, pixels])
        self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
        obstacle39_center = self.o + np.array([pixels * 20, pixels * 2])
        self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
        obstacle40_center = self.o + np.array([pixels * 20, pixels * 3])
        self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
        obstacle41_center = self.o + np.array([pixels * 20, pixels * 4])
        self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
        obstacle42_center = self.o + np.array([pixels * 21, pixels * 4])
        self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
        obstacle43_center = self.o + np.array([pixels * 19, pixels * 4])
        self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
        obstacle44_center = self.o + np.array([pixels * 17, pixels * 10])
        self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
        obstacle45_center = self.o + np.array([pixels * 18, pixels * 10])
        self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
        obstacle46_center = self.o + np.array([pixels * 19, pixels * 10])
        self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
        obstacle47_center = self.o + np.array([pixels * 19, pixels * 9])
        self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
        obstacle48_center = self.o + np.array([pixels * 19, pixels * 8])
        self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
        obstacle49_center = self.o + np.array([pixels * 11, pixels * 23])
        self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
        obstacle50_center = self.o + np.array([pixels * 10, pixels * 23])
        self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
        flag_center = self.o + np.array([pixels * 20, pixels * 20])
        self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
        self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
        self.canvas_widget.pack()

    def reset(self):
        self.update()
        self.canvas_widget.delete(self.agent)
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='red', fill='red')
        self.d = {}
        self.i = 0
        return self.canvas_widget.coords(self.agent)

    def step(self, action):
        state = self.canvas_widget.coords(self.agent)
        base_action = np.array([0, 0])
        if action == 0:
            if state[1] >= pixels:
                base_action[1] -= pixels
        elif action == 1:
            if state[1] < (env_height - 1) * pixels:
                base_action[1] += pixels
        elif action == 2:
            if state[0] < (env_width - 1) * pixels:
                base_action[0] += pixels
        elif action == 3:
            if state[0] >= pixels:
                base_action[0] -= pixels
        self.canvas_widget.move(self.agent, base_action[0], base_action[1])
        self.d[self.i] = self.canvas_widget.coords(self.agent)
        next_state = self.d[self.i]
        self.i += 1
        if next_state == self.coords_flag:
            time.sleep(0.1)
            reward = 1
            done = True
            next_state = 'goal'
            print('Goal!')
            if self.c == True:
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
                self.c = False
                self.longest = len(self.d)
                self.shortest = len(self.d)
            if len(self.d) < len(self.f):
                self.shortest = len(self.d)
                self.f = {}
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
            if len(self.d) > self.longest:
                self.longest = len(self.d)
        elif next_state in [self.coords_obstacle1, self.coords_obstacle2, self.coords_obstacle3, self.coords_obstacle4, self.coords_obstacle5, self.coords_obstacle6, self.coords_obstacle7, self.coords_obstacle8, self.coords_obstacle9, self.coords_obstacle10, self.coords_obstacle11, self.coords_obstacle12, self.coords_obstacle13, self.coords_obstacle14, self.coords_obstacle15, self.coords_obstacle16, self.coords_obstacle17, self.coords_obstacle18, self.coords_obstacle19, self.coords_obstacle20, self.coords_obstacle21, self.coords_obstacle22, self.coords_obstacle23, self.coords_obstacle24, self.coords_obstacle25, self.coords_obstacle26, self.coords_obstacle27, self.coords_obstacle28, self.coords_obstacle29, self.coords_obstacle30, self.coords_obstacle31, self.coords_obstacle32, self.coords_obstacle33, self.coords_obstacle34, self.coords_obstacle35, self.coords_obstacle36, self.coords_obstacle37, self.coords_obstacle38, self.coords_obstacle39, self.coords_obstacle40, self.coords_obstacle41, self.coords_obstacle42, self.coords_obstacle43, self.coords_obstacle44, self.coords_obstacle45, self.coords_obstacle46, self.coords_obstacle47, self.coords_obstacle48, self.coords_obstacle49, self.coords_obstacle50]:
            reward = -1
            done = True
            next_state = 'obstacle'
            self.d = {}
            self.i = 0
        else:
            reward = 0
            done = False
        return (next_state, reward, done)

    def render(self):
        self.update()

    def final(self):
        self.canvas_widget.delete(self.agent)
        print('The shortest route:', self.shortest)
        print('The longest route:', self.longest)
        self.initial_point = self.canvas_widget.create_oval(self.o[0] - 4, self.o[1] - 4, self.o[0] + 4, self.o[1] + 4, fill='blue', outline='blue')
        for j in range(len(self.f)):
            print(self.f[j])
            self.track = self.canvas_widget.create_oval(self.f[j][0] - 3 + self.o[0] - 4, self.f[j][1] - 3 + self.o[1] - 4, self.f[j][0] - 3 + self.o[0] + 4, self.f[j][1] - 3 + self.o[1] + 4, fill='blue', outline='blue')
            a[j] = self.f[j]

def build_environment(self):
    self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
    img_background = Image.open('images/bg.png')
    self.background = ImageTk.PhotoImage(img_background)
    self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
    for column in range(0, env_width * pixels, pixels):
        x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    for row in range(0, env_height * pixels, pixels):
        x0, y0, x1, y1 = (0, row, env_height * pixels, row)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    self.o = np.array([pixels / 2, pixels / 2])
    obstacle1_center = self.o + np.array([pixels, pixels * 2])
    self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
    obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
    self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
    obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
    self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
    obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
    self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
    obstacle5_center = self.o + np.array([pixels * 4, pixels * 10])
    self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
    obstacle6_center = self.o + np.array([pixels * 4, pixels * 11])
    self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
    obstacle7_center = self.o + np.array([pixels * 4, pixels * 12])
    self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
    obstacle8_center = self.o + np.array([pixels * 5, pixels * 12])
    self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
    obstacle9_center = self.o + np.array([pixels * 6, pixels * 12])
    self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
    obstacle10_center = self.o + np.array([pixels * 2, pixels * 18])
    self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
    obstacle11_center = self.o + np.array([pixels * 3, pixels * 18])
    self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
    obstacle12_center = self.o + np.array([pixels * 4, pixels * 18])
    self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
    obstacle13_center = self.o + np.array([pixels * 3, pixels * 19])
    self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
    obstacle14_center = self.o + np.array([pixels * 3, pixels * 20])
    self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
    obstacle15_center = self.o + np.array([pixels * 3, pixels * 21])
    self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
    obstacle16_center = self.o + np.array([pixels * 10, pixels * 22])
    self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
    obstacle17_center = self.o + np.array([pixels * 11, pixels * 15])
    self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
    obstacle18_center = self.o + np.array([pixels * 12, pixels * 15])
    self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
    obstacle19_center = self.o + np.array([pixels * 13, pixels * 15])
    self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
    obstacle20_center = self.o + np.array([pixels * 13, pixels * 14])
    self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
    obstacle21_center = self.o + np.array([pixels * 13, pixels * 13])
    self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
    obstacle22_center = self.o + np.array([pixels * 21, pixels * 22])
    self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
    obstacle23_center = self.o + np.array([pixels * 20, pixels * 22])
    self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
    obstacle24_center = self.o + np.array([pixels * 19, pixels * 22])
    self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
    obstacle25_center = self.o + np.array([pixels * 18, pixels * 22])
    self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
    obstacle26_center = self.o + np.array([pixels * 18, pixels * 21])
    self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
    obstacle27_center = self.o + np.array([pixels * 18, pixels * 20])
    self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
    obstacle28_center = self.o + np.array([pixels * 18, pixels * 19])
    self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
    obstacle29_center = self.o + np.array([pixels * 18, pixels * 18])
    self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
    obstacle30_center = self.o + np.array([pixels * 19, pixels * 18])
    self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
    obstacle31_center = self.o + np.array([pixels * 20, pixels * 18])
    self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
    obstacle32_center = self.o + np.array([pixels * 11, pixels * 6])
    self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
    obstacle33_center = self.o + np.array([pixels * 12, pixels * 6])
    self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
    obstacle34_center = self.o + np.array([pixels * 13, pixels * 6])
    self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
    obstacle35_center = self.o + np.array([pixels * 14, pixels * 6])
    self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
    obstacle36_center = self.o + np.array([pixels * 14, pixels * 7])
    self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
    obstacle37_center = self.o + np.array([pixels * 14, pixels * 5])
    self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
    obstacle38_center = self.o + np.array([pixels * 20, pixels])
    self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
    obstacle39_center = self.o + np.array([pixels * 20, pixels * 2])
    self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
    obstacle40_center = self.o + np.array([pixels * 20, pixels * 3])
    self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
    obstacle41_center = self.o + np.array([pixels * 20, pixels * 4])
    self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
    obstacle42_center = self.o + np.array([pixels * 21, pixels * 4])
    self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
    obstacle43_center = self.o + np.array([pixels * 19, pixels * 4])
    self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
    obstacle44_center = self.o + np.array([pixels * 17, pixels * 10])
    self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
    obstacle45_center = self.o + np.array([pixels * 18, pixels * 10])
    self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
    obstacle46_center = self.o + np.array([pixels * 19, pixels * 10])
    self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
    obstacle47_center = self.o + np.array([pixels * 19, pixels * 9])
    self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
    obstacle48_center = self.o + np.array([pixels * 19, pixels * 8])
    self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
    obstacle49_center = self.o + np.array([pixels * 11, pixels * 23])
    self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
    obstacle50_center = self.o + np.array([pixels * 10, pixels * 23])
    self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
    self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
    flag_center = self.o + np.array([pixels * 20, pixels * 20])
    self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
    self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
    self.canvas_widget.pack()

class Environment(tk.Tk, object):

    def __init__(self):
        super(Environment, self).__init__()
        self.action_space = ['up', 'down', 'left', 'right']
        self.n_actions = len(self.action_space)
        self.title('RL Q-learning. Sichkar Valentyn')
        self.geometry('{0}x{1}'.format(env_height * pixels, env_height * pixels))
        self.build_environment()
        self.d = {}
        self.f = {}
        self.i = 0
        self.c = True
        self.longest = 0
        self.shortest = 0

    def build_environment(self):
        self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
        img_background = Image.open('images/bg.png')
        self.background = ImageTk.PhotoImage(img_background)
        self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
        for column in range(0, env_width * pixels, pixels):
            x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        for row in range(0, env_height * pixels, pixels):
            x0, y0, x1, y1 = (0, row, env_height * pixels, row)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        self.o = np.array([pixels / 2, pixels / 2])
        obstacle1_center = self.o + np.array([pixels, pixels * 2])
        self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
        obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
        self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
        obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
        self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
        obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
        self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
        obstacle5_center = self.o + np.array([pixels * 4, pixels * 10])
        self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
        obstacle6_center = self.o + np.array([pixels * 4, pixels * 11])
        self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
        obstacle7_center = self.o + np.array([pixels * 4, pixels * 12])
        self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
        obstacle8_center = self.o + np.array([pixels * 5, pixels * 12])
        self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
        obstacle9_center = self.o + np.array([pixels * 6, pixels * 12])
        self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
        obstacle10_center = self.o + np.array([pixels * 2, pixels * 18])
        self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
        obstacle11_center = self.o + np.array([pixels * 3, pixels * 18])
        self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
        obstacle12_center = self.o + np.array([pixels * 4, pixels * 18])
        self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
        obstacle13_center = self.o + np.array([pixels * 3, pixels * 19])
        self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
        obstacle14_center = self.o + np.array([pixels * 3, pixels * 20])
        self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
        obstacle15_center = self.o + np.array([pixels * 3, pixels * 21])
        self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
        obstacle16_center = self.o + np.array([pixels * 10, pixels * 22])
        self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
        obstacle17_center = self.o + np.array([pixels * 11, pixels * 15])
        self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
        obstacle18_center = self.o + np.array([pixels * 12, pixels * 15])
        self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
        obstacle19_center = self.o + np.array([pixels * 13, pixels * 15])
        self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
        obstacle20_center = self.o + np.array([pixels * 13, pixels * 14])
        self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
        obstacle21_center = self.o + np.array([pixels * 13, pixels * 13])
        self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
        obstacle22_center = self.o + np.array([pixels * 21, pixels * 22])
        self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
        obstacle23_center = self.o + np.array([pixels * 20, pixels * 22])
        self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
        obstacle24_center = self.o + np.array([pixels * 19, pixels * 22])
        self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
        obstacle25_center = self.o + np.array([pixels * 18, pixels * 22])
        self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
        obstacle26_center = self.o + np.array([pixels * 18, pixels * 21])
        self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
        obstacle27_center = self.o + np.array([pixels * 18, pixels * 20])
        self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
        obstacle28_center = self.o + np.array([pixels * 18, pixels * 19])
        self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
        obstacle29_center = self.o + np.array([pixels * 18, pixels * 18])
        self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
        obstacle30_center = self.o + np.array([pixels * 19, pixels * 18])
        self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
        obstacle31_center = self.o + np.array([pixels * 20, pixels * 18])
        self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
        obstacle32_center = self.o + np.array([pixels * 11, pixels * 6])
        self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
        obstacle33_center = self.o + np.array([pixels * 12, pixels * 6])
        self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
        obstacle34_center = self.o + np.array([pixels * 13, pixels * 6])
        self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
        obstacle35_center = self.o + np.array([pixels * 14, pixels * 6])
        self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
        obstacle36_center = self.o + np.array([pixels * 14, pixels * 7])
        self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
        obstacle37_center = self.o + np.array([pixels * 14, pixels * 5])
        self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
        obstacle38_center = self.o + np.array([pixels * 20, pixels])
        self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
        obstacle39_center = self.o + np.array([pixels * 20, pixels * 2])
        self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
        obstacle40_center = self.o + np.array([pixels * 20, pixels * 3])
        self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
        obstacle41_center = self.o + np.array([pixels * 20, pixels * 4])
        self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
        obstacle42_center = self.o + np.array([pixels * 21, pixels * 4])
        self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
        obstacle43_center = self.o + np.array([pixels * 19, pixels * 4])
        self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
        obstacle44_center = self.o + np.array([pixels * 17, pixels * 10])
        self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
        obstacle45_center = self.o + np.array([pixels * 18, pixels * 10])
        self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
        obstacle46_center = self.o + np.array([pixels * 19, pixels * 10])
        self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
        obstacle47_center = self.o + np.array([pixels * 19, pixels * 9])
        self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
        obstacle48_center = self.o + np.array([pixels * 19, pixels * 8])
        self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
        obstacle49_center = self.o + np.array([pixels * 11, pixels * 23])
        self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
        obstacle50_center = self.o + np.array([pixels * 10, pixels * 23])
        self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
        self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
        flag_center = self.o + np.array([pixels * 20, pixels * 20])
        self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
        self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
        self.canvas_widget.pack()

    def reset(self):
        self.update()
        self.canvas_widget.delete(self.agent)
        self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='red', fill='red')
        self.d = {}
        self.i = 0
        return self.canvas_widget.coords(self.agent)

    def step(self, action):
        state = self.canvas_widget.coords(self.agent)
        base_action = np.array([0, 0])
        if action == 0:
            if state[1] >= pixels:
                base_action[1] -= pixels
        elif action == 1:
            if state[1] < (env_height - 1) * pixels:
                base_action[1] += pixels
        elif action == 2:
            if state[0] < (env_width - 1) * pixels:
                base_action[0] += pixels
        elif action == 3:
            if state[0] >= pixels:
                base_action[0] -= pixels
        self.canvas_widget.move(self.agent, base_action[0], base_action[1])
        self.d[self.i] = self.canvas_widget.coords(self.agent)
        next_state = self.d[self.i]
        self.i += 1
        if next_state == self.coords_flag:
            time.sleep(0.1)
            reward = 1
            done = True
            next_state = 'goal'
            if self.c == True:
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
                self.c = False
                self.longest = len(self.d)
                self.shortest = len(self.d)
            if len(self.d) < len(self.f):
                self.shortest = len(self.d)
                self.f = {}
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
            if len(self.d) > self.longest:
                self.longest = len(self.d)
        elif next_state in [self.coords_obstacle1, self.coords_obstacle2, self.coords_obstacle3, self.coords_obstacle4, self.coords_obstacle5, self.coords_obstacle6, self.coords_obstacle7, self.coords_obstacle8, self.coords_obstacle9, self.coords_obstacle10, self.coords_obstacle11, self.coords_obstacle12, self.coords_obstacle13, self.coords_obstacle14, self.coords_obstacle15, self.coords_obstacle16, self.coords_obstacle17, self.coords_obstacle18, self.coords_obstacle19, self.coords_obstacle20, self.coords_obstacle21, self.coords_obstacle22, self.coords_obstacle23, self.coords_obstacle24, self.coords_obstacle25, self.coords_obstacle26, self.coords_obstacle27, self.coords_obstacle28, self.coords_obstacle29, self.coords_obstacle30, self.coords_obstacle31, self.coords_obstacle32, self.coords_obstacle33, self.coords_obstacle34, self.coords_obstacle35, self.coords_obstacle36, self.coords_obstacle37, self.coords_obstacle38, self.coords_obstacle39, self.coords_obstacle40, self.coords_obstacle41, self.coords_obstacle42, self.coords_obstacle43, self.coords_obstacle44, self.coords_obstacle45, self.coords_obstacle46, self.coords_obstacle47, self.coords_obstacle48, self.coords_obstacle49, self.coords_obstacle50]:
            reward = -1
            done = True
            next_state = 'obstacle'
            self.d = {}
            self.i = 0
        else:
            reward = 0
            done = False
        return (next_state, reward, done)

    def render(self):
        self.update()

    def final(self):
        self.canvas_widget.delete(self.agent)
        print('The shortest route:', self.shortest)
        print('The longest route:', self.longest)
        self.initial_point = self.canvas_widget.create_oval(self.o[0] - 4, self.o[1] - 4, self.o[0] + 4, self.o[1] + 4, fill='blue', outline='blue')
        for j in range(len(self.f)):
            print(self.f[j])
            self.track = self.canvas_widget.create_oval(self.f[j][0] - 3 + self.o[0] - 4, self.f[j][1] - 3 + self.o[1] - 4, self.f[j][0] - 3 + self.o[0] + 4, self.f[j][1] - 3 + self.o[1] + 4, fill='blue', outline='blue')
            a[j] = self.f[j]

def build_environment(self):
    self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
    img_background = Image.open('images/bg.png')
    self.background = ImageTk.PhotoImage(img_background)
    self.bg = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.background)
    for column in range(0, env_width * pixels, pixels):
        x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    for row in range(0, env_height * pixels, pixels):
        x0, y0, x1, y1 = (0, row, env_height * pixels, row)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    self.o = np.array([pixels / 2, pixels / 2])
    obstacle1_center = self.o + np.array([pixels, pixels * 2])
    self.obstacle1 = self.canvas_widget.create_rectangle(obstacle1_center[0] - 10, obstacle1_center[1] - 10, obstacle1_center[0] + 10, obstacle1_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle1 = [self.canvas_widget.coords(self.obstacle1)[0] + 3, self.canvas_widget.coords(self.obstacle1)[1] + 3, self.canvas_widget.coords(self.obstacle1)[2] - 3, self.canvas_widget.coords(self.obstacle1)[3] - 3]
    obstacle2_center = self.o + np.array([pixels * 2, pixels * 2])
    self.obstacle2 = self.canvas_widget.create_rectangle(obstacle2_center[0] - 10, obstacle2_center[1] - 10, obstacle2_center[0] + 10, obstacle2_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle2 = [self.canvas_widget.coords(self.obstacle2)[0] + 3, self.canvas_widget.coords(self.obstacle2)[1] + 3, self.canvas_widget.coords(self.obstacle2)[2] - 3, self.canvas_widget.coords(self.obstacle2)[3] - 3]
    obstacle3_center = self.o + np.array([pixels * 3, pixels * 2])
    self.obstacle3 = self.canvas_widget.create_rectangle(obstacle3_center[0] - 10, obstacle3_center[1] - 10, obstacle3_center[0] + 10, obstacle3_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle3 = [self.canvas_widget.coords(self.obstacle3)[0] + 3, self.canvas_widget.coords(self.obstacle3)[1] + 3, self.canvas_widget.coords(self.obstacle3)[2] - 3, self.canvas_widget.coords(self.obstacle3)[3] - 3]
    obstacle4_center = self.o + np.array([pixels * 3, pixels * 3])
    self.obstacle4 = self.canvas_widget.create_rectangle(obstacle4_center[0] - 10, obstacle4_center[1] - 10, obstacle4_center[0] + 10, obstacle4_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle4 = [self.canvas_widget.coords(self.obstacle4)[0] + 3, self.canvas_widget.coords(self.obstacle4)[1] + 3, self.canvas_widget.coords(self.obstacle4)[2] - 3, self.canvas_widget.coords(self.obstacle4)[3] - 3]
    obstacle5_center = self.o + np.array([pixels * 4, pixels * 10])
    self.obstacle5 = self.canvas_widget.create_rectangle(obstacle5_center[0] - 10, obstacle5_center[1] - 10, obstacle5_center[0] + 10, obstacle5_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle5 = [self.canvas_widget.coords(self.obstacle5)[0] + 3, self.canvas_widget.coords(self.obstacle5)[1] + 3, self.canvas_widget.coords(self.obstacle5)[2] - 3, self.canvas_widget.coords(self.obstacle5)[3] - 3]
    obstacle6_center = self.o + np.array([pixels * 4, pixels * 11])
    self.obstacle6 = self.canvas_widget.create_rectangle(obstacle6_center[0] - 10, obstacle6_center[1] - 10, obstacle6_center[0] + 10, obstacle6_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle6 = [self.canvas_widget.coords(self.obstacle6)[0] + 3, self.canvas_widget.coords(self.obstacle6)[1] + 3, self.canvas_widget.coords(self.obstacle6)[2] - 3, self.canvas_widget.coords(self.obstacle6)[3] - 3]
    obstacle7_center = self.o + np.array([pixels * 4, pixels * 12])
    self.obstacle7 = self.canvas_widget.create_rectangle(obstacle7_center[0] - 10, obstacle7_center[1] - 10, obstacle7_center[0] + 10, obstacle7_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle7 = [self.canvas_widget.coords(self.obstacle7)[0] + 3, self.canvas_widget.coords(self.obstacle7)[1] + 3, self.canvas_widget.coords(self.obstacle7)[2] - 3, self.canvas_widget.coords(self.obstacle7)[3] - 3]
    obstacle8_center = self.o + np.array([pixels * 5, pixels * 12])
    self.obstacle8 = self.canvas_widget.create_rectangle(obstacle8_center[0] - 10, obstacle8_center[1] - 10, obstacle8_center[0] + 10, obstacle8_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle8 = [self.canvas_widget.coords(self.obstacle8)[0] + 3, self.canvas_widget.coords(self.obstacle8)[1] + 3, self.canvas_widget.coords(self.obstacle8)[2] - 3, self.canvas_widget.coords(self.obstacle8)[3] - 3]
    obstacle9_center = self.o + np.array([pixels * 6, pixels * 12])
    self.obstacle9 = self.canvas_widget.create_rectangle(obstacle9_center[0] - 10, obstacle9_center[1] - 10, obstacle9_center[0] + 10, obstacle9_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle9 = [self.canvas_widget.coords(self.obstacle9)[0] + 3, self.canvas_widget.coords(self.obstacle9)[1] + 3, self.canvas_widget.coords(self.obstacle9)[2] - 3, self.canvas_widget.coords(self.obstacle9)[3] - 3]
    obstacle10_center = self.o + np.array([pixels * 2, pixels * 18])
    self.obstacle10 = self.canvas_widget.create_rectangle(obstacle10_center[0] - 10, obstacle10_center[1] - 10, obstacle10_center[0] + 10, obstacle10_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle10 = [self.canvas_widget.coords(self.obstacle10)[0] + 3, self.canvas_widget.coords(self.obstacle10)[1] + 3, self.canvas_widget.coords(self.obstacle10)[2] - 3, self.canvas_widget.coords(self.obstacle10)[3] - 3]
    obstacle11_center = self.o + np.array([pixels * 3, pixels * 18])
    self.obstacle11 = self.canvas_widget.create_rectangle(obstacle11_center[0] - 10, obstacle11_center[1] - 10, obstacle11_center[0] + 10, obstacle11_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle11 = [self.canvas_widget.coords(self.obstacle11)[0] + 3, self.canvas_widget.coords(self.obstacle11)[1] + 3, self.canvas_widget.coords(self.obstacle11)[2] - 3, self.canvas_widget.coords(self.obstacle11)[3] - 3]
    obstacle12_center = self.o + np.array([pixels * 4, pixels * 18])
    self.obstacle12 = self.canvas_widget.create_rectangle(obstacle12_center[0] - 10, obstacle12_center[1] - 10, obstacle12_center[0] + 10, obstacle12_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle12 = [self.canvas_widget.coords(self.obstacle12)[0] + 3, self.canvas_widget.coords(self.obstacle12)[1] + 3, self.canvas_widget.coords(self.obstacle12)[2] - 3, self.canvas_widget.coords(self.obstacle12)[3] - 3]
    obstacle13_center = self.o + np.array([pixels * 3, pixels * 19])
    self.obstacle13 = self.canvas_widget.create_rectangle(obstacle13_center[0] - 10, obstacle13_center[1] - 10, obstacle13_center[0] + 10, obstacle13_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle13 = [self.canvas_widget.coords(self.obstacle13)[0] + 3, self.canvas_widget.coords(self.obstacle13)[1] + 3, self.canvas_widget.coords(self.obstacle13)[2] - 3, self.canvas_widget.coords(self.obstacle13)[3] - 3]
    obstacle14_center = self.o + np.array([pixels * 3, pixels * 20])
    self.obstacle14 = self.canvas_widget.create_rectangle(obstacle14_center[0] - 10, obstacle14_center[1] - 10, obstacle14_center[0] + 10, obstacle14_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle14 = [self.canvas_widget.coords(self.obstacle14)[0] + 3, self.canvas_widget.coords(self.obstacle14)[1] + 3, self.canvas_widget.coords(self.obstacle14)[2] - 3, self.canvas_widget.coords(self.obstacle14)[3] - 3]
    obstacle15_center = self.o + np.array([pixels * 3, pixels * 21])
    self.obstacle15 = self.canvas_widget.create_rectangle(obstacle15_center[0] - 10, obstacle15_center[1] - 10, obstacle15_center[0] + 10, obstacle15_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle15 = [self.canvas_widget.coords(self.obstacle15)[0] + 3, self.canvas_widget.coords(self.obstacle15)[1] + 3, self.canvas_widget.coords(self.obstacle15)[2] - 3, self.canvas_widget.coords(self.obstacle15)[3] - 3]
    obstacle16_center = self.o + np.array([pixels * 10, pixels * 22])
    self.obstacle16 = self.canvas_widget.create_rectangle(obstacle16_center[0] - 10, obstacle16_center[1] - 10, obstacle16_center[0] + 10, obstacle16_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle16 = [self.canvas_widget.coords(self.obstacle16)[0] + 3, self.canvas_widget.coords(self.obstacle16)[1] + 3, self.canvas_widget.coords(self.obstacle16)[2] - 3, self.canvas_widget.coords(self.obstacle16)[3] - 3]
    obstacle17_center = self.o + np.array([pixels * 11, pixels * 15])
    self.obstacle17 = self.canvas_widget.create_rectangle(obstacle17_center[0] - 10, obstacle17_center[1] - 10, obstacle17_center[0] + 10, obstacle17_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle17 = [self.canvas_widget.coords(self.obstacle17)[0] + 3, self.canvas_widget.coords(self.obstacle17)[1] + 3, self.canvas_widget.coords(self.obstacle17)[2] - 3, self.canvas_widget.coords(self.obstacle17)[3] - 3]
    obstacle18_center = self.o + np.array([pixels * 12, pixels * 15])
    self.obstacle18 = self.canvas_widget.create_rectangle(obstacle18_center[0] - 10, obstacle18_center[1] - 10, obstacle18_center[0] + 10, obstacle18_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle18 = [self.canvas_widget.coords(self.obstacle18)[0] + 3, self.canvas_widget.coords(self.obstacle18)[1] + 3, self.canvas_widget.coords(self.obstacle18)[2] - 3, self.canvas_widget.coords(self.obstacle18)[3] - 3]
    obstacle19_center = self.o + np.array([pixels * 13, pixels * 15])
    self.obstacle19 = self.canvas_widget.create_rectangle(obstacle19_center[0] - 10, obstacle19_center[1] - 10, obstacle19_center[0] + 10, obstacle19_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle19 = [self.canvas_widget.coords(self.obstacle19)[0] + 3, self.canvas_widget.coords(self.obstacle19)[1] + 3, self.canvas_widget.coords(self.obstacle19)[2] - 3, self.canvas_widget.coords(self.obstacle19)[3] - 3]
    obstacle20_center = self.o + np.array([pixels * 13, pixels * 14])
    self.obstacle20 = self.canvas_widget.create_rectangle(obstacle20_center[0] - 10, obstacle20_center[1] - 10, obstacle20_center[0] + 10, obstacle20_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle20 = [self.canvas_widget.coords(self.obstacle20)[0] + 3, self.canvas_widget.coords(self.obstacle20)[1] + 3, self.canvas_widget.coords(self.obstacle20)[2] - 3, self.canvas_widget.coords(self.obstacle20)[3] - 3]
    obstacle21_center = self.o + np.array([pixels * 13, pixels * 13])
    self.obstacle21 = self.canvas_widget.create_rectangle(obstacle21_center[0] - 10, obstacle21_center[1] - 10, obstacle21_center[0] + 10, obstacle21_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle21 = [self.canvas_widget.coords(self.obstacle21)[0] + 3, self.canvas_widget.coords(self.obstacle21)[1] + 3, self.canvas_widget.coords(self.obstacle21)[2] - 3, self.canvas_widget.coords(self.obstacle21)[3] - 3]
    obstacle22_center = self.o + np.array([pixels * 21, pixels * 22])
    self.obstacle22 = self.canvas_widget.create_rectangle(obstacle22_center[0] - 10, obstacle22_center[1] - 10, obstacle22_center[0] + 10, obstacle22_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle22 = [self.canvas_widget.coords(self.obstacle22)[0] + 3, self.canvas_widget.coords(self.obstacle22)[1] + 3, self.canvas_widget.coords(self.obstacle22)[2] - 3, self.canvas_widget.coords(self.obstacle22)[3] - 3]
    obstacle23_center = self.o + np.array([pixels * 20, pixels * 22])
    self.obstacle23 = self.canvas_widget.create_rectangle(obstacle23_center[0] - 10, obstacle23_center[1] - 10, obstacle23_center[0] + 10, obstacle23_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle23 = [self.canvas_widget.coords(self.obstacle23)[0] + 3, self.canvas_widget.coords(self.obstacle23)[1] + 3, self.canvas_widget.coords(self.obstacle23)[2] - 3, self.canvas_widget.coords(self.obstacle23)[3] - 3]
    obstacle24_center = self.o + np.array([pixels * 19, pixels * 22])
    self.obstacle24 = self.canvas_widget.create_rectangle(obstacle24_center[0] - 10, obstacle24_center[1] - 10, obstacle24_center[0] + 10, obstacle24_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle24 = [self.canvas_widget.coords(self.obstacle24)[0] + 3, self.canvas_widget.coords(self.obstacle24)[1] + 3, self.canvas_widget.coords(self.obstacle24)[2] - 3, self.canvas_widget.coords(self.obstacle24)[3] - 3]
    obstacle25_center = self.o + np.array([pixels * 18, pixels * 22])
    self.obstacle25 = self.canvas_widget.create_rectangle(obstacle25_center[0] - 10, obstacle25_center[1] - 10, obstacle25_center[0] + 10, obstacle25_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle25 = [self.canvas_widget.coords(self.obstacle25)[0] + 3, self.canvas_widget.coords(self.obstacle25)[1] + 3, self.canvas_widget.coords(self.obstacle25)[2] - 3, self.canvas_widget.coords(self.obstacle25)[3] - 3]
    obstacle26_center = self.o + np.array([pixels * 18, pixels * 21])
    self.obstacle26 = self.canvas_widget.create_rectangle(obstacle26_center[0] - 10, obstacle26_center[1] - 10, obstacle26_center[0] + 10, obstacle26_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle26 = [self.canvas_widget.coords(self.obstacle26)[0] + 3, self.canvas_widget.coords(self.obstacle26)[1] + 3, self.canvas_widget.coords(self.obstacle26)[2] - 3, self.canvas_widget.coords(self.obstacle26)[3] - 3]
    obstacle27_center = self.o + np.array([pixels * 18, pixels * 20])
    self.obstacle27 = self.canvas_widget.create_rectangle(obstacle27_center[0] - 10, obstacle27_center[1] - 10, obstacle27_center[0] + 10, obstacle27_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle27 = [self.canvas_widget.coords(self.obstacle27)[0] + 3, self.canvas_widget.coords(self.obstacle27)[1] + 3, self.canvas_widget.coords(self.obstacle27)[2] - 3, self.canvas_widget.coords(self.obstacle27)[3] - 3]
    obstacle28_center = self.o + np.array([pixels * 18, pixels * 19])
    self.obstacle28 = self.canvas_widget.create_rectangle(obstacle28_center[0] - 10, obstacle28_center[1] - 10, obstacle28_center[0] + 10, obstacle28_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle28 = [self.canvas_widget.coords(self.obstacle28)[0] + 3, self.canvas_widget.coords(self.obstacle28)[1] + 3, self.canvas_widget.coords(self.obstacle28)[2] - 3, self.canvas_widget.coords(self.obstacle28)[3] - 3]
    obstacle29_center = self.o + np.array([pixels * 18, pixels * 18])
    self.obstacle29 = self.canvas_widget.create_rectangle(obstacle29_center[0] - 10, obstacle29_center[1] - 10, obstacle29_center[0] + 10, obstacle29_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle29 = [self.canvas_widget.coords(self.obstacle29)[0] + 3, self.canvas_widget.coords(self.obstacle29)[1] + 3, self.canvas_widget.coords(self.obstacle29)[2] - 3, self.canvas_widget.coords(self.obstacle29)[3] - 3]
    obstacle30_center = self.o + np.array([pixels * 19, pixels * 18])
    self.obstacle30 = self.canvas_widget.create_rectangle(obstacle30_center[0] - 10, obstacle30_center[1] - 10, obstacle30_center[0] + 10, obstacle30_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle30 = [self.canvas_widget.coords(self.obstacle30)[0] + 3, self.canvas_widget.coords(self.obstacle30)[1] + 3, self.canvas_widget.coords(self.obstacle30)[2] - 3, self.canvas_widget.coords(self.obstacle30)[3] - 3]
    obstacle31_center = self.o + np.array([pixels * 20, pixels * 18])
    self.obstacle31 = self.canvas_widget.create_rectangle(obstacle31_center[0] - 10, obstacle31_center[1] - 10, obstacle31_center[0] + 10, obstacle31_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle31 = [self.canvas_widget.coords(self.obstacle31)[0] + 3, self.canvas_widget.coords(self.obstacle31)[1] + 3, self.canvas_widget.coords(self.obstacle31)[2] - 3, self.canvas_widget.coords(self.obstacle31)[3] - 3]
    obstacle32_center = self.o + np.array([pixels * 11, pixels * 6])
    self.obstacle32 = self.canvas_widget.create_rectangle(obstacle32_center[0] - 10, obstacle32_center[1] - 10, obstacle32_center[0] + 10, obstacle32_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle32 = [self.canvas_widget.coords(self.obstacle32)[0] + 3, self.canvas_widget.coords(self.obstacle32)[1] + 3, self.canvas_widget.coords(self.obstacle32)[2] - 3, self.canvas_widget.coords(self.obstacle32)[3] - 3]
    obstacle33_center = self.o + np.array([pixels * 12, pixels * 6])
    self.obstacle33 = self.canvas_widget.create_rectangle(obstacle33_center[0] - 10, obstacle33_center[1] - 10, obstacle33_center[0] + 10, obstacle33_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle33 = [self.canvas_widget.coords(self.obstacle33)[0] + 3, self.canvas_widget.coords(self.obstacle33)[1] + 3, self.canvas_widget.coords(self.obstacle33)[2] - 3, self.canvas_widget.coords(self.obstacle33)[3] - 3]
    obstacle34_center = self.o + np.array([pixels * 13, pixels * 6])
    self.obstacle34 = self.canvas_widget.create_rectangle(obstacle34_center[0] - 10, obstacle34_center[1] - 10, obstacle34_center[0] + 10, obstacle34_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle34 = [self.canvas_widget.coords(self.obstacle34)[0] + 3, self.canvas_widget.coords(self.obstacle34)[1] + 3, self.canvas_widget.coords(self.obstacle34)[2] - 3, self.canvas_widget.coords(self.obstacle34)[3] - 3]
    obstacle35_center = self.o + np.array([pixels * 14, pixels * 6])
    self.obstacle35 = self.canvas_widget.create_rectangle(obstacle35_center[0] - 10, obstacle35_center[1] - 10, obstacle35_center[0] + 10, obstacle35_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle35 = [self.canvas_widget.coords(self.obstacle35)[0] + 3, self.canvas_widget.coords(self.obstacle35)[1] + 3, self.canvas_widget.coords(self.obstacle35)[2] - 3, self.canvas_widget.coords(self.obstacle35)[3] - 3]
    obstacle36_center = self.o + np.array([pixels * 14, pixels * 7])
    self.obstacle36 = self.canvas_widget.create_rectangle(obstacle36_center[0] - 10, obstacle36_center[1] - 10, obstacle36_center[0] + 10, obstacle36_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle36 = [self.canvas_widget.coords(self.obstacle36)[0] + 3, self.canvas_widget.coords(self.obstacle36)[1] + 3, self.canvas_widget.coords(self.obstacle36)[2] - 3, self.canvas_widget.coords(self.obstacle36)[3] - 3]
    obstacle37_center = self.o + np.array([pixels * 14, pixels * 5])
    self.obstacle37 = self.canvas_widget.create_rectangle(obstacle37_center[0] - 10, obstacle37_center[1] - 10, obstacle37_center[0] + 10, obstacle37_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle37 = [self.canvas_widget.coords(self.obstacle37)[0] + 3, self.canvas_widget.coords(self.obstacle37)[1] + 3, self.canvas_widget.coords(self.obstacle37)[2] - 3, self.canvas_widget.coords(self.obstacle37)[3] - 3]
    obstacle38_center = self.o + np.array([pixels * 20, pixels])
    self.obstacle38 = self.canvas_widget.create_rectangle(obstacle38_center[0] - 10, obstacle38_center[1] - 10, obstacle38_center[0] + 10, obstacle38_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle38 = [self.canvas_widget.coords(self.obstacle38)[0] + 3, self.canvas_widget.coords(self.obstacle38)[1] + 3, self.canvas_widget.coords(self.obstacle38)[2] - 3, self.canvas_widget.coords(self.obstacle38)[3] - 3]
    obstacle39_center = self.o + np.array([pixels * 20, pixels * 2])
    self.obstacle39 = self.canvas_widget.create_rectangle(obstacle39_center[0] - 10, obstacle39_center[1] - 10, obstacle39_center[0] + 10, obstacle39_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle39 = [self.canvas_widget.coords(self.obstacle39)[0] + 3, self.canvas_widget.coords(self.obstacle39)[1] + 3, self.canvas_widget.coords(self.obstacle39)[2] - 3, self.canvas_widget.coords(self.obstacle39)[3] - 3]
    obstacle40_center = self.o + np.array([pixels * 20, pixels * 3])
    self.obstacle40 = self.canvas_widget.create_rectangle(obstacle40_center[0] - 10, obstacle40_center[1] - 10, obstacle40_center[0] + 10, obstacle40_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle40 = [self.canvas_widget.coords(self.obstacle40)[0] + 3, self.canvas_widget.coords(self.obstacle40)[1] + 3, self.canvas_widget.coords(self.obstacle40)[2] - 3, self.canvas_widget.coords(self.obstacle40)[3] - 3]
    obstacle41_center = self.o + np.array([pixels * 20, pixels * 4])
    self.obstacle41 = self.canvas_widget.create_rectangle(obstacle41_center[0] - 10, obstacle41_center[1] - 10, obstacle41_center[0] + 10, obstacle41_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle41 = [self.canvas_widget.coords(self.obstacle41)[0] + 3, self.canvas_widget.coords(self.obstacle41)[1] + 3, self.canvas_widget.coords(self.obstacle41)[2] - 3, self.canvas_widget.coords(self.obstacle41)[3] - 3]
    obstacle42_center = self.o + np.array([pixels * 21, pixels * 4])
    self.obstacle42 = self.canvas_widget.create_rectangle(obstacle42_center[0] - 10, obstacle42_center[1] - 10, obstacle42_center[0] + 10, obstacle42_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle42 = [self.canvas_widget.coords(self.obstacle42)[0] + 3, self.canvas_widget.coords(self.obstacle42)[1] + 3, self.canvas_widget.coords(self.obstacle42)[2] - 3, self.canvas_widget.coords(self.obstacle42)[3] - 3]
    obstacle43_center = self.o + np.array([pixels * 19, pixels * 4])
    self.obstacle43 = self.canvas_widget.create_rectangle(obstacle43_center[0] - 10, obstacle43_center[1] - 10, obstacle43_center[0] + 10, obstacle43_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle43 = [self.canvas_widget.coords(self.obstacle43)[0] + 3, self.canvas_widget.coords(self.obstacle43)[1] + 3, self.canvas_widget.coords(self.obstacle43)[2] - 3, self.canvas_widget.coords(self.obstacle43)[3] - 3]
    obstacle44_center = self.o + np.array([pixels * 17, pixels * 10])
    self.obstacle44 = self.canvas_widget.create_rectangle(obstacle44_center[0] - 10, obstacle44_center[1] - 10, obstacle44_center[0] + 10, obstacle44_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle44 = [self.canvas_widget.coords(self.obstacle44)[0] + 3, self.canvas_widget.coords(self.obstacle44)[1] + 3, self.canvas_widget.coords(self.obstacle44)[2] - 3, self.canvas_widget.coords(self.obstacle44)[3] - 3]
    obstacle45_center = self.o + np.array([pixels * 18, pixels * 10])
    self.obstacle45 = self.canvas_widget.create_rectangle(obstacle45_center[0] - 10, obstacle45_center[1] - 10, obstacle45_center[0] + 10, obstacle45_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle45 = [self.canvas_widget.coords(self.obstacle45)[0] + 3, self.canvas_widget.coords(self.obstacle45)[1] + 3, self.canvas_widget.coords(self.obstacle45)[2] - 3, self.canvas_widget.coords(self.obstacle45)[3] - 3]
    obstacle46_center = self.o + np.array([pixels * 19, pixels * 10])
    self.obstacle46 = self.canvas_widget.create_rectangle(obstacle46_center[0] - 10, obstacle46_center[1] - 10, obstacle46_center[0] + 10, obstacle46_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle46 = [self.canvas_widget.coords(self.obstacle46)[0] + 3, self.canvas_widget.coords(self.obstacle46)[1] + 3, self.canvas_widget.coords(self.obstacle46)[2] - 3, self.canvas_widget.coords(self.obstacle46)[3] - 3]
    obstacle47_center = self.o + np.array([pixels * 19, pixels * 9])
    self.obstacle47 = self.canvas_widget.create_rectangle(obstacle47_center[0] - 10, obstacle47_center[1] - 10, obstacle47_center[0] + 10, obstacle47_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle47 = [self.canvas_widget.coords(self.obstacle47)[0] + 3, self.canvas_widget.coords(self.obstacle47)[1] + 3, self.canvas_widget.coords(self.obstacle47)[2] - 3, self.canvas_widget.coords(self.obstacle47)[3] - 3]
    obstacle48_center = self.o + np.array([pixels * 19, pixels * 8])
    self.obstacle48 = self.canvas_widget.create_rectangle(obstacle48_center[0] - 10, obstacle48_center[1] - 10, obstacle48_center[0] + 10, obstacle48_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle48 = [self.canvas_widget.coords(self.obstacle48)[0] + 3, self.canvas_widget.coords(self.obstacle48)[1] + 3, self.canvas_widget.coords(self.obstacle48)[2] - 3, self.canvas_widget.coords(self.obstacle48)[3] - 3]
    obstacle49_center = self.o + np.array([pixels * 11, pixels * 23])
    self.obstacle49 = self.canvas_widget.create_rectangle(obstacle49_center[0] - 10, obstacle49_center[1] - 10, obstacle49_center[0] + 10, obstacle49_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle49 = [self.canvas_widget.coords(self.obstacle49)[0] + 3, self.canvas_widget.coords(self.obstacle49)[1] + 3, self.canvas_widget.coords(self.obstacle49)[2] - 3, self.canvas_widget.coords(self.obstacle49)[3] - 3]
    obstacle50_center = self.o + np.array([pixels * 10, pixels * 23])
    self.obstacle50 = self.canvas_widget.create_rectangle(obstacle50_center[0] - 10, obstacle50_center[1] - 10, obstacle50_center[0] + 10, obstacle50_center[1] + 10, outline='grey', fill='#00BFFF')
    self.coords_obstacle50 = [self.canvas_widget.coords(self.obstacle50)[0] + 3, self.canvas_widget.coords(self.obstacle50)[1] + 3, self.canvas_widget.coords(self.obstacle50)[2] - 3, self.canvas_widget.coords(self.obstacle50)[3] - 3]
    self.agent = self.canvas_widget.create_oval(self.o[0] - 7, self.o[1] - 7, self.o[0] + 7, self.o[1] + 7, outline='#FF1493', fill='#FF1493')
    flag_center = self.o + np.array([pixels * 20, pixels * 20])
    self.flag = self.canvas_widget.create_rectangle(flag_center[0] - 10, flag_center[1] - 10, flag_center[0] + 10, flag_center[1] + 10, outline='grey', fill='yellow')
    self.coords_flag = [self.canvas_widget.coords(self.flag)[0] + 3, self.canvas_widget.coords(self.flag)[1] + 3, self.canvas_widget.coords(self.flag)[2] - 3, self.canvas_widget.coords(self.flag)[3] - 3]
    self.canvas_widget.pack()

class Environment(tk.Tk, object):

    def __init__(self):
        super(Environment, self).__init__()
        self.action_space = ['up', 'down', 'left', 'right']
        self.n_actions = len(self.action_space)
        self.title('RL Q-learning. Sichkar Valentyn')
        self.geometry('{0}x{1}'.format(env_height * pixels, env_height * pixels))
        self.build_environment()
        self.d = {}
        self.f = {}
        self.i = 0
        self.c = True
        self.longest = 0
        self.shortest = 0

    def build_environment(self):
        self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
        for column in range(0, env_width * pixels, pixels):
            x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        for row in range(0, env_height * pixels, pixels):
            x0, y0, x1, y1 = (0, row, env_height * pixels, row)
            self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
        img_obstacle1 = Image.open('images/road_closed1.png')
        self.obstacle1_object = ImageTk.PhotoImage(img_obstacle1)
        img_obstacle2 = Image.open('images/tree1.png')
        self.obstacle2_object = ImageTk.PhotoImage(img_obstacle2)
        img_obstacle3 = Image.open('images/tree2.png')
        self.obstacle3_object = ImageTk.PhotoImage(img_obstacle3)
        img_obstacle4 = Image.open('images/building1.png')
        self.obstacle4_object = ImageTk.PhotoImage(img_obstacle4)
        img_obstacle5 = Image.open('images/building2.png')
        self.obstacle5_object = ImageTk.PhotoImage(img_obstacle5)
        img_obstacle6 = Image.open('images/road_closed2.png')
        self.obstacle6_object = ImageTk.PhotoImage(img_obstacle6)
        img_obstacle7 = Image.open('images/road_closed3.png')
        self.obstacle7_object = ImageTk.PhotoImage(img_obstacle7)
        img_obstacle8 = Image.open('images/traffic_lights.png')
        self.obstacle8_object = ImageTk.PhotoImage(img_obstacle8)
        img_obstacle9 = Image.open('images/pedestrian.png')
        self.obstacle9_object = ImageTk.PhotoImage(img_obstacle9)
        img_obstacle10 = Image.open('images/shop.png')
        self.obstacle10_object = ImageTk.PhotoImage(img_obstacle10)
        img_obstacle11 = Image.open('images/bank1.png')
        self.obstacle11_object = ImageTk.PhotoImage(img_obstacle11)
        img_obstacle12 = Image.open('images/bank2.png')
        self.obstacle12_object = ImageTk.PhotoImage(img_obstacle12)
        self.obstacle1 = self.canvas_widget.create_image(pixels * 3, pixels * 4, anchor='nw', image=self.obstacle2_object)
        self.obstacle2 = self.canvas_widget.create_image(0, pixels * 2, anchor='nw', image=self.obstacle6_object)
        self.obstacle3 = self.canvas_widget.create_image(pixels, 0, anchor='nw', image=self.obstacle5_object)
        self.obstacle4 = self.canvas_widget.create_image(pixels * 3, pixels * 2, anchor='nw', image=self.obstacle2_object)
        self.obstacle5 = self.canvas_widget.create_image(pixels * 4, 0, anchor='nw', image=self.obstacle12_object)
        self.obstacle6 = self.canvas_widget.create_image(pixels * 5, pixels * 3, anchor='nw', image=self.obstacle7_object)
        self.obstacle7 = self.canvas_widget.create_image(pixels * 7, pixels * 3, anchor='nw', image=self.obstacle9_object)
        self.obstacle8 = self.canvas_widget.create_image(pixels * 6, pixels, anchor='nw', image=self.obstacle10_object)
        self.obstacle9 = self.canvas_widget.create_image(pixels * 5, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle10 = self.canvas_widget.create_image(pixels * 6, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle11 = self.canvas_widget.create_image(pixels * 5, pixels * 6, anchor='nw', image=self.obstacle4_object)
        self.obstacle12 = self.canvas_widget.create_image(pixels * 5, pixels * 7, anchor='nw', image=self.obstacle4_object)
        self.obstacle13 = self.canvas_widget.create_image(0, pixels * 8, anchor='nw', image=self.obstacle3_object)
        self.obstacle14 = self.canvas_widget.create_image(pixels * 3, pixels * 7, anchor='nw', image=self.obstacle8_object)
        self.obstacle15 = self.canvas_widget.create_image(0, pixels * 4, anchor='nw', image=self.obstacle1_object)
        self.obstacle16 = self.canvas_widget.create_image(pixels * 8, 0, anchor='nw', image=self.obstacle3_object)
        self.obstacle17 = self.canvas_widget.create_image(pixels * 7, pixels * 7, anchor='nw', image=self.obstacle4_object)
        self.obstacle18 = self.canvas_widget.create_image(pixels, pixels * 6, anchor='nw', image=self.obstacle11_object)
        self.obstacle19 = self.canvas_widget.create_image(pixels * 8, pixels * 3, anchor='nw', image=self.obstacle8_object)
        self.obstacle20 = self.canvas_widget.create_image(pixels * 7, pixels * 6, anchor='nw', image=self.obstacle4_object)
        self.obstacle21 = self.canvas_widget.create_image(pixels * 7, pixels * 5, anchor='nw', image=self.obstacle4_object)
        self.obstacle22 = self.canvas_widget.create_image(pixels * 2, pixels * 3, anchor='nw', image=self.obstacle2_object)
        img_flag = Image.open('images/flag.png')
        self.flag_object = ImageTk.PhotoImage(img_flag)
        self.flag = self.canvas_widget.create_image(pixels * 6, pixels * 6, anchor='nw', image=self.flag_object)
        img_robot = Image.open('images/agent1.png')
        self.robot = ImageTk.PhotoImage(img_robot)
        self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
        self.canvas_widget.pack()

    def reset(self):
        self.update()
        self.canvas_widget.delete(self.agent)
        self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
        self.d = {}
        self.i = 0
        return self.canvas_widget.coords(self.agent)

    def step(self, action):
        state = self.canvas_widget.coords(self.agent)
        base_action = np.array([0, 0])
        if action == 0:
            if state[1] >= pixels:
                base_action[1] -= pixels
        elif action == 1:
            if state[1] < (env_height - 1) * pixels:
                base_action[1] += pixels
        elif action == 2:
            if state[0] < (env_width - 1) * pixels:
                base_action[0] += pixels
        elif action == 3:
            if state[0] >= pixels:
                base_action[0] -= pixels
        self.canvas_widget.move(self.agent, base_action[0], base_action[1])
        self.d[self.i] = self.canvas_widget.coords(self.agent)
        next_state = self.d[self.i]
        self.i += 1
        if next_state == self.canvas_widget.coords(self.flag):
            reward = 1
            done = True
            next_state = 'goal'
            if self.c == True:
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
                self.c = False
                self.longest = len(self.d)
                self.shortest = len(self.d)
            if len(self.d) < len(self.f):
                self.shortest = len(self.d)
                self.f = {}
                for j in range(len(self.d)):
                    self.f[j] = self.d[j]
            if len(self.d) > self.longest:
                self.longest = len(self.d)
        elif next_state in [self.canvas_widget.coords(self.obstacle1), self.canvas_widget.coords(self.obstacle2), self.canvas_widget.coords(self.obstacle3), self.canvas_widget.coords(self.obstacle4), self.canvas_widget.coords(self.obstacle5), self.canvas_widget.coords(self.obstacle6), self.canvas_widget.coords(self.obstacle7), self.canvas_widget.coords(self.obstacle8), self.canvas_widget.coords(self.obstacle9), self.canvas_widget.coords(self.obstacle10), self.canvas_widget.coords(self.obstacle11), self.canvas_widget.coords(self.obstacle12), self.canvas_widget.coords(self.obstacle13), self.canvas_widget.coords(self.obstacle14), self.canvas_widget.coords(self.obstacle15), self.canvas_widget.coords(self.obstacle16), self.canvas_widget.coords(self.obstacle17), self.canvas_widget.coords(self.obstacle18), self.canvas_widget.coords(self.obstacle19), self.canvas_widget.coords(self.obstacle20), self.canvas_widget.coords(self.obstacle21), self.canvas_widget.coords(self.obstacle22)]:
            reward = -1
            done = True
            next_state = 'obstacle'
            self.d = {}
            self.i = 0
        else:
            reward = 0
            done = False
        return (next_state, reward, done)

    def render(self):
        self.update()

    def final(self):
        self.canvas_widget.delete(self.agent)
        print('The shortest route:', self.shortest)
        print('The longest route:', self.longest)
        origin = np.array([20, 20])
        self.initial_point = self.canvas_widget.create_oval(origin[0] - 5, origin[1] - 5, origin[0] + 5, origin[1] + 5, fill='blue', outline='blue')
        for j in range(len(self.f)):
            print(self.f[j])
            self.track = self.canvas_widget.create_oval(self.f[j][0] + origin[0] - 5, self.f[j][1] + origin[0] - 5, self.f[j][0] + origin[0] + 5, self.f[j][1] + origin[0] + 5, fill='blue', outline='blue')
            a[j] = self.f[j]

def build_environment(self):
    self.canvas_widget = tk.Canvas(self, bg='white', height=env_height * pixels, width=env_width * pixels)
    for column in range(0, env_width * pixels, pixels):
        x0, y0, x1, y1 = (column, 0, column, env_height * pixels)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    for row in range(0, env_height * pixels, pixels):
        x0, y0, x1, y1 = (0, row, env_height * pixels, row)
        self.canvas_widget.create_line(x0, y0, x1, y1, fill='grey')
    img_obstacle1 = Image.open('images/road_closed1.png')
    self.obstacle1_object = ImageTk.PhotoImage(img_obstacle1)
    img_obstacle2 = Image.open('images/tree1.png')
    self.obstacle2_object = ImageTk.PhotoImage(img_obstacle2)
    img_obstacle3 = Image.open('images/tree2.png')
    self.obstacle3_object = ImageTk.PhotoImage(img_obstacle3)
    img_obstacle4 = Image.open('images/building1.png')
    self.obstacle4_object = ImageTk.PhotoImage(img_obstacle4)
    img_obstacle5 = Image.open('images/building2.png')
    self.obstacle5_object = ImageTk.PhotoImage(img_obstacle5)
    img_obstacle6 = Image.open('images/road_closed2.png')
    self.obstacle6_object = ImageTk.PhotoImage(img_obstacle6)
    img_obstacle7 = Image.open('images/road_closed3.png')
    self.obstacle7_object = ImageTk.PhotoImage(img_obstacle7)
    img_obstacle8 = Image.open('images/traffic_lights.png')
    self.obstacle8_object = ImageTk.PhotoImage(img_obstacle8)
    img_obstacle9 = Image.open('images/pedestrian.png')
    self.obstacle9_object = ImageTk.PhotoImage(img_obstacle9)
    img_obstacle10 = Image.open('images/shop.png')
    self.obstacle10_object = ImageTk.PhotoImage(img_obstacle10)
    img_obstacle11 = Image.open('images/bank1.png')
    self.obstacle11_object = ImageTk.PhotoImage(img_obstacle11)
    img_obstacle12 = Image.open('images/bank2.png')
    self.obstacle12_object = ImageTk.PhotoImage(img_obstacle12)
    self.obstacle1 = self.canvas_widget.create_image(pixels * 3, pixels * 4, anchor='nw', image=self.obstacle2_object)
    self.obstacle2 = self.canvas_widget.create_image(0, pixels * 2, anchor='nw', image=self.obstacle6_object)
    self.obstacle3 = self.canvas_widget.create_image(pixels, 0, anchor='nw', image=self.obstacle5_object)
    self.obstacle4 = self.canvas_widget.create_image(pixels * 3, pixels * 2, anchor='nw', image=self.obstacle2_object)
    self.obstacle5 = self.canvas_widget.create_image(pixels * 4, 0, anchor='nw', image=self.obstacle12_object)
    self.obstacle6 = self.canvas_widget.create_image(pixels * 5, pixels * 3, anchor='nw', image=self.obstacle7_object)
    self.obstacle7 = self.canvas_widget.create_image(pixels * 7, pixels * 3, anchor='nw', image=self.obstacle9_object)
    self.obstacle8 = self.canvas_widget.create_image(pixels * 6, pixels, anchor='nw', image=self.obstacle10_object)
    self.obstacle9 = self.canvas_widget.create_image(pixels * 5, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle10 = self.canvas_widget.create_image(pixels * 6, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle11 = self.canvas_widget.create_image(pixels * 5, pixels * 6, anchor='nw', image=self.obstacle4_object)
    self.obstacle12 = self.canvas_widget.create_image(pixels * 5, pixels * 7, anchor='nw', image=self.obstacle4_object)
    self.obstacle13 = self.canvas_widget.create_image(0, pixels * 8, anchor='nw', image=self.obstacle3_object)
    self.obstacle14 = self.canvas_widget.create_image(pixels * 3, pixels * 7, anchor='nw', image=self.obstacle8_object)
    self.obstacle15 = self.canvas_widget.create_image(0, pixels * 4, anchor='nw', image=self.obstacle1_object)
    self.obstacle16 = self.canvas_widget.create_image(pixels * 8, 0, anchor='nw', image=self.obstacle3_object)
    self.obstacle17 = self.canvas_widget.create_image(pixels * 7, pixels * 7, anchor='nw', image=self.obstacle4_object)
    self.obstacle18 = self.canvas_widget.create_image(pixels, pixels * 6, anchor='nw', image=self.obstacle11_object)
    self.obstacle19 = self.canvas_widget.create_image(pixels * 8, pixels * 3, anchor='nw', image=self.obstacle8_object)
    self.obstacle20 = self.canvas_widget.create_image(pixels * 7, pixels * 6, anchor='nw', image=self.obstacle4_object)
    self.obstacle21 = self.canvas_widget.create_image(pixels * 7, pixels * 5, anchor='nw', image=self.obstacle4_object)
    self.obstacle22 = self.canvas_widget.create_image(pixels * 2, pixels * 3, anchor='nw', image=self.obstacle2_object)
    img_flag = Image.open('images/flag.png')
    self.flag_object = ImageTk.PhotoImage(img_flag)
    self.flag = self.canvas_widget.create_image(pixels * 6, pixels * 6, anchor='nw', image=self.flag_object)
    img_robot = Image.open('images/agent1.png')
    self.robot = ImageTk.PhotoImage(img_robot)
    self.agent = self.canvas_widget.create_image(0, 0, anchor='nw', image=self.robot)
    self.canvas_widget.pack()

