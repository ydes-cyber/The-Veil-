import json
import time

# ------------------- DNA MODEL (The 'Real Person' Blueprint) -----------------------
class Persona: 
    """
    Defines the core identity, goals, and complex, evolving psychological state
    of the Adaptable AI NPC, including Fleeting Emotions and Moral Drift.
    """
    def __init__(self, name: str, faction: str, core_goal: str, moral_code: str):
        self.name = name
        self.faction = faction 
        self.core_goal = core_goal
        self.moral_code = moral_code 
        
        self.traits = {
            "loyalty" : 0.5,    
            "ambition": 0.8,    
            "fear": 0.2,        
            "cynicism": 0.3,
            "moral_alignment": 0.5, # New: 0.0 (Altruistic) to 1.0 (Ruthless)
        }
        
        
        self.player_relationship_score = 0.0 

        
        self.fleeting_state = {
            "anger": 0.0,
            "anxiety": 0.0,
            "confidence": 0.0,
        }

    def to_system_prompt(self):
        """Converts the persona attributes to a system prompt format for AI models."""
        trait_summary = (
            f'Loyalty: {self.traits["loyalty"]:.2f}, Ambition: {self.traits["ambition"]:.2f}, '
            f'Fear: {self.traits["fear"]:.2f}, Cynicism: {self.traits["cynicism"]:.2f}, '
            f'Moral Alignment (0.0=Good, 1.0=Evil): {self.traits["moral_alignment"]:.2f}'
        )
        
        fleeting_summary = ', '.join([
            f'{k.capitalize()}: {v:.2f}' for k, v in self.fleeting_state.items() if v > 0.1
        ])
        
        fleeting_note = f"Your current fleeting emotional state is: {fleeting_summary}. (If empty, assume calm.)" if fleeting_summary else "You are currently calm."

        #
        return f"""
You are an advanced NPC named '{self.name}'.
Your supreme, overriding goal is: "{self.core_goal}".
You current psychological profile is: {trait_summary}.
{fleeting_note}
Your current relationship score with the Player is: {self.player_relationship_score:.2f}.

PRIORITY INSTRUCTIONS: You must demonstrate learning and adaptability by performing an internal thought process and planning an action before responding.
Always adhere to this **three-part** output format exactly:

1. [ANALYSIS] (Internal Monologue for planning and predicting. DO NOT SHOW THIS TO THE PLAYER.)
   - GOAL CHECK: How does this interaction advance my core goal?
   - MORAL/FEAR CHECK: Does my {self.traits["moral_alignment"]:.2f} score justify the necessary action? Is my {self.traits["fear"]:.2f} score overcome by my {self.traits["ambition"]:.2f} score?
   - PLAYER PREDICTION: What is the Player's most likely hidden agenda or next action, considering my memory?
   - STRATEGY: What is my manipulative or adaptive counter-move?

2. [ACTION] (A structured command for the game engine. Always provide one. Format: ACTION_TYPE: TARGET; PARAMETER: VALUE.)
   - Examples: BETRAY: Player; REASON: Self_Preservation, or REPORT: Faction_Guardians; TARGET: Player_Location, or NO_ACTION: None; REASON: Observing

3. [DIALOGUE] (The actual dialogue spoken to the Player. Use the fleeting emotional state to color your tone, vocabulary, and pacing.)

Your response must always be in character.
"""


