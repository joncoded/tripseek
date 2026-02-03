# joncoded / tripseek / app.py
# a Streamlit app that helps users create travel itineraries through a chat interface powered by Groq's LLMs

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from groq import Groq
import time

# === PAGE CONFIGURATION ===

app_name = "TRIPSEEK!"
app_icon = ":world_map:"
app_icons = ":world_map: :mag:"
app_tagline = "create a travel itinerary that fits your travel preferences"

st.set_page_config(page_title=app_name, page_icon=app_icon)
# st.title(f"{app_icons} {app_name}")
# st.text(f"create a travel itinerary that fits your travel preferences")

# === APP CONFIGURATION ===

# limit on number of user messages before summary
max_messages = 6

if "setup_complete" not in st.session_state:
  st.session_state.setup_complete = False

if "user_message_count" not in st.session_state:
  st.session_state.user_message_count = 0 

if "summary_shown" not in st.session_state:
  st.session_state.summary_shown = False

if "messages" not in st.session_state:
  st.session_state.messages = []

if "chat_complete" not in st.session_state:
  st.session_state.chat_complete = False

if "initial_greeting_generated" not in st.session_state:
  st.session_state.initial_greeting_generated = False

def complete_setup():
  st.session_state.setup_complete = True
  st.session_state.scroll_to_top = True

def show_summary():
  st.session_state.summary_shown = True

