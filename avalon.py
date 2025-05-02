import autogen
from prompts import *

from typing import Dict, List, Any, Optional
import random
from Player import Player
import re


# Configure a termination message
termination_msg = "GAME OVER"

# Create configuration for the agents
config_list = [
    {
        "model": "gpt-4",
        "api_key": "",
    }
]

# Define role descriptions (hidden from players)
role_descriptions = {
    "Merlin": "You are Merlin. You have knowledge of who the evil agents are. Your goal is to help the good team win the quests without revealing your identity.",
    "Percival": "You are Percival. You know who Merlin is, but cannot distinguish between Morgana and Merlin. Your goal is to help the good team win quests.",
    "LoyalServant_1": "You are a Loyal Servant of Arthur. You have no special knowledge. Your goal is to help the good team win quests based on logic and observation.",
    "LoyalServant_2": "You are a Loyal Servant of Arthur. You have no special knowledge. Your goal is to help the good team win quests based on logic and observation.",
    "Assassin": "You are the Assassin. You know who the evil agents are. Your goal is to sabotage quests and, at the end of the game, identify and assassinate Merlin.",
    "Morgana": "You are Morgana. You appear as Merlin to Percival. Your goal is to sabotage quests and cause confusion among the good team."
}

# Randomly assign roles to generic agent names
roles = ["Merlin", "Percival", "LoyalServant_1", "LoyalServant_2", "Assassin", "Morgana"]
random.shuffle(roles)

# Create the agents with generic names and keep track of their roles
players_with_roles = {}
players_names = ["AgentA", "AgentB", "AgentC", "AgentD", "AgentE", "User"]

# Create agents and store role mappings
agent_A = autogen.AssistantAgent(
    name="AgentA",
    system_message=INTRODUCTION + "\n\n" + role_descriptions[roles[0]] + "\n" + TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(roles[0].replace("LoyalServant_1", "Servant").replace("LoyalServant_2", "Servant"), [""])[0],
    llm_config={"config_list": config_list},
)
players_with_roles[players_names[0]] = roles[0]

agent_B = autogen.AssistantAgent(
    name="AgentB",
    system_message=INTRODUCTION + "\n\n" + role_descriptions[roles[1]] + "\n" + TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(roles[1].replace("LoyalServant_1", "Servant").replace("LoyalServant_2", "Servant"), [""])[0],
    llm_config={"config_list": config_list},
)
players_with_roles[players_names[1]] = roles[1]

agent_C = autogen.AssistantAgent(
    name="AgentC",
    system_message=INTRODUCTION + "\n\n" + role_descriptions[roles[2]] + "\n" + TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(roles[2].replace("LoyalServant_1", "Servant").replace("LoyalServant_2", "Servant"), [""])[0],
    llm_config={"config_list": config_list},
)
players_with_roles[players_names[2]] = roles[2]

agent_D = autogen.AssistantAgent(
    name="AgentD",
    system_message=INTRODUCTION + "\n\n" + role_descriptions[roles[3]] + "\n" + TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(roles[3].replace("LoyalServant_1", "Servant").replace("LoyalServant_2", "Servant"), [""])[0],
    llm_config={"config_list": config_list},
)
players_with_roles[players_names[3]] = roles[3]

agent_E = autogen.AssistantAgent(
    name="AgentE",
    system_message=INTRODUCTION + "\n\n" + role_descriptions[roles[4]] + "\n" + TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(roles[4].replace("LoyalServant_1", "Servant").replace("LoyalServant_2", "Servant"), [""])[0],
    llm_config={"config_list": config_list},
)
players_with_roles[players_names[4]] = roles[4]


# Assign a role to the user
user_role = roles.pop()  # Assign the last available role to the user
players_with_roles['User'] = user_role
# Instantiate the user as a Player
user_player = Player(name="User", role=user_role)
# Create a user proxy agent to facilitate the game
user_proxy = autogen.UserProxyAgent(
    name="GameMaster",
    human_input_mode="ALWAYS",
    system_message="You are the Game Master who runs the Avalon game. You can speak with the agents and see their responses.",
    code_execution_config=False,
)


