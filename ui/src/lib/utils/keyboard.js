/**
 * Global keyboard shortcuts manager
 */

export class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  /**
   * Register a keyboard shortcut
   * @param {string} key - The key to listen for (e.g., 'Escape', 'Enter', 'k')
   * @param {function} handler - The handler function to call
   * @param {object} options - Options like ctrlKey, metaKey, shiftKey, altKey
   */
  register(key, handler, options = {}) {
    const shortcutKey = this.getShortcutKey(key, options);
    this.shortcuts.set(shortcutKey, handler);
  }

  /**
   * Unregister a keyboard shortcut
   */
  unregister(key, options = {}) {
    const shortcutKey = this.getShortcutKey(key, options);
    this.shortcuts.delete(shortcutKey);
  }

  /**
   * Start listening for keyboard events
   */
  start() {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', this.handleKeyDown);
    }
  }

  /**
   * Stop listening for keyboard events
   */
  stop() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', this.handleKeyDown);
    }
  }

  /**
   * Handle keydown events
   */
  handleKeyDown(event) {
    // Ignore if user is typing in an input/textarea
    const target = event.target;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable
    ) {
      // Allow Escape in inputs/textareas
      if (event.key !== 'Escape') {
        return;
      }
    }

    const shortcutKey = this.getShortcutKey(event.key, {
      ctrlKey: event.ctrlKey,
      metaKey: event.metaKey,
      shiftKey: event.shiftKey,
      altKey: event.altKey
    });

    const handler = this.shortcuts.get(shortcutKey);
    if (handler) {
      event.preventDefault();
      handler(event);
    }
  }

  /**
   * Generate a unique key for the shortcut
   */
  getShortcutKey(key, options = {}) {
    const parts = [];
    if (options.ctrlKey) parts.push('ctrl');
    if (options.metaKey) parts.push('meta');
    if (options.shiftKey) parts.push('shift');
    if (options.altKey) parts.push('alt');
    parts.push(key.toLowerCase());
    return parts.join('+');
  }
}

// Singleton instance
export const keyboardShortcuts = new KeyboardShortcuts();
