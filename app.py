import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatMessagePromptTemplate, MessagesPlaceholder, ChatPromptTemplate
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()



def get_vectorstore_from_url(url):
    loader = WebBaseLoader(url)
    document = loader.load()

    text_splitter = RecursiveCharacterTextSplitter()
    documents_chunks = text_splitter.split_documents(document)

    vector_store = Chroma.from_documents(documents_chunks,OpenAIEmbeddings(openai_api_key="<YOUR Open AI KEY>") )

    return vector_store

def get_context_retriever_chain(vector_store):
    llm = ChatOpenAI(openai_api_key="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",model_name="gpt-3.5-turbo-1106")
    
    retriever = vector_store.as_retriever()

    prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("user","{input}"),
        ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
    ])

    retriever_chain = create_history_aware_retriever(llm,retriever,prompt)
    return retriever_chain

def get_conversational_rag_chain(retriever_chain):
    llm = ChatOpenAI(openai_api_key="<YOUR Open AI KEY>",model_name="gpt-3.5-turbo-1106")
    
    prompt = ChatPromptTemplate.from_messages([
      ("system", "Answer the user's questions based on the below context:\n\n{context}"),
      MessagesPlaceholder(variable_name="chat_history"),
      ("user", "{input}"),
    ])
    stuff_documents_chain = create_stuff_documents_chain(llm,prompt)
    
    return create_retrieval_chain(retriever_chain,stuff_documents_chain)


def get_response(user_input):
    retriever_chain = get_context_retriever_chain( st.session_state.vector_store)
    conversation_rag_chain = get_conversational_rag_chain(retriever_chain)
    response = conversation_rag_chain.invoke({
            "chat_history": st.session_state.chat_history,
            "input": user_query
        })
    return response['answer']

st.set_page_config(page_title="Chat with Documentation", page_icon="🔍")
st.title("Chat with Tosca Manuals")

with st.sidebar:
    st.header("Settings")
    website_url = st.text_input("Manual URL")
   


if website_url is None or website_url == "":
    st.info("Please enter website URL")

else:

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [AIMessage(content="Hello! I'm your manual hepler, How can I help you?")]
    if " vector_store" not in st.session_state:
         st.session_state.vector_store = get_vectorstore_from_url(website_url)
    
    
   

user_query = st.chat_input("Type your query here...")
if user_query is not None and user_query !="":
        response = get_response(user_query)
        st.session_state.chat_history.append(HumanMessage(content=user_query))
        st.session_state.chat_history.append(AIMessage(content=response))
    
        

for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                st.write(message.content)
        elif isinstance(message,HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)
