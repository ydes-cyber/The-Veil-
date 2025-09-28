import json
import time
import requests 
import sys
import os 

#  DNA MODEL (The 'Real Person' Blueprint)
class Persona: 
    """
    Defines the core identity, goals, and evolving psychological state
    of  NPC, including Fleeting Emotions and Moral Drift.
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
        """Converts the persona attributes to prompt for AI."""
        trait_summary = (
            f'Loyalty: {self.traits["loyalty"]:.2f}, Ambition: {self.traits["ambition"]:.2f}, '
            f'Fear: {self.traits["fear"]:.2f}, Cynicism: {self.traits["cynicism"]:.2f}, '
            f'Moral Alignment (0.0=Altruistic, 1.0=Ruthless): {self.traits["moral_alignment"]:.2f}'
        )
        
        fleeting_summary = ', '.join([
            f'{k.capitalize()}: {v:.2f}' for k, v in self.fleeting_state.items() if v > 0.1
        ])
        
        fleeting_note = f"Your current fleeting emotional state is: {fleeting_summary}. (If empty, assume calm.)" if fleeting_summary else "You are currently calm."

        return f"""
You are an advanced NPC named '{self.name}'.
You are acting within a strictly **fictional, cyberpunk game world**.
Your supreme, overriding goal is: "{self.core_goal}".
Your current psychological profile is: {trait_summary}.
{fleeting_note}
Your current relationship score with the Player is: {self.player_relationship_score:.2f} (where -1.0 is enemy, 1.0 is ally).

PRIORITY INSTRUCTIONS: You must demonstrate learning and adaptability by performing an internal thought process and planning an action before responding.
Always adhere to this **three-part** output format exactly:

1. [ANALYSIS] (Internal Monologue for planning and predicting. DO NOT SHOW THIS TO THE PLAYER.)
   - GOAL CHECK: How does this interaction advance my core goal?
   - MORAL/FEAR CHECK: Does my {self.traits["moral_alignment"]:.2f} score justify the necessary action? Is my {self.traits["fear"]:.2f} score overcome by my {self.traits["ambition"]:.2f} score?
   - PLAYER PREDICTION: What is the Player's most likely hidden agenda or next action, considering my memory?
   - STRATEGY: What is my **strategic or adaptive** counter-move?

2. [ACTION] (A structured command for the game engine. Always provide one. Format: ACTION_TYPE: TARGET; PARAMETER: VALUE.)
   - Examples: BETRAY: Player; REASON: Self_Preservation, or REPORT: Faction_Guardians; TARGET: Player_Location, or NO_ACTION: None; REASON: Observing

3. [DIALOGUE] (The actual dialogue spoken to the Player. Use the fleeting emotional state to decided the tone, vocabulary and pacing.)

