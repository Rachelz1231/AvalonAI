import autogen
from typing import Dict, List, Any, Optional
import random
from prompts import TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT, GAME_RULES
import os
from datetime import datetime

os.makedirs("logs", exist_ok=True)
log_filename = f"logs/avalon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_file = open(log_filename, "w")

def log(msg: str):
    print(msg)
    log_file.write(msg + "\n")


# Configure a termination message
termination_msg = "GAME OVER"

# Create configuration for the agents
config_list = [
    {
        "model": "gpt-4",
        "api_key": "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",
    }
]

# Define role descriptions (hidden from players)
role_descriptions = {
    "Merlin": "You are Merlin. You have knowledge of who the evil agents are. Your goal is to help the good team win the quests without revealing your identity.",
    "Percival": "You are Percival. You know who Merlin is, but cannot distinguish between Morgana and Merlin. Your goal is to help the good team win quests.",
    "LoyalServant": "You are a Loyal Servant of Arthur. You have no special knowledge. Your goal is to help the good team win quests based on logic and observation.",
    "Assassin": "You are the Assassin. You know who the evil agents are. Your goal is to sabotage quests and, at the end of the game, identify and assassinate Merlin.",
    "Morgana": "You are Morgana. You appear as Merlin to Percival. Your goal is to sabotage quests and cause confusion among the good team."
}

# Randomly assign roles to generic agent names
roles = ["Merlin", "Percival", "LoyalServant", "Assassin", "Morgana"]
# random.shuffle(roles)

# Create the agents with generic names and keep track of their roles
agents_with_roles = {}
agent_names = ["AgentA", "AgentB", "AgentC", "AgentD", "AgentE"]

# Create agents and store role mappings
agent_A = autogen.AssistantAgent(
    name="AgentA",
    system_message=role_descriptions[roles[0]],
    llm_config={"config_list": config_list},
)
agents_with_roles[agent_A] = roles[0]

agent_B = autogen.AssistantAgent(
    name="AgentB",
    system_message=role_descriptions[roles[1]],
    llm_config={"config_list": config_list},
)
agents_with_roles[agent_B] = roles[1]

agent_C = autogen.AssistantAgent(
    name="AgentC",
    system_message=role_descriptions[roles[2]],
    llm_config={"config_list": config_list},
)
agents_with_roles[agent_C] = roles[2]

agent_D = autogen.AssistantAgent(
    name="AgentD",
    system_message=role_descriptions[roles[3]],
    llm_config={"config_list": config_list},
)
agents_with_roles[agent_D] = roles[3]

agent_E = autogen.AssistantAgent(
    name="AgentE",
    system_message=role_descriptions[roles[4]],
    llm_config={"config_list": config_list},
)
agents_with_roles[agent_E] = roles[4]

# Create a user proxy agent to facilitate the game
user_proxy = autogen.UserProxyAgent(
    name="GameMaster",
    human_input_mode="ALWAYS",
    system_message="You are the Game Master who runs the Avalon game. You can speak with the agents and see their responses.",
    code_execution_config=False,
)

# All agents in the game
all_agents = [agent_A, agent_B, agent_C, agent_D, agent_E]

# Create the reverse mapping: role -> agent
role_to_agent = {role: agent for agent, role in agents_with_roles.items()}

# Game state tracking
quest_results = []

# Initialize the knowledge base for each agent
def initialize_game():
    # Get agents by their roles
    merlin = role_to_agent["Merlin"]
    percival = role_to_agent["Percival"]
    loyal_servant = role_to_agent["LoyalServant"]
    assassin = role_to_agent["Assassin"]
    morgana = role_to_agent["Morgana"]
    
    # Set up initial game knowledge
    good_team = [merlin, percival, loyal_servant]
    evil_team = [assassin, morgana]
    
    # Share knowledge according to role abilities
    # Only Merlin knows who the evil agents are
    user_proxy.send(
        message=f"You are Merlin. Your name is {merlin.name} You know the evil agents are: {assassin.name} and {morgana.name}",
        recipient=merlin
    )
    
    # Percival knows who Merlin is, but also sees Morgana as Merlin
    user_proxy.send(
        message=f"You are Percival. Your name is {percival.name} You see both {merlin.name} and {morgana.name} as potential Merlins and cannot distinguish between them.",
        recipient=percival
    )

    # Percival knows who Merlin is, but also sees Morgana as Merlin
    user_proxy.send(
        message=f"You are LoyalServant. Your name is {loyal_servant.name}",
        recipient=loyal_servant
    )
    
    # Evil agents know each other
    for evil_agent in evil_team:
        evil_teammates = [agent.name for agent in evil_team if agent != evil_agent]
        user_proxy.send(
            message=f"You are on the evil team. Your name is {evil_agent.name} Your evil teammate is: {', '.join(evil_teammates)}",
            recipient=evil_agent
        )
    
    # log the hidden role mapping (only visible to the game runner, not players)
    log("\n=== SECRET ROLE MAPPING (GAME MASTER ONLY) ===")
    for agent in all_agents:
        log(f"{agent.name} is {agents_with_roles[agent]}")
    log("=============================================\n")

# Format conversation history into a readable string
def format_conversation_history(history):
    formatted = "Conversation so far:\n"
    for entry in history:
        formatted += f"{entry['speaker']}: {entry['message']}\n"
    return formatted

