"""
Supabase client manager for OpenAI Codegen Adapter.
Handles database operations, connection management, and table creation.
"""

import os
import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from contextlib import asynccontextmanager

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .models import (
    EndpointContext, WebsiteConfig, ChatSession, ChatMessage,
    EndpointVariable, BrowserInteraction, EndpointTest,
    SupabaseConnectionConfig, SupabaseConnectionTest,
    EndpointType, EndpointStatus, VariableType
)

logger = logging.getLogger(__name__)


class SupabaseManager:
    """
    Manages Supabase database operations for the OpenAI Codegen Adapter.
    Provides CRUD operations for endpoints, chat sessions, and configurations.
    """
    
    def __init__(self, config: Optional[SupabaseConnectionConfig] = None):
        """Initialize the Supabase manager."""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
        
        self.config = config
        self.client: Optional[Client] = None
        self.connected = False
        self.table_prefix = config.table_prefix if config else "codegen_adapter"
        
        # Table names
        self.tables = {
            'endpoints': f"{self.table_prefix}_endpoints",
            'website_configs': f"{self.table_prefix}_website_configs",
            'chat_sessions': f"{self.table_prefix}_chat_sessions",
            'chat_messages': f"{self.table_prefix}_chat_messages",
            'endpoint_variables': f"{self.table_prefix}_endpoint_variables",
            'browser_interactions': f"{self.table_prefix}_browser_interactions",
            'endpoint_tests': f"{self.table_prefix}_endpoint_tests"
        }
        
        if config:
            asyncio.create_task(self.connect())
    
    async def connect(self, config: Optional[SupabaseConnectionConfig] = None) -> SupabaseConnectionTest:
        """Connect to Supabase database."""
        if config:
            self.config = config
            self.table_prefix = config.table_prefix
            self._update_table_names()
        
        if not self.config:
            return SupabaseConnectionTest(
                success=False,
                message="No configuration provided",
                error_details="Supabase configuration is required"
            )
        
        start_time = datetime.now()
        
        try:
            # Create Supabase client
            options = ClientOptions(
                auto_refresh_token=True,
                persist_session=True
            )
            
            self.client = create_client(
                self.config.url,
                self.config.key,
                options=options
            )
            
            # Test connection by trying to access a system table
            response = self.client.table('information_schema.tables').select('table_name').limit(1).execute()
            
            connection_time = (datetime.now() - start_time).total_seconds()
            
            if response.data is not None:
                self.connected = True
                
                # Check existing tables
                tables_found = await self._check_existing_tables()
                tables_created = []
                
                # Create tables if needed
                if self.config.auto_create_tables:
                    tables_created = await self._create_tables()
                
                return SupabaseConnectionTest(
                    success=True,
                    message="Successfully connected to Supabase",
                    connection_time=connection_time,
                    tables_found=tables_found,
                    tables_created=tables_created
                )
            else:
                return SupabaseConnectionTest(
                    success=False,
                    message="Failed to connect to Supabase",
                    connection_time=connection_time,
                    error_details="Unable to query database"
                )
                
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return SupabaseConnectionTest(
                success=False,
                message=f"Connection failed: {str(e)}",
                connection_time=(datetime.now() - start_time).total_seconds(),
                error_details=str(e)
            )
    
    def _update_table_names(self):
        """Update table names with new prefix."""
        self.tables = {
            'endpoints': f"{self.table_prefix}_endpoints",
            'website_configs': f"{self.table_prefix}_website_configs",
            'chat_sessions': f"{self.table_prefix}_chat_sessions",
            'chat_messages': f"{self.table_prefix}_chat_messages",
            'endpoint_variables': f"{self.table_prefix}_endpoint_variables",
            'browser_interactions': f"{self.table_prefix}_browser_interactions",
            'endpoint_tests': f"{self.table_prefix}_endpoint_tests"
        }
    
    async def _check_existing_tables(self) -> List[str]:
        """Check which tables already exist."""
        if not self.client:
            return []
        
        try:
            # Query information_schema to check for existing tables
            response = self.client.table('information_schema.tables').select('table_name').eq('table_schema', 'public').execute()
            
            if response.data:
                existing_tables = [row['table_name'] for row in response.data]
                return [table for table in self.tables.values() if table in existing_tables]
            
            return []
        except Exception as e:
            logger.warning(f"Could not check existing tables: {e}")
            return []
    
    async def _create_tables(self) -> List[str]:
        """Create database tables if they don't exist."""
        if not self.client:
            return []
        
        created_tables = []
        
        # SQL for creating tables
        table_schemas = {
            self.tables['website_configs']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['website_configs']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    description TEXT,
                    authentication_required BOOLEAN DEFAULT FALSE,
                    authentication_method TEXT,
                    authentication_config JSONB DEFAULT '{{}}',
                    headers JSONB DEFAULT '{{}}',
                    cookies JSONB DEFAULT '{{}}',
                    user_agent TEXT,
                    timeout INTEGER DEFAULT 30,
                    retry_attempts INTEGER DEFAULT 3,
                    wait_for_load FLOAT DEFAULT 2.0,
                    screenshot_on_error BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            self.tables['endpoints']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['endpoints']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL,
                    endpoint_type TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    url TEXT,
                    model_name TEXT,
                    api_key TEXT,
                    website_config_id UUID REFERENCES {self.tables['website_configs']}(id),
                    text_input_selector TEXT,
                    send_button_selector TEXT,
                    response_selector TEXT,
                    request_template TEXT,
                    response_parser TEXT,
                    custom_headers JSONB DEFAULT '{{}}',
                    parameters JSONB DEFAULT '{{}}',
                    description TEXT,
                    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
                    created_by TEXT,
                    last_tested TIMESTAMP WITH TIME ZONE,
                    test_results JSONB,
                    usage_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            self.tables['endpoint_variables']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['endpoint_variables']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    endpoint_id UUID NOT NULL REFERENCES {self.tables['endpoints']}(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    variable_type TEXT NOT NULL,
                    value JSONB NOT NULL,
                    default_value JSONB,
                    description TEXT,
                    is_required BOOLEAN DEFAULT FALSE,
                    is_sensitive BOOLEAN DEFAULT FALSE,
                    validation_pattern TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(endpoint_id, name)
                );
            """,
            
            self.tables['browser_interactions']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['browser_interactions']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    endpoint_id UUID NOT NULL REFERENCES {self.tables['endpoints']}(id) ON DELETE CASCADE,
                    element_type TEXT NOT NULL,
                    selector TEXT NOT NULL,
                    xpath TEXT,
                    element_text TEXT,
                    attributes JSONB DEFAULT '{{}}',
                    interaction_method TEXT NOT NULL,
                    wait_condition TEXT,
                    fallback_selectors TEXT[] DEFAULT ARRAY[]::TEXT[],
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            self.tables['chat_sessions']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['chat_sessions']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id TEXT,
                    session_name TEXT,
                    endpoint_id UUID REFERENCES {self.tables['endpoints']}(id),
                    provider TEXT,
                    context JSONB DEFAULT '{{}}',
                    message_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    settings JSONB DEFAULT '{{}}',
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    ended_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            self.tables['chat_messages']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['chat_messages']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID NOT NULL REFERENCES {self.tables['chat_sessions']}(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    endpoint_id UUID REFERENCES {self.tables['endpoints']}(id),
                    provider TEXT,
                    model TEXT,
                    tokens_used INTEGER,
                    response_time FLOAT,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """,
            
            self.tables['endpoint_tests']: f"""
                CREATE TABLE IF NOT EXISTS {self.tables['endpoint_tests']} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    endpoint_id UUID NOT NULL REFERENCES {self.tables['endpoints']}(id) ON DELETE CASCADE,
                    test_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_data JSONB,
                    response_data JSONB,
                    response_time FLOAT,
                    error_message TEXT,
                    test_config JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """
        }
        
        # Create tables
        for table_name, schema in table_schemas.items():
            try:
                # Execute the CREATE TABLE statement
                self.client.rpc('exec_sql', {'sql': schema}).execute()
                created_tables.append(table_name)
                logger.info(f"Created table: {table_name}")
            except Exception as e:
                logger.error(f"Failed to create table {table_name}: {e}")
        
        return created_tables
    
    def _ensure_connected(self):
        """Ensure we have a valid connection."""
        if not self.connected or not self.client:
            raise RuntimeError("Not connected to Supabase. Call connect() first.")
    
    # Endpoint management methods
    
    async def create_endpoint(self, endpoint: EndpointContext) -> EndpointContext:
        """Create a new endpoint."""
        self._ensure_connected()
        
        endpoint_data = endpoint.dict(exclude={'id', 'created_at', 'updated_at'})
        endpoint_data['id'] = str(uuid.uuid4())
        endpoint_data['created_at'] = datetime.now().isoformat()
        endpoint_data['updated_at'] = datetime.now().isoformat()
        
        # Convert lists and dicts to JSON
        if 'tags' in endpoint_data:
            endpoint_data['tags'] = endpoint_data['tags'] or []
        if 'custom_headers' in endpoint_data:
            endpoint_data['custom_headers'] = json.dumps(endpoint_data['custom_headers'])
        if 'parameters' in endpoint_data:
            endpoint_data['parameters'] = json.dumps(endpoint_data['parameters'])
        if 'test_results' in endpoint_data and endpoint_data['test_results']:
            endpoint_data['test_results'] = json.dumps(endpoint_data['test_results'])
        
        response = self.client.table(self.tables['endpoints']).insert(endpoint_data).execute()
        
        if response.data:
            return EndpointContext(**response.data[0])
        else:
            raise RuntimeError("Failed to create endpoint")
    
    async def get_endpoint(self, endpoint_id: str) -> Optional[EndpointContext]:
        """Get an endpoint by ID."""
        self._ensure_connected()
        
        response = self.client.table(self.tables['endpoints']).select('*').eq('id', endpoint_id).execute()
        
        if response.data:
            endpoint_data = response.data[0]
            # Parse JSON fields
            if endpoint_data.get('custom_headers'):
                endpoint_data['custom_headers'] = json.loads(endpoint_data['custom_headers'])
            if endpoint_data.get('parameters'):
                endpoint_data['parameters'] = json.loads(endpoint_data['parameters'])
            if endpoint_data.get('test_results'):
                endpoint_data['test_results'] = json.loads(endpoint_data['test_results'])
            
            return EndpointContext(**endpoint_data)
        
        return None
    
    async def list_endpoints(self, endpoint_type: Optional[EndpointType] = None, 
                           status: Optional[EndpointStatus] = None) -> List[EndpointContext]:
        """List all endpoints with optional filtering."""
        self._ensure_connected()
        
        query = self.client.table(self.tables['endpoints']).select('*')
        
        if endpoint_type:
            query = query.eq('endpoint_type', endpoint_type.value)
        if status:
            query = query.eq('status', status.value)
        
        response = query.order('created_at', desc=True).execute()
        
        endpoints = []
        if response.data:
            for endpoint_data in response.data:
                # Parse JSON fields
                if endpoint_data.get('custom_headers'):
                    endpoint_data['custom_headers'] = json.loads(endpoint_data['custom_headers'])
                if endpoint_data.get('parameters'):
                    endpoint_data['parameters'] = json.loads(endpoint_data['parameters'])
                if endpoint_data.get('test_results'):
                    endpoint_data['test_results'] = json.loads(endpoint_data['test_results'])
                
                endpoints.append(EndpointContext(**endpoint_data))
        
        return endpoints
    
    async def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> Optional[EndpointContext]:
        """Update an endpoint."""
        self._ensure_connected()
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # Convert complex types to JSON
        if 'custom_headers' in updates:
            updates['custom_headers'] = json.dumps(updates['custom_headers'])
        if 'parameters' in updates:
            updates['parameters'] = json.dumps(updates['parameters'])
        if 'test_results' in updates:
            updates['test_results'] = json.dumps(updates['test_results'])
        
        response = self.client.table(self.tables['endpoints']).update(updates).eq('id', endpoint_id).execute()
        
        if response.data:
            endpoint_data = response.data[0]
            # Parse JSON fields
            if endpoint_data.get('custom_headers'):
                endpoint_data['custom_headers'] = json.loads(endpoint_data['custom_headers'])
            if endpoint_data.get('parameters'):
                endpoint_data['parameters'] = json.loads(endpoint_data['parameters'])
            if endpoint_data.get('test_results'):
                endpoint_data['test_results'] = json.loads(endpoint_data['test_results'])
            
            return EndpointContext(**endpoint_data)
        
        return None
    
    async def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        self._ensure_connected()
        
        response = self.client.table(self.tables['endpoints']).delete().eq('id', endpoint_id).execute()
        return len(response.data) > 0 if response.data else False
    
    # Variable management methods
    
    async def create_variable(self, variable: EndpointVariable) -> EndpointVariable:
        """Create a new endpoint variable."""
        self._ensure_connected()
        
        variable_data = variable.dict(exclude={'id', 'created_at', 'updated_at'})
        variable_data['id'] = str(uuid.uuid4())
        variable_data['created_at'] = datetime.now().isoformat()
        variable_data['updated_at'] = datetime.now().isoformat()
        
        # Convert value to JSON
        variable_data['value'] = json.dumps(variable_data['value'])
        if variable_data.get('default_value') is not None:
            variable_data['default_value'] = json.dumps(variable_data['default_value'])
        
        response = self.client.table(self.tables['endpoint_variables']).insert(variable_data).execute()
        
        if response.data:
            var_data = response.data[0]
            var_data['value'] = json.loads(var_data['value'])
            if var_data.get('default_value'):
                var_data['default_value'] = json.loads(var_data['default_value'])
            return EndpointVariable(**var_data)
        else:
            raise RuntimeError("Failed to create variable")
    
    async def get_endpoint_variables(self, endpoint_id: str) -> List[EndpointVariable]:
        """Get all variables for an endpoint."""
        self._ensure_connected()
        
        response = self.client.table(self.tables['endpoint_variables']).select('*').eq('endpoint_id', endpoint_id).execute()
        
        variables = []
        if response.data:
            for var_data in response.data:
                var_data['value'] = json.loads(var_data['value'])
                if var_data.get('default_value'):
                    var_data['default_value'] = json.loads(var_data['default_value'])
                variables.append(EndpointVariable(**var_data))
        
        return variables
    
    # Chat session methods
    
    async def create_chat_session(self, session: ChatSession) -> ChatSession:
        """Create a new chat session."""
        self._ensure_connected()
        
        session_data = session.dict(exclude={'id', 'created_at', 'updated_at'})
        session_data['id'] = str(uuid.uuid4())
        session_data['created_at'] = datetime.now().isoformat()
        session_data['updated_at'] = datetime.now().isoformat()
        
        # Convert complex types to JSON
        session_data['context'] = json.dumps(session_data['context'])
        session_data['settings'] = json.dumps(session_data['settings'])
        
        response = self.client.table(self.tables['chat_sessions']).insert(session_data).execute()
        
        if response.data:
            session_data = response.data[0]
            session_data['context'] = json.loads(session_data['context'])
            session_data['settings'] = json.loads(session_data['settings'])
            return ChatSession(**session_data)
        else:
            raise RuntimeError("Failed to create chat session")
    
    async def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        self._ensure_connected()
        
        response = self.client.table(self.tables['chat_sessions']).select('*').eq('id', session_id).execute()
        
        if response.data:
            session_data = response.data[0]
            session_data['context'] = json.loads(session_data['context'])
            session_data['settings'] = json.loads(session_data['settings'])
            return ChatSession(**session_data)
        
        return None
    
    async def add_chat_message(self, message: ChatMessage) -> ChatMessage:
        """Add a message to a chat session."""
        self._ensure_connected()
        
        message_data = message.dict(exclude={'id', 'created_at'})
        message_data['id'] = str(uuid.uuid4())
        message_data['created_at'] = datetime.now().isoformat()
        
        # Convert metadata to JSON
        message_data['metadata'] = json.dumps(message_data['metadata'])
        
        response = self.client.table(self.tables['chat_messages']).insert(message_data).execute()
        
        if response.data:
            msg_data = response.data[0]
            msg_data['metadata'] = json.loads(msg_data['metadata'])
            
            # Update session message count and last activity
            await self._update_session_activity(message.session_id)
            
            return ChatMessage(**msg_data)
        else:
            raise RuntimeError("Failed to add chat message")
    
    async def get_chat_messages(self, session_id: str, limit: int = 100) -> List[ChatMessage]:
        """Get messages for a chat session."""
        self._ensure_connected()
        
        response = (self.client.table(self.tables['chat_messages'])
                   .select('*')
                   .eq('session_id', session_id)
                   .order('created_at', desc=False)
                   .limit(limit)
                   .execute())
        
        messages = []
        if response.data:
            for msg_data in response.data:
                msg_data['metadata'] = json.loads(msg_data['metadata'])
                messages.append(ChatMessage(**msg_data))
        
        return messages
    
    async def _update_session_activity(self, session_id: str):
        """Update session activity timestamp and message count."""
        response = self.client.table(self.tables['chat_sessions']).update({
            'last_activity': datetime.now().isoformat(),
            'message_count': self.client.table(self.tables['chat_messages']).select('id', count='exact').eq('session_id', session_id).execute().count + 1
        }).eq('id', session_id).execute()
    
    # Website configuration methods
    
    async def create_website_config(self, config: WebsiteConfig) -> WebsiteConfig:
        """Create a new website configuration."""
        self._ensure_connected()
        
        config_data = config.dict(exclude={'id', 'created_at', 'updated_at'})
        config_data['id'] = str(uuid.uuid4())
        config_data['created_at'] = datetime.now().isoformat()
        config_data['updated_at'] = datetime.now().isoformat()
        
        # Convert complex types to JSON
        config_data['authentication_config'] = json.dumps(config_data['authentication_config'])
        config_data['headers'] = json.dumps(config_data['headers'])
        config_data['cookies'] = json.dumps(config_data['cookies'])
        
        response = self.client.table(self.tables['website_configs']).insert(config_data).execute()
        
        if response.data:
            config_data = response.data[0]
            config_data['authentication_config'] = json.loads(config_data['authentication_config'])
            config_data['headers'] = json.loads(config_data['headers'])
            config_data['cookies'] = json.loads(config_data['cookies'])
            return WebsiteConfig(**config_data)
        else:
            raise RuntimeError("Failed to create website configuration")
    
    async def get_website_config(self, config_id: str) -> Optional[WebsiteConfig]:
        """Get a website configuration by ID."""
        self._ensure_connected()
        
        response = self.client.table(self.tables['website_configs']).select('*').eq('id', config_id).execute()
        
        if response.data:
            config_data = response.data[0]
            config_data['authentication_config'] = json.loads(config_data['authentication_config'])
            config_data['headers'] = json.loads(config_data['headers'])
            config_data['cookies'] = json.loads(config_data['cookies'])
            return WebsiteConfig(**config_data)
        
        return None
    
    # Utility methods
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the database connection."""
        try:
            self._ensure_connected()
            
            # Test basic query
            response = self.client.table(self.tables['endpoints']).select('id').limit(1).execute()
            
            return {
                'status': 'healthy',
                'connected': True,
                'tables': list(self.tables.keys()),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        self._ensure_connected()
        
        stats = {}
        
        try:
            # Count endpoints by type
            endpoints_response = self.client.table(self.tables['endpoints']).select('endpoint_type', count='exact').execute()
            stats['total_endpoints'] = endpoints_response.count if endpoints_response.count else 0
            
            # Count active sessions
            sessions_response = self.client.table(self.tables['chat_sessions']).select('id', count='exact').is_('ended_at', 'null').execute()
            stats['active_sessions'] = sessions_response.count if sessions_response.count else 0
            
            # Count total messages
            messages_response = self.client.table(self.tables['chat_messages']).select('id', count='exact').execute()
            stats['total_messages'] = messages_response.count if messages_response.count else 0
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            stats['error'] = str(e)
        
        return stats


# Global instance
_supabase_manager: Optional[SupabaseManager] = None


def get_supabase_manager() -> Optional[SupabaseManager]:
    """Get the global Supabase manager instance."""
    return _supabase_manager


def set_supabase_manager(manager: SupabaseManager):
    """Set the global Supabase manager instance."""
    global _supabase_manager
    _supabase_manager = manager


async def initialize_supabase(config: SupabaseConnectionConfig) -> SupabaseConnectionTest:
    """Initialize the global Supabase manager."""
    global _supabase_manager
    
    _supabase_manager = SupabaseManager(config)
    result = await _supabase_manager.connect()
    
    if not result.success:
        _supabase_manager = None
    
    return result
