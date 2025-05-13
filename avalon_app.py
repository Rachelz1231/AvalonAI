# avalon_app.py
import streamlit as st
import autogen
# Ensure prompts.py is in the same directory or adjust path
from prompts import (
    INTRODUCTION, TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT,
    CHOOSE_TEAM_LEADER, CHOOSE_TEAM_ACTION, DISCUSSION_SUFFIX,
    VOTE_TEAM_DISCUSSION, VOTE_TEAM_ACTION
)
from Player import Player # Your Player class
import random
import re
from typing import List, Dict, Any, Union

# --- Original Script Content (with minor adaptations for Streamlit) ---

# Default prompt if a role is not found in the dictionary
DEFAULT_PROMPT = "You are a player in Avalon. Play to your role's objectives based on the game's introduction and your role description."

# Configure a termination message
termination_msg = "GAME OVER"

API_KEY = ""

config_list = [
    {
        "model": "gpt-4",
        "api_key": API_KEY
        }
]
role_descriptions = {
    "Merlin": "Your role is Merlin. You have knowledge of who the evil agents are (Minions of Mordred). Your goal is to help the good team win 3 quests. If the Assassin identifies you at the end, Evil wins.",
    "Percival": "Your role is Percival. You know two players: one is Merlin, and the other is Morgana (who also appears as Merlin to you). Your goal is to help Good win 3 quests. Try to identify and protect the real Merlin.",
    "LoyalServant_1": "Your role is a Loyal Servant of Arthur. You have no special knowledge initially. Your goal is to help Good win 3 quests by deducing who is good and evil.",
    "LoyalServant_2": "Your role is a Loyal Servant of Arthur. You have no special knowledge initially. Your goal is to help Good win 3 quests by deducing who is good and evil.",
    "Assassin": "Your role is the Assassin (a Minion of Mordred). You know your fellow evil players. Your goal is to make 3 quests fail. If Good wins 3 quests, you get one chance to assassinate Merlin to win the game for Evil.",
    "Morgana": "Your role is Morgana (a Minion of Mordred). You know your fellow evil players. You appear as Merlin to Percival. Your goal is to make 3 quests fail and to confuse Percival."
}

# --- Helper Functions (Adapted for Streamlit) ---
def add_to_game_log(message, speaker="GameMaster"):
    if "game_log" not in st.session_state:
        st.session_state.game_log = []
    st.session_state.game_log.append(f"**{speaker}:** {message}")

def get_game_context_string(agent_name: str, players_names_list: List[str]) -> str:
    other_players = [name for name in players_names_list if name != agent_name]
    return (
        f"Your name is {agent_name}. You are a player in this game of The Resistance: Avalon.\n"
        f"In the current game, there are {len(players_names_list)} players including you. The other {len(other_players)} players are: {', '.join(other_players)}."
    )

def get_player_object_by_name(name_or_agent: Union[str, Player, autogen.Agent]):
    if isinstance(name_or_agent, (Player, autogen.Agent)):
        return name_or_agent
    if name_or_agent == "User":
        return st.session_state.user_player_obj
    if "all_agents_list" not in st.session_state or not st.session_state.all_agents_list:
        st.error("Agent list not initialized. Cannot find agent by name.")
        return None
    return next((agent for agent in st.session_state.all_agents_list if agent.name == name_or_agent), None)

def format_conversation_history_st(history):
    if not history:
        return "No conversation history yet."
    formatted = "#### Conversation History:\n"
    for entry in history:
        formatted += f"**{entry['speaker']}**: {entry['message']}\n\n"
    return formatted

# --- Game Logic Functions (Adapted for Streamlit state and I/O) ---
# (initialize_game_st, determine_turn_order_st, select_team_members_st, etc. remain the same as the previous version)
# I will paste the full game logic functions again for completeness, assuming they were correct from before.
# Make sure to replace the content of these functions with what I provided in the response before last,
# as they were already updated for your `prompts.py`. The key changes here are outside these functions
# or minor adjustments like st.rerun().

