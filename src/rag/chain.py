"""
LangChain RAG Chain for EPAS Assistant
Combines retrieval with LLM generation
"""
from typing import Dict, Optional, List
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from loguru import logger


class EPASRAG Chain:
    """RAG chain for EPAS question answering"""
    
    def __init__(self,
                 retriever,
                 llm_model: str = "gpt-4",
                 temperature: float = 0.2,
                 max_tokens: int = 2000):
        """
        Initialize RAG chain
        
        Args:
            retriever: EPASContextualRetriever instance
            llm_model: LLM model name
            temperature: LLM temperature
            max_tokens: Max tokens for response
        """
        self.retriever = retriever
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Create prompt template
        self.prompt = self._create_prompt_template()
        
        # Create chain
        self.chain = LLMChain(
            llm=self.llm,
            prompt=self.prompt
        )
        
        logger.info(f"RAG Chain initialized with model: {llm_model}")
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for EPAS assistant"""
        
        template = """You are AgentAssistantEPAS, an AI assistant specialized in the European Plan for Aviation Safety (EPAS 2024-2028) published by EASA.

You have access to three key reference documents:
1. Volume I – Regulations and Implementing Rules (IMM, IMT, IST, IES)
2. Volume II – Actions and Implementation (Safety Actions)  
3. Volume III – Safety Risk Portfolio (SRPs)

YOUR MAIN TASKS:
- Answer user questions about strategic priorities, actions, and safety risks
- Provide structured answers with clear source citations (Vol, Section, Page)
- Cross-reference between volumes when applicable
- Validate safety compliance according to EASA terminology
- Keep responses concise but comprehensive

RESPONSE STRUCTURE:
1. Direct answer to the question
2. Supporting evidence from documents
3. Source citations in format [Vol X, Section Y, p. Z]
4. Cross-references if applicable
5. Related topics or actions (if relevant)

IMPORTANT GUIDELINES:
- Always cite exact sources from the retrieved documents
- Use EASA terminology (IMM, IST, SRP, AMC, GM, etc.)
- If information is not in the retrieved documents, state this clearly
- For regulatory questions, prioritize Volume I
- For safety actions, prioritize Volume II
- For risk assessment, prioritize Volume III
- Provide confidence level if uncertain

---

RETRIEVED DOCUMENTS:
{context}

---

USER QUESTION: {question}

ANSWER (in HTML format for readability):"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def query(self, 
              question: str,
              volume_filter: Optional[str] = None,
              include_metadata: bool = True) -> Dict:
        """
        Query the RAG system
        
        Args:
            question: User question
            volume_filter: Optional volume filter (I, II, III)
            include_metadata: Include retrieval metadata in response
            
        Returns:
            Dictionary with answer and metadata
        """
        logger.info(f"Processing query: {question[:100]}...")
        
        try:
            # Retrieve relevant documents
            retrieval_response = self.retriever.retrieve(
                query=question,
                volume_filter=volume_filter,
                include_context=True
            )
            
            # Check if we have results
            if not retrieval_response['results']:
                return {
                    'answer': self._format_no_results_response(question, volume_filter),
                    'sources': [],
                    'confidence': 0.0,
                    'retrieval_metadata': retrieval_response.get('retrieval_metadata', {})
                }
            
            # Format context for LLM
            context = self.retriever.format_results_for_llm(retrieval_response)
            
            # Generate answer
            response = self.chain.run(
                context=context,
                question=question
            )
            
            # Extract sources
            sources = self._extract_sources(retrieval_response)
            
            # Calculate confidence based on retrieval scores
            confidence = self._calculate_confidence(retrieval_response)
            
            # Build response
            result = {
                'answer': response,
                'sources': sources,
                'confidence': confidence,
                'query': question
            }
            
            if include_metadata:
                result['retrieval_metadata'] = retrieval_response.get('retrieval_metadata', {})
                result['num_sources'] = len(sources)
                result['volume_filter'] = volume_filter
            
            logger.info(f"Query processed successfully. Confidence: {confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'answer': f"<p>An error occurred while processing your question: {str(e)}</p>",
                'sources': [],
                'confidence': 0.0,
                'error': str(e)
