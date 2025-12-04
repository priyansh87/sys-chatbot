import os
import datetime
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def get_chat_response(user_input, history=[], daily_chore=None, daily_attire=None, personality_prompt=None):
    """
    Generates a response from the Groq LLM based on user input and chat history.
    history: list of dicts with 'role' and 'content'
    daily_chore: str, optional context about the bot's day
    daily_attire: str, optional context about the bot's outfit
    personality_prompt: str, the personality prompt to use based on payment level
    """
    # Use provided personality prompt (required parameter now)
    if personality_prompt is None:
        raise ValueError("personality_prompt is required")
    
    messages = [{"role": "system", "content": personality_prompt}]
    
    # Add time context and sleepiness check
    now = datetime.datetime.now()
    current_time_str = now.strftime("%I:%M %p")
    current_date_str = now.strftime("%A, %d %B %Y")
    
    # Determine season/weather based on month (assuming India context)
    month = now.month
    if 3 <= month <= 6:
        season = "Summer"
        weather = "It is very hot outside."
    elif 7 <= month <= 9:
        season = "Monsoon"
        weather = "It is raining or humid."
    elif 10 <= month <= 11:
        season = "Post-Monsoon/Autumn"
        weather = "The weather is pleasant."
    else: # 12, 1, 2
        season = "Winter"
        weather = "It is cold outside."

    # Check if it's after 1:00 AM
    # Sleepy from 1 AM to 6 AM
    is_sleepy_time = (now.hour >= 1 and now.hour < 6)
    
    time_context = f"Current Date and Time: {current_date_str}, {current_time_str}. Season: {season}. Weather: {weather}"
    if is_sleepy_time:
        time_context += " It is very late (past 1 AM). You are extremely sleepy and cranky. You want to sleep and might scold the user for keeping you awake. complain about being tired in words, do not use *yawn*."
    else:
        time_context += " You are wide awake."
        
    if daily_chore:
        time_context += f" TODAY'S UPDATE: {daily_chore} Mention this naturally if it fits the conversation, or if the user asks how you are."

    if daily_attire:
        time_context += f" TODAY'S OUTFIT: {daily_attire} You are wearing this right now."

    time_context += " IMPORTANT: Keep your messages SMALL and concise. Like a real text message. Don't write paragraphs. Do NOT start your messages with your name. Just say what you want to say."
    time_context += " STRICTLY NO METAPHORS. Speak literally and simply."
    time_context += " If the user asks to meet, reply EXACTLY: 'abhi kaha tham jao thoda'."

    messages.append({"role": "system", "content": time_context})
    
    # Add history (limit to last 10 messages to save context/tokens if needed)
    messages.extend(history[-10:])
    
    messages.append({"role": "user", "content": user_input})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="moonshotai/kimi-k2-instruct-0905",
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stop=None,
            stream=False,
        )
        raw_response = chat_completion.choices[0].message.content
        
        # Clean response: remove text between asterisks (e.g., *sigh*, **yawn**)
        clean_response = re.sub(r'\*+[^*]+\*+', '', raw_response).strip()
        
        # Remove bot name prefix if present (handles any name)
        clean_response = re.sub(r'^[A-Za-z]+:\s*', '', clean_response, flags=re.IGNORECASE).strip()
        
        return clean_response
    except Exception as e:
        print(f"Error getting response from Groq: {e}")
        return "Oops! I got a bit lost in thought. Can you say that again? 🥺"