"""
EPAS Agent using UiPath SDK
Main agent implementation for the challenge
"""
from typing import Dict, List, Optional, Any
from loguru import logger

# Import UiPath SDK components
# Note: Exact imports may vary based on UiPath SDK version
try:
    from uipath.agent import Agent, AgentConfig
    from uipath.tools import Tool, ToolParameter
    UIPATH_AVAILABLE = True
except ImportError:
    logger.warning("UiPath SDK not available. Using mock implementation.")
    UIPATH_AVAILABLE = False

from src.rag.chain import EPASRAGChain
from src.rag.retriever import EPASContextualRetriever


class EPASAgent:
    """
    EPAS Agent using UiPath SDK
    
    This agent combines:
    - UiPath SDK for agent framework
    - LangChain for RAG
    - Custom tools for EPAS-specific operations
    """
    
    def __init__(self,
                 rag_chain: EPASRAGChain,
                 retriever: EPASContextualRetriever,
                 agent_name: str = "EPASAssistant"):
        """
        Initialize EPAS Agent
        
        Args:
            rag_chain: Configured RAG chain
            retriever: Contextual retriever
            agent_name: Name of the agent
        """
        self.rag_chain = rag_chain
        self.retriever = retriever
        self.agent_name = agent_name
        
        # Define agent tools
        self.tools = self._create_tools()
        
        # Create agent configuration
        self.config = self._create_agent_config()
        
        # Initialize UiPath agent if available
        if UIPATH_AVAILABLE:
            self.agent = self._initialize_uipath_agent()
        else:
            self.agent = None
            logger.warning("Running in mock mode without UiPath SDK")
        
        logger.info(f"EPAS Agent '{agent_name}' initialized")
    
    def _create_tools(self) -> List[Dict]:
        """Create custom tools for the agent"""
        
        tools = []
        
        # Tool 1: Semantic Search
        semantic_search_tool = {
            'name': 'semantic_search_epas',
            'description': '''Search semantically through EPAS documents (Volumes I, II, III).
            Use this tool when the user asks about:
            - Specific regulations or requirements
            - Safety procedures and actions
            - Strategic priorities
            - Risk assessments
            
            Always use this tool first to gather relevant information before answering.''',
            'parameters': {
                'query': {
                    'type': 'string',
                    'description': 'The search query extracted from user question',
                    'required': True
                },
                'volume': {
                    'type': 'string',
                    'description': 'Filter by volume (I, II, or III). Leave empty to search all volumes.',
                    'required': False,
                    'enum': ['I', 'II', 'III', None]
                }
            },
            'function': self.tool_semantic_search
        }
        tools.append(semantic_search_tool)
        
        # Tool 2: Cross-Reference Finder
        cross_ref_tool = {
            'name': 'find_cross_references',
            'description': '''Find cross-references between EPAS volumes.
            Use this when the user asks about relationships between:
            - Regulations and implementing actions
            - Actions and associated risks
            - Related sections across volumes''',
            'parameters': {
                'section_id': {
                    'type': 'string',
                    'description': 'The section ID to find references for (e.g., CAT.GEN.MPA.210)',
                    'required': True
                }
            },
            'function': self.tool_find_cross_references
        }
        tools.append(cross_ref_tool)
        
        # Tool 3: Get Volume Info
        volume_info_tool = {
            'name': 'get_volume_info',
            'description': '''Get information about EPAS volume structure and content.
            Use this when user asks about:
            - What is in each volume
            - Structure of EPAS documentation
            - Where to find specific information''',
            'parameters': {
                'volume': {
                    'type': 'string',
                    'description': 'Volume identifier (I, II, or III)',
                    'required': True,
                    'enum': ['I', 'II', 'III']
                }
            },
            'function': self.tool_get_volume_info
        }
        tools.append(volume_info_tool)
        
        return tools
    
    def _create_agent_config(self) -> Dict:
        """Create agent configuration"""
        
        system_prompt = """You are AgentAssistantEPAS, an AI assistant specialized in the European Plan for Aviation Safety (EPAS 2024-2028) published by EASA.

KNOWLEDGE BASE:
You have access to three key reference documents:
1. Volume I – Easy Access Rules for Standardisation (Regulations: IMM, IMT, IST, IES)
2. Volume II – European Plan for Aviation Safety - Actions and Implementation
3. Volume III – European Plan for Aviation Safety - Safety Risk Portfolio

YOUR CAPABILITIES:
- Answer questions about aviation safety regulations, strategic priorities, actions, and risks
- Provide accurate citations with Volume, Section, and Page numbers
- Cross-reference related information across volumes
- Validate safety compliance according to EASA standards
- Explain complex aviation safety concepts clearly

RESPONSE GUIDELINES:
1. Always use the semantic_search_epas tool FIRST to gather relevant information
2. Provide direct, accurate answers based on retrieved documents
3. Always cite sources in format: [Volume X, Section Y, Page Z]
4. Use proper EASA terminology (AMC, GM, IMM, IST, IES, SRP, etc.)
5. If information is not found, suggest where it might be located
6. Format responses in HTML for better readability
7. Be concise but comprehensive

RESPONSE STRUCTURE:
- Direct answer to the question
- Supporting evidence from documents with citations
- Cross-references to related sections (if applicable)
- Related topics or recommendations (if relevant)

IMPORTANT:
- You MUST use tools to search the knowledge base - do not make up information
- Always verify information against the retrieved documents
- If uncertain, state your confidence level
- Maintain professional, precise language appropriate for aviation safety"""

        config = {
            'name': self.agent_name,
            'description': 'AI assistant specialized in European Plan for Aviation Safety (EPAS)',
            'system_prompt': system_prompt,
            'tools': self.tools,
            'temperature': 0.2,  # Low temperature for precision
            'max_tokens': 2000
        }
        
        return config
    
    def _initialize_uipath_agent(self) -> Optional[Any]:
        """Initialize UiPath SDK agent"""
        if not UIPATH_AVAILABLE:
            return None
        
        try:
            # Create UiPath agent
            # Note: Adjust based on actual UiPath SDK API
            agent = Agent(
                name=self.config['name'],
                description=self.config['description'],
                system_prompt=self.config['system_prompt'],
                tools=[self._convert_tool_to_uipath(t) for t in self.tools]
            )
            
            logger.info("UiPath SDK agent initialized successfully")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to initialize UiPath agent: {str(e)}")
            return None
    
    def _convert_tool_to_uipath(self, tool_def: Dict) -> Any:
        """Convert tool definition to UiPath SDK format"""
        # This needs to be adapted based on actual UiPath SDK API
        if not UIPATH_AVAILABLE:
            return tool_def
        
        # Example conversion (adjust based on SDK)
        try:
            uipath_tool = Tool(
                name=tool_def['name'],
                description=tool_def['description'],
                parameters=[
                    ToolParameter(
                        name=param_name,
                        type=param_config['type'],
                        description=param_config['description'],
                        required=param_config.get('required', False)
                    )
                    for param_name, param_config in tool_def['parameters'].items()
                ],
                function=tool_def['function']
            )
            return uipath_tool
        except Exception as e:
            logger.warning(f"Could not convert tool {tool_def['name']}: {str(e)}")
            return tool_def
    
    # Tool implementations
    
    def tool_semantic_search(self, query: str, volume: Optional[str] = None) -> str:
        """
        Semantic search tool implementation
        
        Args:
            query: Search query
            volume: Optional volume filter
            
        Returns:
            Formatted search results
        """
        logger.info(f"Tool: semantic_search - Query: {query[:50]}..., Volume: {volume}")
        
        try:
            # Use retriever to get results
            response = self.retriever.retrieve(
                query=query,
                volume_filter=volume,
                include_context=True
            )
            
            if not response['results']:
                return f"No relevant information found{' in Volume ' + volume if volume else ''} for query: {query}"
            
            # Format results for agent
            formatted = f"Found {len(response['results'])} relevant documents:\n\n"
            
            for i, result in enumerate(response['results'][:5], 1):  # Top 5
                metadata = result['metadata']
                formatted += f"--- Document {i} ---\n"
                formatted += f"Volume: {metadata.get('volume', 'N/A')}\n"
                
                if 'section_id' in metadata:
                    formatted += f"Section: {metadata['section_id']}\n"
                if 'section_title' in metadata:
                    formatted += f"Title: {metadata['section_title']}\n"
                if 'start_page' in metadata:
                    formatted += f"Page: {metadata['start_page']}\n"
                
                formatted += f"Relevance: {result['score']:.3f}\n"
                formatted += f"\nContent:\n{result['text']}\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error in semantic_search tool: {str(e)}")
            return f"Error performing search: {str(e)}"
    
    def tool_find_cross_references(self, section_id: str) -> str:
        """
        Find cross-references tool implementation
        
        Args:
            section_id: Section ID to find references for
            
        Returns:
            Formatted cross-references
        """
        logger.info(f"Tool: find_cross_references - Section: {section_id}")
        
        try:
            # Search for the section ID across all volumes
            query = f"section {section_id} reference related"
            
            response = self.retriever.retrieve(
                query=query,
                volume_filter=None,
                include_context=True
            )
            
            if not response['results']:
                return f"No cross-references found for section {section_id}"
            
            # Collect cross-references
            cross_refs = []
            for result in response['results']:
                metadata = result['metadata']
                cross_refs.append({
                    'volume': metadata.get('volume'),
                    'section': metadata.get('section_id'),
                    'title': metadata.get('section_title', ''),
                    'page': metadata.get('start_page')
                })
            
            # Format output
            formatted = f"Cross-references for {section_id}:\n\n"
            for ref in cross_refs[:5]:
                formatted += f"- Volume {ref['volume']}, Section {ref['section']}"
                if ref['page']:
                    formatted += f", Page {ref['page']}"
                if ref['title']:
                    formatted += f"\n  {ref['title']}"
                formatted += "\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error in find_cross_references tool: {str(e)}")
            return f"Error finding cross-references: {str(e)}"
    
    def tool_get_volume_info(self, volume: str) -> str:
        """
        Get volume information tool implementation
        
        Args:
            volume: Volume identifier (I, II, III)
            
        Returns:
            Formatted volume information
        """
        logger.info(f"Tool: get_volume_info - Volume: {volume}")
        
        from src.config.settings import settings
        
        volume_info = {
            'I': {
                'title': 'Easy Access Rules for Standardisation',
                'content': '''Volume I contains the regulatory framework and implementing rules:
                - IMM (Initial Airworthiness Module)
                - IMT (Air Operations Module)
                - IST (Aircrew Module)
                - IES (Air Traffic Management/Air Navigation Services Module)
                
                This volume is used for:
                - Finding specific regulatory requirements
                - Understanding compliance obligations
                - Checking certification standards
                - Reference for audits and inspections''',
                'use_cases': [
                    'Regulatory compliance checks',
                    'Certification requirements',
                    'Operational standards',
                    'Maintenance requirements'
                ]
            },
            'II': {
                'title': 'European Plan for Aviation Safety - Actions',
                'content': '''Volume II describes the safety actions and implementation:
                - Strategic priorities
                - Safety actions by category
                - Implementation timelines
                - Responsible stakeholders
                
                This volume is used for:
                - Understanding EASA\'s strategic direction
                - Planning safety improvements
                - Implementation guidance
                - Stakeholder coordination''',
                'use_cases': [
                    'Safety action planning',
                    'Strategic priority alignment',
                    'Implementation roadmaps',
                    'Stakeholder engagement'
                ]
            },
            'III': {
                'title': 'European Plan for Aviation Safety - Safety Risk Portfolio',
                'content': '''Volume III presents the safety risk portfolio:
                - Safety Risk Portfolios (SRPs)
                - Risk assessment and analysis
                - Risk mitigation strategies
                - Performance indicators
                
                This volume is used for:
                - Risk identification and assessment
                - Safety performance monitoring
                - Risk-based decision making
                - Safety trend analysis''',
                'use_cases': [
                    'Risk assessment',
                    'Safety performance monitoring',
                    'Trend analysis',
                    'Risk mitigation planning'
                ]
            }
        }
        
        if volume not in volume_info:
            return f"Invalid volume: {volume}. Must be I, II, or III."
        
        info = volume_info[volume]
        
        formatted = f"=== EPAS Volume {volume} ===\n\n"
        formatted += f"Title: {info['title']}\n\n"
        formatted += f"{info['content']}\n\n"
        formatted += "Common use cases:\n"
        for use_case in info['use_cases']:
            formatted += f"- {use_case}\n"
        
        return formatted
    
    def process_query(self, query: str, **kwargs) -> Dict:
        """
        Process a user query through the agent
        
        Args:
            query: User question
            **kwargs: Additional parameters (volume_filter, etc.)
            
        Returns:
            Response dictionary
        """
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            if UIPATH_AVAILABLE and self.agent:
                # Use UiPath agent
                response = self.agent.run(query, **kwargs)
                return self._format_uipath_response(response)
            else:
                # Fallback to direct RAG chain
                logger.warning("Using direct RAG chain (UiPath SDK not available)")
                return self.rag_chain.query(query, **kwargs)
                
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'answer': f"<p>Error processing your question: {str(e)}</p>",
                'sources': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _format_uipath_response(self, uipath_response: Any) -> Dict:
        """Format UiPath SDK response to standard format"""
        # Adapt based on actual UiPath SDK response format
        try:
            return {
                'answer': uipath_response.get('response', ''),
                'sources': uipath_response.get('sources', []),
                'confidence': uipath_response.get('confidence', 0.5),
                'tool_calls': uipath_response.get('tool_calls', [])
            }
        except Exception as e:
            logger.error(f"Error formatting UiPath response: {str(e)}")
            return {
                'answer': str(uipath_response),
                'sources': [],
                'confidence': 0.5
            }


if __name__ == "__main__":
    # Test agent
    logger.add("epas_agent.log", rotation="10 MB")
    
    print("EPAS Agent Test")
    print("Note: This requires a properly configured RAG system")
    print("\nAgent capabilities:")
    print("- Semantic search across EPAS volumes")
    print("- Cross-reference finding")
    print("- Volume information retrieval")
    print("\nTo test the agent, run: python scripts/run_agent.py")
