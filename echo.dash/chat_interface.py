import os
import json
import uuid
import logging
import time
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
import psutil
import threading
from queue import Queue

# Load environment variables
load_dotenv()

# Import session manager for automatic conversation saving
try:
    from chat_session_manager import (session_manager, ChatPlatform, 
                                     log_chat_message, create_chat_session)
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False
    logging.warning("Session manager not available - conversations won't be auto-saved")


class ChatInterface:
    def __init__(self):
        """Initialize the ChatGPT interface"""
        self.base_url = "https://chat.openai.com"
        self.session = requests.Session()
        self.session_token = None
        self.conversation_id = None
        self.parent_message_id = None
        
        # Session management for automatic conversation saving
        self.chat_session_id = None
        self.auto_save_enabled = SESSION_MANAGER_AVAILABLE
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more info
        self.logger = logging.getLogger(__name__)
        
        # Initialize session manager if available
        if SESSION_MANAGER_AVAILABLE:
            try:
                session_manager.start_auto_save()
                self.chat_session_id = create_chat_session(
                    "chatgpt", 
                    f"ChatGPT Session - {time.strftime('%Y-%m-%d %H:%M')}"
                )
                self.logger.info(f"Created chat session: {self.chat_session_id}")
            except Exception as e:
                self.logger.warning(f"Failed to initialize session manager: {str(e)}")
                self.auto_save_enabled = False
        
        # Set up logging
        logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for more info
        self.logger = logging.getLogger(__name__)
        
        # Set up headers that mimic ChatGPT desktop app
        self.session.headers.update({
            'authority': 'chat.openai.com',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://chat.openai.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def _generate_uuid(self):
        """Generate a UUID for message tracking"""
        return str(uuid.uuid4())
        
    def _make_request(self, method, endpoint, **kwargs):
        """Make a request to the ChatGPT API with proper error handling"""
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Response text: {e.response.text}")
            raise
            
    def authenticate(self, session_token):
        """Authenticate using session token"""
        try:
            self.session_token = session_token
            
            # Set essential cookies
            self.session.cookies.set(
                '__Secure-next-auth.session-token',
                session_token,
                domain='chat.openai.com',
                path='/',
                secure=True,
                rest={'HttpOnly': True}
            )
            
            # First request - Get CSRF token
            self.logger.info("Getting CSRF token...")
            response = self._make_request(
                'GET',
                '/',
                headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'}
            )
            
            # Second request - Get session info
            self.logger.info("Getting session info...")
            self.session.headers.update({
                'accept': '*/*',
                'authorization': '',
                'cookie': f'__Secure-next-auth.session-token={session_token}'
            })
            
            response = self._make_request('GET', '/backend-api/auth/session')
            data = response.json()
            self.logger.debug(f"Session response: {data}")
            
            if 'accessToken' in data:
                access_token = data['accessToken']
                self.session.headers.update({
                    'authorization': f'Bearer {access_token}',
                    'content-type': 'application/json'
                })
                self.logger.info("Successfully got access token")
                
                # Third request - Get user info
                self.logger.info("Getting user info...")
                user_response = self._make_request('GET', '/backend-api/me')
                user_data = user_response.json()
                self.logger.debug(f"User info: {user_data}")
                
                # Fourth request - Get conversation history
                self.logger.info("Getting conversation history...")
                conv_response = self._make_request(
                    'GET',
                    '/backend-api/conversations',
                    params={'offset': 0, 'limit': 1}
                )
                conv_data = conv_response.json()
                self.logger.debug(f"Conversation data: {conv_data}")
                
                return True
            else:
                self.logger.error("No access token in response")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
            
    def send_query(self, query):
        """Send a query to ChatGPT and get the response"""
        try:
            if not self.session_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
            
            # Log user message to session manager
            if self.auto_save_enabled and self.chat_session_id:
                try:
                    log_chat_message(
                        self.chat_session_id, 
                        "user", 
                        query,
                        platform=ChatPlatform.CHATGPT,
                        metadata={
                            "conversation_id": self.conversation_id,
                            "timestamp": time.time()
                        }
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to log user message: {str(e)}")
            
            # Generate message ID
            message_id = self._generate_uuid()
            parent_id = self.parent_message_id or self._generate_uuid()
            
            # Prepare payload (following the desktop app format)
            payload = {
                "action": "next",
                "messages": [
                    {
                        "id": message_id,
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": [query]},
                        "metadata": {}
                    }
                ],
                "model": "text-davinci-002-render-sha",  # Model used by web interface
                "parent_message_id": parent_id,
                "timezone_offset_min": -120,
                "suggestions": [],
                "history_and_training_disabled": False,
                "conversation_mode": {"kind": "primary_assistant"},
                "force_paragen": False,
                "force_rate_limit": False
            }
            
            if self.conversation_id:
                payload["conversation_id"] = self.conversation_id
            
            self.logger.info(f"Sending query: {query}")
            response = self._make_request(
                'POST',
                '/backend-api/conversation',
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                line = line[6:]  # Remove 'data: ' prefix
                                if line == '[DONE]':
                                    break
                                try:
                                    data = json.loads(line)
                                    if 'message' in data:
                                        message = data['message']
                                        if 'content' in message and 'parts' in message['content']:
                                            full_response = message['content']['parts'][0]
                                            # Update conversation state
                                            self.conversation_id = data.get('conversation_id')
                                            self.parent_message_id = message.get('id')
                                except json.JSONDecodeError:
                                    continue
                        except UnicodeDecodeError:
                            continue
                
                self.logger.info(f"Received response: {full_response}")
                
                # Log assistant response to session manager
                if self.auto_save_enabled and self.chat_session_id and full_response:
                    try:
                        log_chat_message(
                            self.chat_session_id, 
                            "assistant", 
                            full_response,
                            platform=ChatPlatform.CHATGPT,
                            metadata={
                                "conversation_id": self.conversation_id,
                                "parent_message_id": self.parent_message_id,
                                "timestamp": time.time()
                            }
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to log assistant response: {str(e)}")
                
                return full_response
            else:
                self.logger.error(f"Query failed: {response.status_code}")
                self.logger.error(f"Error message: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error sending query: {str(e)}")
            return None

    def monitor_resources(self, stop_event, resource_queue):
        while not stop_event.is_set():
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            resource_queue.put((cpu_usage, memory.percent))
            time.sleep(1)

if __name__ == "__main__":
    # Test the chat interface
    chat = ChatInterface()
    chat.logger.info("Attempting authentication...")
    
    # Get session token from environment variable
    session_token = os.getenv("CHATGPT_SESSION_TOKEN")
    if not session_token:
        chat.logger.error("CHATGPT_SESSION_TOKEN not found in .env file")
        exit(1)
        
    if chat.authenticate(session_token):
        chat.logger.info("Authentication successful!")
        chat.logger.info("Sending test query 'hi'...")
        response = chat.send_query("hi")
        if response:
            chat.logger.info(f"Test successful! Response: {response}")
        else:
            chat.logger.error("Failed to get response")
    else:
        chat.logger.error("Authentication failed")