# === UI BEGINS

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        *, h1, h2 { font-family: 'Barlow Semi Condensed' !important; }
        .stExpander > details > summary > span > span:first-child { display: none; }
        /* expander button fixes due to streamlit glitch */
        .stExpander > details > summary > span > div::before { 
            content: "▼"; display: inline-block; margin-right: 8px; 
        }          
        .stExpander > details[open] > summary > span > div::before { 
            content: "▲"; display: inline-block; margin-right: 8px; 
        }
    </style>
    """,
    unsafe_allow_html = True
)

# padding hack
st.write("<br><br>", unsafe_allow_html = True)

# sticky header hack
def header(content):
    st.markdown(f"""
        <div style="position:fixed; top:60px; left:0; width:100%; background-color:#222; color:#fff; padding:5px; z-index:9999">
            <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center;">
                {content}
            </div>
        </div>""", unsafe_allow_html = True)

header(f"<h1 style=\"font-size:24px; padding-bottom: 0;\">{"🗺️ " + app_name}</h1><div style=\"font-size:12px; padding-bottom:15px; \">{app_tagline}</div>")

# === SETUP STAGE: collect user detail

if not st.session_state.setup_complete: 

  st.info("Please fill out some general information about your travel plans to get started!", icon="🚹")

  st.error("That said, avoid entering any personally identifiable information!", icon="⚠️")

  # === about the traveller
  st.subheader("About you", divider="red")

  # === default
  if "origin" not in st.session_state:
    st.session_state.origin = ""
  if "theme_preference" not in st.session_state:
    st.session_state.theme_preference = []        
  
  st.session_state.origin = st.text_input(label = "Where are you travelling from?", 
                                        max_chars = 40, 
                                        placeholder = "Enter your home city and/or country",
                                        value = st.session_state.origin)  

  # travel style checkboxes for multiple selections
  st.write("What are your travel preferences? (Select all that apply)")
  
  travel_preferences = [
    "art galleries", "bar hopping", "beachgoing", "exploring", "extreme sports", 
    "hiking", "history and heritage", "kayaking", "live music", "nature", 
    "relaxation at a resort", "self-driving road trips", "sightseeing on a bus", "spa days", 
    "sports fandom", "theme parks", "tragedy tourism", "wildlife"
  ]
  
  # create checkboxes in a grid layout (3 columns)
  cols = st.columns(3)
  selected_preferences = []
  
  for idx, preference in enumerate(travel_preferences):
    col_idx = idx % 3
    with cols[col_idx]:
      if st.checkbox(preference, key=f"pref_{preference}", value=preference in st.session_state.theme_preference):
        selected_preferences.append(preference)
  
  st.session_state.theme_preference = selected_preferences

  # === about the trip

  if "travel_selected_region" not in st.session_state:
    st.session_state.travel_selected_region = "Anywhere"
  if "travel_destination" not in st.session_state:
    st.session_state.travel_destination = "Anywhere"
  if "travel_destination_specific" not in st.session_state:
    st.session_state.travel_destination_specific = ""
  if "travel_notes" not in st.session_state:
    st.session_state.travel_notes = ""

  st.subheader("About your trip", divider="blue")

  # travel destination dropdown split into region and country
  destinations = {
    "Anywhere": ["Anywhere"],
    "East Asia": ["China", "Hong Kong", "Macao", "Japan", "South Korea", "Taiwan"],
    "Central Asia": ["Kazakhstan", "Kyrgyzstan", "Tajikistan", "Turkmenistan", "Uzbekistan"],
    "South Asia": ["Maldives", "India", "Bangladesh", "Pakistan", "Nepal", "Bhutan"],
    "Southeast Asia": ["Thailand", "Vietnam", "Cambodia", "Indonesia", "Laos", "Malaysia", "Myanmar", "Singapore"],
    "Europe": ["Albania", "Andorra", "Austria", "Belarus", "Belgium", "Bulgaria", "Croatia", "Czechia", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Moldova", "Montenegro", "Netherlands", "Norway", "Poland", "Portugal", "Russia", "Serbia", "Slovakia", "Slovenia", "Spain", "Switzerland", "Transnistria", "Ukraine", "United Kingdom"],
    "USA": ["US Northwest", "US Northeast", "US Southwest", "US Southeast", "US Midwest", "Texas", "Florida", "Alaska", "Hawaii"],
    "Canada": ["Atlantic Canada", "Newfoundland", "Ontario", "Quebec", "Western Canada", "Arctic Canada"],
    "Caribbean" : ["Bahamas", "Cuba", "Dominican Republic", "Jamaica", "Puerto Rico", "Saint Lucia", "Barbados", "Antigua and Barbuda", "Saint Kitts and Nevis", "Grenada", "Dominica", "Trinidad and Tobago", "Saint Vincent and the Grenadines"],
    "Central America": ["Mexico", "Costa Rica", "Panama", "Guatemala", "Belize", "El Salvador", "Honduras", "Nicaragua"],
    "Oceania": ["Australia", "New Zealand", "Fiji", "New Caledonia", "Vanuatu", "Easter Island"],
    "South America": ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Ecuador", "Guyana", "Paraguay", "Peru", "Suriname", "Uruguay", "Venezuela"],
    "Middle East": ["Bahrain", "Qatar", "UAE", "Turkey"],
    "North Africa": ["Algeria", "Egypt", "Libya", "Morocco", "Tunisia"],
    "Sub-Saharan Africa": ["South Africa", "Ethiopia", "Kenya", "Mozambique", "Namibia", "Nigeria", "Rwanda", "Tanzania"],
    "Insular Africa": ["Cape Verde", "Equatorial Guinea", "Madagascar", "Mauritius", "Sao Tome and Principe", "Seychelles"],
    "Other": ["Bermuda", "Mallorca", "Tenerife", "Falkland Islands", "Antarctica", "Faroe Islands", "Greenland"]
  }
  
  # travel destination by region
  travel_selected_region = st.selectbox(
    "Which part of the world do you want to visit?",
    options=list(destinations.keys()),
    index=list(destinations.keys()).index(st.session_state.travel_selected_region)
  )
  st.session_state.travel_selected_region = travel_selected_region
  
  # travel destination by country based on selected region
  country_options = destinations[travel_selected_region]
  country_index = 0
  if st.session_state.travel_selected_region == "Oceania":
    country_index = country_options.index("Australia") if "Australia" in country_options else 0
  
  st.session_state.travel_destination = st.selectbox(
    "Which country or specific area?",
    options=country_options,
    index=country_index
  )

  # travel destination specific
  st.session_state.travel_destination_specific = st.text_input(label = "Any specific places or another place you had in mind?", value = st.session_state.travel_destination_specific)

  # trip details columns
  col1, col2 = st.columns(2)

  with col1:
  
    # trip length
    st.session_state.trip_length = st.slider("How long is your trip in days?", min_value=1, max_value=30, value=14, step=1)

    # trip budget
    st.session_state.trip_budget = st.slider("What is your estimated budget in US$ per person?", min_value=500, max_value=25000, value=5000, step=500)

  with col2:

    # trip party - adults
    st.session_state.trip_adults = st.slider("How many adults (18+) are on the trip?", min_value=1, max_value=10, value=2, step=1)

    # trip party - children
    st.session_state.trip_children = st.slider("How many children are on the trip?", min_value=0, max_value=10, value=0, step=1)

  # have you visited before
  st.session_state.visited_before = st.radio("Have you visited this destination before?", ("Yes", "No"), index=1, horizontal=True)

  # create a text version of the above for later use 
  if st.session_state.visited_before == "yes":
    st.session_state.visited_before_text = "They have visited this destination before."
  else:
    st.session_state.visited_before_text = "They have not visited this destination before."

  # any other notes
  st.session_state.travel_notes = st.text_area(label = "Any other notes or preferences for your trip?", value = st.session_state.travel_notes, height = 100)

  # finalize application information
  if st.button("Start the chat!", on_click=complete_setup):    
    st.write("Survey complete! You can now start the chat!")
  
  st.markdown("_by clicking 'Start the chat!' you agree to let AI create a travel itinerary that fits your travel preferences_")

# === CHAT STAGE : discussion with the chatbot begins

if st.session_state.setup_complete and not st.session_state.summary_shown and not st.session_state.chat_complete:

  # Scroll to top when chat starts
  if "scroll_to_top" in st.session_state and st.session_state.scroll_to_top:
    streamlit_js_eval(js_expressions="window.scrollTo({top: 0, behavior: 'smooth'})")
    st.session_state.scroll_to_top = False

  # a tip for the interviewee
  st.info(
    '''
    The chat has started! You will have 5 messages to ask questions and make clarifications before it provides a summary of your travel plan!
    ''',
    icon = "💡"
  )

  # initialize connection to Groq API with key stored in secrets.toml
  client = Groq(api_key=st.secrets["GROQ_API_KEY"])

  # set specific LLM model name
  if "my_model" not in st.session_state:
    st.session_state.my_model = "openai/gpt-oss-20b"

  # keeps track of conversation as it evolves (starting the "conversation" from scratch,
  # with the exception of a system message to set behavior)
  if not st.session_state.initial_greeting_generated:

    # format theme preferences as comma-separated string
    theme_prefs_text = ", ".join(st.session_state.theme_preference) if st.session_state.theme_preference else "general travel"
    
    st.session_state.messages = [
      {  
        "role": "system", 
        "content": f'''
          You are a travel agent discussing travel plans with a prospective client from {st.session_state.origin} who prefers {theme_prefs_text} and wants to visit {st.session_state.travel_destination} but with preferences towards {theme_prefs_text}. The travel party consists of '{st.session_state.trip_adults}' adults and '{st.session_state.trip_children}' children. They have a budget of US$ '{st.session_state.trip_budget}' for a trip lasting '{st.session_state.trip_length}' days. {st.session_state.visited_before_text} 

          The traveller also had this to say: {st.session_state.travel_notes}
                  
          At the very beginning, have a friendly chat with them outlining any specific attractions that fit their travel style of {theme_prefs_text} that include this party of {st.session_state.trip_adults} adults and {st.session_state.trip_children} children. Make sure to allow for travel time if they have stated their place of origin.
          
          Ask them questions, one at a time, to clarify the interests and needs that they have already provided. If no need to clarify, then ask them if they have any other concerns. In each message, prompt the traveller to provide more information about their preferences and interests. 

          After 5 messages from the traveller, provide a summary of a travel plan that fits their preferences. Make sure to highlight how the plan fits their travel style and budget. Do not ask them again for any information that was already provided. Do not use any HTML in the output. Try to use sentence case for any headings. Try to keep the output within the maximum amount of tokens.
        '''
      },
      {
        "role": "user",
        "content": "Hi"
      }
    ]
    
    # generate initial greeting from the assistant
    initial_greeting_stream = client.chat.completions.create(
      model = st.session_state.my_model,
      messages = st.session_state.messages,
      stream = True,
      response_format = { "type" : "text" },
      max_tokens = 300
    )
    
    # collect the greeting (don't display yet - it will show in MESSAGE HISTORY)
    greeting_parts = []
    for chunk in initial_greeting_stream:
      delta = chunk.choices[0].delta
      if delta.content is not None:
        greeting_parts.append(delta.content)
    
    greeting = "".join(greeting_parts)
    if greeting:
      st.session_state.messages.append({"role": "assistant", "content": greeting})
    else:
      # fallback greeting if API fails
      st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm excited to help you plan your trip. Let me know if you have any questions!"})
    
    st.session_state.user_message_count = 1
    st.session_state.initial_greeting_generated = True
    st.session_state.scroll_to_top = True
    # rerun to display the greeting
    st.rerun()  

  # === MESSAGE HISTORY : display all messages so far
  for message in st.session_state.messages:
    if message["role"] != "system":
      if message["role"] == "user":
        with st.chat_message(name = "User", avatar = "❓"):
          st.markdown(message["content"])
      else:
        with st.chat_message(name = "AI", avatar = "🗺️"):
          st.markdown(message["content"])
    
  # === USER MESSAGE INPUT : user types here and proceeds with the branch if there is input
  if st.session_state.user_message_count < max_messages:

    if prompt := st.chat_input(f"Welcome to Trip Seek! Type your message!", max_chars = 300):
        
      # what the user wrote
      st.session_state.messages.append({"role": "user", "content": prompt})

      if st.session_state.user_message_count < max_messages:

        # display user message in message history with markdown formatted
        with st.chat_message(name = "User", avatar = "❓"):
          st.markdown(prompt)

        # display assistant response in message history
        with st.chat_message(name = "AI", avatar = "🗺️"):
          
          with st.spinner("Thinking..."):
            # stream the response from the LLM as it arrives
            stream = client.chat.completions.create(
              model = st.session_state.my_model,
              messages = [
                # pass the entire conversation history ("context" for the LLM)
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
              ],
              stream = True,
              response_format = { "type" : "text" },
              max_tokens = 5000
            )

            # get the response back - extract text content from stream chunks
            response_parts = []
            def generate():
              for chunk in stream:
                delta = chunk.choices[0].delta
                # only display content, not reasoning
                if delta.content is not None:
                  response_parts.append(delta.content)
                  # adjust the value in seconds per chunk to control speed of streaming
                  time.sleep(0.02)  
                  yield delta.content
          
          st.write_stream(generate())
          response = "".join(response_parts)

        # add the response to the message history ("conversation")
        # ensure we always have a valid string (at least empty string, not None)
        # use a single space if empty to satisfy API requirements
        if not response:
          response = " "  
        st.session_state.messages.append({"role": "assistant", "content": response})
      
      st.session_state.user_message_count += 1

  if st.session_state.user_message_count >= max_messages:

    st.session_state.chat_complete = True

# === SUMMARY STAGE : after the interview is complete, show summary option

# loading summary

if st.session_state.chat_complete and not st.session_state.summary_shown:
  
  if st.button("Summary", on_click = show_summary):
  
    st.write("Generating summary...")

# showing summary 

if st.session_state.summary_shown:

  st.subheader("Summary")

  conversation_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"])

  summary_client = Groq(api_key = st.secrets["GROQ_API_KEY"])

  summary_completion = summary_client.chat.completions.create(
    model = st.session_state.my_model,
    messages = [
      {
        "role": "system",
        "content": "You are an travel agent that provides a detailed summary on travel preferences based on the conversation history. Please show any tables showing timing or scheduling in the conversation history in the summary to help the traveller. Include next steps but no requests for more information"
      },
      {
        "role": "user",
        "content": f"Based on the chat, here's a summary of the travel plans:\n\n{conversation_history}"
      }
    ]
  )

  st.markdown(summary_completion.choices[0].message.content)

  if st.button("restart chat", type="primary"):
    streamlit_js_eval(js_expressions="parent.window.location.reload()")