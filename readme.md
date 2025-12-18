# tripseek

a travel-oriented chatbot that focuses on user inputs:

- travel habits
- trip origin
- trip destination
- trip length 
- trip budget
- trip party (# of adults and # of children)
- repeat visitor or first timer?

a chat will then occur with:

- AI-powered recommendations
- user clarifications

after a few questions, the AI will process the adjusted recommendations and provide a printable "summary"!

## demo

- see link on sidebar

## requirements

- python installed on local machine
- groq api key

## setup

in the command line: 

```
$ pip install -r
```

on a folder called `.streamlit`, create a file called `secrets.toml` and insert:

```
GROQ_API_KEY="(your Groq API key)" 
```

(include the quotation marks!)

then to run:

```
$ streamlit run app.py
```