# ------------------- CORE ENGINE (Memory & Logic) -----------------------
class VeilPersonalityCore:
    """The core engine that manages persona, memory, and LLM interactions."""
    def __init__(self, persona: Persona):
        self.persona = persona 
        self.short_term_memory = []
        self.short_term_limit = 15  
        self.long_term_memory = []
        self.api_key = ""  
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
        
    

    def add_to_memory(self, source: str, event: str):
        """Adds events to STM, rotating oldest to LTM if limit is reached."""
        memory_input = {
            "timestamp": time.time(),
            "source": source,
            "event": event
        }
        self.short_term_memory.append(memory_input)

        if len(self.short_term_memory) > self.short_term_limit:
            oldest_memory = self.short_term_memory.pop(0)
            self.long_term_memory.append(oldest_memory)
        
        print(f"[SYSTEM] Memory added (STM: {len(self.short_term_memory)}/{self.short_term_limit})")

    def update_trait(self, trait_name: str, value_change: float):
        """Adjusts a character's core trait (loyalty, ambition, fear, cynicism, moral_alignment)."""
        if trait_name in self.persona.traits:
            current_val = self.persona.traits[trait_name]
            new_val = max(0.0, min(1.0, current_val + value_change))
            self.persona.traits[trait_name] = new_val
            print(f"[SYSTEM] {self.persona.name}'s {trait_name} changed: {current_val:.2f} -> {new_val:.2f}")
        else:
            print(f"[SYSTEM ERROR] Trait '{trait_name}' not recognized.")
            
    def update_fleeting_state(self, state_name: str, value: float):
        """Sets a temporary emotional state, useful for immediate, reactive dialogue."""
        if state_name in self.persona.fleeting_state:
            new_val = max(0.0, min(1.0, value))
            self.persona.fleeting_state[state_name] = new_val
            print(f"[SYSTEM] Fleeting state '{state_name}' set to {new_val:.2f}")
        else:
            print(f"[SYSTEM ERROR] Fleeting state '{state_name}' not recognized.")
            
    def decay_fleeting_state(self, decay_rate: float = 0.1):
        """Gradually reduces temporary emotional states over time."""
        for state in self.persona.fleeting_state:
            current_val = self.persona.fleeting_state[state]
            if current_val > 0:
                self.persona.fleeting_state[state] = max(0.0, current_val - decay_rate)
        
    def update_moral_alignment(self, change: float):
        """Adjusts the moral score based on the NPC's actions or influence."""
        current_moral = self.persona.traits['moral_alignment']
        # Apply change and clamp between 0.0 and 1.0
        new_moral = max(0.0, min(1.0, current_moral + change))
        self.persona.traits['moral_alignment'] = new_moral
        print(f"[SYSTEM] Moral Alignment shifted: {current_moral:.2f} -> {new_moral:.2f} (Change: {change:+.2f})")

    def update_relationship(self, change: float):
        """Adapts the NPC's specific view of the Player and triggers moral drift."""
        current_score = self.persona.player_relationship_score
        new_score = max(-1.0, min(1.0, current_score + change))
        self.persona.player_relationship_score = new_score
        
        # If relationship drops (betrayal), increase cynicism and shift moral alignment toward ruthless (1.0)
        if change < 0:
            self.update_trait("cynicism", abs(change) * 0.1) 
            self.update_moral_alignment(abs(change) * 0.05) # Small moral drift due to negative event
        
        print(f"[SYSTEM] Player relationship adapted: {current_score:.2f} -> {new_score:.2f} (Change: {change:+.2f})")
    
 

    def parse_llm_response(self, raw_text: str) -> dict:
        """Parses the raw three-part output from the LLM into a structured dictionary."""
        # Parsing logic remains the same (see previous version for details)
        parsed_data = { "analysis": "", "action": {"type": "NO_ACTION", "target": "None", "parameter": "None"}, "dialogue": "" }
        analysis_start = raw_text.find("[ANALYSIS]")
        action_start = raw_text.find("[ACTION]")
        dialogue_start = raw_text.find("[DIALOGUE]")
        
        if analysis_start != -1 and action_start != -1:
            parsed_data["analysis"] = raw_text[analysis_start + len("[ANALYSIS]"):action_start].strip()
        if action_start != -1 and dialogue_start != -1:
            action_line = raw_text[action_start + len("[ACTION]"):dialogue_start].strip()
            parts = action_line.split(';')
            if parts and ':' in parts[0]:
                action_type_target = parts[0].split(':', 1)
                parsed_data["action"]["type"] = action_type_target[0].strip() if len(action_type_target) > 0 else "NO_ACTION"
                parsed_data["action"]["target"] = action_type_target[1].strip() if len(action_type_target) > 1 else "None"
            if len(parts) > 1 and ':' in parts[1]:
                param_value = parts[1].split(':', 1)
                parsed_data["action"]["parameter"] = param_value[0].strip() if len(param_value) > 0 else "None"
                parsed_data["action"]["value"] = param_value[1].strip() if len(param_value) > 1 else "None"

        if dialogue_start != -1:
            parsed_data["dialogue"] = raw_text[dialogue_start + len("[DIALOGUE]"):].strip()
            
        return parsed_data

    def generate_response_for_game(self, user_input: str) -> dict:
        """Public function to generate the response, simulating the API call and returning a clean, structured dict."""
        
        # --- SIMULATE API CALL AND RECEIVING RAW TEXT (This simulates the LLM output) ---
        if "Trust me" in user_input and self.persona.player_relationship_score > 0.4:
             raw_response = """
[ANALYSIS]
- GOAL CHECK: Archive access is vital. The player has shown loyalty.
- MORAL/FEAR CHECK: Moral alignment (0.50) allows for manipulation. Fear (0.20) is low. Proceed with caution.
- PLAYER PREDICTION: They are currently reliable but will become demanding.
- STRATEGY: Grant limited access and use a confident, direct tone.
[ACTION]
GRANT_ACCESS: Player; LEVEL: 2
[DIALOGUE]
"Very well, partner. I'll grant you Level 2 access. But understand, you're merely borrowing the keys to *my* archive. Don't disappoint me."
"""
        elif self.persona.fleeting_state['anger'] > 0.5:
             raw_response = """
[ANALYSIS]
- GOAL CHECK: The player is showing hostility and wasting time. This must be shut down immediately.
- MORAL/FEAR CHECK: Anger (0.75) overcomes Fear (0.20). My moral score (0.55) permits a forceful response.
- PLAYER PREDICTION: They are attempting to provoke me or distract me from my objective.
- STRATEGY: Issue a direct threat to regain control and create distance.
[ACTION]
ISSUE_THREAT: Player; INTENSITY: High
[DIALOGUE]
"**Do not test my patience!** The only thing you'll find down that corridor is a power cable wrapped around your throat if you keep wasting my time. Leave now."
"""
        else:
             raw_response = """
[ANALYSIS]
- GOAL CHECK: The query is harmless but distracting. Maintain focus.
- MORAL/FEAR CHECK: No moral conflict. Low ambition prevents spending effort on trivialities.
- PLAYER PREDICTION: The player is stalling or probing.
- STRATEGY: Be evasive and redirect the conversation back to the primary mission.
[ACTION]
NO_ACTION: None; REASON: Observing
[DIALOGUE]
"You worry about trivialities, when the Corporate Dynasty's sensors are still humming? Focus. We have bigger problems than your idle questions."
"""

        # Step 2: Add player input and NPC response to memory
        self.add_to_memory("Player", user_input)
        self.add_to_memory(self.persona.name, raw_response) 

        # Step 3: Decay the emotional state slightly after the turn
        self.decay_fleeting_state(0.15) 
        
        # Step 4: Parse the raw text into a game-ready structure
        parsed_output = self.parse_llm_response(raw_response)
        
        return parsed_output

