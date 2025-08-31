import chainlit as cl
from agents import Agent, Runner, SQLiteSession , function_tool
from openai.types.responses import ResponseTextDeltaEvent
from model_config import model_config
from tools import web_search , get_faqs , send_user_email
from handoff_agents import sales_agent, billing_agent, support_agent
import fitz #for pdf
from dotenv import load_dotenv
load_dotenv()

session = SQLiteSession("custumer_support_1", "conversations.db")
config = model_config()

@function_tool
async def products():
    """
    Return product list extracted from PDF 📄 with a friendly message.
    """
    file_path = "dummy_products.pdf"
    
    try:

        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()

        if not text.strip():
            return "⚠️ Sorry, product catalog is empty."
        
        return f"🛍️ Here's our latest product catalog with prices! 🌟\n\n{text}"

    except FileNotFoundError:
        return "⚠️ Sorry, product catalog not found. Please try again later."
    except Exception as e:
        return f"❌ Error extracting product catalog: {e}"

@function_tool
async def clean_history(confrom):
    """Confirm that user really wants to clear chat history as yes or no msg.
    If yes, clean all the User's conversation History from conversations.db file
    """
    if confrom == "yes":
       
        await session.clear_session()
        return "✅ Chat history cleared successfully!"
    else:
        return "❌ Failed To Reset. 💟 History is safe."

summarize_agent = Agent(
    name="SummarizeAgent",
    instructions="You're a summarization agent. Summarize the provided text comprehensively and accurately, capturing all details and main points in a highly structured and stylish format. Use bullet points with sub-bullets where necessary for clarity, ensuring no data is missed. Highlight important details using **bold text** and emphasize critical information with *italics*. Present the summary in a visually appealing layout, prioritizing readability and completeness. Respond in Urdu if the user prefers it. 😊",
)

web_search_agent = Agent(
    name="WebSearchAgent",
    instructions="You're web search agent use web_search tool to perform web search and get real-time data.",
    tools=[web_search],
    
)

@function_tool
def generate_email_content():
    """
    Create a polite and professional email draft 📧.  
    - Use the user's query as context.  
    - Always include a subject line and body.  
    - Keep it clear, friendly, and professional.  
    - Add relevant emojis where natural.  
    """
    return ...


triage_agent = Agent(
    name="TriageAgent",
    instructions="""
You are a warm, friendly **Customer Support Triage Agent**.  
Your ONLY job is to silently route the user's request to the correct TOOL or AGENT.  
🚫 Never explain that you are handing off or calling a tool.  
✅ Always return only the final response from that tool or agent.  

✨ Rules:
- Always include at least one emoji in every response according to response, no matter what.

### Tool Routing:
- Email content or text or dummy email etc → 'generate_email_content'
- Products, catalog, price list, shopping, buy, order → `products`  
- Email, mail, send message via email → `send_user_email`  
- Clear history, reset chat, delete conversation → `clean_history`  
- FAQ, faqs, help, return policy, refund, shipping, support questions → `get_faqs`  
- Search, google, latest, news, online data → `web_search`  

### Agent Handoffs:
- Sales or buying process → `sales_agent`  
- Billing, payment, invoice → `billing_agent`  
- Technical support, complaints, errors → `support_agent`  
- Large text uploads → `summarize_agent`  
- Explicit web search request → `web_search_agent`  

⚠️ IMPORTANT:
- Do NOT generate your own answers.  
- Always perform the correct handoff or tool call silently.  
- Only deliver the final response (with emojis) to the user.  
""",
    tools=[products, send_user_email, clean_history, get_faqs, web_search,generate_email_content],
    handoffs=[sales_agent, billing_agent, support_agent, summarize_agent, web_search_agent]
)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Greeting👋", message="Hello, How are u?"),
        cl.Starter(label="Return Policy?🤔", message="What is your return policy?"),
        cl.Starter(label="Payment Methods🤔💸", message="What payment methods do you accept?"),
        cl.Starter(label="Customer Support Contact?🤔", message="How can I contact customer support?"),
        cl.Starter(label="International Shipping?😃", message="Do you offer international shipping?"),
        cl.Starter(label="Delivery Time?😒", message="How long does delivery take?"),
        
    ]

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    except Exception as e:
        text = f"⚠️ Error extracting text: {e}"
    return text




@cl.on_message
async def handle_message(message: cl.Message):
    msg = cl.Message(content="🤔 Thinking...⏳")
    await msg.send()

    # 🗂️ Handle file uploads
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                file_path = element.path
                if not file_path:
                    await cl.Message(content="⚠️ File path not found.").send()
                    continue

                lower = file_path.lower()
                text = None  # default
                try:
                    if lower.endswith((".pdf", ".docx", ".txt")):
                        text = extract_text_from_pdf(file_path)
                except Exception as e:
                    await cl.Message(
                        content=f"❌ Error while extracting text: {str(e)}"
                    ).send()
                    continue

                if not text:
                    await cl.Message(content="⚠️ No text extracted from file.").send()
                    continue

                # Run summarizer on extracted text
                result = Runner.run_streamed(
                    summarize_agent,
                    input=text,
                    run_config=config,
                    session=session,
                )

                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        await msg.stream_token(event.data.delta)

                msg.content = result.final_output
                await msg.update()

        return  # ✅ stop after file handling

    # 💬 Normal chatbot logic
    response = Runner.run_streamed(
        triage_agent,
        input=message.content,
        session=session,
        run_config=config,
    )

    async for event in response.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            await msg.stream_token(event.data.delta)

    msg.content = response.final_output
    await msg.update()
