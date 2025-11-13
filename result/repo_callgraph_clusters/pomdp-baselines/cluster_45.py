# Cluster 45

class Game(game.AbstractGame):
    """Key To Door Game."""

    def __init__(self, rng, num_apples=10, apple_reward=(1, 10), fix_apple_reward_in_episode=True, final_reward=10.0, respawn_every=common.DEFAULT_APPLE_RESPAWN_TIME, crop=True, max_frames=MAX_FRAMES_PER_PHASE_SR, REWARD_GRID=REWARD_GRID_SR):
        del rng
        self._num_apples = num_apples
        self._apple_reward = apple_reward
        self._fix_apple_reward_in_episode = fix_apple_reward_in_episode
        self._final_reward = final_reward
        self._respawn_every = respawn_every
        self._crop = crop
        self._max_frames = max_frames
        self._episode_length = sum(self._max_frames.values())
        self._REWARD_GRID = REWARD_GRID
        self._num_actions = common.NUM_ACTIONS
        self._colours = common.FIXED_COLOURS.copy()
        self._colours.update(COLOURS)
        self._extra_observation_fields = ['chapter_reward_as_string']

    @property
    def extra_observation_fields(self):
        """The field names of extra observations."""
        return self._extra_observation_fields

    @property
    def num_actions(self):
        """Number of possible actions in the game."""
        return self._num_actions

    @property
    def episode_length(self):
        return self._episode_length

    @property
    def colours(self):
        """Symbol to colour map for key to door."""
        return self._colours

    def _make_explore_phase(self):
        explore_grid = common.keep_n_characters_in_grid(EXPLORE_GRID, common.KEY, 1)
        explore_grid = common.keep_n_characters_in_grid(explore_grid, common.PLAYER, 1)
        return ascii_art.ascii_art_to_game(art=explore_grid, what_lies_beneath=' ', sprites={common.PLAYER: PlayerSprite, common.KEY: KeySprite, common.INDICATOR: ascii_art.Partial(objects.IndicatorObjectSprite, char_to_track=common.KEY, override_position=(0, 5)), common.TIMER: ascii_art.Partial(common.TimerSprite, self._max_frames['explore'])}, update_schedule=[common.PLAYER, common.KEY, common.INDICATOR, common.TIMER], z_order=[common.KEY, common.INDICATOR, common.PLAYER, common.TIMER])

    def _make_distractor_phase(self):
        return common.distractor_phase(player_sprite=PlayerSprite, num_apples=self._num_apples, max_frames=self._max_frames['distractor'], apple_reward=self._apple_reward, fix_apple_reward_in_episode=self._fix_apple_reward_in_episode, respawn_every=self._respawn_every)

    def _make_reward_phase(self):
        reward_grid = common.keep_n_characters_in_grid(self._REWARD_GRID, common.DOOR, 1)
        reward_grid = common.keep_n_characters_in_grid(reward_grid, common.PLAYER, 1)
        return ascii_art.ascii_art_to_game(art=reward_grid, what_lies_beneath=' ', sprites={common.PLAYER: PlayerSprite, common.DOOR: ascii_art.Partial(DoorSprite, pickup_reward=self._final_reward), common.TIMER: ascii_art.Partial(common.TimerSprite, self._max_frames['reward'], track_chapter_reward=True)}, update_schedule=[common.PLAYER, common.DOOR, common.TIMER], z_order=[common.PLAYER, common.DOOR, common.TIMER])

    def make_episode(self):
        """Factory method for generating new episodes of the game."""
        if self._crop:
            croppers = common.get_cropper()
        else:
            croppers = None
        return storytelling.Story([self._make_explore_phase, self._make_distractor_phase, self._make_reward_phase], croppers=croppers)

def make_episode(self):
    """Factory method for generating new episodes of the game."""
    if self._crop:
        croppers = common.get_cropper()
    else:
        croppers = None
    return storytelling.Story([self._make_explore_phase, self._make_distractor_phase, self._make_reward_phase], croppers=croppers)