def initialize_game_st():
    st.session_state.game_log = ["Game Initializing..."] # Ensure it's initialized at the start of this function
    
    roles = ["Merlin", "Percival", "LoyalServant_1", "LoyalServant_2", "Assassin", "Morgana"]
    random.shuffle(roles)

    st.session_state.players_names = ["AgentA", "AgentB", "AgentC", "AgentD", "AgentE", "User"]
    st.session_state.players_with_roles = {} 
    st.session_state.role_to_player_name = {} 
    
    ai_agents = []
    st.session_state.last_agent_letter = st.session_state.players_names[-2][-1] if len(st.session_state.players_names) > 1 else 'A'

    for i in range(5): # AI Agents
        agent_name = st.session_state.players_names[i]
        agent_role = roles[i]
        st.session_state.players_with_roles[agent_name] = agent_role
        st.session_state.role_to_player_name[agent_role] = agent_name
        
        strategy_prompt_list = TUTORIAL_STRATEGIES_PROMPTS_ZERO_SHOT.get(agent_role)
        strategy_prompt = strategy_prompt_list[0] if strategy_prompt_list else DEFAULT_PROMPT
        
        system_msg_content = (
            INTRODUCTION + "\n\n" +
            get_game_context_string(agent_name, st.session_state.players_names) + "\n\n" +
            f"Your assigned role is {agent_role}. {role_descriptions.get(agent_role, '')}\n\n" +
            "STRATEGY TUTORIAL FOR YOUR ROLE:\n" + strategy_prompt
        )
        
        agent = autogen.AssistantAgent(
            name=agent_name,
            system_message=system_msg_content,
            llm_config={"config_list": config_list},
        )
        ai_agents.append(agent)
    
    st.session_state.ai_agents_list = ai_agents

    user_role_assigned = roles[5]
    st.session_state.players_with_roles["User"] = user_role_assigned
    st.session_state.role_to_player_name[user_role_assigned] = "User"
    st.session_state.user_player_obj = Player(name="User", role=user_role_assigned)
    st.session_state.user_role = user_role_assigned

    st.session_state.all_agents_list = ai_agents + [st.session_state.user_player_obj]

    st.session_state.user_proxy = autogen.UserProxyAgent(
        name="GameMaster", human_input_mode="NEVER",
        system_message="You are the Game Master. Your messages are for agents to understand game flow or direct instructions.",
        code_execution_config=False,
    )

    st.session_state.critic_agent = autogen.AssistantAgent(name="CriticAgent", system_message="You are the CriticAgent. Given a proposed response, your task is to define 2–3 criteria for evaluating how strategic and persuasive it is in the context of social deduction.", llm_config={"config_list": config_list})
    st.session_state.quantifier_agent = autogen.AssistantAgent(name="QuantifierAgent", system_message="You are the QuantifierAgent. Your job is to score the draft response on the given criteria from 0 (poor) to 1 (excellent), providing justifications.", llm_config={"config_list": config_list})
    st.session_state.verifier_agent = autogen.AssistantAgent(name="VerifierAgent", system_message="You are the VerifierAgent. Ensure the final response aligns with criteria and scores. If not, revise it. Return only the improved response and do NOT prefix your response with words like 'Final:', 'Conclusion:', or similar summarizing phrases. Speak naturally and directly.", llm_config={"config_list": config_list})
    st.session_state.feedback_agent_c = autogen.AssistantAgent(name="FeedbackAgentC", system_message="You are a self-feedback agent. Given a draft response, your job is to provide natural language feedback on how to improve it for strategic quality, clarity, and impact in a social deduction game.", llm_config={"config_list": config_list})

    add_to_game_log(f"Your assigned role is: {st.session_state.user_role}", speaker="System (To User)")
    st.sidebar.markdown(f"### Your Role: {st.session_state.user_role}")
    st.sidebar.info(role_descriptions.get(st.session_state.user_role, "No description available."))

    merlin_name = st.session_state.role_to_player_name.get("Merlin")
    percival_name = st.session_state.role_to_player_name.get("Percival")
    assassin_name = st.session_state.role_to_player_name.get("Assassin") # Corrected typo from "Assassion" if it was there
    morgana_name = st.session_state.role_to_player_name.get("Morgana")

    evil_player_names = [name for name, role in st.session_state.players_with_roles.items() if role in ["Assassin", "Morgana"]]

    for agent in st.session_state.ai_agents_list:
        agent_role = st.session_state.players_with_roles[agent.name]
        knowledge_msg = ""
        if agent_role == "Merlin":
            evil_names_str = " and ".join(sorted(evil_player_names))
            knowledge_msg = f"You have critical knowledge: The Minions of Mordred (evil players) are: {evil_names_str}."
        elif agent_role == "Percival" and merlin_name and morgana_name:
            potential_merlins = sorted([merlin_name, morgana_name])
            knowledge_msg = f"You have critical knowledge: You see {potential_merlins[0]} and {potential_merlins[1]} as potential Merlins. One is truly Merlin; the other is Morgana."
        elif agent_role in ["Assassin", "Morgana"]:
            other_evil = sorted([name for name in evil_player_names if name != agent.name])
            if other_evil:
                 knowledge_msg = f"You have critical knowledge: Your fellow Minion of Mordred is: {other_evil[0]}."
            else: # Should not happen in a 6-player game with Assassin and Morgana
                 knowledge_msg = "You have critical knowledge: You are the sole Minion of Mordred on your team (this is unusual for this setup)."
        
        if knowledge_msg:
            st.session_state.user_proxy.send(
                message=f"This is a private message for you, {agent.name}.\n{knowledge_msg}\nRemember to use all information, including the game introduction, your role, and this private knowledge, to inform your strategy.", 
                recipient=agent
            )

    user_knowledge_msgs = []
    if st.session_state.user_role == "Merlin":
        evil_names_str = " and ".join(sorted(evil_player_names))
        user_knowledge_msgs.append(f"The evil players are: {evil_names_str}.")
        for evil_name in evil_player_names: st.session_state.user_player_obj.add_teammate(evil_name)
    elif st.session_state.user_role == "Percival" and merlin_name and morgana_name:
        potential_merlins = sorted([merlin_name, morgana_name])
        user_knowledge_msgs.append(f"You see {potential_merlins[0]} and {potential_merlins[1]} as potential Merlins (one is Morgana).")
        for p_merlin in potential_merlins: st.session_state.user_player_obj.add_teammate(p_merlin)
    elif st.session_state.user_role in ["Assassin", "Morgana"]:
        other_evil = sorted([name for name in evil_player_names if name != "User"])
        if other_evil:
            user_knowledge_msgs.append(f"Your evil teammate is: {other_evil[0]}.")
            st.session_state.user_player_obj.add_teammate(other_evil[0])

    if user_knowledge_msgs:
        for msg in user_knowledge_msgs:
            st.sidebar.markdown(f"**Secret Knowledge:** {msg}")
            add_to_game_log(f"User ({st.session_state.user_role}) received secret knowledge: {msg}", speaker="System")

    st.session_state.gm_secret_info = "\n=== SECRET ROLE MAPPING (GAME MASTER ONLY) ===\n"
    for name, role_assigned in st.session_state.players_with_roles.items():
        st.session_state.gm_secret_info += f"{name} is {role_assigned}\n"
    
    # Ensure conversation_history is initialized here if not already
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    st.session_state.quest_results = [] 
    st.session_state.team_sizes = [2, 3, 4, 3, 4] 
    st.session_state.total_quests = 5
    st.session_state.current_quest_number = 0 
    st.session_state.game_stage = "DETERMINE_TURN_ORDER"

def determine_turn_order_st():
    ordered_names = st.session_state.players_names[:] 
    quest_leader_index = random.randint(0, len(ordered_names) - 1)
    
    st.session_state.turn_order = ordered_names 
    st.session_state.current_leader_name = ordered_names[quest_leader_index]
    st.session_state.current_leader_idx = quest_leader_index

    add_to_game_log(f"Initial Quest Leader is: {st.session_state.current_leader_name}")
    st.session_state.game_stage = "QUEST_ROUND_START"

