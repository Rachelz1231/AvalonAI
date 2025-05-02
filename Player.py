class Player:
    def __init__(self, name, role):
        self.name = name
        self.role = role
        self.teammates = []
        self.speech_history = []
        self.actions = []
        self.found_merlin = False  # Only relevant if the player is the Assassin

    def add_teammate(self, teammate):
        self.teammates.append(teammate)

    def add_speech(self, speech):
        self.speech_history.append(speech)

    def add_action(self, action):
        self.actions.append(action)

    def set_found_merlin(self, found):
        self.found_merlin = found
