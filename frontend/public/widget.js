(function() {
  // Prevent duplicate script injection
  if (document.getElementById('whmcs-ai-assistant-widget')) return;

  var container = document.createElement('div');
  container.id = 'whmcs-ai-assistant-widget';
  container.style.position = 'fixed';
  container.style.bottom = '20px';
  container.style.right = '20px';
  container.style.zIndex = '999999';
  container.style.display = 'block';

  var iframe = document.createElement('iframe');
  iframe.src = 'http://localhost:3000/chat-embed';
  iframe.style.border = 'none';
  iframe.style.background = 'transparent';
  iframe.style.width = '80px';
  iframe.style.height = '80px';
  iframe.style.transition = 'width 0.25s cubic-bezier(0.16, 1, 0.3, 1), height 0.25s cubic-bezier(0.16, 1, 0.3, 1)';
  iframe.style.overflow = 'hidden';
  iframe.style.colorScheme = 'normal';

  // Listen to iframe postMessages to resize frame container dynamically
  window.addEventListener('message', function(event) {
    if (event.origin !== 'http://localhost:3000') return;

    if (event.data === 'widget_ready') {
      console.log("WHMCS AI Assistant widget initialized.");
    }
    
    // We can expand when the chat widget opens, but since widget handles its own trigger balloon,
    // we set container size to cover open panel sizes
    if (event.data === 'expand') {
      iframe.style.width = '420px';
      iframe.style.height = '620px';
    } else if (event.data === 'collapse') {
      iframe.style.width = '80px';
      iframe.style.height = '80px';
    }
  });

  // Since we embedded ChatWidget inside iframe, it starts in a collapsed state.
  // We size it to 80x80 to fit the floating trigger bubble without blocking page interactions.
  iframe.style.width = '80px';
  iframe.style.height = '80px';

  container.appendChild(iframe);
  document.body.appendChild(container);
})();