def select_team_members_st():
    leader_name = st.session_state.current_leader_name
    team_size = st.session_state.current_team_size
    history_text = format_conversation_history_st(st.session_state.conversation_history)
    current_leader_role = st.session_state.players_with_roles.get(leader_name, "Unknown Role")

    round_intro = (
        f"Quest {st.session_state.current_quest_number + 1} is starting.\n"
        f"- Quest Leader: {leader_name} ({current_leader_role})\n"
        f"- Required team size: {team_size}\n"
        f"- This is voting attempt #{st.session_state.current_voting_attempt} for this quest team."
    )
    if not st.session_state.get("round_intro_displayed", False):
        add_to_game_log(round_intro)
        for agent in st.session_state.ai_agents_list:
            st.session_state.user_proxy.send(message=round_intro, recipient=agent)
        st.session_state.round_intro_displayed = True

    if leader_name == "User":
        st.subheader(f"You ({st.session_state.user_role}) are the Quest Leader.")
        st.markdown(CHOOSE_TEAM_LEADER)
        user_speech = st.text_area("Your speech:", key=f"user_speech_leader_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}")
        
        st.markdown(CHOOSE_TEAM_ACTION.format(team_size, st.session_state.last_agent_letter))
        available_players_for_selection = [p_name for p_name in st.session_state.players_names]
        selected_team_names = st.multiselect(
            f"Select {team_size} players:",
            options=available_players_for_selection,
            max_selections=team_size,
            key=f"user_team_select_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}"
        )

        if st.button(f"Propose Team & Submit Speech", key=f"submit_user_team_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}"):
            if not user_speech.strip():
                st.error("Please provide a speech.")
            elif len(selected_team_names) != team_size:
                st.error(f"Please select exactly {team_size} players.")
            else:
                st.session_state.conversation_history.append({"speaker": "User", "message": user_speech})
                add_to_game_log(user_speech, speaker=f"User ({leader_name}) (Leader Speech)")
                
                st.session_state.proposed_team_names = selected_team_names
                st.session_state.proposed_team_objects = [get_player_object_by_name(name) for name in selected_team_names]

                team_proposal_msg = f"I propose the team: {', '.join(selected_team_names)}"
                st.session_state.conversation_history.append({"speaker": "User", "message": team_proposal_msg})
                add_to_game_log(team_proposal_msg, speaker=f"User ({leader_name}) (Leader Proposal)")
                st.session_state.game_stage = "SPEECH_ROUND_SETUP"
                st.session_state.round_intro_displayed = False 
                st.rerun() # Replaced experimental_rerun
    else: 
        leader_agent = get_player_object_by_name(leader_name)
        if not leader_agent:
            st.error(f"Could not find leader agent object for {leader_name}")
            st.session_state.game_stage = "GAME_ERROR"
            st.rerun() # Replaced experimental_rerun
            return

        if not st.session_state.get(f"ai_leader_acted_{leader_name}_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}"):
            add_to_game_log(f"{leader_name} ({current_leader_role}) is formulating their speech and team proposal...")
            st.spinner(f"{leader_name} is preparing...")
            
            prompt_for_ai_leader = (
                CHOOSE_TEAM_LEADER + "\n" + 
                CHOOSE_TEAM_ACTION.format(team_size, st.session_state.last_agent_letter) + "\n" + 
                "After your speech, you must propose the team.\n"
                f"Current conversation history (if any):\n{history_text if st.session_state.conversation_history else 'No history yet.'}\n\n"
                f"Valid player names are: {', '.join(st.session_state.players_names)}. "
                "Your response MUST include your speech AND your team proposal on a new line formatted EXACTLY as: Answer: [PlayerName1, PlayerName2, ...]"
            )
            
            response = leader_agent.generate_reply(messages=[{"role": "user", "content": prompt_for_ai_leader}])
            
            speech_part = response 
            parsed_team_names = []
            
            answer_match = re.search(r"Answer:\s*\[([^\]]+)\]", response, re.IGNORECASE | re.DOTALL)

            if answer_match:
                speech_part = response[:answer_match.start()].strip()
                team_names_str = answer_match.group(1)
                raw_selected_names = [name.strip() for name in team_names_str.split(',')]
                
                valid_player_name_set = set(st.session_state.players_names)
                parsed_team_names = [name for name in raw_selected_names if name in valid_player_name_set]

                if len(parsed_team_names) != team_size:
                    add_to_game_log(f"{leader_name} selection error: proposed {len(parsed_team_names)} players, need {team_size}. Selected: {parsed_team_names}. Will attempt to fix or fallback.", speaker="System")
                    if len(parsed_team_names) > team_size:
                        parsed_team_names = parsed_team_names[:team_size]
                    else: 
                        add_to_game_log(f"Fallback: {leader_name} randomly selecting team due to parsing/count error.", speaker="System")
                        parsed_team_names = random.sample(st.session_state.players_names, team_size)
            else: 
                add_to_game_log(f"{leader_name} did not format team selection correctly (expected 'Answer: [team]'). Randomly selecting.", speaker="System")
                parsed_team_names = random.sample(st.session_state.players_names, team_size)
            
            st.session_state.proposed_team_names = parsed_team_names
            st.session_state.conversation_history.append({"speaker": leader_name, "message": speech_part})
            add_to_game_log(speech_part, speaker=f"{leader_name} ({current_leader_role}) (Leader Speech)")

            st.session_state.proposed_team_objects = [get_player_object_by_name(name) for name in st.session_state.proposed_team_names]
            team_proposal_msg = f"I propose the team: {', '.join(st.session_state.proposed_team_names)}"
            st.session_state.conversation_history.append({"speaker": leader_name, "message": team_proposal_msg})
            add_to_game_log(team_proposal_msg, speaker=f"{leader_name} ({current_leader_role}) (Leader Proposal)")
            
            st.session_state[f"ai_leader_acted_{leader_name}_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}"] = True
            st.session_state.game_stage = "SPEECH_ROUND_SETUP"
            st.session_state.round_intro_displayed = False 
            st.rerun() # Replaced experimental_rerun
        else:
            add_to_game_log(f"Skipping AI leader {leader_name} action as it was marked complete. Moving to speech round.")
            st.session_state.game_stage = "SPEECH_ROUND_SETUP"
            st.rerun() # Replaced experimental_rerun

