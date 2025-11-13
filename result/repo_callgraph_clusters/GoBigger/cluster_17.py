# Cluster 17

class RealtimeRender(BaseRender):
    """
    Overview:
        Used in real-time games, giving a global view
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True, padding=20, map_width=128, map_height=128):
        super(RealtimeRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
        self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
        self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
        self.padding = padding

    def render_all_balls_colorful(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        for ball in food_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in thorns_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in spore_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for player in players:
            for ball in player.get_balls():
                x = ball.position.x * self.scale_ratio_w + self.padding
                y = ball.position.y * self.scale_ratio_h + self.padding
                r = ball.radius * self.scale_ratio_w
                pygame.draw.circle(self.screen, PLAYER_COLORS[int(ball.team_id)][0], Vector2(x, y), r)
                pygame.draw.polygon(self.screen, PLAYER_COLORS[int(ball.team_id)][0], to_arrow(Vector2(x, y), r, ball.direction))
                font_size = int(r / 1.6)
                font = pygame.font.SysFont('arial', max(font_size, 8), True)
                txt = font.render('{}'.format(chr(int(ball.player_id % player_num_per_team) + 65)), True, WHITE)
                txt_rect = txt.get_rect(center=(x, y))
                self.screen.blit(txt, txt_rect)

    def fill(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team=1, fps=20, leaderboard=None):
        self.screen.fill(BACKGROUND)
        self.render_all_balls_colorful(food_balls, thorns_balls, spore_balls, players, player_num_per_team)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        font = pygame.font.SysFont('Menlo', 15, True)
        if leaderboard is not None:
            leaderboard = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
            for index, (team_id, team_size) in enumerate(leaderboard):
                pos_txt = font.render('{}: {:.5f}'.format(team_id, team_size), 1, RED)
                self.screen.blit(pos_txt, (20, 10 + 10 * (index * 2 + 1)))

    def show(self):
        pygame.display.update()

    def close(self):
        pygame.quit()

def close(self):
    pygame.quit()

class RealtimePartialRender(BaseRender):
    """
    Overview:
        Used in real-time games to give the player a visible field of view. The corresponding player can be obtained by specifying the player name. The default is the first player
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=0, info_height=0, with_show=True):
        super(RealtimePartialRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)

    def render_all_balls_colorful(self, overlap, player_num_per_team=1, scale_ratio_w=1, scale_ratio_h=1, start_x=0, start_y=0):
        for ball in overlap['food']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in overlap['thorns']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in overlap['spore']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball in overlap['clone']:
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[6], ball[7])
            player_id = int(ball[8])
            team_id = int(ball[9])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def fill(self, global_state, player_state, player_num_per_team=1, fps=20):
        self.screen.fill(BACKGROUND)
        rectangle = player_state['rectangle']
        overlap = player_state['overlap']
        leaderboard = global_state['leaderboard']
        frame_count = global_state['last_frame_count']
        map_width, map_height = global_state['border']
        left, top, right, bottom = rectangle
        width_real, height_real, hw_ratio = (right - left, bottom - top, (right - left) / (bottom - top))
        scale_ratio_w = self.game_screen_width / width_real
        scale_ratio_h = self.game_screen_width / height_real
        start_x = left
        start_y = top
        self.render_all_balls_colorful(overlap, player_num_per_team=player_num_per_team, scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h, start_x=start_x, start_y=start_y)
        pygame.draw.line(self.screen, BLACK, ((map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((0 - start_x) * scale_ratio_w, (map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), width=1)
        font = pygame.font.SysFont('Menlo', 15, True)
        assert len(leaderboard) > 0, 'leaderboard could not be None'
        leaderboard = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
        for index, (team_id, team_score) in enumerate(leaderboard):
            pos_txt = font.render('{}: {:.5f}'.format(team_id, team_score), 1, RED)
            self.screen.blit(pos_txt, (20, 10 + 10 * (index * 2 + 1)))
        fps_txt = font.render('fps: ' + str(fps), 1, RED)
        last_frame_txt = font.render('frame_count: {} / {}'.format(frame_count, int(frame_count / 20)), 1, RED)
        self.screen.blit(fps_txt, (20, self.total_screen_height - 30))
        self.screen.blit(last_frame_txt, (20, self.total_screen_height - 50))

    def show(self):
        pygame.display.update()

    def close(self):
        pygame.quit()

def close(self):
    pygame.quit()

class PBRender(BaseRender):

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=60, info_height=20, padding=20, map_width=128, map_height=128, pb_data=None, player_num_per_team=1):
        super(PBRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=True)
        self.padding = padding
        self.pb_data = pb_data
        assert pb_data is not None
        self.map_width = self.pb_data['cfg']['map_width']
        self.map_height = self.pb_data['cfg']['map_height']
        self.player_num_per_team = self.pb_data['cfg']['player_num_per_team']
        self.speed_button = SpeedButton(20, game_screen_height + info_height / 2, 'x1')
        self.play_button = PlayButton(40, game_screen_height + info_height / 2, '||')
        self.scrollbar = Scrollbar(60, game_screen_height + info_height / 2, game_screen_width - 80)
        self.if_play = True
        self.speed = 1
        self.frame_now = 1
        self.frame_target = self.frame_now + self.speed
        self.overlap = copy.deepcopy(self.pb_data[self.frame_now][0])
        self.leaderboard = self.pb_data[self.frame_now][2]
        self.frame_total = len(self.pb_data)
        self.rate = self.frame_now / self.frame_total

    def set_data(self):
        if self.if_play:
            if self.frame_target == self.frame_now:
                return
            if self.frame_target < self.frame_now:
                self.frame_now = 1
                self.overlap = copy.deepcopy(self.pb_data[self.frame_now][0])
                self.leaderboard = self.pb_data[self.frame_now][2]
            for i in range(self.frame_now + 1, self.frame_target + 1):
                if i in self.pb_data:
                    diff_balls_modify, diff_balls_remove, self.leaderboard = self.pb_data[i]
                    for index, balls in enumerate(diff_balls_modify[:-1]):
                        for ball_id, ball in balls.items():
                            self.overlap[index][ball_id] = ball
                    self.overlap[-1] = diff_balls_modify[-1]
                    for index, ball_ids in enumerate(diff_balls_remove):
                        for ball_id in ball_ids:
                            self.overlap[index].pop(ball_id, None)
        self.frame_now = self.frame_target

    def render_all_balls_colorful(self, scale_ratio_w=1, scale_ratio_h=1):
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(self.screen, BLACK, (self.game_screen_width, 0), (self.game_screen_width, self.game_screen_width + self.padding), width=1)
        for ball_id, ball in self.overlap[0].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[1].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball_id, ball in self.overlap[2].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[3].items():
            x = ball[0] * scale_ratio_w + self.padding
            y = ball[1] * scale_ratio_h + self.padding
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[3], ball[4])
            player_id = int(ball[5])
            team_id = int(ball[6])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % self.player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def render_rect_balls_colorful(self, scale_ratio_w=1, scale_ratio_h=1, start_x=0, start_y=0):
        pygame.draw.line(self.screen, BLACK, ((self.map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((0 - start_x) * scale_ratio_w, (self.map_height - start_y) * scale_ratio_h), width=1)
        pygame.draw.line(self.screen, BLACK, ((0 - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), ((self.map_width - start_x) * scale_ratio_w, (0 - start_y) * scale_ratio_h), width=1)
        for ball_id, ball in self.overlap[0].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, FOOD_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[1].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.polygon(self.screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball_id, ball in self.overlap[2].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            pygame.draw.circle(self.screen, SPORE_COLOR, Vector2(x, y), r)
        for ball_id, ball in self.overlap[3].items():
            x = (ball[0] - start_x) * scale_ratio_w
            y = (ball[1] - start_y) * scale_ratio_h
            r = ball[2] * scale_ratio_w
            direction = Vector2(ball[3], ball[4])
            player_id = int(ball[5])
            team_id = int(ball[6])
            pygame.draw.circle(self.screen, PLAYER_COLORS[team_id][0], Vector2(x, y), r)
            point_list = to_arrow(Vector2(x, y), r, direction)
            pygame.draw.polygon(self.screen, PLAYER_COLORS[team_id][0], point_list)
            font_size = int(r / 1.6)
            font = pygame.font.SysFont('arial', max(font_size, 6), True)
            txt = font.render('{}'.format(chr(player_id % self.player_num_per_team + 65)), True, WHITE)
            txt_rect = txt.get_rect(center=(x, y))
            self.screen.blit(txt, txt_rect)

    def render_leaderboard_colorful(self, leaderboard):
        start = 10
        team_score = sorted(leaderboard.items(), key=lambda d: d[1], reverse=True)
        for index, (team_id, score) in enumerate(team_score):
            start += 20
            font = pygame.font.SysFont('arial', 8, True)
            fps_txt = font.render('{} : {:.2f}'.format(team_id, score), True, PLAYER_COLORS[int(team_id)][0])
            self.screen.blit(fps_txt, (self.game_screen_width + 5, start))

    def fill(self, rectangle=None):
        self.screen.fill(BACKGROUND)
        if rectangle is not None:
            left, top, right, bottom = rectangle
            width_real, height_real, hw_ratio = (right - left, bottom - top, (right - left) / (bottom - top))
            scale_ratio_w = self.game_screen_width / width_real
            scale_ratio_h = self.game_screen_width / height_real
            start_x = left
            start_y = top
            self.render_rect_balls_colorful(scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h, start_x=start_x, start_y=start_y)
        else:
            scale_ratio_w = (self.game_screen_width - self.padding * 2) / self.map_width
            scale_ratio_h = (self.game_screen_height - self.padding * 2) / self.map_height
            start_x = 0
            start_y = 0
            self.render_all_balls_colorful(scale_ratio_w=scale_ratio_w, scale_ratio_h=scale_ratio_h)
        font = pygame.font.SysFont('Menlo', 15, True)
        assert len(self.leaderboard) > 0, 'leaderboard could not be None'
        self.render_leaderboard_colorful(self.leaderboard)
        self.speed_button.display(self.screen)
        self.play_button.display(self.screen)
        self.scrollbar.display(self.screen, self.rate)

    def show(self):
        self.fill()
        pygame.display.update()
        self.set_data()
        if self.if_play:
            self.frame_target = min(self.frame_now + self.speed, self.frame_total)
        self.rate = self.frame_now / self.frame_total

    def close(self):
        pygame.quit()

    def on_pressed(self, position):
        if self.play_button.check_click(position):
            self.if_play = self.play_button.on_pressed()
        elif self.speed_button.check_click(position):
            self.speed = self.speed_button.on_pressed()
        elif self.scrollbar.check_click(position):
            self.rate = self.scrollbar.on_pressed(position)
            self.frame_target = int(self.rate * self.frame_total)

def close(self):
    pygame.quit()

class EnvRender(BaseRender):
    """
    Overview:
        No need to use a new window, giving a global view and the view that each player can see
    """

    def __init__(self, game_screen_width=512, game_screen_height=512, info_width=60, info_height=0, with_show=False, padding=20, map_width=256, map_height=256):
        super(EnvRender, self).__init__(game_screen_width=game_screen_width, game_screen_height=game_screen_height, info_width=info_width, info_height=info_height, with_show=with_show)
        self.scale_ratio_w = (self.game_screen_width - padding * 2) / map_width
        self.scale_ratio_h = (self.game_screen_height - padding * 2) / map_height
        self.padding = padding

    def get_screen(self, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        screen_all = pygame.Surface((self.total_screen_width, self.total_screen_height))
        screen_all = self.render_all_balls_colorful(screen_all, food_balls, thorns_balls, spore_balls, players, player_num_per_team)
        screen_all = self.render_leaderboard_colorful(screen_all, players, player_num_per_team)
        screen_data_all = pygame.surfarray.array3d(screen_all)
        screen_data_all = np.rot90(np.fliplr(cv2.cvtColor(screen_data_all, cv2.COLOR_RGB2BGR)))
        return screen_data_all

    def render_all_balls_colorful(self, screen, food_balls, thorns_balls, spore_balls, players, player_num_per_team):
        screen.fill(BACKGROUND)
        pygame.draw.line(screen, RED, (self.padding, self.padding), (self.game_screen_width - self.padding, self.padding), width=1)
        pygame.draw.line(screen, RED, (self.padding, self.padding), (self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, RED, (self.padding, self.game_screen_width - self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, RED, (self.game_screen_width - self.padding, self.padding), (self.game_screen_width - self.padding, self.game_screen_width - self.padding), width=1)
        pygame.draw.line(screen, BLACK, (self.game_screen_width, 0), (self.game_screen_width, self.game_screen_width + self.padding), width=1)
        for ball in food_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(screen, FOOD_COLOR, Vector2(x, y), r)
        for ball in thorns_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.polygon(screen, THORNS_COLOR, to_aliased_circle(Vector2(x, y), r))
        for ball in spore_balls:
            x = ball.position.x * self.scale_ratio_w + self.padding
            y = ball.position.y * self.scale_ratio_h + self.padding
            r = ball.radius * self.scale_ratio_w
            pygame.draw.circle(screen, SPORE_COLOR, Vector2(x, y), r)
        for player in players:
            for ball in player.get_balls():
                x = ball.position.x * self.scale_ratio_w + self.padding
                y = ball.position.y * self.scale_ratio_h + self.padding
                r = ball.radius * self.scale_ratio_w
                pygame.draw.circle(screen, PLAYER_COLORS[int(ball.team_id)][0], Vector2(x, y), r)
                point_list = to_arrow(Vector2(x, y), r, ball.direction)
                pygame.draw.polygon(screen, PLAYER_COLORS[int(ball.team_id)][0], point_list)
                font_size = int(r / 1.6)
                font = pygame.font.SysFont('arial', max(font_size, 8), True)
                txt = font.render('{}'.format(chr(int(ball.player_id % player_num_per_team) + 65)), True, WHITE)
                txt_rect = txt.get_rect(center=(x, y))
                screen.blit(txt, txt_rect)
        return screen

    def render_leaderboard_colorful(self, screen, players, player_num_per_team):
        team_name_score = {}
        team_score = {}
        for player in players:
            if player.team_id not in team_name_score:
                team_name_score[player.team_id] = {}
                team_score[player.team_id] = 0
            team_name_score[player.team_id][player.player_id] = player.get_total_score()
            team_score[player.team_id] += team_name_score[player.team_id][player.player_id]
        team_score = sorted(team_score.items(), key=lambda d: d[1], reverse=True)
        start = 10
        for index, (team_id, score) in enumerate(team_score):
            start += 20
            font = pygame.font.SysFont('arial', 8, True)
            fps_txt = font.render('{} : {:.2f}'.format(team_id, score), True, PLAYER_COLORS[int(team_id)][0])
            screen.blit(fps_txt, (self.game_screen_width + 5, start))
            start += 20
            font = pygame.font.SysFont('arial', 7, True)
            for player_id, player_score in team_name_score[team_id].items():
                fps_txt = font.render('{} : {:.2f}'.format(chr(player_id % player_num_per_team + 65), player_score), True, PLAYER_COLORS[team_id][0])
                screen.blit(fps_txt, (self.game_screen_width + 5, start))
                start += 20
        return screen

    def show(self):
        raise NotImplementedError

    def close(self):
        pygame.quit()

def close(self):
    pygame.quit()

