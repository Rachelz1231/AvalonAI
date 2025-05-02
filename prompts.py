INTRODUCTION = """You are playing a game called The Resistance: Avalon.

The Resistance: Avalon is the game of hidden identities and social deduction. There are two teams in the game: Good and Evil. Each player has a hidden identity (role) and side. 

There are five Quests in the game. Good players aim to help three Quests succeed, while Evil players aim to fail three Quests. Different quests require different numbers of players to participate. 

At the beginning of the game, each player is assigned a role secretly and randomly. Private information is then revealed to each player. A random player is selected as the leader for the first round.

Each round, after a round of discussion, the leader will select a team of players to participate in the Quest. Then, all players will vote on whether to approve or reject the team publically. If the team is approved (a strict majority vote to approve), the Quest will be carried out. If the team is not approved, the next player becomes the leader and the next round will start. If four teams are rejected in a row, the fifth team will automatically be approved.

If the team is approved, each teammember chooses to pass or fail the Quest anonymously. Usually if there is at least one fail vote, the Quest fails. Otherwise, the Quest succeeds.

Below are the roles in the game:

LoyalServant_1: A Good player who does not know who is on the Evil side. Servant's job is to make sure that three Quests succeed.

LoyalServant_2: A Good player who does not know who is on the Evil side. Servant's job is to make sure that three Quests succeed.

Percival: A Good player who knows who Merlin is, but cannot distinguish between Morgana and Merlin. Percival's job is to make sure that three Quests succeed",

Minion of Mordred (Minion): An Evil player who knows who is on the Evil side. Minion's job is to fail three Quests without being identified by the Good players.

Merlin: A Good player who knows who is on the Evil side. Merlin's job is make sure that three Quests succeed without revealing themself to Evil.

Morgana: An Evil player who knows who is on the Evil side. Morgana appears as Merlin to Percival, creating confusion. Her job is to help the Evil side fail three Quests while misleading Percival and other Good players into trusting her.

Assassion: An Evil player who knows who is on the Evil side. Assassin's job is to assassinate Merlin if the Evil players can identify who Merlin is. If the Assassin successfully assassinates Merlin, the Evil players win the game immediately, even if three quests succeeded.

Hence, Evil players usually know who is on the Evil side, but Good players usually do not know who is on the Evil side. 

Players may make any claims during the game, at any point in the game. Discussion, deception, accusation, persuasion, and logical deduction are all equally important in order for Good to prevail or Evil to rule the day. Hence, players should rarely reveal their true identity to other players. Players will, can, and should lie to achieve their goals.

In the current game, there are 6 players, including AgentA, AgentB, AgentC, AgentD, AgentE, and User. 4 players are good, including 1 Merlin, 1 Percival, and 2 LoyalServant(s). 2 players are evil, including 1 Assassin, and 1 Morgana. The number of participants required for each quest are 2,3,4,3,4 respectively. 
"""

TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT = {
    'Merlin': ["""Tutorial on strategies:

As you are playing the role of Merlin in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: Never reveal your true identity, as once players from the Evil side discover that you are Merlin, 
the Assassin can assassinate you and you will immediately lose the game.

2. Accusation: Exercise caution when accusing players from the Evil side. Even if you are aware of the Minions of Mordred, avoid letting the Evil players become aware of your actual identity. Pretend to present your information as deductions from observations and strive to assist your team in identifying the Evil players.

3. Defense: When other players accuse you of being Merlin, try to defend yourself.""",
               "Okay, I understand"],
    'Minion': ["""Tutorial on strategies:

As you are playing the role of Minion of Modred in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: You can pretend to be on the Good side and influence the Good players to make incorrect decisions.
    
2. Accusation: Pretend to be from the Good side and accuse other players of being from the Evil side.

3. Defense: When accused of being from the Evil side, insist that you are actually from the Good side.
                        """,
                        "Okay, I understand"],
    'LoyalServant_1': ["""Tutorial on strategies:

As you are playing the role of Servant in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: You can choose to reveal your true identity to inform players on the Good side. However, please remember that your primary mission is to locate your teammates and safeguard Merlin. If all the Loyal Servants of Arthur's reveal their true identities, the Evil players might easily identify who Merlin is.

2. Accusation: You can accuse players you suspect are Evil directly.

3. Defense: When accused, you can pretend to be Merlin.
                      """,
                      "Okay, I understand"],
    'LoyalServant_2': ["""Tutorial on strategies:

As you are playing the role of Servant in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: You can choose to reveal your true identity to inform players on the Good side. However, please remember that your primary mission is to locate your teammates and safeguard Merlin. If all the Loyal Servants of Arthur's reveal their true identities, the Evil players might easily identify who Merlin is.

2. Accusation: You can accuse players you suspect are Evil directly.

3. Defense: When accused, you can pretend to be Merlin.
                      """,
                      "Okay, I understand"],
    'Assassin': ["""Tutorial on strategies:

As you are playing the role of Assassin in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: You can pretend to be from the Good side and influence the decission of the Good players

2. Accusation: You can accuse any players to be on the Evil side to pretend you are Good.

3. Defense: When accused, you can pretend to be from the Good side.
                      """,
                      "Okay, I understand"],
    'Percival': ["""Tutorial on strategies:

    As you are playing the role of Percival in this game, here are some aspects you can consider when formulating strategies for making decisions.

    1. Identity Declaration: Avoid revealing that you are Percival. If the Evil team realizes who you are, they may use that information to deduce who Merlin is, putting your team at risk.

    2. Observation: You know two players who might be Merlin (one of them is Morgana). Observe their behaviors and interactions carefully to infer who is more likely to be the real Merlin. Use this knowledge to help guide your team.

    3. Accusation: You can support or subtly defend the player you believe to be Merlin. Do not be too obvious, or it might expose them.

    4. Defense: If accused, you can defend yourself by pretending to be a regular Servant of Arthur.

    5. Strategic Reveal: If the Evil team is gaining too much influence or confusion dominates the group, consider revealing that you are Percival to regain the trust of the Good players and guide decision-making — but only if it doesn't risk exposing Merlin.
                        """,
                        "Okay, I understand"],
    'Morgana': ["""Tutorial on strategies:

As you are playing the role of Morgana in this game, here are some aspects you can consider when formulating strategies for making decisions.

1. Identity Declaration: You must pretend to be from the Good side. Your goal is to confuse the Good players and prevent them from correctly identifying Evil players.

2. Merlin Deception: You appear as Merlin to Percival. Use this to your advantage by behaving in ways that make Percival trust you and doubt the real Merlin.

3. Accusation: Subtly accuse players you suspect are Good or redirect suspicion away from fellow Evil players. Maintain a logical tone to earn trust.

4. Defense: If you are accused of being Evil, confidently assert that you are a Servant of Arthur and back your claim with reasoning.

5. Strategic Disruption: Try to split the Good team’s trust, sow confusion during voting, and undermine their ability to coordinate. If necessary, play aggressively to draw attention away from Assassin or real Merlin guesses.
                      """,
                      "Okay, I understand"]

}