def speech_round_st():
    current_speaker_name = st.session_state.speech_turn_order[st.session_state.current_speaker_idx]
    current_speaker_role = st.session_state.players_with_roles.get(current_speaker_name, "Unknown Role")
    history_text = format_conversation_history_st(st.session_state.conversation_history)
    proposed_team_str = ', '.join(st.session_state.proposed_team_names)

    prompt_core_for_speaker = VOTE_TEAM_DISCUSSION.format(proposed_team_str) + DISCUSSION_SUFFIX
    full_prompt_for_speaker = prompt_core_for_speaker + f"\n\nConversation so far:\n{history_text}"

    if current_speaker_name == "User":
        st.subheader(f"Your ({st.session_state.user_role}) turn to speak.")
        st.markdown(f"Leader **{st.session_state.current_leader_name}** proposed: **{proposed_team_str}**")
        st.markdown(VOTE_TEAM_DISCUSSION.format(proposed_team_str))
        
        user_speech_discussion = st.text_area("Your opinion/statement:", key=f"user_speech_discuss_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}_{st.session_state.current_speaker_idx}")
        if st.button("Submit Statement", key=f"submit_user_discuss_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}_{st.session_state.current_speaker_idx}"):
            if not user_speech_discussion.strip():
                st.error("Please provide a statement.")
            else:
                st.session_state.conversation_history.append({"speaker": "User", "message": user_speech_discussion})
                add_to_game_log(user_speech_discussion, speaker=f"User ({st.session_state.user_role})")
                st.session_state.current_speaker_idx += 1
                st.rerun() # Replaced experimental_rerun
    else: 
        ai_speaker = get_player_object_by_name(current_speaker_name)
        if not ai_speaker:
             st.error(f"Could not find AI speaker object for {current_speaker_name}")
             st.session_state.current_speaker_idx +=1 
             st.rerun() # Replaced experimental_rerun
             return

        add_to_game_log(f"{current_speaker_name} ({current_speaker_role}) is thinking about their statement...")
        st.spinner(f"{current_speaker_name} is speaking...")
        
        response = ""
        if current_speaker_name == "AgentB":
            draft = ai_speaker.generate_reply(messages=[{"role": "user", "content": full_prompt_for_speaker}])
            criteria = st.session_state.critic_agent.generate_reply(messages=[{"role": "user", "content": f"Draft response for {current_speaker_name}: {draft}"}])
            scores = st.session_state.quantifier_agent.generate_reply(messages=[{"role": "user", "content": f"Criteria: {criteria}\n\nDraft by {current_speaker_name}: {draft}"}])
            response = st.session_state.verifier_agent.generate_reply(messages=[{"role": "user", "content": f"Original Draft by {current_speaker_name}: {draft}\n\nEvaluation Criteria: {criteria}\n\nScores: {scores}\nRevise and provide final response."}])
        elif current_speaker_name == "AgentC":
            draft_response = ai_speaker.generate_reply(messages=[{"role": "user", "content": full_prompt_for_speaker}])
            for _ in range(2): 
                feedback = st.session_state.feedback_agent_c.generate_reply(messages=[{"role": "user", "content": f"Provide feedback to improve this response from {current_speaker_name}:\n{draft_response}"}])
                draft_response = ai_speaker.generate_reply(messages=[{"role": "user", "content": f"Here is feedback on your previous message:\n{feedback}\n\nPlease revise your message as {current_speaker_name} accordingly. Return only the improved response."}])
            response = draft_response
        else:
            response = ai_speaker.generate_reply(messages=[{"role": "user", "content": full_prompt_for_speaker}])

        st.session_state.conversation_history.append({"speaker": current_speaker_name, "message": response})
        add_to_game_log(response, speaker=f"{current_speaker_name} ({current_speaker_role})")
        st.session_state.current_speaker_idx += 1
        st.rerun() # Replaced experimental_rerun

    if st.session_state.current_speaker_idx >= len(st.session_state.speech_turn_order):
        add_to_game_log("Speech round concluded. Moving to vote on the team.")
        st.session_state.game_stage = "VOTE_ON_TEAM_SETUP"

def vote_on_team_st():
    voter_name = st.session_state.voting_order[st.session_state.current_voter_idx]
    voter_role = st.session_state.players_with_roles.get(voter_name, "Unknown Role")
    history_text = format_conversation_history_st(st.session_state.conversation_history)
    team_names_str = ', '.join(st.session_state.proposed_team_names)
    
    vote_prompt_for_ai = VOTE_TEAM_ACTION.format(team_names_str) + f"\n\nRelevant history:\n{history_text}"

    if voter_name == "User":
        st.subheader(f"Your ({st.session_state.user_role}) turn to vote on the team: **{team_names_str}**")
        st.markdown(VOTE_TEAM_ACTION.format(team_names_str))
        vote_options = ("Yes", "No") 
        user_vote_choice = st.radio("Approve this team?", vote_options, key=f"user_vote_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}_{st.session_state.current_voter_idx}")
        if st.button("Submit Vote", key=f"submit_user_vote_btn_{st.session_state.current_quest_number}_{st.session_state.current_voting_attempt}_{st.session_state.current_voter_idx}"):
            st.session_state.team_votes[voter_name] = user_vote_choice.upper() 
            add_to_game_log(f"You voted: {user_vote_choice}", speaker="User")
            st.session_state.current_voter_idx += 1
            st.rerun() # Replaced experimental_rerun
    else: 
        ai_voter = get_player_object_by_name(voter_name)
        if not ai_voter:
            st.error(f"Could not find AI voter object for {voter_name}")
            st.session_state.current_voter_idx += 1 
            st.rerun() # Replaced experimental_rerun
            return

        add_to_game_log(f"{voter_name} ({voter_role}) is voting...")
        st.spinner(f"{voter_name} is voting...")
        
        ai_vote_response = ai_voter.generate_reply(messages=[
            {"role": "user", "content": vote_prompt_for_ai}
        ]).strip().upper()
        
        final_ai_vote = "YES" # Default
        if "NO" in ai_vote_response: # Check for "NO" first as it's usually more explicit if intended
            final_ai_vote = "NO"
        elif "YES" in ai_vote_response: # Then check for "YES"
            final_ai_vote = "YES"
        else: # Fallback if neither "YES" nor "NO" is clearly indicated
            add_to_game_log(f"{voter_name} gave an unclear vote ('{ai_vote_response}'), defaulting to YES.", speaker="System")
        
        st.session_state.team_votes[voter_name] = final_ai_vote
        add_to_game_log(f"{final_ai_vote}", speaker=f"{voter_name} ({voter_role}) (Vote)")
        st.session_state.current_voter_idx += 1
        st.rerun() # Replaced experimental_rerun

    if st.session_state.current_voter_idx >= len(st.session_state.voting_order):
        st.session_state.game_stage = "VOTE_ON_TEAM_PROCESS"