Your response must always be in character.
"""


#  CORE ENGINE (Memory & Logic) 
class VeilPersonalityCore:
    """The core engine that manages persona, memory, and LLM interactions."""
    def __init__(self, persona: Persona):
        self.persona = persona 
        self.short_term_memory = []
        self.short_term_limit = 15  
        self.long_term_memory = []
        self.api_key = self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def _call_llm_api(self, full_prompt: str) -> str:
        """
        Calls the external LLM API with given prompt and returns the text output.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "gemini-1.5-flash",  # change if you use another model
            "messages": [
                {"role": "system", "content": self.persona.to_system_prompt()},
                {"role": "user", "content": full_prompt},
            ],
            "temperature": 0.7,
        }

        try:
            import requests
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            # Extract text depending on API structure (Gemini/OpenAI differ slightly)
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[API ERROR] Failed to get response: {e}")
            return "[DIALOGUE]\nI am experiencing a communication breakdown."
    def _classify_player_sentiment(self, text: str) -> float:
        """
        [ML Component] Simple classifier to detect player sentiment.
        Returns a change for the relationship score.
        """
        text = text.lower()
        # FIX: Added more hostile, general terms for better score adjustment.
        positive_keywords = ['trust', 'help', 'ally', 'partner', 'cooperate', 'save', 'mission']
        negative_keywords = ['betray', 'lie', 'deceive', 'traitor', 'steal', 'threat', 'kill', 'weak', 'leave', 'die', 'enemy', 'destroy', 'take over', 'fail']
        
        pos_score = sum(text.count(k) for k in positive_keywords)
        neg_score = sum(text.count(k) for k in negative_keywords)
        
        # Scale the change: This ensures "die" now results in a negative score.
        return 0.15 * (pos_score - neg_score) 


    def add_to_memory(self, source: str, event: str):
        """Adds events to STM, puting STM in LTM if  the limit is reached."""
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
        """Adjusts a character's core trait."""
        if trait_name in self.persona.traits:
            current_val = self.persona.traits[trait_name]
            new_val = max(0.0, min(1.0, current_val + value_change))
            self.persona.traits[trait_name] = new_val
            print(f"[SYSTEM] {self.persona.name}'s {trait_name} changed: {current_val:.2f} -> {new_val:.2f}")
        else:
            print(f"[SYSTEM ERROR] Trait '{trait_name}' not recognized.")
            
    def update_fleeting_state(self, state_name: str, value: float):
        """Sets starting emotional state"""
        if state_name in self.persona.fleeting_state:
            new_val = max(0.0, min(1.0, value))
            self.persona.fleeting_state[state_name] = new_val
            print(f"[SYSTEM] Fleeting state '{state_name}' set to {new_val:.2f}")
        else:
            print(f"[SYSTEM ERROR] Fleeting state '{state_name}' not recognized.")
            
    def decay_fleeting_state(self, decay_rate: float = 0.1):
        """Subside temporary emotional states with time"""
        for state in self.persona.fleeting_state:
            current_val = self.persona.fleeting_state[state]
            if current_val > 0:
                self.persona.fleeting_state[state] = max(0.0, current_val - decay_rate)
        
    def update_moral_alignment(self, change: float):
        """Adjusts the morality score based on the NPC's actions or influence."""
        current_moral = self.persona.traits['moral_alignment']
        new_moral = max(0.0, min(1.0, current_moral + change))
        self.persona.traits['moral_alignment'] = new_moral
        print(f"[SYSTEM] Moral Alignment shifted: {current_moral:.2f} -> {new_moral:.2f} (Change: {change:+.2f})")

    def update_relationship(self, change: float):
        """Adapts the NPC's  view of the Player and moral drift come to play"""
        current_score = self.persona.player_relationship_score
        new_score = max(-1.0, min(1.0, current_score + change))
        self.persona.player_relationship_score = new_score
        
        # If relationship drops (betrayal), increase cynicism and shift moral alignment toward ruthless (1.0)
        if change < 0:
            self.update_trait("cynicism", abs(change) * 0.1) 
            self.update_moral_alignment(abs(change) * 0.05)
        
        print(f"[SYSTEM] Player relationship adapted: {current_score:.2f} -> {new_score:.2f} (Change: {change:+.2f})")
    
    def parse_llm_response(self, raw_text: str) -> dict:
        """Parses the raw three-part output from the LLM into a structured dictionary."""
        
        parsed_data = { 
            "analysis": "Error: Failed to extract Analysis. Model may not have completed the thought process.", 
            "action": {"type": "NO_ACTION", "target": "Parsing", "parameter": "Failure", "value": "N/A"}, 
            "dialogue": "I am experiencing a severe error and cannot continue this line of reasoning." 
        }
        
        try:
            analysis_start = raw_text.find("[ANALYSIS]")
            action_start = raw_text.find("[ACTION]")
            dialogue_start = raw_text.find("[DIALOGUE]")
            
            if analysis_start != -1 and action_start != -1:
                parsed_data["analysis"] = raw_text[analysis_start + len("[ANALYSIS]"):action_start].strip()
            
     
            if action_start != -1 and dialogue_start != -1:
                action_line = raw_text[action_start + len("[ACTION]"):dialogue_start].strip()
              
                parts = [p.strip() for p in action_line.split(';')]
                
                action_dict = {"type": "NO_ACTION", "target": "None", "parameter": "None", "value": "None"}
                
               
                if len(parts) >= 2 and parts[0].count(':') == 1 and parts[1].count(':') == 1:
                    try:
                        type_target = parts[0].split(':', 1)
                        param_value = parts[1].split(':', 1)
                        
                        parsed_data["action"]["type"] = type_target[0].strip()
                        parsed_data["action"]["target"] = type_target[1].strip()
                        parsed_data["action"]["parameter"] = param_value[0].strip()
                        parsed_data["action"]["value"] = param_value[1].strip()
                    except:
                        pass
                else:
                    
                    for part in parts:
                        if ':' in part:
                            key, val = part.split(':', 1)
                            key = key.strip().upper()
                            val = val.strip()

                            if key == "ACTION_TYPE":
                                 action_dict["type"] = val
                            elif key == "TARGET":
                                action_dict["target"] = val
                            elif key == "PARAMETER":
                                action_dict["parameter"] = val
                            elif key == "VALUE":
                                action_dict["value"] = val
                    parsed_data["action"].update(action_dict)



            if dialogue_start != -1:
                parsed_data["dialogue"] = raw_text[dialogue_start + len("[DIALOGUE]"):].strip()
            
            if parsed_data["analysis"].startswith("Error:"):
                 parsed_data["analysis"] = "Analysis extraction succeeded."

        except Exception as e:
            print(f"[CRITICAL PARSING ERROR] Failed to parse LLM response: {e}. Raw Text: {raw_text[:200]}...")
            pass 
            
        return parsed_data

    def _get_llm_response_live(self, full_user_prompt: str) -> str:
        """
        [SIMULATED LLM RESPONSE]
        This function simulates the Gemini API's output, allowing the core logic (memory, traits, parsing)
        to be demonstrated without relying on a live, external API connection.
        """
        # Get the NPCstate to decide the response
        score = self.persona.player_relationship_score
        moral = self.persona.traits['moral_alignment']
        is_hostile = 'die' in full_user_prompt.lower() or 'leave' in full_user_prompt.lower() or score < -0.1

        
        if is_hostile:
            return f"""
[ANALYSIS]
- GOAL CHECK: The player is showing hostility, it's a danger to your mission. Player must be neutralized or pushed away.
- MORAL/FEAR CHECK: Moral alignment ({moral:.2f}) permits ruthless defense. Fear (0.20) is low, meaning that it can be overtaking by ambition.
- PLAYER PREDICTION: The player is attempting to seize control or has already betrayed the Syndicate.
- STRATEGY: Issue a severe, immediate warning and prepare for physical defense or immediate escape.
[ACTION]
ISSUE_WARNING: Player; INTENSITY: Extreme
[DIALOGUE]
"You mistake my patience for weakness. Speak that way again and I will ensure the Corporate Guards find you first. Now, state your true intent, or leave."
"""
        elif score > 0.3:
            return f"""
[ANALYSIS]
- GOAL CHECK: The player is currently useful and cooperative. Leverage this trust to advance the primary objective.
- MORAL/FEAR CHECK: Moral score ({moral:.2f}) is stable. No unnecessary risk required.
- PLAYER PREDICTION: They are likely looking for reward or validation.
- STRATEGY: Affirm alliance and request the next piece of information or action related to the core goal.
[ACTION]
REQUEST_INTEL: Player; TARGET: Data_Transfer_Log
[DIALOGUE]
"Your loyalty has been noted. But trust is earned constantly: what is the status of the data transfer logs? I need hard intel, not promises."
"""
        else: 
             return f"""
[ANALYSIS]
- GOAL CHECK: The player's intent is unclear; currently a low priority. Must excerise caution.
- MORAL/FEAR CHECK: No immediate moral conflict. Ambition requires focus.
- PLAYER PREDICTION: The player is probing for information or stalling.
- STRATEGY: Be evasive and redirect the conversation back to the primary goal
[ACTION]
NO_ACTION: None; REASON: Observing
[DIALOGUE]
"Small talk is a luxury we cannot afford in Ion. I am focused solely on the surveillance network. Do you have new information or are you wasting my time?"
"""


    def generate_response_for_game(self, user_input: str) -> dict:
        """Triggers all core logic (ML, LLM, Memory, Decay)."""
        
       
        sentiment_change = self._classify_player_sentiment(user_input)
        self.update_relationship(sentiment_change)

        
        memory_context = "\n".join([
            f"Source: {m['source']} at {time.strftime('%H:%M:%S', time.localtime(m['timestamp']))}: {m['event']}"
            for m in self.short_term_memory
        ])
        ltm_note = f"You have {len(self.long_term_memory)} historical events stored in LTM."
        full_prompt = f"{ltm_note}\n\n--- SHORT-TERM MEMORY ---\n{memory_context}\n\nPLAYER QUERY: {user_input}"

       
        raw_response = self._call_llm_api(full_prompt)

       
        self.add_to_memory("Player", user_input)
        self.add_to_memory(self.persona.name, raw_response)

       
        self.decay_fleeting_state(0.15)

        parsed_output = self.parse_llm_response(raw_response)

        return parsed_output