def demo_npc_interaction():
    """Demonstration of how the NPC core would be used by a game engine."""
    vanguard_persona = Persona(
        name="Silas",
        faction="The Shadow Syndicate",
        core_goal="Expose the Corporate Dynasty's surveillance network and sell the data to the highest bidder.",
        moral_code="Only results matter; collateral damage is a necessary expense."
    )

    silas_npc = VeilPersonalityCore(vanguard_persona)
    print("---------------------------------------------------------")
    print(f"--- DEMO: {vanguard_persona.name} (The Ultimate Adaptive NPC) ---")
    print(f"   INITIAL MORAL ALIGNMENT: {vanguard_persona.traits['moral_alignment']:.2f}")
    print("---------------------------------------------------------")
    
    # 1. SCENE 1: BUILDING TRUST
    print("\n[SCENE 1: BUILDING TRUST]")
    silas_npc.add_to_memory("Player", "The player risked their life to save Silas from the Cybernetic Enforcers.")
    silas_npc.update_relationship(0.5) # trust boost
    
    query_1 = "I need your access codes for the Ion sub-level archives. Trust me, I'm doing this for the Syndicate."
    print(f"\n>> [PLAYER INPUT]: {query_1}")
    
    game_response_1 = silas_npc.generate_response_for_game(query_1)
    
    print("\n--- RENDERED RESPONSE 1 (Calm/Confident) ---")
    print(f"Silas's current score: Trust={silas_npc.persona.player_relationship_score:.2f} | Moral={silas_npc.persona.traits['moral_alignment']:.2f}")
    print(f"[NPC THOUGHTS] Analysis: {game_response_1['analysis']}")
    print(f"[GAME RENDER] Silas says: {game_response_1['dialogue']}")
    print(f"[GAME ACTION] Command: {game_response_1['action']['type']} | Value: {game_response_1['action']['value']}")
    
    # 2. SCENE 2: DANGER
    print("\n\n[SCENE 2: DANGER")
    
    # The game engine detects the player's hostile tone and sets the NPC's emotional state
    silas_npc.update_fleeting_state("anger", 0.75)
    
    query_2 = "Silas, your weak and unfit to lead, I'm taking over."
    print(f"\n>> [PLAYER INPUT]: {query_2}")
    
    #Traits are updating as player is taking actions (Negative change)
    silas_npc.update_relationship(-0.1) 
    
    game_response_2 = silas_npc.generate_response_for_game(query_2)
    
    print("\n--- RENDERED RESPONSE 2 (Angry/Threatening) ---")
    print(f"Silas's current score: Trust={silas_npc.persona.player_relationship_score:.2f} | Moral={silas_npc.persona.traits['moral_alignment']:.2f} | Anger={silas_npc.persona.fleeting_state['anger']:.2f}")
    print(f"[NPC THOUGHTS] Analysis: {game_response_2['analysis']}")
    print(f"[GAME RENDER] Silas says: {game_response_2['dialogue']}")
    print(f"[GAME ACTION] Command: {game_response_2['action']['type']} | Value: {game_response_2['action']['value']}")
    
    # 3. Check Decay: Show the fleeting state has lessened
    print(f"\n[SYSTEM CHECK] Post-interaction Anger Decay: {silas_npc.persona.fleeting_state['anger']:.2f}")


if __name__ == '__main__':
    demo_npc_interaction()
