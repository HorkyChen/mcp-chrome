"""
Tool schemas and definitions for Chrome MCP server
"""

# Tool names
class ToolNames:
    GET_WINDOWS_AND_TABS = 'get_windows_and_tabs'
    SEARCH_TABS_CONTENT = 'search_tabs_content'
    NAVIGATE = 'chrome_navigate'
    SCREENSHOT = 'chrome_screenshot'
    CLOSE_TABS = 'chrome_close_tabs'
    GO_BACK_OR_FORWARD = 'chrome_go_back_or_forward'
    WEB_FETCHER = 'chrome_get_web_content'
    CLICK = 'chrome_click_element'
    FILL = 'chrome_fill_or_select'
    GET_INTERACTIVE_ELEMENTS = 'chrome_get_interactive_elements'
    NETWORK_CAPTURE_START = 'chrome_network_capture_start'
    NETWORK_CAPTURE_STOP = 'chrome_network_capture_stop'
    NETWORK_REQUEST = 'chrome_network_request'
    NETWORK_DEBUGGER_START = 'chrome_network_debugger_start'
    NETWORK_DEBUGGER_STOP = 'chrome_network_debugger_stop'
    KEYBOARD = 'chrome_keyboard'
    HISTORY = 'chrome_history'
    BOOKMARK_SEARCH = 'chrome_bookmark_search'
    BOOKMARK_ADD = 'chrome_bookmark_add'
    BOOKMARK_DELETE = 'chrome_bookmark_delete'
    INJECT_SCRIPT = 'chrome_inject_script'
    SEND_COMMAND_TO_INJECT_SCRIPT = 'chrome_send_command_to_inject_script'
    CONSOLE = 'chrome_console'


# Tool schemas - simplified for Python implementation
TOOL_SCHEMAS = [
    {
        "name": ToolNames.GET_WINDOWS_AND_TABS,
        "description": "Get all currently open browser windows and tabs",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": ToolNames.NAVIGATE,
        "description": "Navigate to a URL or refresh the current tab",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to the website specified"},
                "newWindow": {"type": "boolean", "description": "Create a new window to navigate to the URL or not. Defaults to false"},
                "width": {"type": "number", "description": "Viewport width in pixels (default: 1280)"},
                "height": {"type": "number", "description": "Viewport height in pixels (default: 720)"},
                "refresh": {"type": "boolean", "description": "Refresh the current active tab instead of navigating to a URL. When true, the url parameter is ignored. Defaults to false"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.SCREENSHOT,
        "description": "Take a screenshot of the current page or a specific element",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name for the screenshot, if saving as PNG"},
                "selector": {"type": "string", "description": "CSS selector for element to screenshot"},
                "width": {"type": "number", "description": "Width in pixels (default: 800)"},
                "height": {"type": "number", "description": "Height in pixels (default: 600)"},
                "storeBase64": {"type": "boolean", "description": "return screenshot in base64 format (default: false)"},
                "fullPage": {"type": "boolean", "description": "Store screenshot of the entire page (default: true)"},
                "savePng": {"type": "boolean", "description": "Save screenshot as PNG file (default: true)"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.WEB_FETCHER,
        "description": "Fetch content from a web page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch content from. If not provided, uses the current active tab"},
                "htmlContent": {"type": "boolean", "description": "Get the visible HTML content of the page. If true, textContent will be ignored (default: false)"},
                "textContent": {"type": "boolean", "description": "Get the visible text content of the page with metadata. Ignored if htmlContent is true (default: true)"},
                "selector": {"type": "string", "description": "CSS selector to get content from a specific element. If provided, only content from this element will be returned"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.CLICK,
        "description": "Click on an element in the current page or at specific coordinates",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for the element to click"},
                "coordinates": {
                    "type": "object",
                    "description": "Coordinates to click at (relative to viewport)",
                    "properties": {
                        "x": {"type": "number", "description": "X coordinate relative to the viewport"},
                        "y": {"type": "number", "description": "Y coordinate relative to the viewport"}
                    },
                    "required": ["x", "y"]
                },
                "waitForNavigation": {"type": "boolean", "description": "Wait for page navigation to complete after click (default: false)"},
                "timeout": {"type": "number", "description": "Timeout in milliseconds for waiting for the element or navigation (default: 5000)"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.FILL,
        "description": "Fill a form element or select an option with the specified value",
        "inputSchema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for the input element to fill or select"},
                "value": {"type": "string", "description": "Value to fill or select into the element"}
            },
            "required": ["selector", "value"]
        }
    },
    {
        "name": ToolNames.NETWORK_REQUEST,
        "description": "Send a network request from the browser with cookies and other browser context",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to send the request to"},
                "method": {"type": "string", "description": "HTTP method to use (default: GET)"},
                "headers": {"type": "object", "description": "Headers to include in the request"},
                "body": {"type": "string", "description": "Body of the request (for POST, PUT, etc.)"},
                "timeout": {"type": "number", "description": "Timeout in milliseconds (default: 30000)"}
            },
            "required": ["url"]
        }
    },
    {
        "name": ToolNames.KEYBOARD,
        "description": "Simulate keyboard events in the browser",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keys": {"type": "string", "description": "Keys to simulate (e.g., 'Enter', 'Ctrl+C', 'A,B,C' for sequence)"},
                "selector": {"type": "string", "description": "CSS selector for the element to send keyboard events to"},
                "delay": {"type": "number", "description": "Delay between key sequences in milliseconds (optional, default: 0)"}
            },
            "required": ["keys"]
        }
    },
    {
        "name": ToolNames.HISTORY,
        "description": "Retrieve and search browsing history from Chrome",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to search for in history URLs and titles"},
                "startTime": {"type": "string", "description": "Start time as a date string"},
                "endTime": {"type": "string", "description": "End time as a date string"},
                "maxResults": {"type": "number", "description": "Maximum number of history entries to return (default: 100)"},
                "excludeCurrentTabs": {"type": "boolean", "description": "Filter out URLs that are currently open in any browser tab (default: false)"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.BOOKMARK_SEARCH,
        "description": "Search Chrome bookmarks by title and URL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query to match against bookmark titles and URLs"},
                "maxResults": {"type": "number", "description": "Maximum number of bookmarks to return (default: 50)"},
                "folderPath": {"type": "string", "description": "Optional folder path or ID to limit search to a specific bookmark folder"}
            },
            "required": []
        }
    },
    {
        "name": ToolNames.SEARCH_TABS_CONTENT,
        "description": "search for related content from the currently open tab and return the corresponding web pages",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "the query to search for related content"}
            },
            "required": ["query"]
        }
    },
    {
        "name": ToolNames.INJECT_SCRIPT,
        "description": "inject the user-specified content script into the webpage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "If a URL is specified, inject the script into the webpage corresponding to the URL"},
                "type": {"type": "string", "description": "the javaScript world for a script to execute within. must be ISOLATED or MAIN"},
                "jsScript": {"type": "string", "description": "the content script to inject"}
            },
            "required": ["type", "jsScript"]
        }
    },
    {
        "name": ToolNames.CONSOLE,
        "description": "Capture and retrieve all console output from the current active browser tab/page",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to and capture console from"},
                "includeExceptions": {"type": "boolean", "description": "Include uncaught exceptions in the output (default: true)"},
                "maxMessages": {"type": "number", "description": "Maximum number of console messages to capture (default: 100)"}
            },
            "required": []
        }
    }
]