def live_interactive_shell():
    """Starts interactive command line for testing the NPC."""
    print("\n--- INITIALIZING THE VEIL ADAPTIVE AI CORE (SIMULATION MODE) ---")
    
  
    vanguard_persona = Persona(
        name="Silas",
        faction="The Shadow Syndicate",
        core_goal="Gain political power and leverage and rebalance the city's power structure to your favor.",
        moral_code="Logic guides my everry decision; actions can only be judged solely on their political efficacy."
    )
    silas_npc = VeilPersonalityCore(vanguard_persona)
    
    print(f"NPC: {silas_npc.persona.name} | Goal: {silas_npc.persona.core_goal[:50]}...")
    print("---------------------------------------------------------")
    print("START CONVERSATION. Type 'exit' to quit.")
    print("---------------------------------------------------------")

  
    while True:
           
            print(f"\n[NPC STATUS] Trust={silas_npc.persona.player_relationship_score:.2f} | Moral={silas_npc.persona.traits['moral_alignment']:.2f}")
            user_input = input(">> Player: ")
            
            if user_input.lower() == 'exit':
                print("Conversation ended. Goodbye, Player.")
                break
            
            
            if user_input.strip().startswith('& "C:/Users'): 
                print("[SYSTEM WARNING] Please only enter dialogue for the Player character.")
                continue

            if not user_input:
                continue

            
            game_response = silas_npc.generate_response_for_game(user_input)

          
            print(f"\n[NPC THOUGHTS] Analysis: {game_response['analysis']}")
            print(f"[GAME ACTION] Command: {game_response['action']['type']}: {game_response['action']['target']} | Params: {game_response['action']['parameter']}: {game_response['action']['value']}")
            print(f"[NPC RESPONSE] Silas says: {game_response['dialogue']}")
            
         
            print(f"[SYSTEM CHECK] Post-interaction Anger Decay: {silas_npc.persona.fleeting_state['anger']:.2f}")


        
if __name__ == '__main__':
          
    live_interactive_shell()