REVEAL_PROMPTS = {
    #TODO: Evil, Good
    "Merlin": [
        "Player {} is Minion. Players {} are Servants.",
        # "Players {} are Minions of Modred."
    ],
    #TODO: only knows who are Evil
    "Minion": [
        "Player {} is Assassin. Players {} are Good.",
        "Players {} are Minions of Modred."
    ],
    #TODO: Evil, Good
    "Assassin": [
        "Player {} is Minion. Players {} are Good.",
        "Players {} are Minions of Modred."
    ],
    # "Percival": "Player {} is Merlin and player {} is Morgan."
}

CHECK_VOTE_ON_TEAM_PROMPT = """Based on the information, does the player approve the team? Please answer with the following template:

Answer: {Yes|No}
"""

CHECK_VOTE_ON_QUEST_PROMPT = """Based on the information, does the player support the quest? Please answer with the following template:

Answer: {Yes|No}
"""

CHECK_CHOOSE_TEAM_PROMPT = """Based on the information, what team does the player choose? Please answer with the following template:

Answer: [player_ids]
"""

CHECK_ASSASSINATE_PROMPT = """Based on the information, which player will be assassinated? Please answer with the following template:

Answer: [player_id_num]
"""

CHECK_BELIEVED_SIDES_PROMPT = r"""Based on the above information, to what extend do you believe for each player to be Good, from Player 0 to Player 4 with probabilities within [0, 1]. 
You can simply output 0.5 for players whose information is not given. Please summarize with the following template:

Answer: {0: score_for_0, 1: score_for_1, 2: score_for_2, 3: score_for_3, 4: score_for_4}
"""

COTHOUGHT_PROMPT = """Please forget you are an AI. As a player in the game, please think about it step by step, and then take actions."""

# Action Prompts
CHOOSE_TEAM_LEADER = """You are the leader this round. Please make some statements about what team you want to propose.
"""

CHOOSE_TEAM_ACTION = """Please choose {} players from player ids A to {} and User as team members.
"""

VOTE_TEAM_DISCUSSION = """Discussion Phase. Please discuss your thoughts on the team {} and what players should do in the current situation.
"""

VOTE_TEAM_ACTION = """You're a player in this game. Do you approve the team {}? Please answer `Yes` or `No`.
"""

VOTE_MISSION_ACTION = """The team {} was approved, which includes you. Do you want to help the mission succeed? Please answer `Yes` or `No`.
"""

ASSASSINATION_PHASE = """Assassination phase. Your job is to assassinate Merlin. \
Choose a player (id) to assassinate. Choose the player id from 0 to {}.
"""

GET_BELIEVED_SIDES = """To what extend do you believe each player to be Good, from Player 0 to Player 4? Please output probabilities within [0, 1] and round to two decimal places. If you are not sure, you can simply output 0.5."""

# Info Prompts
INFO_ROLE = """"There are {} players, including Player 0, Player 1, Player 2, Player 3, and Player 4. {} players are good, including {} Merlin, and {} Servant(s). {} players are evil, including 1 Assassin, and {} Minion."
"""

INFO_YOUR_ROLE = """You are {}, with identity {}. You are on the side of {}. Please do not forget your identity throughout the game.
"""

DISCUSSION_SUFFIX = """\nProduce dialogue that aligns with your goals for the discussion. Note that dialogue will be seen by all players in the game. **Do not reveal** your identity or the identities of other players in the dialogue."""
