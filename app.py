import gradio as gr
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings  # Use an alternative embedding
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.text_splitter import CharacterTextSplitter

from langchain_community.document_loaders import CSVLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

def csv_input(csv_paths, question):
    model_local = ChatOllama(model = "llama3")

    paths_list = csv_paths.split("\n")
    docs = [CSVLoader(file_path = path).load() for path in paths_list]
    docs_list = [item for sublist in docs for item in sublist]

    text_splitter = CharacterTextSplitter(chunk_size = 2000, chunk_overlap = 100)
    chunks = text_splitter.split_documents(documents = docs_list)

    vector_store = Chroma.from_documents(
        documents = chunks,
        embedding = FastEmbedEmbeddings
    )
    retriever = vector_store.as_retriever()

    memory_store = ConversationBufferMemory(memory_key = "chat_history", return_messages = True)
    chatQA = ConversationalRetrievalChain.from_llm(llm = model_local, retriever = retriever, memory = memory_store)

    prompt = ChatPromptTemplate.from_template( """
            <s> [INST] You are assistant chatbot who specializes in answering questions and performing analysis regarding data in csv files [/INST] </s> 
            [INST] Question: {question} 
            Context: {context} 
            Answer: [/INST]
            """)

    chain = ({"context": retriever, "question": RunnablePassthrough()}
                    | prompt
                    | model_local
                    | StrOutputParser())
    
    if (chain is None):
        return "Please add a csv file first"
    
    return chain.invoke(question)

# def process_input(urls, question):
#     # can switch to llama3 and try
#     model_local = ChatOllama(model="mistral")
    
#     # Convert string of URLs to list
#     urls_list = urls.split("\n")
#     docs = [WebBaseLoader(url).load() for url in urls_list]
#     docs_list = [item for sublist in docs for item in sublist]
    
#     text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=7500, chunk_overlap=100)
#     doc_splits = text_splitter.split_documents(docs_list)

#     vectorstore = Chroma.from_documents(
#         documents=doc_splits,
#         collection_name="rag-chroma",
#         embedding=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'),  # Using HuggingFaceEmbeddings as an alternative
#     )
#     retriever = vectorstore.as_retriever()

#     after_rag_template = """Answer the question based only on the following context:
#     {context}
#     Question: {question}
#     """
#     after_rag_prompt = ChatPromptTemplate.from_template(after_rag_template)
#     after_rag_chain = (
#         {"context": retriever, "question": RunnablePassthrough()}
#         | after_rag_prompt
#         | model_local
#         | StrOutputParser()
#     )
#     return after_rag_chain.invoke(question)

# Define Gradio interface
# iface = gr.Interface(fn=process_input,
#                      inputs=[gr.Textbox(label="Enter URLs separated by new lines"), gr.Textbox(label="Question")],
#                      outputs="text",
#                      title="Document Query with Ollama",
#                      description="Enter URLs and a question to query the documents.")
# iface.launch()

# https://ollama.com/
# https://ollama.com/blog/