def run_quest_st():
    quester_name = st.session_state.current_quest_team_names[st.session_state.current_quester_idx]
    quester_role = st.session_state.players_with_roles.get(quester_name, "Unknown")
    history_text = format_conversation_history_st(st.session_state.conversation_history)
    is_evil_quester = quester_role in ["Assassin", "Morgana"]

    if quester_name == "User":
        st.subheader(f"You ({st.session_state.user_role}) are on the Quest!")
        st.markdown(f"Team on quest: {', '.join(st.session_state.current_quest_team_names)}")
        quest_action_options = ["SUCCEED"]
        if is_evil_quester:
            quest_action_options.append("FAIL")
        
        user_quest_action = st.radio(
            "Choose your action for the quest (this is secret):", 
            quest_action_options, 
            key=f"user_quest_action_{st.session_state.current_quest_number}_{st.session_state.current_quester_idx}"
        )
        if st.button("Submit Quest Action (Secret)", key=f"user_quest_action_btn_{st.session_state.current_quest_number}_{st.session_state.current_quester_idx}"):
            st.session_state.quest_actions[quester_name] = user_quest_action
            add_to_game_log(f"You have secretly submitted your quest action.", speaker="System (To User)")
            st.session_state.current_quester_idx += 1
            st.rerun() # Replaced experimental_rerun
    else: 
        ai_quester = get_player_object_by_name(quester_name)
        if not ai_quester:
            st.error(f"Could not find AI quester object {quester_name}")
            st.session_state.current_quester_idx +=1 
            st.rerun() # Replaced experimental_rerun
            return

        add_to_game_log(f"{quester_name} ({quester_role}) is secretly performing their quest action...")
        st.spinner(f"{quester_name} is on the quest...")

        if is_evil_quester:
            action_prompt = "You are on this quest. As an evil player, you can choose to make the quest FAIL or SUCCEED. Your choice is secret. Respond with only 'SUCCEED' or 'FAIL'."
        else:
            action_prompt = "You are on this quest. As a good player, you must help the quest SUCCEED. Your choice is secret. Respond with only 'SUCCEED'."
        
        ai_quest_action_response = ai_quester.generate_reply(messages=[
            {"role": "user", "content": history_text},
            {"role": "user", "content": action_prompt}
        ]).strip().upper()

        final_ai_action = "SUCCEED" 
        if "FAIL" in ai_quest_action_response and is_evil_quester:
            final_ai_action = "FAIL"
        elif "SUCCEED" in ai_quest_action_response: # Explicit SUCCEED
            final_ai_action = "SUCCEED"
        # If good, they must succeed (already handled by prompt, but good fallback)
        elif not is_evil_quester:
             final_ai_action = "SUCCEED"
        # If evil and unclear, default to SUCCEED to avoid accidental easy fails if AI is confused
        elif is_evil_quester and "FAIL" not in ai_quest_action_response:
            add_to_game_log(f"{quester_name} (Evil) gave unclear quest action '{ai_quest_action_response}', defaulting to SUCCEED.", speaker="System")
            final_ai_action = "SUCCEED"


        st.session_state.quest_actions[quester_name] = final_ai_action
        add_to_game_log(f"{quester_name} has secretly completed their quest action.", speaker="System")
        st.session_state.current_quester_idx += 1
        st.rerun() # Replaced experimental_rerun

    if st.session_state.current_quester_idx >= len(st.session_state.current_quest_team_names):
        st.session_state.game_stage = "RUN_QUEST_PROCESS"

def assassin_guess_merlin_st():
    assassin_name = st.session_state.role_to_player_name.get("Assassin")
    if not assassin_name:
        st.error("Assassin role not found in game. Cannot proceed with assassination.")
        st.session_state.game_stage = "GAME_OVER_GOOD_WINS" 
        st.rerun() # Replaced experimental_rerun
        return

    history_text = format_conversation_history_st(st.session_state.conversation_history)
    valid_targets = [name for name in st.session_state.players_names if name != assassin_name]

    add_to_game_log("The Good team has won 3 quests! The Assassin now attempts to find and assassinate Merlin.", speaker="GameMaster")

    if assassin_name == "User":
        st.subheader(f"You ({st.session_state.user_role}) are the Assassin! Choose who you believe is Merlin.")
        st.markdown(f"Valid targets: {', '.join(valid_targets)}")
        target_guess = st.selectbox("Select player to assassinate:", options=valid_targets, key="assassin_guess_user")
        if st.button("Confirm Assassination Target", key="assassin_guess_btn_user"):
            st.session_state.assassin_guess = target_guess
            st.session_state.game_stage = "ASSASSIN_GUESS_PROCESS"
            st.rerun() # Replaced experimental_rerun
    else: 
        ai_assassin = get_player_object_by_name(assassin_name)
        if not ai_assassin:
            st.error(f"Could not find AI Assassin object {assassin_name}")
            st.session_state.assassin_guess = random.choice(valid_targets) 
            st.session_state.game_stage = "ASSASSIN_GUESS_PROCESS"
            st.rerun() # Replaced experimental_rerun
            return

        add_to_game_log(f"{assassin_name} (Assassin) is choosing who to assassinate...")
        st.spinner(f"{assassin_name} is deciding...")
        
        guess_prompt_for_ai = (
            f"You are the Assassin. The Good team has won 3 quests. Your final task is to identify and assassinate Merlin. "
            f"If you succeed, Evil wins. Choose one player to assassinate from the following list: {', '.join(valid_targets)}. "
            f"Respond with only the player's name you choose to assassinate.\n"
            f"Consider all game history:\n{history_text}"
        )
        ai_guess_response = ai_assassin.generate_reply(messages=[
            {"role": "user", "content": guess_prompt_for_ai}
        ]).strip()
        
        final_ai_guess = ""
        for target_name in valid_targets: 
            if target_name.lower() in ai_guess_response.lower():
                final_ai_guess = target_name
                break
        
        if not final_ai_guess: 
            add_to_game_log(f"{assassin_name} made an unclear guess ('{ai_guess_response}'). Randomly choosing a target.", speaker="System")
            final_ai_guess = random.choice(valid_targets)
        
        st.session_state.assassin_guess = final_ai_guess
        st.session_state.game_stage = "ASSASSIN_GUESS_PROCESS"
        st.rerun() # Replaced experimental_rerun