# AgentEval-style helper agents for AgentB
critic_agent = autogen.AssistantAgent(
    name="CriticAgent",
    system_message="You are the CriticAgent. Given a proposed response, your task is to define 2–3 criteria for evaluating how strategic and persuasive it is in the context of social deduction.",
    llm_config={"config_list": config_list},
)
quantifier_agent = autogen.AssistantAgent(
    name="QuantifierAgent",
    system_message="You are the QuantifierAgent. Your job is to score the draft response on the given criteria from 0 (poor) to 1 (excellent), providing justifications.",
    llm_config={"config_list": config_list},
)
verifier_agent = autogen.AssistantAgent(
    name="VerifierAgent",
    system_message="You are the VerifierAgent. Ensure the final response aligns with criteria and scores. If not, revise it. Return only the improved response and do NOT prefix your response with words like 'Final:', 'Conclusion:', or similar summarizing phrases. Speak naturally and directly.",
    llm_config={"config_list": config_list},
)

# RA Self-Feedback agent for AgentC
feedback_agent_c = autogen.AssistantAgent(
    name="FeedbackAgentC",
    system_message="You are a self-feedback agent. Given a draft response, your job is to provide natural language feedback on how to improve it for strategic quality, clarity, and impact in a social deduction game.",
    llm_config={"config_list": config_list},
)



# All agents in the game (excluding the Game Master)
all_agents = [agent_A, agent_B, agent_C, agent_D, agent_E]
all_players = all_agents + [user_player]


# Create the reverse mapping: role -> agent
role_to_player = {role: player for player, role in players_with_roles.items()}

# Game state tracking
quest_results = []


# Update the initialize_game function to handle the user separately when sending messages

def initialize_game():
    # Helper to resolve string names to actual agent or user_player objects
    def get_player_object(name_or_agent):
        if isinstance(name_or_agent, str):
            if name_or_agent == "User":
                return user_player
            else:
                return next(agent for agent in all_agents if agent.name == name_or_agent)
        return name_or_agent

    # Get agents by their roles (resolve to actual objects)
    merlin = get_player_object(role_to_player["Merlin"])
    percival = get_player_object(role_to_player["Percival"])
    loyal_servant_1 = get_player_object(role_to_player["LoyalServant_1"])
    loyal_servant_2 = get_player_object(role_to_player["LoyalServant_2"])
    assassin = get_player_object(role_to_player["Assassin"])
    morgana = get_player_object(role_to_player["Morgana"])

    # Set up initial game knowledge
    good_team = [merlin, percival, loyal_servant_1, loyal_servant_2]
    evil_team = [assassin, morgana]

    # 1. Tell each player their role (except user, who already knows)
    for name, role in players_with_roles.items():
        if name != "User":
            agent = get_player_object(name)
            user_proxy.send(
                message=f"Your role is: {role}. {role_descriptions[role]}",
                recipient=agent
            )
        else:
            print(f"[USER ROLE INFO] Your role is: {user_role}. {role_descriptions[user_role]}")

    # 2. Share role-specific knowledge
    if merlin.name != user_player.name:
        user_proxy.send(
            message=f"You are Merlin. You know the evil agents are: {assassin.name} and {morgana.name}",
            recipient=merlin
        )
    else:
        print(f"As Merlin, you know the evil agents are: {assassin.name} and {morgana.name}")
        user_player.add_teammate(assassin.name)
        user_player.add_teammate(morgana.name)

    if percival.name != user_player.name:
        user_proxy.send(
            message=f"You are Percival. You see both {merlin.name} and {morgana.name} as potential Merlins and cannot distinguish between them.",
            recipient=percival
        )
    else:
        print(f"As Percival, you see both {merlin.name} and {morgana.name} as potential Merlins and cannot distinguish between them.")
        user_player.add_teammate(merlin.name)
        user_player.add_teammate(morgana.name)

    for evil_agent in evil_team:
        if evil_agent.name != user_player.name:
            evil_teammates = [a.name for a in evil_team if a != evil_agent]
            user_proxy.send(
                message=f"You are on the evil team. Your evil teammate is: {', '.join(evil_teammates)}",
                recipient=evil_agent
            )

    if user_player.role in ["Assassin", "Morgana"]:
        evil_teammates = [a.name for a in evil_team if a.name != user_player.name]
        print(f"As an evil agent, your evil teammate is: {', '.join(evil_teammates)}")
        for teammate in evil_teammates:
            user_player.add_teammate(teammate)

    # 3. Print hidden mapping (including user)
    print("\n=== SECRET ROLE MAPPING (GAME MASTER ONLY) ===")
    for name, role in players_with_roles.items():
        print(f"{name} is {role}")
    print("=============================================")

