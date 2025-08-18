import tkinter as tk

class Tooltip:
    """
    Creates a tooltip for a given widget.
    
    Parameters:
        widget: The widget to add the tooltip to
        text: The text to display in the tooltip
        delay: Delay in milliseconds before the tooltip appears (default: 500ms)
        wraplength: Maximum width of tooltip text (default: 180 pixels)
        background: Background color of the tooltip (default: light yellow)
        foreground: Text color of the tooltip (default: black)
    """
    def __init__(self, widget, text='widget info', delay=500, wraplength=180,
                 background='#FFFFEA', foreground='black'):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.background = background
        self.foreground = foreground
        
        # Store original widget event bindings
        self.widget_bind_enter = widget.bind("<Enter>", self.on_enter)
        self.widget_bind_leave = widget.bind("<Leave>", self.on_leave)
        self.widget_bind_button = widget.bind("<ButtonPress>", self.on_leave)
        
        # Variables to track tooltip state
        self.tooltip_window = None
        self.schedule_id = None
    
    def on_enter(self, event=None):
        """Schedule the tooltip to appear after the delay"""
        self.schedule_id = self.widget.after(self.delay, self.show_tooltip)
    
    def on_leave(self, event=None):
        """Cancel scheduled tooltip and hide if showing"""
        if self.schedule_id:
            self.widget.after_cancel(self.schedule_id)
            self.schedule_id = None
        self.hide_tooltip()
    
    def show_tooltip(self):
        """Display the tooltip"""
        # Get absolute coordinates of the widget
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # Create a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        # Remove window decorations
        self.tooltip_window.wm_overrideredirect(True)
        # Position the tooltip
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create a label for the tooltip text
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                          background=self.background, foreground=self.foreground,
                          relief='solid', borderwidth=1, wraplength=self.wraplength)
        label.pack(ipadx=1)
    
    def hide_tooltip(self):
        """Hide the tooltip if it exists"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None