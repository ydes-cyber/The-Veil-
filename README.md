# The-Veil-
Inspiration This project came directly from my game idea, The Veil. In a world defined by "Factional Politics & Dynamic Alliances," I quickly realized that traditional, scripted NPCs wouldn't work. The game demanded characters who could scheme, remember years of events, and betray you convincingly. I needed a psychological character that evolves its entire worldview based on the player’s choices.

What It Does This is the Adaptive Character Core, a plug-and-play system for any game engine that replaces scripts with evolving personalities. It turns NPCs into autonomous thinkers.

Every time the player interacts, the NPC executes a three-step cycle:

Thought ([ANALYSIS]): The hidden internal monologue. The NPC assesses its core goal, checks its morality, and predicts the player's next move.

Action ([ACTION]): A structured, immediate command for the game world. It could be something overt like ISSUE_THREAT or subtle like REPORT: Player_Location.

Speech ([DIALOGUE]): The actual line spoken, colored by the character's momentary Fleeting Emotional State (ex. anxiety or rage).

How We Built It We built a Hybrid ML Engine to power the characters:

Generative AI (Gemini LLM): This is the character's brain, used for high-level reasoning and complex strategy. I inject the character's Persona DNA (traits, goal, memory) into the prompt, forcing the model to follow the strict [ANALYSIS] output rules.

Traditional Machine Learning: A separate Sentiment Classifier analyzes the player's text for emotional cues. This allows the system to autonomously classify if the player is being hostile or cooperative, immediately feeding back into the NPC's Player Relationship Score.

State Management: The Python core manages the Moral Drift and the rotation of memories between the Short-Term Context and the vast Long-Term History.

Challenges We Ran Into The biggest hurdle was getting the AI to act like an engineer, not just a writer. It’s hard to force creative models to follow rigid rules. We struggled to ensure the LLM consistently stuck to the exact [ANALYSIS] / [ACTION] / [DIALOGUE] command format, which is essential for game integration. We solved this by creating a highly restrictive system prompt and custom parsing logic, transforming the model from a dialogue generator into a strategic reasoning engine.

Accomplishments We're Proud Of We are most proud of simulating genuine psychological evolution and autonomy:

Dynamic Moral Drift: The NPC's core Moral Alignment can shift. If a loyal character is repeatedly forced into ruthless actions, their morality permanently slides toward self-serving ruthlessness, changing how they justify their actions forever.

Autonomous Decision-Making: The NPC is fully unsupervised. It uses the Sentiment Classifier to react, its Fleeting State to feel, and its Moral Alignment to choose, making every decision a unique consequence of its experiences.

Game-Ready Output: The complete approach results in a clean, easily parsable command structure that meets the project's goal of being instantly plug-and-play with any external game engine.

What We Learned I learned that building an adaptable personality requires combining different types of ML. Generative AI is critical for strategy and dialogue, but efficient, real-time adaptation requires the structure of traditional machine learning. The project proved that an LLM can be directed to act as a Strategic Reasoning Partner, capable of self-analysis, prediction, and action, far beyond simple conversation.

Architecting a Universal AI Brain: I'll refine the massive Long-Term Memory (LTM) into a concise "Character History" summary. This makes the core truly platform-agnostic, able to plug into any AI or game engine by simply feeding it the prompt and traits. It gives the NPC context spanning years without token overload.

Multi-Modal Realism: Integrate input from things like voice tone or avatar microexpressions to automatically adjust the NPC's Fleeting Emotional States (e.g., setting "Anger" to 0.9). This is the key to deep, non-verbal realism.

Scaling the Political Landscape: Expand the core to manage nested relationships with multiple rival Factions. The NPC will have to weigh complex, multi-party alliances and betrayals against external groups, making its decisions even more dangerous.