# Run a quest with the selected agents
def run_quest(selected_agents, conversation_history):
    log("\n=== QUEST BEGINS ===\n")
    log(f"Selected agents for this quest: {', '.join([a.name for a in selected_agents])}")
    
    # Track quest votes (success/fail)
    quest_success_votes = 0
    quest_fail_votes = 0
    
    # Add quest information to conversation history
    quest_start_msg = f"Quest begins with {', '.join([a.name for a in selected_agents])} on the quest."
    conversation_history.append({"speaker": "GameMaster", "message": quest_start_msg})
    log(f"GameMaster: {quest_start_msg}")
    
    # Get votes from selected agents
    for agent in selected_agents:
        # Format conversation history
        history_text = format_conversation_history(conversation_history)
        
        # Evil agents (Assassin and Morgana) can choose to fail the quest
        is_evil = agents_with_roles[agent] in ["Assassin", "Morgana"]
        
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
    
    log(result_message)
    conversation_history.append({"speaker": "GameMaster", "message": result_message})
    
    log("\n=== QUEST ENDS ===\n")
    return quest_succeeded

# Select agents for a quest
def select_agents_for_quest(is_initial=False):
    if is_initial:
        log("\n=== INITIAL TEAM SELECTION ===\n")
        log("Select three agents for the initial team (e.g., 'A B C' or 'AgentA AgentB AgentC'):")
    else:
        log("\n=== FINAL TEAM SELECTION ===\n")
        log("Select three agents for the quest (e.g., 'A B C' or 'AgentA AgentB AgentC'):")
    
    while True:
        selection = input().strip()
        
        # Parse selection
        selected_agents = []
        selected_names = [name.strip() for name in selection.split()]
        
        for name in selected_names:
            # Allow both 'A' and 'AgentA' formats
            if name.lower() in ["a", "b", "c", "d", "e"]:
                name = "Agent" + name.upper()
            
            # Find the corresponding agent
            for agent in all_agents:
                if agent.name.lower() == name.lower():
                    selected_agents.append(agent)
                    break
        
        # Validate selection
        if len(selected_agents) != 3:
            log(f"Please select exactly 3 agents. You selected {len(selected_agents)}.")
            continue
        
        # Confirm selection
        log(f"You've selected: {', '.join([a.name for a in selected_agents])}")
        log("Is this correct? (y/n)")
        confirmation = input().strip().lower()
        
        if confirmation == 'y':
            return selected_agents
        log("Select three agents for the quest (e.g., 'A B C' or 'AgentA AgentB AgentC'):")

# Main game loop
def run_game():
    # Initialize the game and share role knowledge
    initialize_game()
    
    # Start tracking conversation history
    conversation_history = []
    
    # Step 1: Select initial 3 players
    log("\nStep 1: Select the initial 3 players for the team.")
    initial_team = select_agents_for_quest(is_initial=True)
    initial_team_msg = f"Initial team: {', '.join([a.name for a in initial_team])}"
    log(initial_team_msg)
    conversation_history.append({"speaker": "GameMaster", "message": initial_team_msg})
    
    # Step 2: Everyone speaks once
    log("\nStep 2: Now everyone speaks once about the initial team.")
    
    # User speaks first
    log("\nYour turn to speak. What do you want to say about the initial team?")
    user_input = input("You: ")
    conversation_history.append({"speaker": "You", "message": user_input})
    
    # Each agent speaks once
    log("\n=== AGENT RESPONSES ===")
    for agent in all_agents:
        # Format conversation history
        history_text = format_conversation_history(conversation_history)
        
        # Ask the agent for their opinion
        response = agent.generate_reply(
            messages=[
                {"role": "user", "content": history_text},
                {"role": "user", "content": f"Based on the conversation so far and your role, give your honest opinion about the proposed team: {', '.join([a.name for a in initial_team])}. DO NOT REVEAL YOUR ROLE directly."}
            ]
        )
        
        # add zero-shot prompting for agent D, Assasin:
        if agent == agent_D or agent == agent_A:
            print(f"{agent.name:}")
            role = agents_with_roles[agent]
            strategy_guide = TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(role, [""])[0] # zero shot prompting

            response = agent.generate_reply(
                messages=[
                    {"role": "user", "content": f"{GAME_RULES}\n\nYou are playing as {role}. Read this strategy guide:\n{strategy_guide}"},
                    {"role": "user", "content": history_text},
                    {"role": "user", "content": f"Now, based on your role, the conversation so far, share your opinion about the proposed team: {', '.join([a.name for a in initial_team])}. DO NOT reveal your identity directly, but you may deceive, deduce, accuse, or persuade others as needed. Keep your response short and in-character."}
                ]
            )

        log(f"{agent.name}: {response}")
        log("---")
        
        # Add to conversation history
        conversation_history.append({"speaker": agent.name, "message": response})
    
    # Step 3: Select 3 players for the quest again
    log("\nStep 3: After hearing everyone's opinion, select the final 3 players for the quest.")
    final_team = select_agents_for_quest(is_initial=False)
    
    # Step 4: Execute quest and see results
    log("\nStep 4: Execute the quest with the selected team.")
    quest_succeeded = run_quest(final_team, conversation_history)
    
    # Display final result
    log("\n=== GAME COMPLETED ===\n")
    if quest_succeeded:
        log("The GOOD team won the quest!")
    else:
        log("The EVIL team sabotaged the quest!")

if __name__ == "__main__":
    run_game()
