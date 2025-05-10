import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import calendar
import csv
import sv_ttk  # Sunvalley ttk theme for modern UI
import numpy as np  # Import numpy for numerical operations
from tkcalendar import DateEntry

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)
        
        self.config = {}
        
        # Apply saved theme or default to dark
        self.current_theme = self.config.get("theme", "dark")
        sv_ttk.set_theme(self.current_theme)
        
        # Configure colors
        self.colors = {
            "dark": {
                "bg": "#303030",
                "accent": "#8ab4f8",
                "text": "#ffffff",
                "success": "#81c995",
                "warning": "#fdd663",
                "error": "#f28b82",
                "card_bg": "#424242"
            },
            "light": {
                "bg": "#f5f5f5",
                "accent": "#1a73e8",
                "text": "#202124",
                "success": "#0f9d58",
                "warning": "#f29900",
                "error": "#d93025",
                "card_bg": "#ffffff"
            }
        }
        
        # Initialize expense data
        self.expenses = []
        self.filename = "expenses.json"
        self.load_data()
        
        # Define preset categories
        self.preset_categories = ["Food", "Utilities", "Transportation", "Healthcare", "Entertainment", "Savings", "Other"]
        
        # Create fonts
        self.heading_font = ("Segoe UI", 16, "bold")
        self.subheading_font = ("Segoe UI", 12, "bold")
        self.normal_font = ("Segoe UI", 10)
        
        # Main container with padding
        main_container = ttk.Frame(root, padding="20 20 20 20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo and title
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
         # Create a simple logo
        self.logo_canvas = tk.Canvas(header_frame, width=40, height=40, 
                               highlightthickness=0)
        self.logo_canvas.pack(side=tk.LEFT, padx=(0, 10))
        
        # App title
        title_label = ttk.Label(header_frame, text="Expense Tracker", 
                             font=("Segoe UI", 20, "bold"))
        title_label.pack(side=tk.LEFT)

        # Theme toggle button
        self.theme_icon_var = tk.StringVar(value="🌙" if self.current_theme == "light" else "☀️")
        theme_btn = ttk.Button(header_frame, textvariable=self.theme_icon_var,
                            width=3, command=self.toggle_theme)
        theme_btn.pack(side=tk.RIGHT)
        
        # Set up the main frame with a notebook (tabs)
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=('Segoe UI', 11))
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.setup_dashboard_tab()
        self.setup_expenses_tab()
        self.setup_reports_tab()
        
        # Create status bar
        status_frame = ttk.Frame(main_container)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, 
                            anchor=tk.W, padding=(5, 2))
        status_bar.pack(side=tk.LEFT, fill=tk.X)
        self.status_var.set(f"Loaded {len(self.expenses)} expenses")
        
        # Version info
        version_label = ttk.Label(status_frame, text="v2.5", anchor=tk.E)
        version_label.pack(side=tk.RIGHT)

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        # Switch theme
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        sv_ttk.set_theme(self.current_theme)
            
        # Update theme icon
        self.theme_icon_var.set("🌙" if self.current_theme == "light" else "☀️")
            
        # Update logo with new theme colors
        self.update_logo()
            
        # Save theme preference
        self.config["theme"] = self.current_theme
        self.save_config()
            
        # Update charts if they exist
        self.refresh_reports()
            
        # Update status
        self.status_var.set(f"Theme changed to {self.current_theme}")

    def update_logo(self):
        """Update the logo with current theme colors"""
        current_colors = self.colors[self.current_theme]
        
        # Clear canvas
        self.logo_canvas.delete("all")
        
        # Configure canvas background
        bg_color = current_colors["bg"]
        self.logo_canvas.configure(bg=bg_color)
        
        # Draw logo with theme colors
        self.logo_canvas.create_oval(5, 5, 35, 35, fill=current_colors["accent"], outline="")
        self.logo_canvas.create_text(20, 20, text="₱", fill=bg_color, 
                                font=("Arial", 20, "bold"))

    def setup_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Split into two columns
        left_frame = ttk.Frame(dashboard_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(dashboard_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Left column - Stats cards
        self.setup_summary_cards(left_frame)
        
        # Right column - Quick add
        quick_add_frame = ttk.LabelFrame(right_frame, text="Add New Expense", padding=15)
        quick_add_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Amount with ₱ prefix
        amount_frame = ttk.Frame(quick_add_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amount_frame, text="₱", font=self.normal_font).pack(side=tk.LEFT)
        self.quick_amount_entry = ttk.Entry(amount_frame, font=self.normal_font, width=15)
        self.quick_amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Category with dropdown - using preset categories
        ttk.Label(quick_add_frame, text="Category", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        self.quick_category_entry = ttk.Combobox(quick_add_frame, values=self.preset_categories, 
                                            font=self.normal_font)
        self.quick_category_entry.pack(fill=tk.X)
        
        # Description
        ttk.Label(quick_add_frame, text="Description", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        self.quick_desc_entry = ttk.Entry(quick_add_frame, font=self.normal_font)
        self.quick_desc_entry.pack(fill=tk.X)
        
        # Date with default today
        ttk.Label(quick_add_frame, text="Date", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        self.quick_date_entry = ttk.Entry(quick_add_frame, font=self.normal_font)
        self.quick_date_entry.pack(fill=tk.X)
        DateEntry(self.quick_date_entry, width=12, background='darkblue',       
                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd').pack(fill=tk.X) 
        self.quick_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        # Submit button with modern style
        submit_frame = ttk.Frame(quick_add_frame)
        submit_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Style the button
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        ttk.Button(submit_frame, text="Add Expense", command=self.quick_add_expense, 
               style="Accent.TButton").pack(side=tk.RIGHT)
        
        # Recent transactions
        ttk.Label(dashboard_frame, text="Recent Transactions", 
              font=self.subheading_font).pack(anchor=tk.W, pady=(20, 10))
        
        # Recent expenses in a modern table
        recent_frame = ttk.Frame(dashboard_frame)
        recent_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("date", "amount", "category", "description")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=6)
        self.recent_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Configure treeview style for modern look
        self.style.configure("Treeview", font=self.normal_font, rowheight=25)
        self.style.configure("Treeview.Heading", font=self.normal_font)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_tree.configure(yscroll=scrollbar.set)
        
        # Configure columns
        self.recent_tree.heading("date", text="Date")
        self.recent_tree.heading("amount", text="Amount")
        self.recent_tree.heading("category", text="Category")
        self.recent_tree.heading("description", text="Description")
        
        self.recent_tree.column("date", width=100)
        self.recent_tree.column("amount", width=100)
        self.recent_tree.column("category", width=150)
        self.recent_tree.column("description", width=300)
        
        # Update dashboard
        self.update_dashboard()

    def setup_summary_cards(self, parent_frame):
        # Card container with grid layout
        cards_frame = ttk.Frame(parent_frame)
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.rowconfigure(0, weight=1)
        cards_frame.rowconfigure(1, weight=1)
        
        # Card style
        self.style.configure("Card.TFrame", background=self.colors[self.current_theme]["card_bg"])
        
        # Total expenses card
        total_card = ttk.Frame(cards_frame, padding=15, style="Card.TFrame")
        total_card.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(total_card, text="TOTAL EXPENSES", font=self.normal_font).pack(anchor=tk.W)
        self.total_expenses_var = tk.StringVar()
        ttk.Label(total_card, textvariable=self.total_expenses_var, 
              font=("Segoe UI", 22, "bold")).pack(anchor=tk.W, pady=10)
        
        # Monthly expenses card
        monthly_card = ttk.Frame(cards_frame, padding=15, style="Card.TFrame")
        monthly_card.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(monthly_card, text="THIS MONTH", font=self.normal_font).pack(anchor=tk.W)
        self.month_expenses_var = tk.StringVar()
        ttk.Label(monthly_card, textvariable=self.month_expenses_var, 
              font=("Segoe UI", 22, "bold")).pack(anchor=tk.W, pady=10)
        
        # Average expense card
        avg_card = ttk.Frame(cards_frame, padding=15, style="Card.TFrame")
        avg_card.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(avg_card, text="AVERAGE EXPENSE", font=self.normal_font).pack(anchor=tk.W)
        self.avg_expense_var = tk.StringVar()
        ttk.Label(avg_card, textvariable=self.avg_expense_var, 
              font=("Segoe UI", 22, "bold")).pack(anchor=tk.W, pady=10)
        
        # Categories card
        categories_card = ttk.Frame(cards_frame, padding=15, style="Card.TFrame")
        categories_card.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        ttk.Label(categories_card, text="CATEGORIES", font=self.normal_font).pack(anchor=tk.W)
        self.category_count_var = tk.StringVar()
        ttk.Label(categories_card, textvariable=self.category_count_var, 
              font=("Segoe UI", 22, "bold")).pack(anchor=tk.W, pady=10)

    def setup_expenses_tab(self):
        expenses_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(expenses_frame, text="Expenses")
        
        # Search and actions bar
        actions_frame = ttk.Frame(expenses_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Search box with icon
        search_container = ttk.Frame(actions_frame)
        search_container.pack(side=tk.LEFT)
        
        ttk.Label(search_container, text="🔍").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_container, width=25, font=self.normal_font)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<KeyRelease>", self.search_expenses)
        self.search_entry.insert(0, "Search expenses...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) 
                                           if self.search_entry.get() == "Search expenses..." else None)
        self.search_entry.bind("<FocusOut>", lambda e: self.search_entry.insert(0, "Search expenses...") 
                                            if self.search_entry.get() == "" else None)
        
        # Category filter dropdown
        filter_container = ttk.Frame(actions_frame)
        filter_container.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(filter_container, text="Filter by:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_filter = ttk.Combobox(filter_container, width=15, font=self.normal_font, 
                                        values=["All Categories"] + self.preset_categories)
        self.category_filter.pack(side=tk.LEFT)
        self.category_filter.current(0)  # Default to "All Categories"
        self.category_filter.bind("<<ComboboxSelected>>", self.filter_expenses)
        
        # Action buttons
        ttk.Button(actions_frame, text="+ Add New", command=self.show_add_expense_dialog, 
               style="Accent.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(actions_frame, text="Export CSV", 
               command=self.export_to_csv).pack(side=tk.RIGHT, padx=5)
        
        # Expense list with modern table
        list_frame = ttk.Frame(expenses_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview for expenses
        columns = ("id", "date", "amount", "category", "description")
        self.expense_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.expense_tree.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.expense_tree.xview)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.expense_tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)
        self.expense_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure columns
        self.expense_tree.heading("id", text="ID")
        self.expense_tree.heading("date", text="Date")
        self.expense_tree.heading("amount", text="Amount")
        self.expense_tree.heading("category", text="Category")
        self.expense_tree.heading("description", text="Description")
        
        self.expense_tree.column("id", width=50, anchor=tk.CENTER)
        self.expense_tree.column("date", width=100)
        self.expense_tree.column("amount", width=100, anchor=tk.E)
        self.expense_tree.column("category", width=150)
        self.expense_tree.column("description", width=300)
        
        # Bind double-click to edit
        self.expense_tree.bind("<Double-1>", lambda event: self.edit_expense())
        
        # Context menu
        self.setup_context_menu()
        
        # Load expenses into the tree
        self.load_expenses()

    def filter_expenses(self, event=None):
        """Filter expenses by selected category"""
        selected_category = self.category_filter.get()
        search_text = self.search_entry.get().lower()
        if search_text == "search expenses...":
            search_text = ""
            
        # Clear the existing items
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
            
        # Add matching expenses to the tree
        for expense in sorted(self.expenses, key=lambda x: x["date"], reverse=True):
            # Check if expense matches the category filter (if selected)
            category_match = (selected_category == "All Categories" or expense["category"] == selected_category)
            
            # Check if expense matches the search text
            search_match = (not search_text or
                      search_text in str(expense["amount"]).lower() or
                      search_text in expense["category"].lower() or
                      search_text in expense["description"].lower() or
                      search_text in expense["date"].lower())
            
            # Add expense to tree if both category and search criteria match
            if category_match and search_match:
                self.expense_tree.insert("", tk.END, values=(
                    expense["id"],
                    expense["date"],
                    f"₱{expense['amount']:.2f}",
                    expense["category"],
                    expense["description"]
                ))

    def setup_context_menu(self):
        """Setup right-click context menu for expense tree"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self.edit_expense)
        self.context_menu.add_command(label="Delete", command=self.delete_expense)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="View Details", command=self.view_expense_details)
        
        self.expense_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu on right click"""
        # Select row under mouse
        iid = self.expense_tree.identify_row(event.y)
        if iid:
            self.expense_tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    def setup_reports_tab(self):
        reports_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(reports_frame, text="Reports")
        
        # Top section for report options
        options_frame = ttk.Frame(reports_frame)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left side: Report type selection
        report_selector_frame = ttk.LabelFrame(options_frame, text="Report Type", padding=10)
        report_selector_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.report_type = tk.StringVar(value="category")
        ttk.Radiobutton(report_selector_frame, text="Category Breakdown", 
                     variable=self.report_type, value="category", 
                     command=self.refresh_reports).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(report_selector_frame, text="Monthly Summary", 
                     variable=self.report_type, value="monthly", 
                     command=self.refresh_reports).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(report_selector_frame, text="Trend Analysis", 
                     variable=self.report_type, value="trend", 
                     command=self.refresh_reports).pack(anchor=tk.W, pady=2)
        
        # Right side: Date range selection
        date_frame = ttk.LabelFrame(options_frame, text="Date Range", padding=10)
        date_frame.pack(side=tk.RIGHT)
        
        # Calculate default date range (current month)
        today = datetime.datetime.now()
        first_day = today.replace(day=1).strftime("%Y-%m-%d")
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime("%Y-%m-%d")
        
        # From date
        from_frame = ttk.Frame(date_frame)
        from_frame.pack(fill=tk.X, pady=5)
        ttk.Label(from_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        self.from_date_entry = ttk.Entry(from_frame, width=12)
        self.from_date_entry.pack(side=tk.LEFT)
        self.from_date_entry.insert(0, first_day)
        
        # To date
        to_frame = ttk.Frame(date_frame)
        to_frame.pack(fill=tk.X, pady=5)
        ttk.Label(to_frame, text="To:").pack(side=tk.LEFT, padx=(0, 5))
        self.to_date_entry = ttk.Entry(to_frame, width=12)
        self.to_date_entry.pack(side=tk.LEFT)
        self.to_date_entry.insert(0, last_day)
        
        # Apply button
        ttk.Button(date_frame, text="Apply", command=self.refresh_reports, 
               style="Accent.TButton").pack(pady=(10, 0))
        
        # Frame for displaying charts
        self.chart_frame = ttk.Frame(reports_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initial report
        self.current_chart = None
        self.show_category_report()

    def show_add_expense_dialog(self):
        """Show a dialog to add a new expense"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Expense")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Add padding around the dialog content
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(content_frame, text="Add New Expense", 
              font=self.heading_font).pack(anchor=tk.W, pady=(0, 15))
        
        # Form fields
        # Amount field with ₱ prefix
        amount_frame = ttk.Frame(content_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amount_frame, text="₱", font=self.normal_font).pack(side=tk.LEFT)
        amount_entry = ttk.Entry(amount_frame, font=self.normal_font)
        amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        amount_entry.focus_set()  # Set focus to amount field
        
        # Category dropdown using preset categories
        ttk.Label(content_frame, text="Category", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        category_entry = ttk.Combobox(content_frame, values=self.preset_categories, font=self.normal_font)
        category_entry.pack(fill=tk.X)
        
        # Description
        ttk.Label(content_frame, text="Description", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        desc_entry = ttk.Entry(content_frame, font=self.normal_font)
        desc_entry.pack(fill=tk.X)
        
        # Date with default today
        ttk.Label(content_frame, text="Date", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        date_entry = ttk.Entry(content_frame, font=self.normal_font)
        date_entry.pack(fill=tk.X)
        date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        # Button frame
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_expense():
            try:
                amount = float(amount_entry.get())
                category = category_entry.get()
                description = desc_entry.get()
                date_str = date_entry.get()
                
                # Validate input
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                    
                if not category:
                    messagebox.showerror("Error", "Category is required")
                    return
                    
                try:
                    # Validate date format
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                    return
                    
                self.add_expense_data(amount, category, description, date_str)
                
                # Update UI
                self.load_expenses()
                self.update_dashboard()
                self.refresh_reports()
                
                self.status_var.set(f"Expense added: ₱{amount:.2f} for {description}")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
        
        ttk.Button(button_frame, text="Cancel", 
               command=dialog.destroy).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save", 
               command=save_expense, style="Accent.TButton").pack(side=tk.RIGHT)
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def view_expense_details(self):
        """Show detailed view of the selected expense"""
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select an expense to view")
            return
            
        # Get the ID of the selected expense
        expense_id = int(self.expense_tree.item(selected_item[0], "values")[0])
        
        # Find the expense
        for expense in self.expenses:
            if expense["id"] == expense_id:
                # Create a details dialog
                dialog = tk.Toplevel(self.root)
                dialog.title("Expense Details")
                dialog.geometry("400x300")
                dialog.transient(self.root)
                dialog.grab_set()
                
                # Add padding around the dialog content
                content_frame = ttk.Frame(dialog, padding=20)
                content_frame.pack(fill=tk.BOTH, expand=True)
                
                # Details
                ttk.Label(content_frame, text="Expense Details", 
                      font=self.heading_font).pack(anchor=tk.W, pady=(0, 15))
                
                # Display all details
                details_frame = ttk.Frame(content_frame)
                details_frame.pack(fill=tk.BOTH, expand=True)
                
                row = 0
                for field, value in [
                    ("ID", expense["id"]),
                    ("Date", expense["date"]),
                    ("Amount", f"₱{expense['amount']:.2f}"),
                    ("Category", expense["category"]),
                    ("Description", expense["description"])
                ]:
                    ttk.Label(details_frame, text=field, font=(self.normal_font[0], self.normal_font[1], "bold")).grid(
                        row=row, column=0, sticky=tk.W, pady=5)
                    ttk.Label(details_frame, text=str(value), font=self.normal_font).grid(
                        row=row, column=1, sticky=tk.W, padx=15, pady=5)
                    row += 1
                
                # Action buttons
                button_frame = ttk.Frame(content_frame)
                button_frame.pack(fill=tk.X, pady=(20, 0))
                
                ttk.Button(button_frame, text="Close", 
                       command=dialog.destroy).pack(side=tk.RIGHT)
                ttk.Button(button_frame, text="Edit", 
                       command=lambda: [dialog.destroy(), self.edit_expense()]).pack(side=tk.RIGHT, padx=5)
                
                # Center the dialog
                dialog.update_idletasks()
                width = dialog.winfo_width()
                height = dialog.winfo_height()
                x = (dialog.winfo_screenwidth() // 2) - (width // 2)
                y = (dialog.winfo_screenheight() // 2) - (height // 2)
                dialog.geometry(f'{width}x{height}+{x}+{y}')
                
                break

    def quick_add_expense(self):
        try:
            amount = float(self.quick_amount_entry.get())
            category = self.quick_category_entry.get()
            description = self.quick_desc_entry.get()
            date_str = self.quick_date_entry.get()
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
                
            if not category:
                messagebox.showerror("Error", "Category is required")
                return
            
            try:
                # Validate date format
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                return
            # Add the expense
            self.add_expense_data(amount, category, description, date_str)
            
            # Reset form fields
            self.quick_amount_entry.delete(0, tk.END)
            self.quick_desc_entry.delete(0, tk.END)
            self.quick_date_entry.delete(0, tk.END)
            self.quick_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
            
            # Update UI
            self.load_expenses()
            self.update_dashboard()
            self.refresh_reports()
            
            self.status_var.set(f"Expense added: ₱{amount:.2f} for {description}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")

    def edit_expense(self):
        """Edit the selected expense"""
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select an expense to edit")
            return
            
        # Get the selected expense ID
        expense_id = int(self.expense_tree.item(selected_item[0], "values")[0])
        
        # Find the expense
        selected_expense = None
        for expense in self.expenses:
            if expense["id"] == expense_id:
                selected_expense = expense
                break
                
        if not selected_expense:
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Expense")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Add padding around the dialog content
        content_frame = ttk.Frame(dialog, padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(content_frame, text="Edit Expense", 
              font=self.heading_font).pack(anchor=tk.W, pady=(0, 15))
        
        # Form fields
        # Amount field with ₱ prefix
        amount_frame = ttk.Frame(content_frame)
        amount_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amount_frame, text="₱", font=self.normal_font).pack(side=tk.LEFT)
        amount_entry = ttk.Entry(amount_frame, font=self.normal_font)
        amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        amount_entry.insert(0, str(selected_expense["amount"]))
        
        # Category dropdown
        ttk.Label(content_frame, text="Category", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        category_entry = ttk.Combobox(content_frame, values=self.preset_categories, font=self.normal_font)
        category_entry.pack(fill=tk.X)
        category_entry.set(selected_expense["category"])
        
        # Description
        ttk.Label(content_frame, text="Description", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        desc_entry = ttk.Entry(content_frame, font=self.normal_font)
        desc_entry.pack(fill=tk.X)
        desc_entry.insert(0, selected_expense["description"])
        
        # Date
        ttk.Label(content_frame, text="Date", font=self.normal_font).pack(anchor=tk.W, pady=(10, 5))
        date_entry = ttk.Entry(content_frame, font=self.normal_font)
        date_entry.pack(fill=tk.X)
        date_entry.insert(0, selected_expense["date"])
        
        # Button frame
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_edited_expense():
            try:
                amount = float(amount_entry.get())
                category = category_entry.get()
                description = desc_entry.get()
                date_str = date_entry.get()
                
                # Validate input
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                    
                if not category:
                    messagebox.showerror("Error", "Category is required")
                    return
                    
                try:
                    # Validate date format
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                    return
                
                # Update expense
                selected_expense["amount"] = amount
                selected_expense["category"] = category
                selected_expense["description"] = description
                selected_expense["date"] = date_str
                
                # Save changes
                self.save_data()
                
                # Update UI
                self.load_expenses()
                self.update_dashboard()
                self.refresh_reports()
                
                self.status_var.set(f"Expense updated: ₱{amount:.2f} for {description}")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid amount")
        
        ttk.Button(button_frame, text="Cancel", 
               command=dialog.destroy).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Save", 
               command=save_edited_expense, style="Accent.TButton").pack(side=tk.RIGHT)
        
        # Center the dialog
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

    def delete_expense(self):
        """Delete the selected expense"""
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Please select an expense to delete")
            return
        
        # Get selected expense ID
        expense_id = int(self.expense_tree.item(selected_item[0], "values")[0])
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?")
        if not confirm:
            return
            
        # Find and remove the expense
        for i, expense in enumerate(self.expenses):
            if expense["id"] == expense_id:
                description = expense["description"]
                amount = expense["amount"]
                self.expenses.pop(i)
                break
                
        # Save changes
        self.save_data()
        
        # Update UI
        self.load_expenses()
        self.update_dashboard()
        self.refresh_reports()
        
        self.status_var.set(f"Expense deleted: ₱{amount:.2f} for {description}")

    def search_expenses(self, event=None):
        """Search expenses by text input"""
        self.filter_expenses()

    def add_expense_data(self, amount, category, description, date_str):
        """Add a new expense to the data"""
        # Generate new ID
        new_id = 1
        if self.expenses:
            new_id = max(expense["id"] for expense in self.expenses) + 1
            
        # Create expense object
        expense = {
            "id": new_id,
            "amount": amount,
            "category": category,
            "description": description,
            "date": date_str
        }
        
        # Add to expenses list
        self.expenses.append(expense)
        
        # Save to file
        self.save_data()

    def load_data(self):
        """Load expense data from file"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, "r") as file:
                    self.expenses = json.load(file)
            else:
                self.expenses = []
        except (json.JSONDecodeError, IOError):
            messagebox.showerror("Error", "Failed to load expense data")
            self.expenses = []

    def save_data(self):
        """Save expense data to file"""
        try:
            with open(self.filename, "w") as file:
                json.dump(self.expenses, file, indent=2)
        except IOError:
            messagebox.showerror("Error", "Failed to save expense data")

    def load_expenses(self):
        """Load expenses into the expense tree"""
        # Clear existing items
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
            
        # Load expenses sorted by date (newest first)
        for expense in sorted(self.expenses, key=lambda x: x["date"], reverse=True):
            self.expense_tree.insert("", tk.END, values=(
                expense["id"],
                expense["date"],
                f"₱{expense['amount']:.2f}",
                expense["category"],
                expense["description"]
            ))
        
        # Update category filter
        categories = set(expense["category"] for expense in self.expenses)
        self.category_filter["values"] = ["All Categories"] + sorted(list(categories))

    def update_dashboard(self):
        """Update dashboard UI elements"""
        # Calculate stats
        total_expenses = sum(expense["amount"] for expense in self.expenses)
        
        # Monthly expenses
        current_month = datetime.datetime.now().strftime("%Y-%m")
        monthly_expenses = sum(expense["amount"] for expense in self.expenses 
                          if expense["date"].startswith(current_month))
        
        # Average expense
        avg_expense = 0
        if self.expenses:
            avg_expense = total_expenses / len(self.expenses)
        
        # Categories count
        categories = set(expense["category"] for expense in self.expenses)
        
        # Update UI
        self.total_expenses_var.set(f"₱{total_expenses:.2f}")
        self.month_expenses_var.set(f"₱{monthly_expenses:.2f}")
        self.avg_expense_var.set(f"₱{avg_expense:.2f}")
        self.category_count_var.set(f"{len(categories)}")
        
        # Update recent transactions
        self.update_recent_transactions()

    def update_recent_transactions(self):
        """Update recent transactions in dashboard"""
        # Clear existing items
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
            
        # Add 5 most recent transactions
        recent = sorted(self.expenses, key=lambda x: x["date"], reverse=True)[:5]
        
        for expense in recent:
            self.recent_tree.insert("", tk.END, values=(
                expense["date"],
                f"₱{expense['amount']:.2f}",
                expense["category"],
                expense["description"]
            ))

    def refresh_reports(self, event=None):
        """Refresh the reports based on selected options"""
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        # Get report type
        report_type = self.report_type.get()
        
        if report_type == "category":
            self.show_category_report()
        elif report_type == "monthly":
            self.show_monthly_report()
        elif report_type == "trend":
            self.show_trend_report()

    def show_category_report(self):
        """Show category breakdown report"""
        try:
            # Get date range
            from_date = self.from_date_entry.get()
            to_date = self.to_date_entry.get()
            
            # Filter expenses by date range
            filtered_expenses = [expense for expense in self.expenses
                            if from_date <= expense["date"] <= to_date]
            
            if not filtered_expenses:
                ttk.Label(self.chart_frame, text="No data available for selected date range",
                      font=self.normal_font).pack(expand=True)
                return
                
            # Calculate category totals
            category_totals = defaultdict(float)
            for expense in filtered_expenses:
                category_totals[expense["category"]] += expense["amount"]
                
            # Sort categories by total amount
            sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            
            # Create figure and axis
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
            fig.tight_layout(pad=3.0)
            
            # Pie chart
            labels = [f"{cat} (₱{amt:.2f})" for cat, amt in sorted_categories]
            sizes = [amt for _, amt in sorted_categories]
            
            # Use a colorful color map
            cmap = plt.cm.viridis
            colors = cmap(np.linspace(0, 1, len(labels)))
            
            wedges, texts, autotexts = ax1.pie(sizes, labels=None, autopct='%1.1f%%', 
                                           startangle=90, colors=colors)
            
            # Customize pie chart
            ax1.set_title('Expense Distribution by Category')
            ax1.axis('equal')  # Equal aspect ratio ensures pie is circular
            
            # Add legend
            ax1.legend(wedges, labels, title="Categories", 
                    loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            # Bar chart
            categories = [cat for cat, _ in sorted_categories]
            amounts = [amt for _, amt in sorted_categories]
            
            # Create horizontal bar chart
            bars = ax2.barh(categories, amounts, color=colors)
            ax2.set_title('Category Expenses')
            ax2.set_xlabel('Amount (₱)')
            
            # Add amount labels to bars
            for bar in bars:
                width = bar.get_width()
                ax2.text(width + 0.3, bar.get_y() + bar.get_height()/2, 
                      f'₱{width:.2f}', ha='left', va='center')
            
            # Create canvas to display the figure
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add a summary text below
            total = sum(amounts)
            summary = f"Total expenses: ₱{total:.2f} from {from_date} to {to_date}"
            ttk.Label(self.chart_frame, text=summary, font=self.normal_font).pack(pady=10)
            
        except Exception as e:
            ttk.Label(self.chart_frame, text=f"Error generating report: {str(e)}",
                  font=self.normal_font).pack(expand=True)

    def show_monthly_report(self):
        """Show monthly summary report"""
        try:
            # Get date range
            from_date = self.from_date_entry.get()
            to_date = self.to_date_entry.get()
            
            # Parse dates to get year and month
            start_date = datetime.datetime.strptime(from_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d")
            
            # Filter expenses by date range
            filtered_expenses = [expense for expense in self.expenses
                            if from_date <= expense["date"] <= to_date]
            
            if not filtered_expenses:
                ttk.Label(self.chart_frame, text="No data available for selected date range",
                      font=self.normal_font).pack(expand=True)
                return
                
            # Group expenses by month
            monthly_totals = defaultdict(float)
            for expense in filtered_expenses:
                date = datetime.datetime.strptime(expense["date"], "%Y-%m-%d")
                month_key = date.strftime("%Y-%m")
                monthly_totals[month_key] += expense["amount"]
                
            # Sort months chronologically
            sorted_months = sorted(monthly_totals.items())
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # Format month labels nicely (e.g., "Jan 2023")
            month_labels = []
            for month_key, _ in sorted_months:
                year, month = month_key.split("-")
                month_name = datetime.datetime(int(year), int(month), 1).strftime("%b %Y")
                month_labels.append(month_name)
                
            amounts = [amt for _, amt in sorted_months]
            
            # Create bar chart
            bars = ax.bar(month_labels, amounts, color='skyblue')
            
            # Add data labels on top of bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                     f'₱{height:.2f}', ha='center', va='bottom')
            
            # Customize chart
            ax.set_title('Monthly Expense Summary')
            ax.set_xlabel('Month')
            ax.set_ylabel('Total Amount (₱)')
            plt.xticks(rotation=45)
            fig.tight_layout()
            
            # Create canvas to display the figure
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Add a summary text below
            avg_monthly = sum(amounts) / len(amounts)
            highest_month = max(sorted_months, key=lambda x: x[1])
            highest_month_name = datetime.datetime(
                int(highest_month[0].split("-")[0]), 
                int(highest_month[0].split("-")[1]), 1
            ).strftime("%B %Y")
            
            summary = (f"Average monthly expenses: ₱{avg_monthly:.2f}\n"
                    f"Highest spending month: {highest_month_name} (₱{highest_month[1]:.2f})")
            ttk.Label(self.chart_frame, text=summary, font=self.normal_font).pack(pady=10)
            
        except Exception as e:
            ttk.Label(self.chart_frame, text=f"Error generating report: {str(e)}",
                  font=self.normal_font).pack(expand=True)

    def show_trend_report(self):
        """Show expense trend analysis"""
        try:
            # Get date range
            from_date = self.from_date_entry.get()
            to_date = self.to_date_entry.get()
            
            # Filter expenses by date range
            filtered_expenses = [expense for expense in self.expenses
                            if from_date <= expense["date"] <= to_date]
            
            if not filtered_expenses:
                ttk.Label(self.chart_frame, text="No data available for selected date range",
                      font=self.normal_font).pack(expand=True)
                return
                
            # Sort expenses by date
            sorted_expenses = sorted(filtered_expenses, key=lambda x: x["date"])
            
            # Extract dates and cumulative amounts
            dates = []
            amounts = []
            cumulative = 0
            
            for expense in sorted_expenses:
                dates.append(datetime.datetime.strptime(expense["date"], "%Y-%m-%d"))
                cumulative += expense["amount"]
                amounts.append(cumulative)
                
            # Create figure and axes
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
            fig.tight_layout(pad=3.0)
            
            # Cumulative spending over time
            ax1.plot(dates, amounts, marker='o', linestyle='-', color='blue', 
                  linewidth=2, markersize=4)
            ax1.set_title('Cumulative Spending Over Time')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Cumulative Amount (₱)')
            ax1.grid(True, linestyle='--', alpha=0.7)
            
            # Format dates nicely
            fig.autofmt_xdate()
            
            # Individual expense amounts
            individual_amounts = [expense["amount"] for expense in sorted_expenses]
            ax2.bar(dates, individual_amounts, color='green', alpha=0.7)
            ax2.set_title('Individual Expense Amounts')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Amount (₱)')
            ax2.grid(True, linestyle='--', alpha=0.7)
            
            # Create canvas to display the figure
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Calculate statistics for summary
            total_spent = amounts[-1]
            avg_expense = total_spent / len(sorted_expenses)
            daily_avg = total_spent / ((dates[-1] - dates[0]).days + 1)
            
            # Add a summary text below
            summary = (f"Total spent: ₱{total_spent:.2f}\n"
                    f"Average expense: ₱{avg_expense:.2f}\n"
                    f"Daily average: ₱{daily_avg:.2f}")
            ttk.Label(self.chart_frame, text=summary, font=self.normal_font).pack(pady=10)
            
        except Exception as e:
            ttk.Label(self.chart_frame, text=f"Error generating report: {str(e)}",
                  font=self.normal_font).pack(expand=True)
    
    def export_to_csv(self):
        """Export expenses to CSV file"""
        try:
            # Ask for file location
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Expenses to CSV"
            )
            
            if not filename:  # User cancelled
                return
                
            # Write to CSV
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow(['ID', 'Date', 'Amount', 'Category', 'Description'])
                
                # Write data
                for expense in sorted(self.expenses, key=lambda x: x["date"], reverse=True):
                    writer.writerow([
                        expense["id"],
                        expense["date"],
                        expense["amount"],
                        expense["category"],
                        expense["description"]
                    ])
                    
            messagebox.showinfo("Export Successful", f"Expenses exported to {filename}")
            self.status_var.set(f"Exported {len(self.expenses)} expenses to CSV")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

def main():
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()