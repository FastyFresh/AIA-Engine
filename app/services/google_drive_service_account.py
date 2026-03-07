"""
Google Drive Service Account Sync
For automated server-to-server uploads without browser auth
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

logger = logging.getLogger(__name__)

# Service account credentials
SERVICE_ACCOUNT_FILE = "/root/.openclaw/secrets/google-service-account.json"
# Rick's Shared Drive (found via API)
SHARED_DRIVE_ID = "0AGJgVkKQKTUgUk9PVA"

class GoogleDriveServiceSync:
    """
    Syncs content to Google Drive using Service Account (no browser auth).
    
    Setup:
    1. Create service account in Google Cloud Console
    2. Download JSON key
    3. Share target Google Drive folder with service account email
    4. Place JSON key at SERVICE_ACCOUNT_FILE
    """
    
    def __init__(self):
        self.service_account_file = SERVICE_ACCOUNT_FILE
        self.service = None
        
    def _authenticate(self):
        """Authenticate with service account"""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            if not os.path.exists(self.service_account_file):
                logger.error(f"Service account file not found: {self.service_account_file}")
                return False
            
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES)
            
            self.service = build('drive', 'v3', credentials=credentials)
            return True
            
        except ImportError:
            logger.error("Google API libraries not installed")
            return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def _get_or_create_folder(self, folder_name: str, parent_id: str = None) -> str:
        """Get or create folder in Google Drive"""
        try:
            # Search for folder
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query, spaces='drive').execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            # Create folder
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id] if parent_id else []
            }
            
            folder = self.service.files().create(body=metadata, fields='id').execute()
            return folder['id']
            
        except Exception as e:
            logger.error(f"Folder error: {e}")
            return None
    
    def _create_folder_in_shared_drive(self, folder_name: str, drive_id: str) -> str:
        """Create folder in Shared Drive"""
        try:
            # Search for existing folder in Shared Drive
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(
                q=query, 
                spaces='drive',
                driveId=drive_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            # Create folder in Shared Drive
            metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'driveId': drive_id
            }
            
            folder = self.service.files().create(
                body=metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            return folder['id']
            
        except Exception as e:
            logger.error(f"Shared Drive folder error: {e}")
            return None
    
    def _upload_file(self, file_path: Path, folder_id: str) -> Dict:
        """Upload file to Drive"""
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
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            return {
                'success': True,
                'id': file['id'],
                'name': file['name'],
                'url': file.get('webViewLink', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def sync_content(self) -> Dict:
        """Sync all content to Google Drive Shared Drive"""
        if not self.service:
            if not self._authenticate():
                return {'success': False, 'error': 'Auth failed - check service account file'}
        
        content_dirs = [
            "/root/.openclaw/workspace/aia-content-backup/content/final/starbright_monroe",
            "/root/aia-engine/content/generated/starbright_monroe"
        ]
        
        results = {'uploaded': [], 'failed': [], 'total': 0}
        
        try:
            # Use Rick's Shared Drive
            drive_id = SHARED_DRIVE_ID
            
            # Create date folder in Shared Drive
            today = datetime.now().strftime("%Y-%m-%d")
            date_folder_id = self._create_folder_in_shared_drive(today, drive_id)
            
            # Collect images
            images = []
            for dir_path in content_dirs:
                path = Path(dir_path)
                if path.exists():
                    images.extend(path.glob("transform_*.png"))
                    images.extend(path.glob("*.jpg"))
            
            results['total'] = len(images)
            
            # Upload
            for img in images:
                result = self._upload_file(img, date_folder_id)
                if result['success']:
                    results['uploaded'].append(result)
                else:
                    results['failed'].append({'name': img.name, 'error': result.get('error')})
            
            results['success'] = True
            results['drive_folder'] = f"https://drive.google.com/drive/folders/{date_folder_id}"
            
            return results
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Singleton
gdrive_service_sync = GoogleDriveServiceSync()
