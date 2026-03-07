"""
Google Drive Sync Service for Starbright Content
Auto-uploads all generated images to Google Drive for backup
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

# Google Drive settings
GDRIVE_CREDENTIALS = "/root/.openclaw/secrets/google-drive-credentials.json"
GDRIVE_FOLDER_NAME = "Starbright AI Content"

class GoogleDriveSync:
    """
    Syncs generated content to Google Drive for backup.
    
    Setup:
    1. Requires Google Drive API credentials (OAuth2)
    2. First run opens browser for authorization
    3. Token saved for future runs
    """
    
    def __init__(self):
        self.credentials_path = GDRIVE_CREDENTIALS
        self.token_path = "/root/.openclaw/secrets/gdrive_token.json"
        self.service = None
        
    def _authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            creds = None
            # Load existing token
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
            # Refresh or create new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        logger.error("Google Drive credentials not found")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save token
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except ImportError:
            logger.error("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Get or create a folder in Google Drive"""
        try:
            # Search for existing folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            # Create new folder
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else []
            }
            
            folder = self.service.files().create(body=metadata, fields='id').execute()
            return folder['id']
            
        except Exception as e:
            logger.error(f"Folder creation failed: {e}")
            return None
    
    def _upload_file(self, file_path: Path, folder_id: str) -> Dict:
        """Upload a single file to Google Drive"""
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {
                'name': file_path.name,
                'parents': [folder_id]
            }
            
            media = MediaFileUpload(str(file_path), resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            return {
                'success': True,
                'id': file['id'],
                'name': file['name'],
                'url': file.get('webViewLink', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Upload failed for {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def sync_content(self, content_dirs: List[str] = None) -> Dict:
        """
        Sync all content to Google Drive
        
        Args:
            content_dirs: List of directories to sync (default: final + generated)
        
        Returns:
            Dict with sync results
        """
        if not self.service:
            if not self._authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        
        if content_dirs is None:
            content_dirs = [
                "/root/.openclaw/workspace/aia-content-backup/content/final/starbright_monroe",
                "/root/aia-engine/content/generated/starbright_monroe"
            ]
        
        results = {
            'uploaded': [],
            'failed': [],
            'skipped': []
        }
        
        try:
            # Create main folder
            main_folder_id = self._get_or_create_folder(GDRIVE_FOLDER_NAME)
            if not main_folder_id:
                return {'success': False, 'error': 'Failed to create main folder'}
            
            # Create date subfolder
            today = datetime.now().strftime("%Y-%m-%d")
            date_folder_id = self._get_or_create_folder(today, main_folder_id)
            
            # Find all images
            images = []
            for dir_path in content_dirs:
                path = Path(dir_path)
                if path.exists():
                    images.extend(path.glob("*.png"))
                    images.extend(path.glob("*.jpg"))
            
            logger.info(f"Found {len(images)} images to sync")
            
            # Upload each image
            for img in images:
                # Check if already uploaded (simple name check)
                # TODO: Implement proper tracking
                
                result = self._upload_file(img, date_folder_id)
                
                if result['success']:
                    results['uploaded'].append({
                        'name': img.name,
                        'drive_id': result['id'],
                        'url': result['url']
                    })
                else:
                    results['failed'].append({
                        'name': img.name,
                        'error': result.get('error')
                    })
            
            results['success'] = True
            results['total'] = len(images)
            results['drive_folder'] = f"https://drive.google.com/drive/folders/{date_folder_id}"
            
            return results
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return {'success': False, 'error': str(e)}

# Singleton instance
gdrive_sync = GoogleDriveSync()
