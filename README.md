# A1-Cost-Tracker ( using 2 LLMs)

I made Python command-line tool that sends the same prompts three times to *OpenRouter* and *Groq* at the same time to compare their responses side by side, telling real token usage from each API response, calculates the exact cost in USD, and saving the results in "results.json".


# Structure of project
"tracker.py" = Main script that calls both providers, prints responses and a comparison table, and writes "results.json".
"pyproject.toml" = Project configuration and required Python dependencies ("openai" , "groq" , "python-dotenv").
".env.example" = Template showing the required environment variables without real API keys.
".gitignore" = Prevents ".env", virtual environments, and cache files from being committed.

# How to Run

1. Create a ".env" file in the project root and add your API keys and model settings.
2. Then, Run 1st prompt in terminal: uv run tracker.py "Explain why people procrastinate in two short sentences."
Result:
--- OPENROUTER (openrouter/free) ---
Procrastination is driven by the urge to avoid negative emotions—like anxiety, fear of failure, or boredom—rather than by laziness or poor time management. It’s maintained because delaying the task provides immediate emotional relief, even though it worsens stress long-term.

--- GROQ (openai/gpt-oss-20b) ---
People procrastinate because their brains prioritize immediate pleasure over long‑term goals, creating an instant reward loop. They also often fear failure or feel overwhelmed, so delaying tasks feels like an easier escape.

=== Summary Table ===
provider   | input tokens | output tokens | seconds | cost in USD
-----------+--------------+---------------+---------+------------
openrouter | 28           | 628           | 4.71    | $0.00000000
groq       | 81           | 114           | 0.77    | $0.00004027

Saved results.json

3. What lesson I learnt:

Different providers and models count tokens in their own way, eventhough the prompt is same. So it's more easy to read the real token counts from each API response as compared to make guesses.Also, keep your API keys in ".env" file while only sharing a ".env.example" file — this will keep your secrets from leaking into Git.

