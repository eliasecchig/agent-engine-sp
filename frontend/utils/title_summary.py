from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model_name="gemini-1.5-flash-001", temperature=0)

title_template = ChatPromptTemplate.from_messages(
    [("system", """Given a list of messages between a human and AI, come up with a short and relevant title for the conversation. Use up to 10 words. The title needs to be concise.
Examples:
**Input:**
```
Human: hi, what is the best italian dish?
AI: That's a tough one! Italy has so many amazing dishes, it's hard to pick just one "best." To help me give you a great suggestion, tell me a little more about what you're looking for.
```
**Output:** Best italian dish

**Input:**

```
Human: How to fix a broken laptop screen?
AI: Fixing a broken laptop screen can be tricky and often requires professional help. However, there are a few things you can try at home before resorting to a repair shop. 
```

**Output:** Fixing a broken laptop screen

**Input:**

```
Human: Can you write me a poem about the beach?
AI: As the sun dips down below the horizon
And the waves gently kiss the shore,
I sit here and watch the ocean
And feel its power evermore.
```

**Output:** Poem about the beach

**Input:**

```
Human: What's the best way to learn to code?
AI: There are many ways to learn to code, and the best method for you will depend on your learning style and goals. 
```

**Output:** How to learn to code
"""),

     MessagesPlaceholder(variable_name="messages"),
     ])

chain_title = title_template | llm
