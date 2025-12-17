import os.path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import sys
import os
import config_loader

class CalendarManager:
    def __init__(self, config=None):
        self.creds = None
        self.service_calendar = None
        self.service_admin = None
        
        if config is None:
            self.config = config_loader.load_config()
        else:
            self.config = config

        self.authenticate()

    def authenticate(self):
        """Authenticates the 'Directory' service as the Admin to list users."""
        service_account_path = config_loader.get_service_account_path(self.config)
        delegated_user = self.config.get('delegated_user')
        
        if not delegated_user:
             raise ValueError("Missing 'delegated_user' in configuration.")

        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/admin.directory.user.readonly'
        ]

        if os.path.exists(service_account_path):
            # Base credentials
            self.base_creds = service_account.Credentials.from_service_account_file(
                service_account_path, scopes=SCOPES
            )
            # Admin Service (for Directory API)
            self.admin_creds = self.base_creds.with_subject(delegated_user)
            self.service_admin = build('admin', 'directory_v1', credentials=self.admin_creds)
        else:
            raise FileNotFoundError(f"Service account file '{service_account_path}' not found.")

    def get_users(self, domain):
        """Fetches all users from the specified domain."""
        users = []
        page_token = None
        try:
            while True:
                results = self.service_admin.users().list(
                    domain=domain,
                    maxResults=500,
                    pageToken=page_token,
                    query="orgUnitPath='/'" 
                ).execute()

                users_page = results.get('users', [])
                for user in users_page:
                    email = user.get('primaryEmail', '')
                    is_suspended = user.get('suspended', False)
                    if email.endswith(f'@{domain}') and not is_suspended:
                        users.append(email)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
        except HttpError as error:
            print(f'An error occurred fetching users describing {domain}: {error}')
            return []
        return users

    def _get_user_calendar_service(self, user_email):
        """Returns a Calendar service instance impersonating the specific user."""
        # Impersonate the target user
        creds = self.base_creds.with_subject(user_email)
        return build('calendar', 'v3', credentials=creds)

    def search_events(self, user_email, query_string=None, time_min=None, time_max=None):
        """Searches a specific user's calendar (impersonating them) with pagination."""
        all_events = []
        page_token = None
        try:
            service = self._get_user_calendar_service(user_email)
            while True:
                events_result_obj = service.events().list(
                    calendarId='primary',
                    q=query_string,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime',
                    pageToken=page_token
                ).execute()
                
                items = events_result_obj.get('items', [])
                all_events.extend(items)
                
                page_token = events_result_obj.get('nextPageToken')
                if not page_token:
                    break
                    
        except HttpError as error:
            # Common error: User suspended or service account access denied
            print(f'Error searching calendar for {user_email}: {error}')
        except Exception as e:
             print(f'General error for {user_email}: {e}')
        
        return all_events

    def delete_event(self, user_email, event_id):
        """Deletes a specific event from a user's calendar (impersonating them)."""
        try:
            service = self._get_user_calendar_service(user_email)
            service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f'Error deleting event {event_id} for {user_email}: {error}')
            return False
