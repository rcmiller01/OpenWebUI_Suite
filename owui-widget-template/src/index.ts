/**
 * OpenWebUI Widget Template
 * 
 * This module exports functions for registering and managing
 * frontend widgets in the OpenWebUI extension system.
 */

export interface WidgetConfig {
  id: string;
  title: string;
  description?: string;
  version?: string;
  mount: (element: HTMLElement) => Promise<void> | void;
  unmount?: (element: HTMLElement) => Promise<void> | void;
  onResize?: (element: HTMLElement) => void;
}

export interface WidgetAPI {
  sendMessage: (message: any) => void;
  onMessage: (handler: (message: any) => void) => void;
  getConfig: () => Record<string, any>;
  setConfig: (config: Record<string, any>) => void;
}

/**
 * Register a widget with the OpenWebUI widget system
 */
export function registerWidget(): WidgetConfig {
  return {
    id: "template",
    title: "Template Widget",
    description: "A template widget for OpenWebUI extensions",
    version: "0.1.0",
    mount: async (element: HTMLElement) => {
      // Create the widget content
      const container = document.createElement("div");
      container.className = "owui-widget-template";
      container.style.cssText = `
        padding: 16px;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      `;
      
      // Header
      const header = document.createElement("h3");
      header.textContent = "Template Widget";
      header.style.cssText = `
        margin: 0 0 12px 0;
        color: #495057;
        font-size: 18px;
        font-weight: 600;
      `;
      
      // Content
      const content = document.createElement("div");
      content.innerHTML = `
        <p style="margin: 0 0 12px 0; color: #6c757d;">
          This is a template widget demonstrating the OpenWebUI widget system.
        </p>
        <div style="display: flex; gap: 8px; margin-bottom: 12px;">
          <button id="template-btn-1" style="
            padding: 6px 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
          ">Action 1</button>
          <button id="template-btn-2" style="
            padding: 6px 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
          ">Action 2</button>
        </div>
        <div id="template-output" style="
          padding: 8px;
          background: #e9ecef;
          border-radius: 4px;
          font-family: monospace;
          font-size: 12px;
          color: #495057;
        ">Ready</div>
      `;
      
      // Assemble the widget
      container.appendChild(header);
      container.appendChild(content);
      element.appendChild(container);
      
      // Add event handlers
      const btn1 = container.querySelector("#template-btn-1") as HTMLButtonElement;
      const btn2 = container.querySelector("#template-btn-2") as HTMLButtonElement;
      const output = container.querySelector("#template-output") as HTMLDivElement;
      
      btn1?.addEventListener("click", () => {
        output.textContent = `Action 1 triggered at ${new Date().toLocaleTimeString()}`;
      });
      
      btn2?.addEventListener("click", () => {
        output.textContent = `Action 2 triggered at ${new Date().toLocaleTimeString()}`;
      });
      
      // Simulate some initialization
      setTimeout(() => {
        output.textContent = "Widget initialized successfully";
      }, 1000);
    },
    
    unmount: async (element: HTMLElement) => {
      // Clean up the widget
      element.innerHTML = "";
    },
    
    onResize: (element: HTMLElement) => {
      // Handle resize events if needed
      console.log("Widget resized:", element.offsetWidth, element.offsetHeight);
    }
  };
}

/**
 * Create a widget API for communication with the host application
 */
export function createWidgetAPI(): WidgetAPI {
  const messageHandlers: Array<(message: any) => void> = [];
  let config: Record<string, any> = {};
  
  return {
    sendMessage: (message: any) => {
      // Send message to host application
      window.postMessage({
        type: "owui-widget-message",
        source: "template",
        data: message
      }, "*");
    },
    
    onMessage: (handler: (message: any) => void) => {
      messageHandlers.push(handler);
      
      // Listen for messages from host
      const listener = (event: MessageEvent) => {
        if (event.data.type === "owui-host-message" && event.data.target === "template") {
          handler(event.data.data);
        }
      };
      
      window.addEventListener("message", listener);
      
      // Return cleanup function
      return () => {
        window.removeEventListener("message", listener);
        const index = messageHandlers.indexOf(handler);
        if (index > -1) {
          messageHandlers.splice(index, 1);
        }
      };
    },
    
    getConfig: () => ({ ...config }),
    
    setConfig: (newConfig: Record<string, any>) => {
      config = { ...config, ...newConfig };
    }
  };
}

// Export the widget registration function as default
export default registerWidget;