# --- Streamlit App Main Flow ---
st.set_page_config(layout="wide", page_title="Avalon Game")
st.title("Multi-Agent Resistance: Avalon")

# Initialize session state variables robustly
if "game_stage" not in st.session_state:
    st.session_state.game_stage = "PRE_GAME"
if "game_log" not in st.session_state: # Always ensure these exist
    st.session_state.game_log = []
if "conversation_history" not in st.session_state: # Always ensure these exist
    st.session_state.conversation_history = []


# Sidebar for Game Log and Persistent Info
st.sidebar.title("Game Information")
if "user_role" in st.session_state and st.session_state.user_role:
    st.sidebar.markdown(f"**Your Role:** {st.session_state.user_role}")
    role_desc_key = st.session_state.user_role 
    if role_desc_key not in role_descriptions and "LoyalServant" in role_desc_key: 
        role_desc_key = "LoyalServant_1" 
    st.sidebar.info(f"{role_descriptions.get(role_desc_key, 'No role description.')}")
    
    if hasattr(st.session_state.get("user_player_obj"), 'teammates') and st.session_state.user_player_obj.teammates:
        knowledge_str = ""
        if st.session_state.user_role == "Merlin":
            knowledge_str = f"Known evil players: {', '.join(st.session_state.user_player_obj.teammates)}"
        elif st.session_state.user_role == "Percival":
             knowledge_str = f"Potential Merlins (one is Morgana): {', '.join(st.session_state.user_player_obj.teammates)}"
        elif st.session_state.user_role in ["Assassin", "Morgana"]:
            teammates_display = ', '.join(st.session_state.user_player_obj.teammates) if st.session_state.user_player_obj.teammates else 'None (you are solo evil or error)'
            knowledge_str = f"Your evil teammate(s): {teammates_display}"
        if knowledge_str:
            st.sidebar.markdown(f"**Your Secret Knowledge:** {knowledge_str}")

st.sidebar.markdown("### Game Log")
log_container_sidebar = st.sidebar.expander("View Full Log", expanded=False)
# Check if game_log exists before trying to access it
if "game_log" in st.session_state and st.session_state.game_log:
    for log_entry in reversed(st.session_state.game_log[-5:]): 
        st.sidebar.markdown(f"<small>{log_entry}</small>", unsafe_allow_html=True)
    with log_container_sidebar:
        for log_entry in reversed(st.session_state.game_log):
            st.markdown(f"<small>{log_entry}</small>", unsafe_allow_html=True)
else:
    st.sidebar.markdown("<small>No game log yet.</small>", unsafe_allow_html=True)


# Main Game Area
game_area_col, history_col = st.columns([2,1])