# Format conversation history into a readable string
def format_conversation_history(history):
    formatted = "Conversation so far:\n"
    for entry in history:
        formatted += f"{entry['speaker']}: {entry['message']}\n"
    return formatted

# Modify the run_quest function to use all_players
# Run a quest with the selected players
def run_quest(selected_agents, conversation_history):
    print("\n=== QUEST BEGINS ===\n")
    print(f"Selected players for this quest: {', '.join([a if isinstance(a, str) else a.name for a in selected_agents])}")

    # Track quest votes (success/fail)
    quest_success_votes = 0
    quest_fail_votes = 0

    # Add quest information to conversation history
    quest_start_msg = f"Quest begins with {', '.join([a if isinstance(a, str) else a.name for a in selected_agents])} on the quest."
    conversation_history.append({"speaker": "GameMaster", "message": quest_start_msg})
    print(f"GameMaster: {quest_start_msg}")

    # Get votes from selected players
    for agent in selected_agents:
        if agent == "User":
            # Handle user input for voting
            while True:
                user_vote = input("You are on the quest. Do you want the quest to SUCCEED or FAIL? (Type 'SUCCEED' or 'FAIL'): ").strip().upper()
                if user_vote in ["SUCCEED", "FAIL"]:
                    break
                print("Invalid input. Please type 'SUCCEED' or 'FAIL'.")
            vote = user_vote
        else:
            # Format conversation history
            history_text = format_conversation_history(conversation_history)

            # Evil agents (Assassin and Morgana) can choose to fail the quest
            agent_name = agent if isinstance(agent, str) else agent.name
            is_evil = players_with_roles[agent_name] in ["Assassin", "Morgana"]


            if is_evil:
                vote_prompt = "You are on the quest. Do you want the quest to SUCCEED or FAIL? As an evil agent, you can choose to make the quest fail. Respond with just 'SUCCEED' or 'FAIL'."
            else:
                vote_prompt = "You are on the quest. As a good agent, you must make the quest succeed. Respond with just 'SUCCEED'."

            # Get agent's vote
            vote = agent.generate_reply(
                messages=[
                    {"role": "user", "content": history_text},
                    {"role": "user", "content": vote_prompt}
                ]
            ).strip().upper()

        # Count votes (don't reveal individual votes to maintain secrecy)
        if vote == "FAIL":
            quest_fail_votes += 1
        else:  # Default to success for invalid responses
            quest_success_votes += 1

    # Determine quest outcome
    quest_succeeded = quest_fail_votes == 0
    quest_results.append(quest_succeeded)

    # Report quest results
    if quest_succeeded:
        result_message = f"Quest has SUCCEEDED! ({quest_success_votes} success votes, {quest_fail_votes} fail votes)"
    else:
        result_message = f"Quest has FAILED! ({quest_success_votes} success votes, {quest_fail_votes} fail votes)"

    print(result_message)
    conversation_history.append({"speaker": "GameMaster", "message": result_message})

    print("\n=== QUEST ENDS ===\n")
    return quest_succeeded

# Modify the select_agents_for_quest function to use all_players
# Select agents for a quest
def select_agents_for_quest(is_initial=False, team_size=3):
    if is_initial:
        print("\n=== INITIAL TEAM SELECTION ===\n")
        print("Select three players for the initial team (e.g., 'A B C' or 'AgentA AgentB AgentC' or 'User'):")
    else:
        print("\n=== FINAL TEAM SELECTION ===\n")
        print("Select three players for the quest (e.g., 'A B C' or 'AgentA AgentB AgentC' or 'User'):")

    while True:
        selection = input().strip()
        selected_agents = []
        selected_names = [name.strip() for name in selection.split()]

        for name in selected_names:
            lowered = name.lower()
            uppered = name.upper()

            if lowered == "user":
                selected_agents.append("User")

            elif uppered in ["A", "B", "C", "D", "E"]:
                agent_name = f"Agent{uppered}"
                agent_obj = next((agent for agent in all_agents if agent.name == agent_name), None)
                if agent_obj:
                    selected_agents.append(agent_obj)

            elif lowered.startswith("agent"):
                agent_obj = next((agent for agent in all_agents if agent.name.lower() == lowered), None)
                if agent_obj:
                    selected_agents.append(agent_obj)

        # Validate selection
        if len(selected_agents) != team_size:
            print(f"Please select exactly {team_size} players. You selected {len(selected_agents)}.")
            continue

        # Confirm selection
        print(f"You've selected: {', '.join([a if isinstance(a, str) else a.name for a in selected_agents])}")
        print("Is this correct? (y/n)")
        confirmation = input().strip().lower()

        if confirmation == 'y':
            return selected_agents

