import customtkinter as ctk
import threading
import concurrent.futures
from tkinter import messagebox
from calendar_manager import CalendarManager
import datetime

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CalendarNukeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Calendar Nuke")
        self.geometry("900x750")

        self.mgr = None
        try:
            self.mgr = CalendarManager()
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize Calendar Manager:\n{e}")

        # Data storage
        self.found_events = [] 
        self.abort_event = threading.Event()
        self.is_running = False

        self._init_ui()

    def _init_ui(self):
        # --- Top Panel: Search Criteria ---
        self.frame_search = ctk.CTkFrame(self)
        self.frame_search.pack(pady=10, padx=10, fill="x")

        # Grid layout for search frame
        self.frame_search.grid_columnconfigure(1, weight=1)
        self.frame_search.grid_columnconfigure(3, weight=1)

        # Domain Selection
        self.domain_var = ctk.StringVar()
        lbl_domain = ctk.CTkLabel(self.frame_search, text="Target Group:")
        lbl_domain.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.frame_radios = ctk.CTkFrame(self.frame_search, fg_color="transparent")
        self.frame_radios.grid(row=0, column=1, columnspan=3, sticky="w")
        
        # Dynamic Radio Buttons from Config
        self.target_groups = self.mgr.config.get('target_groups', [])
        if self.target_groups:
             # Default to first group
             self.domain_var.set(self.target_groups[0]['domain'])
             
             for group in self.target_groups:
                 name = group['name']
                 domain = group['domain']
                 rb = ctk.CTkRadioButton(self.frame_radios, text=name, variable=self.domain_var, value=domain)
                 rb.pack(side="left", padx=10)
        else:
             ctk.CTkLabel(self.frame_radios, text="No target groups configured", text_color="red").pack()

        # Keyword
        ctk.CTkLabel(self.frame_search, text="Keyword (Subject/Desc):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_keyword = ctk.CTkEntry(self.frame_search, placeholder_text="e.g. 'Mandatory Meeting'")
        self.entry_keyword.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Organizer
        ctk.CTkLabel(self.frame_search, text="Organizer Email (Optional):").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.entry_organizer = ctk.CTkEntry(self.frame_search, placeholder_text="attacker@bad.com")
        self.entry_organizer.grid(row=1, column=3, padx=10, pady=5, sticky="ew")

        # Date Range
        ctk.CTkLabel(self.frame_search, text="Start Date (YYYY-MM-DD):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.entry_start = ctk.CTkEntry(self.frame_search)
        self.entry_start.insert(0, datetime.date.today().isoformat())
        self.entry_start.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.frame_search, text="End Date (YYYY-MM-DD):").grid(row=2, column=2, padx=10, pady=5, sticky="w")
        self.entry_end = ctk.CTkEntry(self.frame_search, placeholder_text=datetime.date.today().isoformat())
        self.entry_end.grid(row=2, column=3, padx=10, pady=5, sticky="ew")

        # Scan Button
        # Scan Button (and Reset)
        self.btn_reset = ctk.CTkButton(self.frame_search, text="Reset", width=80, fg_color="gray", command=self.reset_fields)
        self.btn_reset.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.btn_scan = ctk.CTkButton(self.frame_search, text="SCAN DOMAIN FOR EVENTS", fg_color="#D32F2F", hover_color="#B71C1C", command=self.start_scan)
        self.btn_scan.grid(row=3, column=1, columnspan=3, padx=10, pady=10, sticky="ew")

        # --- Progress Bar & Abort ---
        self.frame_progress = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_progress.pack(padx=10, pady=5, fill="x")

        self.progress_bar = ctk.CTkProgressBar(self.frame_progress)
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_abort = ctk.CTkButton(self.frame_progress, text="ABORT", width=100, fg_color="gray", command=self.abort_process, state="disabled")
        self.btn_abort.pack(side="right")

        self.status_label = ctk.CTkLabel(self, text="Ready")
        self.status_label.pack(pady=2)

        # --- Middle Panel: Results ---
        self.frame_results_container = ctk.CTkFrame(self)
        self.frame_results_container.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(self.frame_results_container, text="Found Events", font=("Arial", 16, "bold")).pack(pady=5)
        
        # Headers
        headers_frame = ctk.CTkFrame(self.frame_results_container, fg_color="transparent")
        headers_frame.pack(fill="x", padx=5)
        ctk.CTkLabel(headers_frame, text="Select", width=50).pack(side="left")
        ctk.CTkLabel(headers_frame, text="User", width=200, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Summary", width=250, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(headers_frame, text="Date", width=150, anchor="w").pack(side="left", padx=5)

        self.scroll_results = ctk.CTkScrollableFrame(self.frame_results_container, label_text="")
        self.scroll_results.pack(pady=5, padx=5, fill="both", expand=True)

        # --- Bottom Panel: Actions ---
        self.frame_actions = ctk.CTkFrame(self)
        self.frame_actions.pack(pady=10, padx=10, fill="x")

        self.btn_select_all = ctk.CTkButton(self.frame_actions, text="Select All", command=self.select_all)
        self.btn_select_all.pack(side="left", padx=10, pady=10)

        self.btn_nuke = ctk.CTkButton(self.frame_actions, text="NUKE SELECTED EVENTS", fg_color="#D32F2F", hover_color="#B71C1C", command=self.start_nuke)
        self.btn_nuke.pack(side="right", padx=10, pady=10)


    def log(self, message):
        self.after(0, lambda: self.status_label.configure(text=message))

    def set_running(self, running):
        self.is_running = running
        state = "normal" if not running else "disabled"
        abort_state = "normal" if running else "disabled"
        abort_color = "#D32F2F" if running else "gray"
        
        self.btn_scan.configure(state=state)
        self.btn_nuke.configure(state=state)
        self.btn_abort.configure(state=abort_state, fg_color=abort_color)

    def abort_process(self):
        if self.is_running:
            self.abort_event.set()
            self.log("Aborting... please wait for current tasks to finish.")

    def reset_fields(self):
        if self.is_running:
            return
        
        # self.domain_var.set("staff") # Removed to preserve selection and avoid hardcoding
        self.entry_keyword.delete(0, "end")
        self.entry_organizer.delete(0, "end")
        
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, datetime.date.today().isoformat())
        
        self.entry_end.delete(0, "end")
        
        # Set focus to main window to ensure placeholders appear
        self.focus()

        self.found_events = []
        for widget in self.scroll_results.winfo_children():
            widget.destroy()
            
        self.progress_bar.set(0)
        self.log("Ready")

    def start_scan(self):
        if not self.mgr:
            messagebox.showerror("Error", "Backend not initialized.")
            return
            
        keyword = self.entry_keyword.get().strip()
        organizer = self.entry_organizer.get().strip()
        start_date = self.entry_start.get().strip()
        end_date = self.entry_end.get().strip()
        
        
        # The variable now holds the domain directly
        domain = self.domain_var.get()

        if not keyword and not organizer:
            messagebox.showwarning("Input Required", "Please enter a keyword or organizer email.")
            return

        t_min = f"{start_date}T00:00:00Z" if start_date else None
        t_max = f"{end_date}T23:59:59Z" if end_date else None

        self.set_running(True)
        self.abort_event.clear()
        self.found_events = []
        for widget in self.scroll_results.winfo_children():
            widget.destroy()

        threading.Thread(target=self._scan_thread, args=(domain, keyword, organizer, t_min, t_max), daemon=True).start()

    def _scan_thread(self, domain, keyword, organizer, t_min, t_max):
        self.log(f"Fetching user list for {domain}...")
        users = self.mgr.get_users(domain)
        total_users = len(users)
        
        if total_users == 0:
            self.log("No users found or error fetching users.")
            self.after(0, lambda: self.set_running(False))
            return

        self.log(f"Scanning {total_users} calendars (10 threads)...")
        
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_user = {executor.submit(self.mgr.search_events, user, keyword, t_min, t_max): user for user in users}
            
            for future in concurrent.futures.as_completed(future_to_user):
                if self.abort_event.is_set():
                    self.log("Scan Aborted. Cancelling pending tasks...")
                    # Note: We can't easily cancel running tasks, but we stop processing results
                    break

                user = future_to_user[future]
                processed_count += 1
                
                # Update progress roughly
                progress = (processed_count / total_users)
                self.progress_bar.set(progress)
                self.log(f"Scanning: {processed_count}/{total_users} ({user})")

                try:
                    events = future.result()
                    # Filter organizer
                    if organizer and events:
                        filtered = []
                        for e in events:
                            org = e.get('organizer', {}).get('email', '')
                            creator = e.get('creator', {}).get('email', '')
                            if organizer.lower() in org.lower() or organizer.lower() in creator.lower():
                                filtered.append(e)
                        events = filtered

                    if events:
                        for e in events:
                            self._add_result_row(user, e)
                except Exception as exc:
                    print(f'{user} generated an exception: {exc}')

        self.progress_bar.set(1.0)
        if not self.abort_event.is_set():
            self.log(f"Scan Complete. Found {len(self.found_events)} events.")
        
        self.after(0, lambda: self.set_running(False))

    def _add_result_row(self, user, event):
        self.after(0, lambda: self._create_row_widget(user, event))

    def _create_row_widget(self, user, event):
        row_frame = ctk.CTkFrame(self.scroll_results)
        row_frame.pack(fill="x", pady=2)

        chk_var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(row_frame, text="", variable=chk_var, width=50)
        chk.pack(side="left", padx=5)

        lbl_user = ctk.CTkLabel(row_frame, text=user, width=200, anchor="w")
        lbl_user.pack(side="left", padx=5)

        summary = event.get('summary', '(No Title)')
        lbl_summary = ctk.CTkLabel(row_frame, text=summary, width=250, anchor="w")
        lbl_summary.pack(side="left", padx=5)

        start = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown'))
        lbl_date = ctk.CTkLabel(row_frame, text=start, width=150, anchor="w")
        lbl_date.pack(side="left", padx=5)

        self.found_events.append({
            'user': user,
            'event': event,
            'var': chk_var,
            'widget': row_frame
        })

    def select_all(self):
        if not self.found_events:
            return
        # Toggle based on first item
        new_val = not self.found_events[0]['var'].get()
        for item in self.found_events:
            item['var'].set(new_val)

    def start_nuke(self):
        to_nuke = [item for item in self.found_events if item['var'].get()]
        if not to_nuke:
            messagebox.showinfo("Info", "No events selected.")
            return

        if not messagebox.askyesno("Confirm Nuke", f"Are you sure you want to delete {len(to_nuke)} events?"):
            return

        self.set_running(True)
        self.abort_event.clear()
        
        threading.Thread(target=self._nuke_thread, args=(to_nuke,), daemon=True).start()

    def _nuke_thread(self, to_nuke):
        total = len(to_nuke)
        success_count = 0
        processed_count = 0

        self.log(f"Nuking {total} events with 10 threads...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # We need to map future back to the specific item to update UI
            future_to_item = {}
            for item in to_nuke:
                user = item['user']
                event_id = item['event']['id']
                # Submit delete task
                future = executor.submit(self.mgr.delete_event, user, event_id)
                future_to_item[future] = item

            for future in concurrent.futures.as_completed(future_to_item):
                if self.abort_event.is_set():
                    self.log("Nuke Aborted.")
                    break

                item = future_to_item[future]
                processed_count += 1
                self.progress_bar.set(processed_count / total)
                
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                        self.after(0, lambda w=item['widget']: w.configure(fg_color="#442222"))
                    else:
                        self.after(0, lambda w=item['widget']: w.configure(fg_color="#444400"))
                except Exception as exc:
                     print(f'Delete generated an exception: {exc}')
                     self.after(0, lambda w=item['widget']: w.configure(fg_color="#444400"))

        self.progress_bar.set(1.0)
        self.log(f"Nuke Finished. Deleted {success_count}/{processed_count} processed.")
        self.after(0, lambda: self.set_running(False))
        self.after(0, lambda: messagebox.showinfo("Done", "Process finished."))

if __name__ == "__main__":
    app = CalendarNukeApp()
    app.mainloop()