with game_area_col:
    if st.session_state.game_stage != "PRE_GAME":
        st.header("Current Game State")
        if "current_quest_number" in st.session_state and \
           "current_leader_name" in st.session_state and \
           "players_with_roles" in st.session_state and \
           "team_sizes" in st.session_state and \
           st.session_state.current_quest_number < len(st.session_state.team_sizes):
            
            role_of_leader = st.session_state.players_with_roles.get(st.session_state.current_leader_name, "")
            team_size_for_quest = st.session_state.team_sizes[st.session_state.current_quest_number]
            st.info(f"Quest {st.session_state.current_quest_number + 1} | Leader: {st.session_state.current_leader_name} ({role_of_leader}) | Team Size: {team_size_for_quest}")

    if st.session_state.game_stage == "PRE_GAME":
        st.header("Welcome to The Resistance: Avalon")
        st.markdown(INTRODUCTION) 
        if API_KEY == "YOUR_API_KEY_HERE" or not API_KEY:
            st.error("Please enter a valid OpenAI API Key in the sidebar to start the game.")
        elif st.button("Start New Game"):
            # Clear most session state keys but keep API key and ensure essential lists are re-initialized
            keys_to_keep = ['openai_api_key']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep: 
                    del st.session_state[key]
            # Explicitly re-initialize after clearing
            st.session_state.game_stage = "INITIALIZE_GAME"
            st.session_state.game_log = [] 
            st.session_state.conversation_history = []
            st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "INITIALIZE_GAME":
        if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
            with st.spinner("Initializing game, assigning roles, agents are preparing... This may take a moment."):
                initialize_game_st()
            st.success("Game initialized! Roles assigned.")
            st.rerun() # Replaced experimental_rerun
        else:
            st.error("API Key is missing. Cannot initialize game.")
            st.session_state.game_stage = "PRE_GAME"
            st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "DETERMINE_TURN_ORDER":
        with st.spinner("Determining first quest leader..."):
            determine_turn_order_st()
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "QUEST_ROUND_START":
        st.session_state.current_quest_number = len(st.session_state.quest_results) # quest_results should be initialized
        st.session_state.current_team_size = st.session_state.team_sizes[st.session_state.current_quest_number]
        st.session_state.current_voting_attempt = 1 
        st.session_state.round_intro_displayed = False 
        
        add_to_game_log(f"--- Starting QUEST ROUND {st.session_state.current_quest_number + 1} (Team Size: {st.session_state.current_team_size}) ---")
        st.session_state.game_stage = "TEAM_SELECTION"
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "TEAM_SELECTION":
        select_team_members_st() 

    elif st.session_state.game_stage == "SPEECH_ROUND_SETUP":
        add_to_game_log(f"Team proposed by {st.session_state.current_leader_name}: {', '.join(st.session_state.proposed_team_names)}. Initiating discussion round.")
        leader_idx_in_turn_order = st.session_state.turn_order.index(st.session_state.current_leader_name)
        
        speech_potential_order = st.session_state.turn_order[leader_idx_in_turn_order+1:] + st.session_state.turn_order[:leader_idx_in_turn_order]
        st.session_state.speech_turn_order = [p_name for p_name in speech_potential_order if p_name != st.session_state.current_leader_name] 

        if not st.session_state.speech_turn_order: 
             add_to_game_log("No other players to speak. Moving directly to vote.", speaker="System")
             st.session_state.game_stage = "VOTE_ON_TEAM_SETUP"
        else:
            st.session_state.current_speaker_idx = 0
            st.session_state.game_stage = "SPEECH_ROUND_EXECUTE"
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "SPEECH_ROUND_EXECUTE":
        if st.session_state.current_speaker_idx < len(st.session_state.speech_turn_order):
            speech_round_st() 
        else: 
            add_to_game_log("Discussion round concluded.")
            st.session_state.game_stage = "VOTE_ON_TEAM_SETUP"
            st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "VOTE_ON_TEAM_SETUP":
        add_to_game_log(f"Proceeding to vote on the team: {', '.join(st.session_state.proposed_team_names)}")
        st.session_state.voting_order = st.session_state.players_names[:] 
        st.session_state.current_voter_idx = 0
        st.session_state.team_votes = {} 
        st.session_state.game_stage = "VOTE_ON_TEAM_EXECUTE"
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "VOTE_ON_TEAM_EXECUTE":
        if st.session_state.current_voter_idx < len(st.session_state.voting_order):
            vote_on_team_st() 
        else: 
            st.session_state.game_stage = "VOTE_ON_TEAM_PROCESS"
            st.rerun() # Replaced experimental_rerun
            
    elif st.session_state.game_stage == "VOTE_ON_TEAM_PROCESS":
        yes_votes = sum(1 for v in st.session_state.team_votes.values() if v == "YES")
        no_votes = len(st.session_state.players_names) - yes_votes
        
        vote_summary = "Team Vote Results:\n"
        for player_name_vote, vote_cast in st.session_state.team_votes.items(): 
            player_role_vote = st.session_state.players_with_roles.get(player_name_vote, "N/A")
            vote_summary += f"- {player_name_vote} ({player_role_vote}): {vote_cast}\n"
        add_to_game_log(vote_summary, speaker="Team Vote Tally")

        team_approved = yes_votes > len(st.session_state.players_names) // 2
        result_message = f"Vote Tally: {yes_votes} YES, {no_votes} NO. "
        
        if team_approved:
            result_message += "Team APPROVED!"
            add_to_game_log(result_message)
            st.session_state.current_quest_team_names = st.session_state.proposed_team_names 
            st.session_state.game_stage = "RUN_QUEST_SETUP"
        else: 
            result_message += "Team REJECTED."
            add_to_game_log(result_message)
            st.session_state.current_voting_attempt += 1
            max_voting_rounds_for_quest = 3 

            if st.session_state.current_voting_attempt > max_voting_rounds_for_quest: # This means if attempt 3 just failed (attempt becomes 4)
                add_to_game_log(f"Team rejected on attempt {st.session_state.current_voting_attempt-1}. This team ({', '.join(st.session_state.proposed_team_names)}) proceeds due to repeated rejections (Hammer Rule).")
                st.session_state.current_quest_team_names = st.session_state.proposed_team_names
                st.session_state.game_stage = "RUN_QUEST_SETUP"
            else: 
                add_to_game_log("Passing leadership for new team proposal...")
                st.session_state.current_leader_idx = (st.session_state.current_leader_idx + 1) % len(st.session_state.turn_order)
                st.session_state.current_leader_name = st.session_state.turn_order[st.session_state.current_leader_idx]
                add_to_game_log(f"New Quest Leader: {st.session_state.current_leader_name}")
                st.session_state.round_intro_displayed = False 
                st.session_state.game_stage = "TEAM_SELECTION" 
        
        st.session_state.conversation_history.append({"speaker": "GameMaster", "message": result_message + f" Votes: {st.session_state.team_votes}"})
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "RUN_QUEST_SETUP":
        team_on_quest_str = ', '.join(st.session_state.current_quest_team_names)
        add_to_game_log(f"Quest {st.session_state.current_quest_number + 1} is now active with team: {team_on_quest_str}")
        st.session_state.quest_actions = {} 
        st.session_state.current_quester_idx = 0
        st.session_state.game_stage = "RUN_QUEST_EXECUTE"
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "RUN_QUEST_EXECUTE":
        if st.session_state.current_quester_idx < len(st.session_state.current_quest_team_names):
            run_quest_st() 
        else: 
            st.session_state.game_stage = "RUN_QUEST_PROCESS"
            st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "RUN_QUEST_PROCESS":
        fail_votes = sum(1 for action in st.session_state.quest_actions.values() if action == "FAIL")
        success_votes = len(st.session_state.current_quest_team_names) - fail_votes
        
        quest_succeeded_bool = (fail_votes == 0)
        
        st.session_state.quest_results.append(quest_succeeded_bool)
        
        result_str = "SUCCEEDED" if quest_succeeded_bool else "FAILED"
        quest_summary_msg = f"Quest {st.session_state.current_quest_number + 1} has {result_str}! (Number of FAIL cards played: {fail_votes})"
        add_to_game_log(quest_summary_msg)
        st.session_state.conversation_history.append({"speaker": "GameMaster", "message": quest_summary_msg + f" Actions: {st.session_state.quest_actions}"})

        good_wins = sum(1 for res in st.session_state.quest_results if res is True)
        evil_wins = len(st.session_state.quest_results) - good_wins

        st.markdown(f"**Overall Quest Track:** Good: {good_wins} | Evil: {evil_wins}")
        quest_track_display = []
        for i_res, res_val in enumerate(st.session_state.quest_results): # Use enumerate to get index
            status = "✅ Success" if res_val else "❌ Fail"
            # Ensure team_sizes has been initialized and is long enough
            team_size_info = st.session_state.team_sizes[i_res] if "team_sizes" in st.session_state and i_res < len(st.session_state.team_sizes) else '?'
            quest_track_display.append(f"Q{i_res+1} ({team_size_info}p): {status}")
        st.progress(good_wins / 3 if good_wins < 3 else 1.0, text=f"Good Quests: {good_wins}/3")
        st.progress(evil_wins / 3 if evil_wins < 3 else 1.0, text=f"Evil Quests: {evil_wins}/3")
        st.markdown(" | ".join(quest_track_display))


        if good_wins >= 3:
            st.session_state.game_stage = "ASSASSIN_GUESS_SETUP"
        elif evil_wins >= 3:
            st.session_state.game_stage = "GAME_OVER_EVIL_WINS"
        else:
            st.session_state.current_leader_idx = (st.session_state.current_leader_idx + 1) % len(st.session_state.turn_order)
            st.session_state.current_leader_name = st.session_state.turn_order[st.session_state.current_leader_idx]
            st.session_state.game_stage = "QUEST_ROUND_START" 
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "ASSASSIN_GUESS_SETUP":
        assassin_guess_merlin_st() 

    elif st.session_state.game_stage == "ASSASSIN_GUESS_PROCESS":
        merlin_is = st.session_state.role_to_player_name.get("Merlin")
        guess = st.session_state.assassin_guess
        assassin_name = st.session_state.role_to_player_name.get("Assassin")

        add_to_game_log(f"The Assassin ({assassin_name}) has chosen to assassinate: **{guess}**", speaker="GameMaster")
        if guess == merlin_is:
            add_to_game_log(f"Assassination Successful! {guess} was indeed Merlin.", speaker="GameMaster")
            st.session_state.game_stage = "GAME_OVER_EVIL_WINS_ASSASSINATION"
        else:
            add_to_game_log(f"Assassination Failed! {guess} was not Merlin. The true Merlin was {merlin_is}.", speaker="GameMaster")
            st.session_state.game_stage = "GAME_OVER_GOOD_WINS"
        st.rerun() # Replaced experimental_rerun

    elif st.session_state.game_stage == "GAME_OVER_GOOD_WINS":
        st.balloons()
        st.success("🎉 THE GOOD TEAM WINS! 🎉 (Merlin survived or was not targeted correctly.)")
        add_to_game_log("GAME OVER: GOOD TEAM WINS.")
        if st.button("Play Again?", key="play_again_good"): 
            st.session_state.game_stage = "PRE_GAME" 
            st.rerun() # Replaced experimental_rerun
        if st.button("Reveal All Roles", key="reveal_good"): st.session_state.show_all_roles = True

    elif st.session_state.game_stage == "GAME_OVER_EVIL_WINS":
        st.error("😈 THE EVIL TEAM WINS! 😈 (They successfully failed 3 Quests.)")
        add_to_game_log("GAME OVER: EVIL TEAM WINS (3 failed quests).")
        if st.button("Play Again?", key="play_again_evil_quest"): 
            st.session_state.game_stage = "PRE_GAME"
            st.rerun() # Replaced experimental_rerun
        if st.button("Reveal All Roles", key="reveal_evil_quest"): st.session_state.show_all_roles = True

    elif st.session_state.game_stage == "GAME_OVER_EVIL_WINS_ASSASSINATION":
        st.error("💀 THE EVIL TEAM WINS! 💀 (The Assassin successfully identified and assassinated Merlin!)")
        add_to_game_log("GAME OVER: EVIL TEAM WINS (Merlin assassinated).")
        if st.button("Play Again?", key="play_again_evil_assassin"): 
            st.session_state.game_stage = "PRE_GAME"
            st.rerun() # Replaced experimental_rerun
        if st.button("Reveal All Roles", key="reveal_evil_assassin"): st.session_state.show_all_roles = True
    
    if st.session_state.get("show_all_roles", False) and \
       "game_stage" in st.session_state and \
       st.session_state.game_stage.startswith("GAME_OVER"):
        st.subheader("Final Role Reveal:")
        if "players_with_roles" in st.session_state:
            for name_reveal, role_assigned_reveal in st.session_state.players_with_roles.items():
                st.write(f"- {name_reveal}: {role_assigned_reveal}")
        else:
            st.write("Role information not available.")

with history_col:
    st.header("Game Dialogue")
    chat_container = st.container()
    with chat_container:
        # Ensure conversation_history exists
        if "conversation_history" in st.session_state and st.session_state.conversation_history:
            for entry in st.session_state.conversation_history:
                speaker_display = entry['speaker']
                if entry['speaker'] == "User" and "user_role" in st.session_state : # Check user_role exists
                    speaker_display = f"You ({st.session_state.user_role})"
                elif "players_with_roles" in st.session_state and entry['speaker'] in st.session_state.players_with_roles:
                     speaker_display = f"{entry['speaker']} ({st.session_state.players_with_roles[entry['speaker']]})"
                
                # Use a default avatar or logic to choose one
                avatar_icon = "🧑‍🚀" if entry['speaker'] not in ["GameMaster", "System"] else "🤖"
                with st.chat_message(name=entry['speaker'], avatar=avatar_icon):
                    st.markdown(f"**{speaker_display}:** {entry['message']}")
        else:
            st.write("No conversation yet.")

# For debugging session state:
# if st.sidebar.checkbox("Show Session State Debug", False):
#    st.sidebar.subheader("Session State Debug")
#    st.sidebar.json(st.session_state, expanded=False)