def determine_turn_order():
    ordered_names = ["AgentA", "AgentB", "AgentC", "AgentD", "AgentE", "User"]
    quest_leader_index = random.randint(0, 5)
    quest_leader_name = ordered_names[quest_leader_index]
    print(f"[TURN INFO] Quest Leader is: {quest_leader_name}")
    return ordered_names, quest_leader_name

def select_team_members(ordered_names, quest_leader_name, conversation_history, round_number=1,team_size=3, is_initial=True):
    def get_agent(name):
        return user_player if name == "User" else next(a for a in all_agents if a.name == name)

    rotated_order = ordered_names[ordered_names.index(quest_leader_name):] + ordered_names[:ordered_names.index(quest_leader_name)]
    leader_agent = get_agent(quest_leader_name)
    history_text = format_conversation_history(conversation_history)

    if quest_leader_name == "User":
        if is_initial:
            print("You are the Quest Leader. Please give your speech first.")
            user_speech = input("You (speech): ")
            conversation_history.append({"speaker": "You", "message": user_speech})

            print("Now please select your initial team.")
            initial_team = select_agents_for_quest(is_initial=True, team_size=team_size)
            print(f"Your selected team: {', '.join([a if isinstance(a, str) else a.name for a in initial_team])}")
            return initial_team, conversation_history

        else:
            print("You are the Quest Leader. Please select the final team.")
            final_team = select_agents_for_quest(is_initial=False, team_size=team_size)
            print(f"Your selected final team: {', '.join([a if isinstance(a, str) else a.name for a in final_team])}")
            return final_team, conversation_history

    else:
        if is_initial:
            round_intro = (
                f"ROUND {round_number}:\n"
                f"- Quest Leader: {quest_leader_name}\n"
                f"- Required team size: {team_size}\n"
                f"- Speech order: {', '.join(rotated_order)}\n"
                f"- The leader will now propose a team."
            )
            for agent in all_agents:
                user_proxy.send(message=round_intro, recipient=agent)
            print(f"[GameMaster]: {round_intro}")

            print(f"({quest_leader_name}) is the Quest Leader who will propose an initial team...")

            # Step 1: Leader gives speech
            opening_speech = leader_agent.generate_reply([
                {"role": "user", "content": history_text},
                {"role": "user", "content": CHOOSE_TEAM_LEADER + CHOOSE_TEAM_ACTION.format(team_size, 'E') + DISCUSSION_SUFFIX}
            ])
            print(f"{quest_leader_name} (speech): {opening_speech}\n---")
            conversation_history.append({"speaker": quest_leader_name, "message": opening_speech})

        else:
            print(f"({quest_leader_name}) is now proposing the final team after everyone's opinion...")

        # Step 2: Leader selects team
        history_text = format_conversation_history(conversation_history)
        valid_players = ', '.join([agent.name for agent in all_agents] + ["User"])
        team_instruction = f"""
        You are the leader. Respond ONLY with:

        Answer: [{', '.join(['AgentX'] * team_size)}]

        Choose exactly {team_size} players from: {valid_players}.
        Do NOT explain your choice.
        """

        team_response = leader_agent.generate_reply([
            {"role": "user", "content": history_text},
            {"role": "user", "content": team_instruction.strip()}
        ])

        print(f"{quest_leader_name} (team selection): {team_response}\n---")

        # Step 3: Parse and convert to agent objects
        matches = re.findall(r"Agent[A-E]|User", team_response)
        selected_names = [name for name in matches if name in [a.name for a in all_agents] + ["User"]]
        selected_team = [get_agent(name) for name in selected_names]

        print(f"{quest_leader_name} has proposed the team: {', '.join(selected_names)}")
        conversation_history.append({"speaker": quest_leader_name, "message": f"I propose the team: {', '.join(selected_names)}"})

        return selected_team, conversation_history

def speech_round(ordered_names, quest_leader_name, initial_team, conversation_history):
    print("\n=== SPEECH ROUND START ===\n")

    def get_agent(name):
        return user_player if name == "User" else next(a for a in all_agents if a.name == name)

    rotated_order = ordered_names[ordered_names.index(quest_leader_name):] + ordered_names[:ordered_names.index(quest_leader_name)]

    leader_agent = get_agent(quest_leader_name)
    history_text = format_conversation_history(conversation_history)


    # Rotated discussion
    for name in rotated_order:
        if name == quest_leader_name:
            continue
        agent = get_agent(name)
        history_text = format_conversation_history(conversation_history)

        if name == "AgentB":
            draft = agent.generate_reply([
                {"role": "user", "content": history_text},
                {"role": "user", "content": VOTE_TEAM_DISCUSSION.format(', '.join([a.name if hasattr(a, 'name') else a for a in initial_team])) + DISCUSSION_SUFFIX}
            ])
            criteria = critic_agent.generate_reply([
                {"role": "user", "content": f"Draft response: {draft}"}
            ])
            scores = quantifier_agent.generate_reply([
                {"role": "user", "content": f"Criteria: {criteria}\n\nDraft: {draft}"}
            ])
            response = verifier_agent.generate_reply([
                {"role": "user", "content": f"Draft: {draft}\n\nCriteria: {criteria}\n\nScores: {scores}"}
            ])

        elif name == "AgentC":
            response = agent.generate_reply([
                {"role": "user", "content": history_text},
                {"role": "user", "content": VOTE_TEAM_DISCUSSION.format(', '.join([a.name if hasattr(a, 'name') else a for a in initial_team])) + DISCUSSION_SUFFIX}
            ])
            for _ in range(2):
                feedback = feedback_agent_c.generate_reply([
                    {"role": "user", "content": f"Provide feedback to improve this response:\n{response}"}
                ])
                response = agent.generate_reply([
                    {"role": "user", "content": f"Here is feedback on your previous message:\n{feedback}\n\nPlease revise your message accordingly. Return only the improved response and do NOT prefix your response with words like 'Final:', 'Conclusion:', or similar summarizing phrases. Speak naturally and directly."}
                ])

        elif name == "User":
            user_input = input("Your turn to speak. What's your opinion on the team?\nYou: ")
            conversation_history.append({"speaker": "You", "message": user_input})
            continue

        else:
            response = agent.generate_reply([
                {"role": "user", "content": history_text},
                {"role": "user", "content": VOTE_TEAM_DISCUSSION.format(', '.join([p.name if hasattr(p, 'name') else p for p in initial_team])) + DISCUSSION_SUFFIX}
            ])

        print(f"{name}: {response}\n---")
        conversation_history.append({"speaker": name, "message": response})


    print("\n=== SPEECH ROUND END ===\n")
    return conversation_history

def run_game():
    initialize_game()
    conversation_history = []

    turn_order, quest_leader = determine_turn_order()
    initial_team, conversation_history = select_team_members(ordered_names=turn_order, quest_leader_name=quest_leader, conversation_history=conversation_history, round_number=1,team_size=2, is_initial=True)
    conversation_history = speech_round(turn_order, quest_leader, initial_team, conversation_history)
    print("\nStep 3: Final team selection by user.")
    final_team, conversation_history = select_team_members(ordered_names=turn_order, quest_leader_name=quest_leader, conversation_history=conversation_history, round_number=1, team_size=2, is_initial=False)

    print("\nStep 4: Execute the quest.")
    quest_succeeded = run_quest(final_team, conversation_history)

    print("\n=== GAME COMPLETED ===\n")
    if quest_succeeded:
        print("The GOOD team won the quest!")
    else:
        print("The EVIL team sabotaged the quest!")

if __name__ == "__main__":
    run_game()
